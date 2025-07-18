"""
Cross-encoder reranking service for improving retrieval quality.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from functools import lru_cache
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RerankingResult:
    """Container for reranking results."""
    paper_id: str
    chunk_id: Optional[str]
    chunk_text: str
    original_score: float
    rerank_score: float
    final_score: float
    metadata: Dict[str, Any]
    context_match: Optional[float] = None


class CrossEncoderReranker:
    """
    Cross-encoder based reranking for academic paper retrieval.
    """
    
    # Recommended models for academic search
    MODELS = {
        'ms-marco-MiniLM': 'cross-encoder/ms-marco-MiniLM-L-12-v2',
        'ms-marco-base': 'cross-encoder/ms-marco-electra-base',
        'scibert': 'allenai/scibert_scivocab_uncased',  # Can be fine-tuned as cross-encoder
        'multi-qa': 'cross-encoder/stsb-roberta-base',
        'qnli': 'cross-encoder/qnli-electra-base'
    }
    
    def __init__(
        self,
        model_name: str = 'ms-marco-MiniLM',
        device: Optional[str] = None,
        max_length: int = 512,
        batch_size: int = 32,
        cache_size: int = 1000
    ):
        self.model_name = self.MODELS.get(model_name, model_name)
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.max_length = max_length
        self.batch_size = batch_size
        
        # Initialize model and tokenizer
        logger.info(f"Loading cross-encoder model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        
        # Thread pool for CPU-bound operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Cache for reranking scores
        self._score_cache = {}
    
    @lru_cache(maxsize=1000)
    def _cached_score(self, query: str, text: str) -> float:
        """Cache individual scoring results."""
        return self._score_single(query, text)
    
    def _score_single(self, query: str, text: str) -> float:
        """Score a single query-text pair."""
        with torch.no_grad():
            inputs = self.tokenizer(
                query,
                text,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors='pt'
            ).to(self.device)
            
            outputs = self.model(**inputs)
            logits = outputs.logits
            
            # Convert to probability score
            if logits.shape[-1] > 1:
                # Multi-class classification model
                scores = torch.nn.functional.softmax(logits, dim=-1)
                score = scores[:, -1].item()  # Use last class as positive
            else:
                # Binary classification or regression
                score = torch.sigmoid(logits).item()
        
        return score
    
    def score_batch(
        self,
        query: str,
        texts: List[str],
        show_progress: bool = False
    ) -> List[float]:
        """
        Score multiple texts against a query in batches.
        
        Args:
            query: The search query
            texts: List of texts to score
            show_progress: Whether to show progress
            
        Returns:
            List of scores
        """
        scores = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            
            with torch.no_grad():
                # Tokenize batch
                inputs = self.tokenizer(
                    [query] * len(batch_texts),
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors='pt'
                ).to(self.device)
                
                # Get predictions
                outputs = self.model(**inputs)
                logits = outputs.logits
                
                # Convert to scores
                if logits.shape[-1] > 1:
                    batch_scores = torch.nn.functional.softmax(logits, dim=-1)
                    batch_scores = batch_scores[:, -1].cpu().numpy()
                else:
                    batch_scores = torch.sigmoid(logits).cpu().numpy().flatten()
                
                scores.extend(batch_scores)
            
            if show_progress and i % 100 == 0:
                logger.info(f"Reranked {i + len(batch_texts)}/{len(texts)} texts")
        
        return scores
    
    async def score_batch_async(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        """Async wrapper for batch scoring."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.score_batch,
            query,
            texts,
            False
        )


