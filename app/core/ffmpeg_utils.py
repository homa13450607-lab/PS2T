import subprocess
from pathlib import Path
from app.core.logger import error_logger, app_logger

def extract_audio_to_wav(input_path: Path, output_path: Path) -> bool:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["ffmpeg", "-y", "-i", str(input_path), "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(output_path)]
        app_logger.info("Extracting audio: %s", input_path.name)
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception:
        error_logger.exception("FFmpeg extraction failed for %s", input_path)
        return False
