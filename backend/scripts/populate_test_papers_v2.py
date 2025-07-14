"""Script to populate database with test papers for development and testing."""
import asyncio
import json
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

# Add parent directory to path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import get_db, engine
from app.models.paper import Paper
from app.models.user import User
from app.services.embedding import EmbeddingService
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test papers data - simplified to match our model
TEST_PAPERS = [
    {
        "title": "Deep Learning for Natural Language Processing: A Survey",
        "authors": ["Young, Tom", "Hazarika, Devamanyu", "Poria, Soujanya", "Cambria, Erik"],
        "year": 2023,
        "abstract": "Deep learning has revolutionized natural language processing (NLP) by enabling models to automatically learn representations from data. This comprehensive survey examines the latest advances in deep learning techniques for NLP, including transformer architectures, pre-trained language models, and neural machine translation. We discuss the evolution from traditional statistical methods to modern neural approaches, highlighting key breakthroughs like attention mechanisms and BERT. The survey also covers emerging areas such as few-shot learning, multimodal NLP, and ethical considerations in language AI.",
        "journal": "ACM Computing Surveys",
        "doi": "10.1145/1234567.1234567",
        "citation_count": 245,
    },
    {
        "title": "Attention Is All You Need",
        "authors": ["Vaswani, Ashish", "Shazeer, Noam", "Parmar, Niki", "Uszkoreit, Jakob"],
        "year": 2017,
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
        "journal": "NeurIPS",
        "doi": "10.5555/3295222.3295349",
        "citation_count": 75000,
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": ["Devlin, Jacob", "Chang, Ming-Wei", "Lee, Kenton", "Toutanova, Kristina"],
        "year": 2019,
        "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks.",
        "journal": "NAACL",
        "doi": "10.18653/v1/N19-1423",
        "citation_count": 65000,
    },
    {
        "title": "GPT-3: Language Models are Few-Shot Learners",
        "authors": ["Brown, Tom", "Mann, Benjamin", "Ryder, Nick", "Subbiah, Melanie"],
        "year": 2020,
        "abstract": "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task. We show that scaling up language models greatly improves task-agnostic, few-shot performance, sometimes even reaching competitiveness with prior state-of-the-art fine-tuning approaches. We train GPT-3, an autoregressive language model with 175 billion parameters, and test its performance in the few-shot setting.",
        "journal": "NeurIPS",
        "doi": "10.5555/3495724.3495883",
        "citation_count": 25000,
    },
    {
        "title": "A Survey on Transfer Learning for Natural Language Processing",
        "authors": ["Ruder, Sebastian", "Peters, Matthew E.", "Swayamdipta, Swabha", "Wolf, Thomas"],
        "year": 2021,
        "abstract": "Transfer learning has revolutionized natural language processing by enabling models to leverage knowledge from large-scale pre-training. This survey provides a comprehensive overview of transfer learning techniques in NLP, covering pre-trained word embeddings, contextual representations, and full model pre-training. We discuss various pre-training objectives, model architectures, and fine-tuning strategies. The survey also examines domain adaptation, cross-lingual transfer, and recent advances in parameter-efficient fine-tuning methods.",
        "journal": "Journal of Machine Learning Research",
        "doi": "10.5555/3546258.3546259",
        "citation_count": 450,
    },
    {
        "title": "Transformers for Computer Vision: A Survey",
        "authors": ["Khan, Salman", "Naseer, Muzammal", "Hayat, Munawar", "Zamir, Syed Waqas"],
        "year": 2022,
        "abstract": "Transformers have emerged as a powerful alternative to convolutional neural networks in computer vision. This survey comprehensively reviews the application of transformer architectures to various vision tasks, including image classification, object detection, and segmentation. We discuss Vision Transformer (ViT) and its variants, hybrid CNN-Transformer architectures, and self-supervised pre-training methods. The survey also covers computational efficiency improvements and compares transformers with traditional CNN-based approaches.",
        "journal": "ACM Computing Surveys",
        "doi": "10.1145/3505244",
        "citation_count": 850,
    },
    {
        "title": "Efficient Transformers: A Survey",
        "authors": ["Tay, Yi", "Dehghani, Mostafa", "Bahri, Dara", "Metzler, Donald"],
        "year": 2022,
        "abstract": "Transformer models have achieved remarkable success but suffer from quadratic complexity in sequence length. This survey reviews recent advances in efficient transformer architectures that reduce computational and memory requirements. We categorize approaches into fixed patterns, learnable patterns, memory-based, low-rank approximations, and kernel methods. The survey provides a comprehensive comparison of different efficiency techniques and discusses their trade-offs between computational efficiency and model performance.",
        "journal": "ACM Computing Surveys",
        "doi": "10.1145/3530811",
        "citation_count": 550,
    },
    {
        "title": "Foundation Models for Natural Language Processing",
        "authors": ["Bommasani, Rishi", "Hudson, Drew A.", "Adeli, Ehsan", "Altman, Russ"],
        "year": 2023,
        "abstract": "Foundation models represent a paradigm shift in AI, where large-scale models trained on broad data can be adapted to a wide range of downstream tasks. This comprehensive study examines the capabilities, limitations, and societal impact of foundation models in NLP. We analyze their emergent abilities, discuss techniques for adaptation and alignment, and address concerns about bias, safety, and environmental impact. The paper also explores future directions including multimodal foundation models and their potential applications.",
        "journal": "Nature Machine Intelligence",
        "doi": "10.1038/s42256-023-00623-7",
        "citation_count": 320,
    },
    {
        "title": "Neural Machine Translation: A Review",
        "authors": ["Stahlberg, Felix", "Byrne, Bill"],
        "year": 2022,
        "abstract": "Neural machine translation (NMT) has become the dominant approach to machine translation, achieving remarkable improvements over statistical methods. This review provides a comprehensive overview of NMT architectures, training techniques, and evaluation methods. We cover sequence-to-sequence models, attention mechanisms, transformer-based NMT, and recent advances in multilingual and low-resource translation. The review also discusses challenges including domain adaptation, document-level translation, and simultaneous translation.",
        "journal": "Journal of Artificial Intelligence Research",
        "doi": "10.1613/jair.1.13123",
        "citation_count": 680,
    },
    {
        "title": "Prompt Engineering for Large Language Models: A Comprehensive Guide",
        "authors": ["Liu, Pengfei", "Yuan, Weizhe", "Fu, Jinlan", "Jiang, Zhengbao"],
        "year": 2023,
        "abstract": "Prompt engineering has emerged as a crucial technique for effectively utilizing large language models. This comprehensive guide examines various prompting strategies, including zero-shot, few-shot, and chain-of-thought prompting. We analyze the theoretical foundations of prompt-based learning, discuss automatic prompt generation methods, and provide practical guidelines for different applications. The guide also covers advanced techniques like prompt tuning, instruction tuning, and constitutional AI approaches for aligning model behavior.",
        "journal": "ACL",
        "doi": "10.18653/v1/2023.acl-tutorials.1",
        "citation_count": 190,
    }
]


