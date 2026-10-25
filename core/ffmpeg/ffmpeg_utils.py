###############################################################
# PS2T - Persian Speech To Text
#
# FFmpeg Utilities
#
# Version : 2.1.0
#
###############################################################

import subprocess

from pathlib import Path

from app.core.logger import (
    app_logger,
    error_logger
)

from app.core.config import settings


###############################################################
# Locate FFmpeg
###############################################################

BASE_DIR = settings.base_dir

FFMPEG_PATH = (
    BASE_DIR
    / "tools"
    / "ffmpeg"
    / "ffmpeg.exe"
)


###############################################################
# Extract Audio
###############################################################

def extract_audio_to_wav(
    input_path: Path,
    output_path: Path
) -> bool:

    """
    Convert Audio/Video to
    16KHz Mono WAV
    """


    if not FFMPEG_PATH.exists():

        error_logger.error(
            f"FFmpeg not found: {FFMPEG_PATH}"
        )

        return False


    cmd = [

        str(FFMPEG_PATH),

        "-y",

        "-i",

        str(input_path),

        "-vn",

        "-acodec",

        "pcm_s16le",

        "-ar",

        "16000",

        "-ac",

        "1",

        str(output_path)

    ]


    app_logger.info(

        f"Extracting audio via FFmpeg: "

        f"{input_path.name}"

        f" -> "

        f"{output_path.name}"

    )


    try:

        subprocess.run(

            cmd,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            check=True

        )

        return True


    except subprocess.CalledProcessError as e:

        error_logger.error(

            e.stderr.decode(

                errors="ignore"

            )

        )

        return False


    except Exception as e:

        error_logger.exception(e)

        return False