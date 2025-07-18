#!/usr/bin/env python3
"""Create a test user for development - simple version without password hashing."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
import uuid

async def create_test_user():
    """Create a test user."""
    async for db in get_db():
        try:
            # Check if test user already exists
            existing = await db.get(User, uuid.UUID("00000000-0000-0000-0000-000000000001"))
            if existing:
                print("Test user already exists")
                return
            
            # Create test user without password hashing (for development only)
            test_user = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                email="test@example.com",
                hashed_password="dummy_hash_for_dev",  # Not secure, just for development
                full_name="Test User",
                is_active=True,
                is_verified=True,
                is_superuser=False
            )
            
            db.add(test_user)
            await db.commit()
            print("Test user created successfully")
            
        except Exception as e:
            print(f"Error creating test user: {e}")
            await db.rollback()
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())