async def populate_papers():
    """Populate database with test papers."""
    # Initialize embedding service
    embedding_service = EmbeddingService()
    
    async with AsyncSession(engine) as session:
        # Check if papers already exist
        result = await session.execute(select(Paper))
        existing_papers = result.scalars().all()
        
        if existing_papers:
            logger.info(f"Database already contains {len(existing_papers)} papers")
            return
        
        logger.info(f"Populating database with {len(TEST_PAPERS)} test papers...")
        
        # Process each paper
        for i, paper_data in enumerate(TEST_PAPERS):
            logger.info(f"Processing paper {i+1}/{len(TEST_PAPERS)}: {paper_data['title']}")
            
            # Generate embedding for the abstract
            try:
                embedding = await embedding_service.generate_embedding(paper_data['abstract'])
                
                # Create paper object - let SQLAlchemy handle the UUID
                paper = Paper(
                    title=paper_data['title'],
                    authors=paper_data['authors'],
                    year=paper_data['year'],
                    abstract=paper_data['abstract'],
                    journal=paper_data.get('journal'),
                    doi=paper_data.get('doi'),
                    embedding=embedding.tolist(),  # Convert numpy array to list
                    citation_count=paper_data.get('citation_count', 0),
                    source='test_data',
                    is_processed=True
                )
                
                session.add(paper)
                
            except Exception as e:
                logger.error(f"Failed to process paper '{paper_data['title']}': {e}")
                continue
        
        # Commit all papers
        await session.commit()
        logger.info("Successfully populated test papers!")
        
        # Verify papers were added
        result = await session.execute(select(Paper))
        papers = result.scalars().all()
        logger.info(f"Total papers in database: {len(papers)}")
        
        # Test a sample embedding
        if papers:
            sample_paper = papers[0]
            logger.info(f"Sample paper: {sample_paper.title}")
            logger.info(f"Embedding dimension: {len(sample_paper.embedding)}")


async def test_similarity_search():
    """Test similarity search with a sample query - using simple query for now."""
    embedding_service = EmbeddingService()
    
    async with AsyncSession(engine) as session:
        # Test query
        test_query = "How do transformers work in natural language processing?"
        logger.info(f"\nTesting similarity search with query: '{test_query}'")
        
        # Generate embedding
        query_embedding = await embedding_service.generate_embedding(test_query)
        
        # For now, just check if we have papers with embeddings
        result = await session.execute(
            select(Paper).where(Paper.embedding.isnot(None)).limit(5)
        )
        papers = result.scalars().all()
        
        logger.info(f"Found {len(papers)} papers with embeddings")
        for i, paper in enumerate(papers):
            logger.info(f"{i+1}. {paper.title}")
            logger.info(f"   Authors: {', '.join(paper.authors[:2]) if paper.authors else 'Unknown'}...")
            logger.info(f"   Year: {paper.year}")


async def main():
    """Main function to run the population script."""
    logger.info("Starting paper population script...")
    
    # Populate papers
    await populate_papers()
    
    # Test similarity search
    await test_similarity_search()
    
    logger.info("Script completed!")


if __name__ == "__main__":
    asyncio.run(main())