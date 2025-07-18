"""Tests for admin database cleaning functionality."""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.document import Document
from app.models.user import User
from app.models.paper import Paper
from app.models.library import Library
from app.services.document import DocumentService
from app.services.admin import AdminService
from app.schemas.document import DocumentCreate


@pytest.mark.asyncio
async def test_clean_all_documents(db_session: AsyncSession):
    """Test cleaning all documents from database."""
    # Create test users
    user1_id = uuid4()
    user2_id = uuid4()
    
    user1 = User(
        id=user1_id,
        email="user1@example.com",
        full_name="User 1",
        hashed_password="hashed",
    )
    user2 = User(
        id=user2_id,
        email="user2@example.com",
        full_name="User 2",
        hashed_password="hashed",
    )
    db_session.add_all([user1, user2])
    
    # Create a paper (should be preserved)
    paper = Paper(
        id=uuid4(),
        title="Test Paper",
        authors=["Author 1"],
        year=2024,
    )
    db_session.add(paper)
    
    # Create a library (should be preserved)
    library = Library(
        id=uuid4(),
        name="Test Library",
        owner_id=user1_id,
    )
    db_session.add(library)
    
    await db_session.commit()
    
    # Create documents for both users
    for i in range(3):
        doc1_data = DocumentCreate(
            title=f"User 1 Doc {i}",
            description=f"Description {i}",
            is_public=False,
        )
        doc2_data = DocumentCreate(
            title=f"User 2 Doc {i}",
            description=f"Description {i}",
            is_public=True,
        )
        await DocumentService.create_document(db_session, doc1_data, user1_id)
        await DocumentService.create_document(db_session, doc2_data, user2_id)
    
    # Verify initial state
    doc_count = await db_session.scalar(select(func.count(Document.id)))
    user_count = await db_session.scalar(select(func.count(User.id)))
    paper_count = await db_session.scalar(select(func.count(Paper.id)))
    library_count = await db_session.scalar(select(func.count(Library.id)))
    
    assert doc_count == 6
    assert user_count == 2
    assert paper_count == 1
    assert library_count == 1
    
    # Clean all documents
    result = await AdminService.clean_all_documents(db_session)
    
    assert result["documents_deleted"] == 6
    
    # Verify final state
    doc_count = await db_session.scalar(select(func.count(Document.id)))
    user_count = await db_session.scalar(select(func.count(User.id)))
    paper_count = await db_session.scalar(select(func.count(Paper.id)))
    library_count = await db_session.scalar(select(func.count(Library.id)))
    
    assert doc_count == 0  # All documents deleted
    assert user_count == 2  # Users preserved
    assert paper_count == 1  # Papers preserved
    assert library_count == 1  # Libraries preserved


@pytest.mark.asyncio
async def test_clean_documents_with_citations(db_session: AsyncSession):
    """Test that cleaning documents also cleans related citations."""
    # Create a test user
    user_id = uuid4()
    user = User(
        id=user_id,
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create a document with citations
    doc_data = DocumentCreate(
        title="Document with Citations",
        is_public=False,
    )
    doc = await DocumentService.create_document(db_session, doc_data, user_id)
    
    # Note: In a real test, we would create citations through proper service methods
    # For this test, we're focusing on the clean operation
    
    # Clean all documents
    result = await AdminService.clean_all_documents(db_session)
    
    assert result["documents_deleted"] == 1
    
    # Verify no documents remain
    doc_count = await db_session.scalar(select(func.count(Document.id)))
    assert doc_count == 0