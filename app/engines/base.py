from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any
from app.engines.schema import SpeechResult

class BaseSpeechEngine(ABC):
    
    @abstractmethod
    async def load_model(self, model_name: str, device: str) -> None:
        """بارگذاری مدل هوش مصنوعی در حافظه"""
        pass

    @abstractmethod
    async def transcribe(
        self, audio_path: str, initial_prompt: str = ""
    ) -> SpeechResult:
        """پردازش فایل صوتی و ارجاع شیء استاندارد SpeechResult"""
        pass