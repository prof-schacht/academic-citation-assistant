"""Zotero API integration service."""
import asyncio
import os
import tempfile
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import logging
import aiohttp
import hashlib
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import Paper, User, ZoteroSync, ZoteroConfig
from app.services.paper_processor import PaperProcessorService
from app.core.config import settings

logger = logging.getLogger(__name__)


class ZoteroService:
    """Service for syncing papers from Zotero."""
    
    BASE_URL = "https://api.zotero.org"
    ITEMS_PER_PAGE = 50  # Zotero's recommended limit
    
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self._config: Optional[ZoteroConfig] = None
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._load_config()
        self._session = aiohttp.ClientSession(
            headers={
                "Zotero-API-Key": self._config.api_key if self._config else "",
                "Zotero-API-Version": "3"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def _load_config(self) -> None:
        """Load Zotero configuration for the user."""
        result = await self.db.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == self.user_id)
        )
        self._config = result.scalar_one_or_none()
        if not self._config:
            raise ValueError(f"No Zotero configuration found for user {self.user_id}")
    
    async def test_connection(self) -> bool:
        """Test if the Zotero API connection works."""
        try:
            url = f"{self.BASE_URL}/users/{self._config.zotero_user_id}/items?limit=1"
            async with self._session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Zotero connection test failed: {e}")
            return False
    
    async def fetch_library_items(self, modified_since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Fetch all items from Zotero library.
        
        Args:
            modified_since: Only fetch items modified after this date
            
        Returns:
            List of Zotero items
        """
        items = []
        start = 0
        
        # Build base URL with filters for academic papers
        base_url = f"{self.BASE_URL}/users/{self._config.zotero_user_id}/items"
        params = {
            "limit": self.ITEMS_PER_PAGE,
            "itemType": "journalArticle || book || bookSection || conferencePaper || report || thesis"
        }
        
        # Add modification date filter if provided
        if modified_since:
            params["since"] = int(modified_since.timestamp())
        
        while True:
            params["start"] = start
            
            async with self._session.get(base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch Zotero items: {response.status}")
                    break
                
                batch = await response.json()
                if not batch:
                    break
                
                items.extend(batch)
                
                # Check if there are more items
                total_results = int(response.headers.get("Total-Results", "0"))
                if start + len(batch) >= total_results:
                    break
                
                start += self.ITEMS_PER_PAGE
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
        
        logger.info(f"Fetched {len(items)} items from Zotero")
        return items
    
    def _extract_paper_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract paper metadata from Zotero item."""
        data = item.get("data", {})
        
        # Extract authors
        authors = []
        for creator in data.get("creators", []):
            if creator.get("creatorType") == "author":
                first = creator.get("firstName", "")
                last = creator.get("lastName", "")
                name = f"{first} {last}".strip() if first else last
                if name:
                    authors.append(name)
        
        # Extract other metadata
        metadata = {
            "title": data.get("title", ""),
            "authors": authors,
            "abstract": data.get("abstractNote", ""),
            "year": self._extract_year(data),
            "journal": data.get("publicationTitle", "") or data.get("bookTitle", ""),
            "doi": data.get("DOI", ""),
            "source": "zotero",
            "zotero_key": item.get("key", ""),
            "citation_count": 0,  # Zotero doesn't provide this
        }
        
        # Add URL if available
        if data.get("url"):
            metadata["source_url"] = data["url"]
        
        return metadata
    
    def _extract_year(self, data: Dict[str, Any]) -> Optional[int]:
        """Extract publication year from various date fields."""
        # Try different date fields
        date_str = data.get("date", "") or data.get("dateAdded", "")
        
        if date_str:
            # Extract year from date string (handles various formats)
            import re
            year_match = re.search(r"(\d{4})", date_str)
            if year_match:
                return int(year_match.group(1))
        
        return None
    
    async def _download_attachment(self, item_key: str, filename: str) -> Optional[str]:
        """
        Download PDF attachment for a Zotero item.
        
        Returns:
            Path to downloaded file or None if failed
        """
        # First, get the attachment items
        attachments_url = f"{self.BASE_URL}/users/{self._config.zotero_user_id}/items/{item_key}/children"
        
        async with self._session.get(attachments_url) as response:
            if response.status != 200:
                logger.warning(f"No attachments found for item {item_key}")
                return None
            
            children = await response.json()
        
        # Find PDF attachments
        pdf_key = None
        for child in children:
            child_data = child.get("data", {})
            if (child_data.get("itemType") == "attachment" and 
                child_data.get("contentType") == "application/pdf"):
                pdf_key = child.get("key")
                break
        
        if not pdf_key:
            logger.warning(f"No PDF attachment found for item {item_key}")
            return None
        
        # Download the PDF
        file_url = f"{self.BASE_URL}/users/{self._config.zotero_user_id}/items/{pdf_key}/file"
        
        async with self._session.get(file_url) as response:
            if response.status != 200:
                logger.error(f"Failed to download PDF for item {item_key}: {response.status}")
                return None
            
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, filename)
            
            # Save PDF
            content = await response.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info(f"Downloaded PDF for item {item_key} to {file_path}")
            return file_path
    
    async def sync_library(self) -> Tuple[int, int, int]:
        """
        Sync entire Zotero library.
        
        Returns:
            Tuple of (new_papers, updated_papers, failed_papers)
        """
        new_papers = 0
        updated_papers = 0
        failed_papers = 0
        
        # Get last sync time
        last_sync = self._config.last_sync if self._config else None
        
        # Fetch items from Zotero
        items = await self.fetch_library_items(modified_since=last_sync)
        
        for item in items:
            try:
                # Check if we already have this paper
                zotero_key = item.get("key")
                zotero_version = item.get("version", 0)
                
                result = await self.db.execute(
                    select(ZoteroSync).where(
                        and_(
                            ZoteroSync.user_id == self.user_id,
                            ZoteroSync.zotero_key == zotero_key
                        )
                    )
                )
                existing_sync = result.scalar_one_or_none()
                
                # Skip if already synced and not updated
                if existing_sync and existing_sync.zotero_version >= zotero_version:
                    continue
                
                # Extract metadata
                metadata = self._extract_paper_metadata(item)
                
                if existing_sync:
                    # Update existing paper
                    paper = existing_sync.paper
                    for key, value in metadata.items():
                        if hasattr(paper, key):
                            setattr(paper, key, value)
                    
                    existing_sync.zotero_version = zotero_version
                    existing_sync.last_synced = datetime.utcnow()
                    
                    updated_papers += 1
                else:
                    # Create new paper
                    paper = Paper(**metadata)
                    self.db.add(paper)
                    await self.db.flush()  # Get paper ID
                    
                    # Create sync record
                    sync_record = ZoteroSync(
                        zotero_key=zotero_key,
                        zotero_version=zotero_version,
                        paper_id=paper.id,
                        user_id=self.user_id
                    )
                    self.db.add(sync_record)
                    
                    new_papers += 1
                
                # Download and process PDF if it's a new paper
                if not existing_sync:
                    file_path = await self._download_attachment(
                        zotero_key,
                        f"{paper.id}.pdf"
                    )
                    
                    if file_path:
                        # Process the paper (chunks, embeddings)
                        paper.file_path = file_path
                        paper.file_hash = self._calculate_file_hash(file_path)
                        
                        # Queue for processing
                        await PaperProcessorService.process_paper(
                            str(paper.id),
                            file_path
                        )
                
            except Exception as e:
                logger.error(f"Failed to sync Zotero item {item.get('key')}: {e}")
                failed_papers += 1
        
        # Update last sync time
        if self._config:
            self._config.last_sync = datetime.utcnow()
            self._config.last_sync_status = f"Synced: {new_papers} new, {updated_papers} updated, {failed_papers} failed"
        
        await self.db.commit()
        
        logger.info(f"Zotero sync complete: {new_papers} new, {updated_papers} updated, {failed_papers} failed")
        return new_papers, updated_papers, failed_papers
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    async def configure(self, api_key: str, zotero_user_id: str) -> ZoteroConfig:
        """
        Configure or update Zotero settings for the user.
        
        Args:
            api_key: Zotero API key
            zotero_user_id: Numeric Zotero user ID
            
        Returns:
            ZoteroConfig object
        """
        # Check if config exists
        result = await self.db.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == self.user_id)
        )
        config = result.scalar_one_or_none()
        
        if config:
            # Update existing
            config.api_key = api_key
            config.zotero_user_id = zotero_user_id
            config.updated_at = datetime.utcnow()
        else:
            # Create new
            config = ZoteroConfig(
                user_id=self.user_id,
                api_key=api_key,
                zotero_user_id=zotero_user_id
            )
            self.db.add(config)
        
        await self.db.commit()
        return config