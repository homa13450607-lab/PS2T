from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.core.config import settings
from app.core.logger import app_logger
from app.hardware.detector import HardwareDetector
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.app_name,
    version=settings.version
)

app.include_router(api_router, prefix="/api/v1")

# ایجاد و Mount پوشه UI و Static
ui_static_dir = settings.base_dir / "app" / "ui" / "static"
ui_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=ui_static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    template_path = settings.base_dir / "app" / "ui" / "templates" / "index.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>واسط کاربری آماده نشده است. لطفاً فایل index.html را قرار دهید.</h1>"

@app.get("/api/v1/hardware/status")
async def get_hardware_status():
    return HardwareDetector.get_system_info()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)