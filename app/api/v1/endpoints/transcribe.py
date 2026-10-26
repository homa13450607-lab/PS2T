import asyncio
import subprocess
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.job_manager import job_manager, JobStatus
from app.core.ffmpeg_utils import extract_audio_to_wav
from app.core.logger import app_logger, error_logger
from app.engines.manager import speech_engine_manager
from app.engines.schema import SegmentResult, SpeechResult
from app.dictionary.processor import DictionaryProcessor
from app.export.txt_exporter import TxtExporter
from app.export.word_exporter import WordExporter
from app.export.srt_exporter import SrtExporter

router = APIRouter()
dict_processor = DictionaryProcessor()
CHUNK_SECONDS = 300


def _format_time(seconds: float) -> str:
    total = max(0, int(seconds))
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def _split_audio(input_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = output_dir / "chunk_%04d.wav"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(input_path),
           "-f", "segment", "-segment_time", str(CHUNK_SECONDS), "-reset_timestamps", "1",
           "-c", "copy", str(pattern)]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    chunks = sorted(output_dir.glob("chunk_*.wav"))
    if not chunks:
        raise RuntimeError("FFmpeg did not create audio chunks")
    return chunks


async def process_job_background(job_id: str, input_file_path: Path):
    started_at = time.monotonic()
    wav_path = settings.temp_dir / f"{job_id}.wav"
    chunk_dir = settings.temp_dir / f"{job_id}_chunks"
    try:
        job_manager.update_progress(job_id, 5, stage="استخراج صوت")
        loop = asyncio.get_running_loop()
        extracted = await loop.run_in_executor(None, extract_audio_to_wav, input_file_path, wav_path)
        if not extracted:
            raise RuntimeError("استخراج صوت با FFmpeg ناموفق بود")

        job_manager.update_progress(job_id, 15, stage="تقسیم صوت به قطعات ۵ دقیقه‌ای")
        chunks = await loop.run_in_executor(None, _split_audio, wav_path, chunk_dir)
        initial_prompt = dict_processor.get_initial_prompt() if settings.dictionary_enabled else ""
        all_segments = []
        full_text_parts = []
        total = len(chunks)
        first_result = None
        for index, chunk in enumerate(chunks):
            pct = 20 + (70 * index / total)
            job_manager.update_progress(job_id, pct, stage=f"تبدیل قطعه {index + 1} از {total}")
            result = await speech_engine_manager.transcribe(str(chunk), initial_prompt)
            if first_result is None:
                first_result = result
            offset = index * CHUNK_SECONDS
            for seg in result.segments:
                start = float(seg.start_seconds) + offset
                end = float(seg.end_seconds) + offset
                text = dict_processor.apply_post_processing(seg.text) if settings.dictionary_enabled else seg.text
                all_segments.append(SegmentResult(
                    id=len(all_segments) + 1,
                    start_time=_format_time(start), end_time=_format_time(end),
                    start_seconds=start, end_seconds=end, text=text,
                    confidence=seg.confidence, is_low_confidence=seg.is_low_confidence
                ))
            text_part = result.full_text.strip()
            if settings.dictionary_enabled:
                text_part = dict_processor.apply_post_processing(text_part)
            if text_part:
                full_text_parts.append(text_part)
            chunk.unlink(missing_ok=True)

        if first_result is None:
            raise RuntimeError("هیچ قطعه‌ای برای پردازش تولید نشد")
        duration = max((s.end_seconds for s in all_segments), default=0.0)
        combined = SpeechResult(
            job_id=job_id,
            full_text="\n".join(full_text_parts),
            segments=all_segments,
            language=first_result.language,
            audio_duration_seconds=max(duration, first_result.audio_duration_seconds),
            processing_time_seconds=round(time.monotonic() - started_at, 2),
            engine_name=first_result.engine_name,
            model_name=first_result.model_name,
            device_used=first_result.device_used
        )
        job_manager.update_progress(job_id, 95, stage="آماده‌سازی خروجی")
        job_manager.complete_job(job_id, combined)
        app_logger.info("Job completed successfully: %s", job_id)
    except Exception as exc:
        error_logger.exception("Job processing failed %s: %s", job_id, exc)
        job_manager.fail_job(job_id, str(exc))
    finally:
        for path in [wav_path, input_file_path]:
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass
        if chunk_dir.exists():
            import shutil
            shutil.rmtree(chunk_dir, ignore_errors=True)


@router.post("/transcribe")
async def create_transcription_job(file: UploadFile = File(...)):
    filename = file.filename or "audio"
    allowed = {".mp3", ".wav", ".m4a", ".mp4", ".avi", ".mkv", ".flac", ".ogg", ".aac"}
    extension = Path(filename).suffix.lower()
    if extension not in allowed:
        raise HTTPException(status_code=400, detail="فرمت فایل پشتیبانی نمی‌شود")
    job_id = str(uuid.uuid4())
    saved_path = settings.uploads_dir / f"{job_id}{extension}"
    try:
        with saved_path.open("wb") as stream:
            while True:
                block = await file.read(1024 * 1024)
                if not block:
                    break
                stream.write(block)
    except Exception:
        saved_path.unlink(missing_ok=True)
        raise
    job = job_manager.create_job(job_id, filename)
    asyncio.create_task(process_job_background(job_id, saved_path))
    return {"job_id": job_id, "status": job.status, "filename": filename}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="وظیفه یافت نشد")
    return {
        "job_id": job.job_id, "filename": job.filename, "status": job.status.value,
        "progress": job.progress, "stage": job.stage, "result": job.result,
        "error": job.error_message
    }


@router.get("/dictionary")
async def get_dictionary():
    return {"entries": dict_processor.reload()}


@router.put("/dictionary")
async def update_dictionary(payload: dict):
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        raise HTTPException(status_code=400, detail="ساختار ورودی باید شامل entries باشد")
    try:
        saved = dict_processor.save_dictionary(entries)
        return {"saved": True, "count": len(saved), "entries": saved}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/download/{job_id}/{export_format}")
async def download_result(job_id: str, export_format: str):
    job = job_manager.get_job(job_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail="نتیجه پردازش در دسترس نیست")
    safe_name = Path(job.filename).stem
    if export_format == "txt":
        file_path = TxtExporter.export(job.result, safe_name)
        media_type = "text/plain; charset=utf-8"
    elif export_format == "docx":
        file_path = WordExporter.export(job.result, safe_name)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif export_format == "srt":
        file_path = SrtExporter.export(job.result, safe_name)
        media_type = "application/x-subrip; charset=utf-8"
    else:
        raise HTTPException(status_code=400, detail="فرمت خروجی نامعتبر است")
    return FileResponse(file_path, filename=f"{safe_name}.{export_format}", media_type=media_type)
