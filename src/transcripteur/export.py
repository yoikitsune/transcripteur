"""Gestion de l'export des transcriptions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from transcripteur.transcription import Segment, TranscriptionResult


def export_text(transcription: TranscriptionResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        for segment in transcription.segments:
            fp.write(segment.text.strip() + "\n")
    return output_path


def export_json(transcription: TranscriptionResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "language": transcription.language,
        "segments": [
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            }
            for segment in transcription.segments
        ],
        "raw": transcription.raw,
    }
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, ensure_ascii=False)
    return output_path


def export_srt(transcription: TranscriptionResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        for idx, segment in enumerate(transcription.segments, start=1):
            start_ts = _format_srt_timestamp(segment.start)
            end_ts = _format_srt_timestamp(segment.end)
            fp.write(f"{idx}\n{start_ts} --> {end_ts}\n{segment.text.strip()}\n\n")
    return output_path


def export_all(transcription: TranscriptionResult, output_dir: Path, basename: str) -> Iterable[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / basename
    yield export_text(transcription, base.with_suffix(".txt"))
    yield export_json(transcription, base.with_suffix(".json"))
    yield export_srt(transcription, base.with_suffix(".srt"))


def _format_srt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
