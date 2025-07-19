#!/usr/bin/env python3
"""
Download and cache required models for the citation assistant.
Run this script during setup or container build.
"""
import os
import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_models():
    """Download all required models to the cache."""
    
    # Set cache directory
    cache_dir = os.path.join(os.path.dirname(__file__), '..', 'model_cache')
    os.makedirs(cache_dir, exist_ok=True)
    os.environ['TRANSFORMERS_CACHE'] = cache_dir
    os.environ['HF_HOME'] = cache_dir
    
    logger.info(f"Downloading models to cache directory: {cache_dir}")
    
    # 1. Download embedding model
    logger.info("Downloading embedding model...")
    try:
        embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder=cache_dir)
        logger.info("✓ Embedding model downloaded successfully")
    except Exception as e:
        logger.error(f"Failed to download embedding model: {e}")
    
    # 2. Download cross-encoder reranking models
    reranking_models = [
        'cross-encoder/ms-marco-MiniLM-L-12-v2',
        # Add other models if needed
    ]
    
    for model_name in reranking_models:
        logger.info(f"Downloading reranking model: {model_name}...")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
            model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=cache_dir)
            logger.info(f"✓ Reranking model {model_name} downloaded successfully")
        except Exception as e:
            logger.error(f"Failed to download reranking model {model_name}: {e}")
    
    logger.info("Model download complete!")
    logger.info(f"Models cached in: {cache_dir}")
    
    # List cached files
    logger.info("\nCached files:")
    for root, dirs, files in os.walk(cache_dir):
        level = root.replace(cache_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        logger.info(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # Show first 5 files per directory
            logger.info(f"{sub_indent}{file}")
        if len(files) > 5:
            logger.info(f"{sub_indent}... and {len(files) - 5} more files")

if __name__ == "__main__":
    download_models()