class RerankingService:
    """
    Service for reranking search results using cross-encoders and additional signals.
    """
    
    def __init__(
        self,
        cross_encoder_model: str = 'ms-marco-MiniLM',
        rerank_weight: float = 0.6,
        original_weight: float = 0.4,
        context_weight: float = 0.2,
        use_cache: bool = True
    ):
        self.cross_encoder = CrossEncoderReranker(model_name=cross_encoder_model)
        self.rerank_weight = rerank_weight
        self.original_weight = original_weight
        self.context_weight = context_weight
        self.use_cache = use_cache
        
        # Normalize weights
        total_weight = rerank_weight + original_weight
        self.rerank_weight = rerank_weight / total_weight
        self.original_weight = original_weight / total_weight
    
    async def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        query_context: Optional[Dict[str, str]] = None,
        top_k: Optional[int] = None
    ) -> List[RerankingResult]:
        """
        Rerank search results using cross-encoder and additional signals.
        
        Args:
            query: The search query
            results: List of search results with 'chunk_text', 'score', etc.
            query_context: Optional context (previous/next sentences)
            top_k: Return only top K results
            
        Returns:
            List of reranked results
        """
        if not results:
            return []
        
        # Extract texts and prepare for reranking
        texts = []
        for result in results:
            # Combine chunk text with metadata for richer context
            text_parts = [result.get('chunk_text', '')]
            
            # Add title if available
            if 'metadata' in result and 'title' in result['metadata']:
                text_parts.insert(0, f"Title: {result['metadata']['title']}")
            
            # Add abstract snippet if available
            if 'metadata' in result and 'abstract' in result['metadata']:
                abstract = result['metadata']['abstract']
                if abstract and len(abstract) > 200:
                    abstract = abstract[:200] + "..."
                if abstract:
                    text_parts.insert(1, f"Abstract: {abstract}")
            
            combined_text = "\n".join(text_parts)
            texts.append(combined_text)
        
        # Score with cross-encoder
        rerank_scores = await self.cross_encoder.score_batch_async(query, texts)
        
        # Calculate context scores if context provided
        context_scores = None
        if query_context:
            context_scores = await self._calculate_context_scores(
                query_context, results
            )
        
        # Combine scores and create reranked results
        reranked_results = []
        for i, (result, rerank_score) in enumerate(zip(results, rerank_scores)):
            original_score = result.get('score', result.get('hybrid_score', 0.0))
            
            # Calculate final score
            final_score = (
                self.rerank_weight * rerank_score +
                self.original_weight * original_score
            )
            
            # Add context score if available
            context_match = None
            if context_scores:
                context_match = context_scores[i]
                final_score += self.context_weight * context_match
                # Renormalize
                final_score = final_score / (1 + self.context_weight)
            
            reranked_results.append(RerankingResult(
                paper_id=result.get('paper_id'),
                chunk_id=result.get('chunk_id'),
                chunk_text=result.get('chunk_text', ''),
                original_score=original_score,
                rerank_score=rerank_score,
                final_score=final_score,
                metadata=result.get('metadata', {}),
                context_match=context_match
            ))
        
        # Sort by final score
        reranked_results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Return top K if specified
        if top_k:
            reranked_results = reranked_results[:top_k]
        
        return reranked_results
    
    async def _calculate_context_scores(
        self,
        query_context: Dict[str, str],
        results: List[Dict[str, Any]]
    ) -> List[float]:
        """Calculate context matching scores."""
        context_scores = []
        
        # Combine context into a single query
        context_parts = []
        if 'previous' in query_context:
            context_parts.append(query_context['previous'])
        if 'current' in query_context:
            context_parts.append(query_context['current'])
        if 'next' in query_context:
            context_parts.append(query_context['next'])
        
        extended_query = ' '.join(context_parts)
        
        # Score each result against extended context
        texts = [result.get('chunk_text', '') for result in results]
        if extended_query and texts:
            scores = await self.cross_encoder.score_batch_async(extended_query, texts)
            context_scores = scores
        else:
            context_scores = [0.0] * len(results)
        
        return context_scores
    
    def update_weights(
        self,
        rerank_weight: Optional[float] = None,
        original_weight: Optional[float] = None,
        context_weight: Optional[float] = None
    ):
        """Update scoring weights."""
        if rerank_weight is not None:
            self.rerank_weight = rerank_weight
        if original_weight is not None:
            self.original_weight = original_weight
        if context_weight is not None:
            self.context_weight = context_weight
        
        # Renormalize
        total = self.rerank_weight + self.original_weight
        self.rerank_weight = self.rerank_weight / total
        self.original_weight = self.original_weight / total