"""Document service for business logic."""
from typing import Optional, List
from datetime import datetime
import uuid
import secrets
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentUpdate


class DocumentService:
    """Service for document operations."""
    
    @staticmethod
    async def create_document(
        db: AsyncSession,
        document_data: DocumentCreate,
        owner_id: uuid.UUID
    ) -> Document:
        """Create a new document."""
        # Extract plain text from content if available
        plain_text = ""
        word_count = 0
        
        if document_data.content:
            # Simple extraction of text from Lexical format
            plain_text = DocumentService._extract_plain_text(document_data.content)
            word_count = len(plain_text.split())
        
        # Create document
        document = Document(
            title=document_data.title,
            description=document_data.description,
            content=document_data.content,
            plain_text=plain_text,
            word_count=word_count,
            is_public=document_data.is_public,
            owner_id=owner_id,
            share_token=secrets.token_urlsafe(16) if document_data.is_public else None,
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return document
    
    @staticmethod
    async def get_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> Optional[Document]:
        """Get a document by ID."""
        query = select(Document).where(Document.id == document_id)
        
        # If user_id provided, check ownership or public access
        if user_id:
            query = query.where(
                (Document.owner_id == user_id) | (Document.is_public == True)
            )
        else:
            # Only public documents for anonymous users
            query = query.where(Document.is_public == True)
        
        result = await db.execute(query.options(selectinload(Document.owner)))
        document = result.scalar_one_or_none()
        
        # Update last accessed timestamp
        if document:
            document.last_accessed_at = datetime.utcnow()
            await db.commit()
        
        return document
    
    @staticmethod
    async def get_documents(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        is_public_only: bool = False
    ) -> tuple[List[Document], int]:
        """Get documents with pagination."""
        # Base query
        query = select(Document)
        count_query = select(func.count(Document.id))
        
        # Filter by ownership or public access
        if user_id and not is_public_only:
            filter_condition = (Document.owner_id == user_id) | (Document.is_public == True)
        else:
            filter_condition = Document.is_public == True
        
        query = query.where(filter_condition)
        count_query = count_query.where(filter_condition)
        
        # Search filter
        if search:
            search_filter = (
                Document.title.ilike(f"%{search}%") |
                Document.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(Document.updated_at.desc())
        query = query.offset(skip).limit(limit)
        query = query.options(selectinload(Document.owner))
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        return documents, total
    
    @staticmethod
    async def update_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        document_data: DocumentUpdate,
        user_id: uuid.UUID
    ) -> Optional[Document]:
        """Update a document."""
        # Get document and check ownership
        query = select(Document).where(
            and_(Document.id == document_id, Document.owner_id == user_id)
        )
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            return None
        
        # Update fields
        update_data = document_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(document, field, value)
        
        # Update plain text and word count if content changed
        if "content" in update_data and update_data["content"]:
            document.plain_text = DocumentService._extract_plain_text(update_data["content"])
            document.word_count = len(document.plain_text.split())
        
        # Generate share token if making public
        if "is_public" in update_data:
            if update_data["is_public"] and not document.share_token:
                document.share_token = secrets.token_urlsafe(16)
            elif not update_data["is_public"]:
                document.share_token = None
        
        document.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(document)
        
        return document
    
    @staticmethod
    async def delete_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Delete a document."""
        # Get document and check ownership
        query = select(Document).where(
            and_(Document.id == document_id, Document.owner_id == user_id)
        )
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            return False
        
        await db.delete(document)
        await db.commit()
        
        return True
    
    @staticmethod
    async def bulk_delete_documents(
        db: AsyncSession,
        document_ids: List[uuid.UUID],
        user_id: uuid.UUID
    ) -> int:
        """Delete multiple documents at once."""
        # Get all documents that belong to the user
        query = select(Document).where(
            and_(
                Document.id.in_(document_ids),
                Document.owner_id == user_id
            )
        )
        result = await db.execute(query)
        documents = result.scalars().all()
        
        deleted_count = 0
        for document in documents:
            await db.delete(document)
            deleted_count += 1
        
        await db.commit()
        
        return deleted_count
    
    @staticmethod
    def _extract_plain_text(content: dict) -> str:
        """Extract plain text from Lexical editor content."""
        # This is a simplified extraction - in production, you'd parse the Lexical format properly
        text_parts = []
        
        def extract_text(node):
            if isinstance(node, dict):
                if node.get("type") == "text" and "text" in node:
                    text_parts.append(node["text"])
                elif "children" in node:
                    for child in node["children"]:
                        extract_text(child)
            elif isinstance(node, list):
                for item in node:
                    extract_text(item)
        
        if "root" in content:
            extract_text(content["root"])
        
        return " ".join(text_parts)