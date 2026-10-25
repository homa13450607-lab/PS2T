import uuid
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.job_manager import job_manager, JobStatus
from app.core.ffmpeg_utils import extract_audio_to_wav
from app.dictionary.processor import DictionaryProcessor
from app.engines.whisper_adapter import WhisperEngineAdapter
from app.export.txt_exporter import TxtExporter
from app.export.word_exporter import WordExporter

router = APIRouter()
whisper_adapter = WhisperEngineAdapter()
dict_processor = DictionaryProcessor()

async def process_job_background(job_id: str, input_file_path: Path):
    try:
        job_manager.update_progress(job_id, 10.0, JobStatus.PROCESSING)
        wav_path = settings.get_path("uploads_dir") / f"{job_id}.wav"

        # 1. استخراج صوت با FFmpeg
        loop = asyncio.get_event_loop()
        extracted = await loop.run_in_executor(None, extract_audio_to_wav, input_file_path, wav_path)
        if not extracted:
            job_manager.fail_job(job_id, "خطا در استخراج فایل صوتی با FFmpeg")
            return

        job_manager.update_progress(job_id, 30.0, JobStatus.PROCESSING)

        # 2. دریافت Prompt اولیه از واژه‌نامه
        initial_prompt = dict_processor.get_initial_prompt()

        # 3. پردازش تبدیل گفتار به متن
        result = await whisper_adapter.transcribe(str(wav_path), initial_prompt=initial_prompt)
        result.job_id = job_id

        # 4. اعمال Post-processing واژه‌نامه سفارشی
        result.full_text = dict_processor.apply_post_processing(result.full_text)
        for seg in result.segments:
            seg.text = dict_processor.apply_post_processing(seg.text)

        # 5. تکمیل Job
        job_manager.complete_job(job_id, result)

        # پاک‌سازی فایل موقت WAV
        if wav_path.exists():
            wav_path.unlink()

    except Exception as e:
        job_manager.fail_job(job_id, str(e))

@router.post("/transcribe")
async def create_transcription_job(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    upload_dir = settings.get_path("uploads_dir")
    file_ext = Path(file.filename).suffix
    saved_file_path = upload_dir / f"{job_id}{file_ext}"

    with open(saved_file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    job = job_manager.create_job(job_id, file.filename)
    asyncio.create_task(process_job_background(job_id, saved_file_path))

    return {"job_id": job_id, "status": job.status, "filename": file.filename}

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job یافت نشد")
    return {
        "job_id": job.job_id,
        "filename": job.filename,
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error_message
    }

@router.get("/download/{job_id}/{export_format}")
async def download_result(job_id: str, export_format: str):
    job = job_manager.get_job(job_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail="نتیجه پردازش یافت نشد")

    safe_name = Path(job.filename).stem
    if export_format == "txt":
        file_path = TxtExporter.export(job.result, safe_name)
        return FileResponse(file_path, filename=f"{safe_name}.txt", media_type="text/plain; charset=utf-8")
    elif export_format == "docx":
        file_path = WordExporter.export(job.result, safe_name)
        return FileResponse(file_path, filename=f"{safe_name}.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        raise HTTPException(status_code=400, detail="فرمت خروجی نامعتبر است")