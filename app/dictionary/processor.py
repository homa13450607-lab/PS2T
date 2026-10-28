import json
import re
import threading
from pathlib import Path
from app.core.config import settings

class DictionaryProcessor:
    def __init__(self, dict_path=None):
        self.dict_file = Path(dict_path) if dict_path else settings.dictionary_path
        self._lock = threading.RLock()
        self.dictionary = self._load_dictionary()

    def _default_dictionary(self):
        return {
            "وی ام ور": "VMware",
            "زبیکس": "Zabbix",
            "گرافانا": "Grafana",
            "پرمتئوس": "Prometheus",
            "پایتون": "Python",
            "خوغان میشدو دروان میشدو": "ای کاش غوغا نمی‌شد و در وا نمی‌شد",
            "خوغان میشد": "غوغا می‌شد",
            "دروان میشد": "در وا می‌شد",
            "آتش دخیل چادور زهران میشدو": "آتش دخیل چادر زهرا نمی‌شد و"
        }

    def _load_dictionary(self):
        if not self.dict_file.exists():
            data = self._default_dictionary()
            self.save_dictionary(data)
            return data
        try:
            data = json.loads(self.dict_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
                raise ValueError("Dictionary must be a JSON object of string pairs")
            return data
        except (OSError, ValueError, json.JSONDecodeError):
            # Keep the existing file untouched; expose safe defaults until it is corrected.
            return self._default_dictionary()

    def reload(self):
        with self._lock:
            self.dictionary = self._load_dictionary()
            return dict(self.dictionary)

    def save_dictionary(self, data):
        if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) and k.strip() and v.strip() for k, v in data.items()):
            raise ValueError("Dictionary must contain non-empty string keys and values")
        self.dict_file.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.dict_file.with_suffix(self.dict_file.suffix + ".tmp")
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp_path.replace(self.dict_file)
        with self._lock:
            self.dictionary = dict(data)
        return dict(self.dictionary)

    def get_initial_prompt(self):
        with self._lock:
            return ", ".join(self.dictionary.values())

    def apply_post_processing(self, text):
        processed_text = text
        with self._lock:
            items = sorted(self.dictionary.items(), key=lambda item: len(item[0]), reverse=True)
        for wrong, correct in items:
            processed_text = re.sub(re.escape(wrong), lambda _match: correct, processed_text, flags=re.IGNORECASE)
        return processed_text
