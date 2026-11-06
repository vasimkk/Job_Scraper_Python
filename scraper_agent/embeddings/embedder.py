"""
Job Embedding Module using BAAI/bge-base-en-v1.5.

Converts scraped job details into 768-dimensional normalized vector embeddings
stored directly into PostgreSQL pgvector column `job_embedding vector(768)`.

Input Text Format:
  Combines Title + full Description up to 2,500 characters:
  f"{title}\\n\\n{description}"[:2500]
  ensuring complete domain, technology, and skill capture.
"""
import logging
from typing import List, Optional, Sequence, Union

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIMENSION = 768
MAX_INPUT_CHARS = 2500

_EMBEDDER_INSTANCE = None


class JobEmbedder:
    """Wrapper around SentenceTransformer with lazy model loading and batch processing."""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            import torch
            from sentence_transformers import SentenceTransformer

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading embedding model '{self.model_name}' on device '{device}'...")
            self._model = SentenceTransformer(self.model_name, device=device)
            logger.info(f"Embedding model '{self.model_name}' loaded successfully.")
        return self._model

    @staticmethod
    def prepare_input_text(title: str, description: Optional[str]) -> str:
        """
        Combines Title + full Description up to 2,500 characters
        to ensure complete domain and skill capture.
        """
        clean_title = (title or "").strip()
        clean_desc = (description or "").strip()
        combined = f"{clean_title}\n\n{clean_desc}".strip()
        return combined[:MAX_INPUT_CHARS]

    def embed_text(self, text: str) -> List[float]:
        """Generates a 768-dim normalized embedding for a single string."""
        model = self._ensure_model()
        vec = model.encode(text, normalize_embeddings=True)
        return [float(x) for x in vec]

    def embed_job(self, title: str, description: Optional[str]) -> List[float]:
        """Prepares text and generates embedding for a single job."""
        text = self.prepare_input_text(title, description)
        return self.embed_text(text)

    def embed_texts(
        self, texts: Sequence[str], batch_size: int = 64
    ) -> List[List[float]]:
        """
        Generates 768-dim normalized embeddings for a batch of strings.
        """
        if not texts:
            return []
        model = self._ensure_model()
        embeddings = model.encode(
            list(texts),
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [[float(x) for x in vec] for vec in embeddings]

    def embed_jobs(
        self, jobs: Sequence[Union[dict, object]], batch_size: int = 64
    ) -> List[List[float]]:
        """
        Generates embeddings for a batch of jobs (accepts objects with title/description attrs or dicts).
        """
        texts = []
        for j in jobs:
            if isinstance(j, dict):
                t = j.get("title", "")
                d = j.get("description", "")
            else:
                t = getattr(j, "title", "")
                d = getattr(j, "description", "")
            texts.append(self.prepare_input_text(t, d))

        return self.embed_texts(texts, batch_size=batch_size)

    @staticmethod
    def vector_to_pg_string(vec: Optional[Sequence[float]]) -> Optional[str]:
        """Formats a float vector into PostgreSQL pgvector literal: '[v1,v2,...,v768]'."""
        if vec is None:
            return None
        return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


def get_embedder() -> JobEmbedder:
    """Singleton getter for the global JobEmbedder."""
    global _EMBEDDER_INSTANCE
    if _EMBEDDER_INSTANCE is None:
        _EMBEDDER_INSTANCE = JobEmbedder()
    return _EMBEDDER_INSTANCE

