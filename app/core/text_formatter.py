"""Conservative paragraph formatting for speech transcripts.

This module preserves recognized words. It only normalizes whitespace and groups
existing timestamped segments into readable paragraphs using pauses and length
limits; it does not guess or rewrite punctuation.
"""
from typing import Iterable, Any


PARAGRAPH_PAUSE_SECONDS = 1.35
MAX_PARAGRAPH_CHARS = 420
MAX_PARAGRAPH_WORDS = 75


def _value(segment: Any, name: str, default=None):
    if isinstance(segment, dict):
        return segment.get(name, default)
    return getattr(segment, name, default)


def format_segments(segments: Iterable[Any]) -> str:
    """Build readable paragraphs from timestamped segments without changing words."""
    paragraphs = []
    current_parts = []
    current_chars = 0
    current_words = 0
    previous_end = None

    for segment in segments:
        text = " ".join(str(_value(segment, "text", "") or "").split())
        if not text:
            continue

        start = _value(segment, "start_seconds")
        end = _value(segment, "end_seconds")
        try:
            start = float(start) if start is not None else None
            end = float(end) if end is not None else None
        except (TypeError, ValueError):
            start = end = None

        gap = start - previous_end if start is not None and previous_end is not None else 0.0
        next_chars = current_chars + (1 if current_parts else 0) + len(text)
        next_words = current_words + len(text.split())

        should_break = bool(current_parts) and (
            gap >= PARAGRAPH_PAUSE_SECONDS
            or current_chars >= MAX_PARAGRAPH_CHARS
            or current_words >= MAX_PARAGRAPH_WORDS
            or next_chars > MAX_PARAGRAPH_CHARS
            or next_words > MAX_PARAGRAPH_WORDS
        )
        if should_break:
            paragraphs.append(" ".join(current_parts))
            current_parts = []
            current_chars = 0
            current_words = 0

        current_parts.append(text)
        current_chars += (1 if current_chars else 0) + len(text)
        current_words += len(text.split())
        if end is not None:
            previous_end = end

    if current_parts:
        paragraphs.append(" ".join(current_parts))

    return "\n\n".join(paragraphs)
