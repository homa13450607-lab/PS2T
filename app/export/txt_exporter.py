from pathlib import Path
from app.engines.schema import SpeechResult
from app.core.config import settings

class TxtExporter:
    @staticmethod
    def export(result: SpeechResult, filename: str) -> Path:
        output_dir = settings.get_path("outputs_dir") / "txt"
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"{filename}.txt"

        lines = [
            f"عنوان فایل: {filename}",
            f"مدت زمان صوت: {result.audio_duration_seconds} ثانیه",
            f"زمان پردازش: {result.processing_time_seconds} ثانیه",
            f"موتور پردازش: {result.engine_name} ({result.model_name}) - {result.device_used}",
            "=" * 60,
            "\n[متن کامل]\n",
            result.full_text,
            "\n" + "=" * 60,
            "\n[بخش‌های زمان‌بندی‌شده]\n"
        ]

        for seg in result.segments:
            conf_str = f" ⚠️ [اطمینان پایین: {seg.confidence}%]" if seg.is_low_confidence else f" [{seg.confidence}%]"
            lines.append(f"[{seg.start_time} --> {seg.end_time}]{conf_str} {seg.text}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return file_path