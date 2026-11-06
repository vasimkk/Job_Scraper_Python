"""Embedding module for job vectorization using BAAI/bge-base-en-v1.5."""
from scraper_agent.embeddings.embedder import JobEmbedder, get_embedder

__all__ = ["JobEmbedder", "get_embedder"]
