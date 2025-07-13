"""Script to create a test user for development."""
import asyncio
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User


async def create_test_user():
    """Create a test user with a specific UUID."""
    # Create engine
    engine = create_async_engine(settings.database_url, echo=True)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check if test user already exists
        test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        existing = await session.get(User, test_user_id)
        
        if existing:
            print(f"Test user already exists: {existing.email}")
            return
        
        # Create test user
        test_user = User(
            id=test_user_id,
            email="test@example.com",
            hashed_password="hashed_password_here",  # In production, this would be properly hashed
            full_name="Test User",
            bio="A test user for development",
            affiliation="Test University",
            is_active=True,
            is_verified=True,
            is_superuser=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        session.add(test_user)
        await session.commit()
        
        print(f"Created test user: {test_user.email} with ID: {test_user.id}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_user())