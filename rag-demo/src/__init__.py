"""
RAG Demo System

A demonstration of Retrieval-Augmented Generation (RAG) system
with vector database, embedding models, and hybrid retrieval.
"""

__version__ = "1.0.0"
__author__ = "Hermes Knowledge System"

from .rag_engine import RAGEngine, Chunk
from .document_processor import DocumentProcessor, Document
from .llm_generator import LLMGenerator, SimpleRAGChain, GenerationResult

__all__ = [
    "RAGEngine",
    "Chunk",
    "DocumentProcessor",
    "Document",
    "LLMGenerator",
    "SimpleRAGChain",
    "GenerationResult",
]
