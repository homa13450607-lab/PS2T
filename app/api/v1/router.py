from fastapi import APIRouter
from app.api.v1.endpoints import transcribe

api_router = APIRouter()
api_router.include_router(transcribe.router, tags=["Transcription"])