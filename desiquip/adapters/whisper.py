"""Transcriber adapter: faster-whisper (Whisper models, CTranslate2 runtime; CUDA on the GPU laptop)."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from ..domain.models import Word

log = logging.getLogger(__name__)


def _register_cuda_dlls() -> None:
    """pip-installed nvidia-cublas/cudnn wheels put DLLs in site-packages/nvidia/*/bin on Windows."""
    if sys.platform != "win32":
        return
    import site

    for base in site.getsitepackages():
        for lib in ("cublas", "cudnn"):
            d = Path(base) / "nvidia" / lib / "bin"
            if d.is_dir():
                os.add_dll_directory(str(d))
                os.environ["PATH"] = f"{d}{os.pathsep}{os.environ.get('PATH', '')}"


class FasterWhisperTranscriber:
    def __init__(self, model: str, device: str = "auto") -> None:
        self.model_name, self.device = model, device
        self._model = None

    def _load(self):
        from faster_whisper import WhisperModel

        if self.device in ("auto", "cuda"):
            _register_cuda_dlls()
            try:
                return WhisperModel(self.model_name, device="cuda", compute_type="int8_float16")
            except Exception as e:  # noqa: BLE001
                if self.device == "cuda":
                    raise
                log.warning("CUDA unavailable (%s); using CPU with model 'small'", e)
                return WhisperModel("small", device="cpu", compute_type="int8")
        return WhisperModel(self.model_name, device="cpu", compute_type="int8")

    def transcribe(self, audio: Path, language: str) -> list[Word]:
        if self._model is None:
            self._model = self._load()
        segments, _ = self._model.transcribe(str(audio), language=language,
                                             word_timestamps=True, vad_filter=True)
        return [Word(text=w.word.strip(), start=round(w.start, 3), end=round(w.end, 3))
                for seg in segments for w in (seg.words or []) if w.word.strip()]
