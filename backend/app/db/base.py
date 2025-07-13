"""Database base configuration."""
from app.db.base_class import Base

# Import all models here to ensure they are registered with SQLAlchemy
from app.models.user import User
from app.models.document import Document
from app.models.paper import Paper
from app.models.citation import Citation
from app.models.library import Library, LibraryPaper

__all__ = ["Base", "User", "Document", "Paper", "Citation", "Library", "LibraryPaper"]