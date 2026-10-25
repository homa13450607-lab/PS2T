from pydantic import BaseModel
from typing import List, Optional

class SegmentResult(BaseModel):
    id: int
    start_time: str            # HH:MM:SS
    end_time: str              # HH:MM:SS
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float          # 0 to 100
    is_low_confidence: bool    # True if confidence < 70%

class SpeechResult(BaseModel):
    job_id: str
    full_text: str
    segments: List[SegmentResult]
    language: str = "fa"
    audio_duration_seconds: float
    processing_time_seconds: float
    engine_name: str
    model_name: str
    device_used: str