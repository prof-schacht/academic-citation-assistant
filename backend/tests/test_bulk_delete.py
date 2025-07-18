"""Tests for bulk delete functionality."""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.user import User
from app.services.document import DocumentService
from app.schemas.document import DocumentCreate


@pytest.mark.asyncio
async def test_bulk_delete_documents(db_session: AsyncSession):
    """Test bulk deletion of multiple documents."""
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
    
    # Create multiple documents
    doc_ids = []
    for i in range(5):
        doc_data = DocumentCreate(
            title=f"Test Document {i}",
            description=f"Description {i}",
            is_public=False,
        )
        doc = await DocumentService.create_document(db_session, doc_data, user_id)
        doc_ids.append(doc.id)
    
    # Bulk delete first 3 documents
    deleted_count = await DocumentService.bulk_delete_documents(
        db_session, doc_ids[:3], user_id
    )
    
    assert deleted_count == 3
    
    # Verify only 2 documents remain
    remaining_docs, total = await DocumentService.get_documents(
        db_session, user_id=user_id
    )
    assert total == 2
    assert all(doc.id in doc_ids[3:] for doc in remaining_docs)


@pytest.mark.asyncio
async def test_bulk_delete_only_owned_documents(db_session: AsyncSession):
    """Test that bulk delete only deletes documents owned by the user."""
    # Create two test users
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
    await db_session.commit()
    
    # Create documents for both users
    doc1_data = DocumentCreate(title="User 1 Doc", is_public=False)
    doc2_data = DocumentCreate(title="User 2 Doc", is_public=False)
    
    doc1 = await DocumentService.create_document(db_session, doc1_data, user1_id)
    doc2 = await DocumentService.create_document(db_session, doc2_data, user2_id)
    
    # Try to delete both documents as user1
    deleted_count = await DocumentService.bulk_delete_documents(
        db_session, [doc1.id, doc2.id], user1_id
    )
    
    # Should only delete user1's document
    assert deleted_count == 1
    
    # Verify user2's document still exists
    user2_docs, total = await DocumentService.get_documents(
        db_session, user_id=user2_id
    )
    assert total == 1
    assert user2_docs[0].id == doc2.id


@pytest.mark.asyncio
async def test_bulk_delete_empty_list(db_session: AsyncSession):
    """Test bulk delete with empty document list."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    
    deleted_count = await DocumentService.bulk_delete_documents(
        db_session, [], user_id
    )
    
    assert deleted_count == 0