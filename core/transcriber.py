import os
import subprocess
import wave
import numpy as np
from faster_whisper import WhisperModel
from hardware.detector import HardwareDetector
from app.dictionary.processor import DictionaryProcessor

class OfflineTranscriber:
    def __init__(self, model_size="medium", device=None, compute_type=None):
        detector = HardwareDetector()
        optimal_config = detector.get_optimal_config()

        self.model_size = model_size
        self.device = device or optimal_config["device"]
        self.compute_type = compute_type or optimal_config["compute_type"]
        self.threads = optimal_config["threads"]
        self.beam_size = 5
        self.vad_filter = optimal_config["vad_filter"]

        self.dict_processor = DictionaryProcessor()

        print(f"[*] بارگذاری مدل Whisper ({self.model_size}) روی {self.device.upper()} با فرمت {self.compute_type}...")
        
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            cpu_threads=self.threads
        )

    def _load_audio_as_array(self, input_path):
        output_path = os.path.splitext(input_path)[0] + "_converted.wav"
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", output_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except Exception:
            output_path = input_path

        with wave.open(output_path, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        
        return audio_data

    def transcribe_audio(self, audio_path):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"فایل صوتی در مسیر {audio_path} یافت نشد.")

        print(f"[*] در حال آماده‌سازی و خواندن صوت: {audio_path}")
        audio_array = self._load_audio_as_array(audio_path)

        dynamic_prompt = self.dict_processor.get_initial_prompt()

        print(f"[*] شروع پردازش هوش مصنوعی با پرامپت اختصاصی...")
        
        segments, info = self.model.transcribe(
            audio_array,
            beam_size=self.beam_size,
            vad_filter=self.vad_filter,
            vad_parameters=dict(min_silence_duration_ms=500),
            language="fa",
            initial_prompt=f"متن زیر یک صوت فارسی است. کلمات تخصصی شامل: {dynamic_prompt}"
        )

        transcript_result = []
        for segment in segments:
            line = f"[{segment.start:.2f}s -> {segment.end:.2f}s]: {segment.text}"
            transcript_result.append(line)

        raw_text = "\n".join(transcript_result)
        final_text = self.dict_processor.apply_post_processing(raw_text)

        return final_text, info