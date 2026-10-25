import json
import re
from pathlib import Path

class DictionaryProcessor:
    def __init__(self, dict_path: str = "custom_dict.json"):
        self.dict_file = Path(__file__).resolve().parent / dict_path
        self.dictionary = self._load_dictionary()

    def _load_dictionary(self) -> dict:
        default_dict = {
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

        # اگر فایل وجود نداشت، آن را با مقادیر پیش‌فرض می‌سازیم
        if not self.dict_file.exists():
            self.dict_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.dict_file, "w", encoding="utf-8") as f:
                json.dump(default_dict, f, ensure_ascii=False, indent=2)
            print(f"[*] دیکشنری پیش‌فرض ایجاد شد.")
            return default_dict
        
        # خواندن امن فایل با کنترل خطای ساختار JSON
        try:
            with open(self.dict_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[*] دیکشنری سفارشی با {len(data)} کلمه بارگذاری شد.")
                return data
        except Exception as e:
            print(f"[!] هشدار: فایل دیکشنری نامعتبر است ({e}). استفاده از دیکشنری پیش‌فرض ایمن...")
            return default_dict

    def get_initial_prompt(self) -> str:
        return ", ".join(self.dictionary.values())

    def apply_post_processing(self, text: str) -> str:
        processed_text = text
        for wrong, correct in self.dictionary.items():
            pattern = re.compile(re.escape(wrong), re.IGNORECASE)
            processed_text = pattern.sub(correct, processed_text)
        return processed_text