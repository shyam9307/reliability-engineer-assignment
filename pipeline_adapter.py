
from abc import ABC, abstractmethod
import random
import time


class PipelineAdapter(ABC):
    """Interface for interchangeable STT → LLM → TTS implementations."""

    @abstractmethod
    def process(self, audio_ref: str) -> dict:
        """Process audio and return transcript and response audio reference."""
        raise NotImplementedError


class MockPipelineAdapter(PipelineAdapter):
    """Synthetic pipeline for local development and reliability testing."""

    def process(self, audio_ref: str) -> dict:
        delay_ms = random.lognormvariate(5.7, 0.35)
        time.sleep(delay_ms / 1000)

        # Each individual dependency attempt has a 20% failure probability.
        if random.random() < 0.20:
            raise TimeoutError("downstream_timeout")

        return {
            "transcript": "synthetic transcript",
            "response_audio_ref": "synthetic",
        }
