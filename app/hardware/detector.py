import os
import psutil
import torch

try:
    import GPUtil
except ImportError:
    GPUtil = None

class HardwareDetector:
    def __init__(self):
        self.cpu_cores_logical = psutil.cpu_count(logical=True)
        self.cpu_cores_physical = psutil.cpu_count(logical=False)
        self.total_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        self.available_ram_gb = round(psutil.virtual_memory().available / (1024 ** 3), 2)
        self.gpu_info = self._detect_gpu()

    def _detect_gpu(self):
        gpu_data = {
            "has_gpu": False,
            "name": "N/A",
            "vram_total_mb": 0,
            "vram_free_mb": 0,
            "cuda_available": torch.cuda.is_available()
        }

        if torch.cuda.is_available():
            gpu_data["has_gpu"] = True
            gpu_data["name"] = torch.cuda.get_device_name(0)
            
            if GPUtil:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu_data["vram_total_mb"] = gpus[0].memoryTotal
                        gpu_data["vram_free_mb"] = gpus[0].memoryFree
                except Exception:
                    pass
            
            # پشتیبانی جایگزین در صورت عدم دسترسی به GPUtil
            if gpu_data["vram_total_mb"] == 0:
                gpu_data["vram_total_mb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 2))
                gpu_data["vram_free_mb"] = gpu_data["vram_total_mb"] # تقریبی

        return gpu_data

    def get_optimal_config(self):
        """
        محاسبه پیکربندی بهینه برای Whisper بر اساس توان سخت‌افزاری
        """
        config = {
            "device": "cpu",
            "compute_type": "int8",
            "model_size": "medium",
            "beam_size": 3,
            "threads": max(1, self.cpu_cores_physical - 1) if self.cpu_cores_physical else 4,
            "vad_filter": True,
            "recommendation_reason": ""
        }

        # اگر کارت گرافیک NVIDIA کشف شد
        if self.gpu_info["has_gpu"]:
            vram = self.gpu_info["vram_total_mb"]
            config["device"] = "cuda"
            
            if vram >= 10000:  # بیشتر از 10 گیگ VRAM (مانند RTX 3080/4080 یا T4/A100)
                config["compute_type"] = "float16"
                config["model_size"] = "large-v3"
                config["beam_size"] = 5
                config["recommendation_reason"] = f"کارت گرافیک قوی ({self.gpu_info['name']}) با VRAM بالا کشف شد. بالاترین دقت و سرعت فعال شد."
            elif vram >= 6000:  # بین 6 تا 10 گیگ VRAM (مانند RTX 2060/3060)
                config["compute_type"] = "float16"
                config["model_size"] = "medium"
                config["beam_size"] = 5
                config["recommendation_reason"] = f"کارت گرافیک مناسب ({self.gpu_info['name']}) کشف شد. حالت کارآمد float16 انتخاب شد."
            elif vram >= 3500:  # بین 3.5 تا 6 گیگ VRAM (کارت‌های متوسط/لپ‌تاپی)
                config["compute_type"] = "int8"
                config["model_size"] = "medium"
                config["beam_size"] = 3
                config["recommendation_reason"] = f"حافظه کارت گرافیک محدود است ({vram}MB). حالت بهینه شده int8 روی CUDA انتخاب شد."
            else:  # کمتر از 3.5 گیگ VRAM
                config["compute_type"] = "int8"
                config["model_size"] = "small"
                config["beam_size"] = 3
                config["recommendation_reason"] = "حافظه VRAM پایین است. برای جلوگیری از خطای Out of Memory مدل small انتخاب شد."
        else:
            # پردازش روی CPU
            if self.available_ram_gb >= 12 and self.cpu_cores_logical >= 8:
                config["model_size"] = "medium"
                config["compute_type"] = "int8"
                config["recommendation_reason"] = "پردازش روی CPU قدرتمند به همراه RAM کافی انجام می‌شود."
            else:
                config["model_size"] = "small"
                config["compute_type"] = "int8"
                config["recommendation_reason"] = "پردازش روی CPU پایه انجام می‌شود. جهت حفظ سرعت، مدل سبک انتخاب شد."

        return config

    def get_full_report(self):
        return {
            "hardware": {
                "cpu_physical_cores": self.cpu_cores_physical,
                "cpu_logical_cores": self.cpu_cores_logical,
                "ram_total_gb": self.total_ram_gb,
                "ram_available_gb": self.available_ram_gb,
                "gpu": self.gpu_info
            },
            "suggested_config": self.get_optimal_config()
        }