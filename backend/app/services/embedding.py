"""Embedding service for generating text embeddings using sentence-transformers."""
import numpy as np
from typing import List, Optional, Dict
from sentence_transformers import SentenceTransformer
import hashlib
import json
from functools import lru_cache
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding service with specified model."""
        self.model_name = model_name
        self.model = None
        self._load_model()
        
        # Thread pool for CPU-bound embedding generation
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # In-memory cache for embeddings (LRU with 1000 entries)
        self._cache_size = 1000
        
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
            
    def _text_to_hash(self, text: str) -> str:
        """Generate a hash for the text to use as cache key."""
        return hashlib.md5(text.encode()).hexdigest()
        
    @lru_cache(maxsize=1000)
    def _get_cached_embedding(self, text_hash: str) -> Optional[np.ndarray]:
        """Get embedding from cache if available."""
        return None  # LRU cache will handle this
        
    def _generate_embedding_sync(self, text: str) -> np.ndarray:
        """Synchronously generate embedding for a single text."""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
            
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)
        
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text asynchronously."""
        # Check cache first
        text_hash = self._text_to_hash(text)
        
        # Try to get from cache
        cached = self._get_cached_embedding(text_hash)
        if cached is not None:
            return cached
            
        # Generate embedding in thread pool
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            self.executor, 
            self._generate_embedding_sync, 
            text
        )
        
        # Cache the result
        self._get_cached_embedding.cache_clear()  # Clear if cache is full
        self._get_cached_embedding(text_hash)  # This will cache it
        
        return embedding
        
    def _generate_batch_embeddings_sync(self, texts: List[str]) -> List[np.ndarray]:
        """Synchronously generate embeddings for multiple texts."""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
            
        # Generate embeddings in batch
        embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
        return [emb.astype(np.float32) for emb in embeddings]
        
    async def generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts asynchronously."""
        if not texts:
            return []
            
        # Separate cached and uncached texts
        uncached_texts = []
        uncached_indices = []
        results = [None] * len(texts)
        
        for i, text in enumerate(texts):
            text_hash = self._text_to_hash(text)
            cached = self._get_cached_embedding(text_hash)
            
            if cached is not None:
                results[i] = cached
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                
        # Generate embeddings for uncached texts
        if uncached_texts:
            loop = asyncio.get_event_loop()
            new_embeddings = await loop.run_in_executor(
                self.executor,
                self._generate_batch_embeddings_sync,
                uncached_texts
            )
            
            # Place new embeddings in results and cache them
            for idx, embedding, text in zip(uncached_indices, new_embeddings, uncached_texts):
                results[idx] = embedding
                # Cache the embedding
                text_hash = self._text_to_hash(text)
                self._get_cached_embedding(text_hash)  # This will cache it
                
        return results
        
    def get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from cache if available (sync method)."""
        text_hash = self._text_to_hash(text)
        return self._get_cached_embedding(text_hash)
        
    def precompute_common_embeddings(self, common_texts: List[str]) -> Dict[str, np.ndarray]:
        """Precompute embeddings for common queries."""
        logger.info(f"Precomputing embeddings for {len(common_texts)} common texts")
        
        embeddings = {}
        for text in common_texts:
            try:
                embedding = self._generate_embedding_sync(text)
                embeddings[text] = embedding
                # Also cache it
                text_hash = self._text_to_hash(text)
                self._get_cached_embedding(text_hash)
            except Exception as e:
                logger.error(f"Failed to generate embedding for '{text}': {e}")
                
        logger.info(f"Precomputed {len(embeddings)} embeddings successfully")
        return embeddings
        
    def clear_cache(self):
        """Clear the embedding cache."""
        self._get_cached_embedding.cache_clear()
        logger.info("Embedding cache cleared")
        
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)