###############################################################
# PS2T - Persian Speech To Text
#
# Whisper Engine Adapter
#
# Version: 2.1.0
#
# Responsibility:
#
#   - Faster Whisper Engine Management
#   - Offline Local Model Loading
#   - Audio Transcription
#   - SpeechResult Generation
#
###############################################################


import math
import time


from datetime import timedelta
from typing import Optional


from faster_whisper import WhisperModel


from app.engines.base import BaseSpeechEngine

from app.engines.schema import (
    SpeechResult,
    SegmentResult
)


from app.core.config import settings

from app.core.logger import (
    app_logger,
    error_logger
)





###############################################################
# Timestamp Formatter
###############################################################


def format_timestamp(seconds: float) -> str:


    total_seconds = int(seconds)


    hours = (
        total_seconds // 3600
    )


    minutes = (
        total_seconds % 3600
    ) // 60


    secs = (
        total_seconds % 60
    )


    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d}"
    )







###############################################################
# Whisper Adapter
###############################################################


class WhisperEngineAdapter(BaseSpeechEngine):


    def __init__(self):


        self.model: Optional[
            WhisperModel
        ] = None



        self.current_model_name = None


        self.current_device = None





    ###########################################################
    # Load Model
    ###########################################################


    async def load_model(
        self,
        model_name: str = None,
        device: str = None
    ) -> None:



        if model_name is None:

            model_name = (
                settings.default_model
            )



        if device is None:

            device = (
                settings.device
            )





        #######################################################
        # Detect Device
        #######################################################


        if device == "auto":


            try:

                import torch


                if torch.cuda.is_available():

                    device = "cuda"


                else:

                    device = "cpu"



            except Exception:


                device = "cpu"






        #######################################################
        # Avoid Reload
        #######################################################


        if (

            self.model

            and

            self.current_model_name == model_name

            and

            self.current_device == device

        ):


            app_logger.info(
                "Whisper model already loaded."
            )


            return






        #######################################################
        # Compute Type
        #######################################################


        if device == "cuda":


            compute_type = (
                settings.gpu_compute_type
            )


        else:


            compute_type = (
                settings.cpu_compute_type
            )






        #######################################################
        # Offline Local Model
        #######################################################


        model_path = (
            settings.model_path
        )



        if not model_path.exists():


            raise FileNotFoundError(

                f"Offline Whisper model not found: {model_path}"

            )







        app_logger.info(

            "Loading Faster-Whisper Offline Model"

            f" | Path={model_path}"

            f" | Device={device}"

            f" | Compute={compute_type}"

        )







        try:


            self.model = WhisperModel(


                str(model_path),


                device=device,


                compute_type=compute_type


            )



            self.current_model_name = (
                model_name
            )


            self.current_device = (
                device
            )



            app_logger.info(

                "Faster-Whisper model loaded successfully."

            )






        except Exception as e:



            error_logger.exception(

                f"Failed loading Whisper model: {e}"

            )


            self.model = None


            raise e







    ###########################################################
    # Transcribe
    ###########################################################


    async def transcribe(

        self,

        audio_path: str,

        initial_prompt: str = ""

    ) -> SpeechResult:



        if self.model is None:


            await self.load_model()






        start_time = time.time()






        whisper_cfg = (
            settings.whisper_config
        )






        segments_generator, info = (

            self.model.transcribe(


                audio_path,


                language=(

                    settings.default_language

                ),



                initial_prompt=initial_prompt,



                beam_size=(

                    whisper_cfg.get(
                        "beam_size",
                        5
                    )

                ),



                vad_filter=(

                    whisper_cfg.get(
                        "vad_filter",
                        True
                    )

                )


            )

        )







        segments = []


        texts = []



        segment_id = 1






        for seg in segments_generator:




            confidence = (

                min(

                    100.0,


                    max(

                        0.0,


                        math.exp(
                            seg.avg_logprob
                        )

                        *

                        100

                    )

                )

            )





            segment = SegmentResult(



                id=segment_id,



                start_time=format_timestamp(
                    seg.start
                ),



                end_time=format_timestamp(
                    seg.end
                ),



                start_seconds=round(
                    seg.start,
                    2
                ),



                end_seconds=round(
                    seg.end,
                    2
                ),



                text=seg.text.strip(),



                confidence=round(
                    confidence,
                    1
                ),



                is_low_confidence=(

                    confidence < 70

                )

            )





            segments.append(segment)



            texts.append(
                seg.text.strip()
            )



            segment_id += 1







        elapsed = (
            time.time()
            -
            start_time
        )








        return SpeechResult(



            job_id="",



            full_text=(

                " ".join(texts)

            ),



            segments=segments,



            language=info.language,



            audio_duration_seconds=round(

                info.duration,

                2

            ),



            processing_time_seconds=round(

                elapsed,

                2

            ),



            engine_name="Faster-Whisper",



            model_name=(

                self.current_model_name

            ),



            device_used=(

                self.current_device.upper()

            )

        )