###############################################################
# PS2T - Persian Speech To Text
#
# Speech Engine Manager
#
# Version: 2.2.0
#
###############################################################

from typing import Dict, Optional

from app.core.config import settings
from app.core.logger import (
    app_logger,
    error_logger
)

from app.engines.base import BaseSpeechEngine
from app.engines.schema import SpeechResult

from app.engines.whisper_adapter import WhisperEngineAdapter



class SpeechEngineManager:


    def __init__(self):

        self.engines: Dict[str, BaseSpeechEngine] = {}

        self.active_engine_name: Optional[str] = None

        self.active_engine: Optional[
            BaseSpeechEngine
        ] = None

        self.loaded = False

        self._register_engines()



    ###########################################################
    # Register Engines
    ###########################################################

    def _register_engines(self):

        self.engines["whisper"] = WhisperEngineAdapter()

        app_logger.info(
            "Speech engines registered successfully."
        )



    ###########################################################
    # Select Engine
    ###########################################################

    def get_engine(
            self,
            engine_name: Optional[str] = None
    ) -> BaseSpeechEngine:


        if engine_name is None:
            engine_name = settings.default_engine



        if engine_name not in self.engines:

            raise ValueError(
                f"Speech engine '{engine_name}' not available"
            )



        if self.active_engine_name != engine_name:

            self.active_engine_name = engine_name

            self.active_engine = (
                self.engines[engine_name]
            )

            self.loaded = False


            app_logger.info(
                f"Active speech engine changed: {engine_name}"
            )


        return self.active_engine



    ###########################################################
    # Load Engine Model
    ###########################################################

    async def load_engine(self):


        engine = self.get_engine()



        if self.loaded:

            app_logger.info(
                "Speech model already loaded."
            )

            return



        try:

            app_logger.info(
                "Loading speech model..."
            )


            await engine.load_model(

                model_name=settings.default_model,

                device=settings.device

            )


            self.loaded = True


            app_logger.info(
                "Speech model loaded successfully."
            )



        except Exception as e:


            self.loaded = False


            error_logger.exception(
                f"Model loading failed: {e}"
            )


            raise e



    ###########################################################
    # Transcribe
    ###########################################################

    async def transcribe(

            self,

            audio_path: str,

            initial_prompt: str = ""

    ) -> SpeechResult:


        try:


            await self.load_engine()


            engine = self.get_engine()



            result = await engine.transcribe(

                audio_path,

                initial_prompt

            )


            return result



        except Exception as e:


            error_logger.exception(
                f"Speech Engine Manager error: {e}"
            )


            raise e




###############################################################
# Singleton Instance
###############################################################

speech_engine_manager = SpeechEngineManager()