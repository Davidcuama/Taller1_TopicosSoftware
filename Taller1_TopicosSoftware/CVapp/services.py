"""
Service classes and strategies for the CVapp.

This module defines abstractions for extracting text from uploaded files
and generating embeddings.  By encapsulating these behaviours in
Strategy objects and services we decouple the views from concrete
implementations (Dependency Inversion) and enable easy extension or
replacement (Strategy pattern).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO
from typing import Optional
import numpy as np

try:
    from PyPDF2 import PdfReader  # type: ignore
except ImportError:  # pragma: no cover
    PdfReader = None  # type: ignore

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


class FileExtractionStrategy(ABC):
    """Abstract base class for strategies that extract text from uploaded files."""

    @abstractmethod
    def extract(self, file) -> str:
        """Return the extracted text from the given file object."""


class PdfExtractionStrategy(FileExtractionStrategy):
    """Extract text from PDF files using PyPDF2."""

    def extract(self, file) -> str:
        if not PdfReader:
            raise RuntimeError("PyPDF2 is not installed")
        reader = PdfReader(file)  # type: ignore[call-arg]
        return "".join(page.extract_text() or "" for page in reader.pages)


class TextExtractionStrategy(FileExtractionStrategy):
    """Extract text from plain text or binary files by decoding as UTF‑8."""

    def extract(self, file) -> str:
        data = file.read()
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return str(data)


class EmbeddingService(ABC):
    """Abstract base class for services that compute embeddings for text."""

    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        """Return the embedding of the given text as a numpy array."""


class OpenAIEmbeddingService(EmbeddingService):
    """Embedding service backed by the OpenAI API."""

    def __init__(self, api_key: Optional[str]) -> None:
        if not OpenAI:
            raise RuntimeError("openai package is not installed")
        self.client = OpenAI(api_key=api_key)

    def embed(self, text: str) -> np.ndarray:
        response = self.client.embeddings.create(input=[text], model="text-embedding-3-small")
        return np.array(response.data[0].embedding, dtype=np.float32)


class MockEmbeddingService(EmbeddingService):
    """Mock embedding service returning random embeddings (for testing)."""

    def __init__(self, dimension: int = 1536) -> None:
        self.dimension = dimension

    def embed(self, text: str) -> np.ndarray:
        # For testing purposes we generate a reproducible vector based on the text
        rng = np.random.default_rng(abs(hash(text)) % (2 ** 32))
        return rng.random(self.dimension, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute the cosine similarity between two vectors."""
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)