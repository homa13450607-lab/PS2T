import os
import yaml
from pathlib import Path
from typing import Dict, Any

class Settings:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.config_file = self.base_dir / config_path
        self._config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found at: {self.config_file}")
        with open(self.config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @property
    def app_name(self) -> str:
        return self._config.get("app", {}).get("name", "PS2T")

    @property
    def version(self) -> str:
        return self._config.get("app", {}).get("version", "1.0.0")

    @property
    def default_engine(self) -> str:
        return self._config.get("engine", {}).get("default_engine", "whisper")

    @property
    def default_model(self) -> str:
        return self._config.get("engine", {}).get("default_model", "large-v3")

    def get_path(self, key: str) -> Path:
        rel_path = self._config.get("paths", {}).get(key, key)
        full_path = self.base_dir / rel_path
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

settings = Settings()