import subprocess
from pathlib import Path
from app.core.logger import error_logger, app_logger

def extract_audio_to_wav(input_path: Path, output_path: Path) -> bool:
    """
    استخراج صوت و تبدیل استاندارد به فرمت 16kHz Mono WAV جهت تغذیه به Whisper
    """
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_path)
        ]
        app_logger.info(f"Extracting audio via FFmpeg: {input_path.name} -> {output_path.name}")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception as e:
        error_logger.error(f"FFmpeg extraction failed for {input_path}: {e}")
        return False