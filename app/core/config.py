from pathlib import Path
from typing import Any, Dict
import yaml


class Settings:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.base_dir = Path(__file__).resolve().parents[2]
        self.config_file = self.base_dir / config_path
        with self.config_file.open("r", encoding="utf-8") as stream:
            self._config: Dict[str, Any] = yaml.safe_load(stream) or {}

    def get(self, section: str, key: str, default=None):
        return self._config.get(section, {}).get(key, default)

    @property
    def app_name(self): return self.get("app", "name", "PS2T")
    @property
    def version(self): return self.get("app", "version", "1.0.0")
    @property
    def host(self): return self.get("app", "host", "127.0.0.1")
    @property
    def port(self): return self.get("app", "port", 8000)
    @property
    def default_engine(self): return self.get("engine", "default_engine", "whisper")
    @property
    def default_model(self): return self.get("engine", "default_model", "medium")
    @property
    def default_language(self): return self.get("engine", "default_language", "fa")
    @property
    def model_path(self): return self.base_dir / self.get("engine", "model_path", "models/faster-whisper-medium")
    @property
    def device(self): return self.get("engine", "device", "auto")
    @property
    def whisper_config(self): return self._config.get("engine", {}).get("whisper", {})
    @property
    def cpu_compute_type(self): return self.whisper_config.get("cpu_compute_type", "int8")
    @property
    def gpu_compute_type(self): return self.whisper_config.get("gpu_compute_type", "float16")
    def get_path(self, key: str) -> Path:
        relative = self._config.get("paths", {}).get(key, key)
        path = self.base_dir / relative
        path.mkdir(parents=True, exist_ok=True)
        return path
    @property
    def models_dir(self): return self.get_path("models_dir")
    @property
    def uploads_dir(self): return self.get_path("uploads_dir")
    @property
    def outputs_dir(self): return self.get_path("outputs_dir")
    @property
    def logs_dir(self): return self.get_path("logs_dir")
    @property
    def temp_dir(self): return self.get_path("temp_dir")
    @property
    def max_file_size_mb(self): return self.get("upload", "max_file_size_mb", 2048)
    @property
    def max_parallel_jobs(self): return self.get("processing", "max_parallel_jobs", 1)
    @property
    def cleanup_temp_files(self): return self.get("processing", "cleanup_temp_files", True)
    @property
    def dictionary_enabled(self): return self.get("dictionary", "enabled", True)
    @property
    def punctuation_enabled(self): return self.get("punctuation", "enabled", True)
    @property
    def punctuation_model_path(self): return self.base_dir / self.get("punctuation", "model_path", "models/persian-punctuation")
    @property
    def dictionary_path(self): return self.base_dir / self.get("dictionary", "path", "app/dictionary/custom_dict.json")


settings = Settings()
