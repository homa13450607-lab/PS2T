from pathlib import Path
from app.core.config import settings
from app.engines.schema import SpeechResult

def _srt_time(value: float) -> str:
    milliseconds = max(0, int(round(float(value) * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

class SrtExporter:
    @staticmethod
    def export(result: SpeechResult, filename: str) -> Path:
        output_dir = settings.get_path("outputs_dir") / "srt"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{filename}.srt"
        blocks = []
        for index, segment in enumerate(result.segments, 1):
            start = getattr(segment, "start_seconds", None)
            end = getattr(segment, "end_seconds", None)
            if start is None or end is None:
                continue
            text = str(segment.text).strip()
            if text:
                blocks.append(f"{index}\n{_srt_time(start)} --> {_srt_time(end)}\n{text}")
        path.write_text("\n\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")
        return path
