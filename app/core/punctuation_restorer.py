"""Optional offline Persian punctuation restoration.

Only punctuation is inserted; the original recognized characters are not rewritten.
The model is loaded from a local directory and never downloaded at runtime.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("ps2t.punctuation")


class PersianPunctuationRestorer:
    def __init__(self) -> None:
        self._tokenizer = None
        self._model = None
        self._torch = None
        self._device = "cpu"
        self._load_attempted = False
        self._warned = False

    def _load(self) -> bool:
        if self._model is not None and self._tokenizer is not None:
            return True
        if self._load_attempted:
            return False
        self._load_attempted = True

        if not settings.punctuation_enabled:
            return False

        model_dir: Path = settings.punctuation_model_path
        required = ("config.json", "tokenizer_config.json", "tokenizer.json")
        has_weights = model_dir.is_dir() and any(
            (model_dir / name).is_file()
            for name in ("model.safetensors", "pytorch_model.bin")
        )
        if not model_dir.is_dir() or not all((model_dir / name).is_file() for name in required) or not has_weights:
            self._warn_once(
                "Persian punctuation model not found at %s; keeping transcript text unchanged. "
                "See config/settings.yaml and the model setup instructions.",
                model_dir,
            )
            return False

        try:
            import torch
            from transformers import AutoModelForTokenClassification, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(
                str(model_dir), local_files_only=True, use_fast=True
            )
            self._model = AutoModelForTokenClassification.from_pretrained(
                str(model_dir), local_files_only=True
            )
            # CPU is the safe default so punctuation restoration does not compete
            # with faster-whisper for GPU memory.
            self._device = "cpu"
            self._torch = torch
            self._model.to(self._device)
            self._model.eval()
            logger.info("Offline Persian punctuation model loaded from %s", model_dir)
            return True
        except Exception:
            self._tokenizer = None
            self._model = None
            self._torch = None
            logger.exception(
                "Could not load local Persian punctuation model from %s; "
                "transcription will continue without model punctuation.",
                model_dir,
            )
            return False

    def _warn_once(self, message: str, *args) -> None:
        if not self._warned:
            logger.warning(message, *args)
            self._warned = True

    @staticmethod
    def _punctuation_for(label: str) -> Optional[str]:
        name = str(label).upper().split(".")[-1]
        return {
            "COMMA": "،",
            "QUESTION": "؟",
            "PERIOD": ".",
            "COLON": ":",
        }.get(name)

    def _restore_paragraph(self, text: str) -> str:
        if not text.strip() or not self._load():
            return text

        torch = self._torch
        tokenizer = self._tokenizer
        model = self._model
        # Paragraphs from text_formatter are deliberately short enough for this
        # model's 512-token input window in normal use.
        encoded = tokenizer(
            text,
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True,
            max_length=510,
            add_special_tokens=True,
        )
        offsets = encoded.pop("offset_mapping")[0].tolist()
        model_inputs = {key: value.to(self._device) for key, value in encoded.items()}

        with torch.inference_mode():
            logits = model(**model_inputs).logits[0]
            predictions = logits.argmax(dim=-1).tolist()

        id2label = getattr(model.config, "id2label", {}) or {}
        insertions = []
        existing_marks = "،؛؟.!:"

        for (start, end), pred_id in zip(offsets, predictions):
            if end <= start or start < 0 or end > len(text):
                continue
            # Only place marks after the end of an original word, not inside a
            # multi-piece tokenizer word.
            if end < len(text) and not text[end].isspace():
                continue
            label = id2label.get(pred_id, id2label.get(str(pred_id), str(pred_id)))
            mark = self._punctuation_for(label)
            if not mark:
                continue
            if end > 0 and text[end - 1] in existing_marks:
                continue
            if end < len(text) and text[end] in existing_marks:
                continue
            insertions.append((end, mark))

        # Apply from right to left so character offsets remain valid.
        result = text
        seen_positions = set()
        for position, mark in sorted(insertions, reverse=True):
            if position in seen_positions:
                continue
            result = result[:position] + mark + result[position:]
            seen_positions.add(position)
        return result

    def restore(self, text: str) -> str:
        """Restore punctuation paragraph-by-paragraph while preserving all words."""
        if not text or not settings.punctuation_enabled:
            return text
        paragraphs = text.split("\n\n")
        return "\n\n".join(self._restore_paragraph(paragraph) for paragraph in paragraphs)


punctuation_restorer = PersianPunctuationRestorer()
