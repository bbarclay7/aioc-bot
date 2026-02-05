"""Speech-to-text via lightning-whisper-mlx (Apple Silicon optimized)."""

import tempfile
import logging

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class STT:
    def __init__(self, config: dict):
        self.model_name = config["stt"]["model"]
        self._model = None

    def _ensure_loaded(self):
        if self._model is not None:
            return
        from lightning_whisper_mlx import LightningWhisperMLX

        logger.info(f"Loading STT model: {self.model_name} ...")
        self._model = LightningWhisperMLX(
            model=self.model_name,
            batch_size=12,
            quant=None,
        )
        logger.info("STT model loaded.")

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """Transcribe a float32 numpy audio array to text."""
        self._ensure_loaded()

        # lightning-whisper-mlx expects a file path
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
            sf.write(f.name, audio, sample_rate)
            result = self._model.transcribe(f.name)

        text = result.get("text", "").strip()
        logger.info(f"Transcription: {text!r}")
        return text
