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
    
    async def fetch_library_items(self, modified_since: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Fetch all items from Zotero library, including papers and their PDF attachments.
        
        Args:
            modified_since: Only fetch items modified after this date
            
        Returns:
            Tuple of (papers, attachments_by_parent)
        """
        all_papers = []
        all_attachments = {}
        
        # Parse selected groups and collections
        import json
        selected_groups = []
        selected_collections = []
        
        if self._config.selected_groups:
            try:
                selected_groups = json.loads(self._config.selected_groups)
            except:
                selected_groups = []
                
        if self._config.selected_collections:
            try:
                selected_collections = json.loads(self._config.selected_collections)
            except:
                selected_collections = []
        
        # If no groups/collections selected, fetch from user's personal library
        if not selected_groups and not selected_collections:
            selected_groups = [f"users/{self._config.zotero_user_id}"]
        
        # Fetch items from each selected library/group
        for library_id in selected_groups:
            papers, attachments = await self._fetch_items_from_library(library_id, modified_since, selected_collections)
            all_papers.extend(papers)
            # Merge attachments dictionaries
            for key, value in attachments.items():
                if key not in all_attachments:
                    all_attachments[key] = []
                all_attachments[key].extend(value)
        
        logger.info(f"Fetched {len(all_papers)} papers and {sum(len(atts) for atts in all_attachments.values())} PDF attachments from Zotero")
        return all_papers, all_attachments
    
    async def _fetch_items_from_library(
        self, 
        library_id: str, 
        modified_since: Optional[datetime] = None,
        filter_collections: List[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Fetch items from a specific library, including both papers and their PDF attachments.
        
        Args:
            library_id: Library ID (e.g., "users/12345" or "groups/67890")
            modified_since: Only fetch items modified after this date
            filter_collections: If provided, only fetch items from these collections
            
        Returns:
            Tuple of (papers, attachments_by_parent)
                - papers: List of paper items
                - attachments_by_parent: Dict mapping parent item keys to their PDF attachments
        """
        papers = []
        attachments_by_parent = {}
        start = 0
        
        # Build base URL - library_id already contains the prefix (e.g., "groups/4965330")
        base_url = f"{self.BASE_URL}/{library_id}/items"
        params = {
            "limit": self.ITEMS_PER_PAGE,
            # Don't filter by itemType here - we'll process all items
        }
        
        # Add modification date filter if provided
        if modified_since:
            params["since"] = int(modified_since.timestamp())
        
        while True:
            params["start"] = start
            
            async with self._session.get(base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch Zotero items from {library_id}: {response.status}")
                    break
                
                batch = await response.json()
                if not batch:
                    break
                
                # Process items - separate papers from PDF attachments
                for item in batch:
                    item_type = item.get("data", {}).get("itemType", "")
                    
                    # Handle PDF attachments
                    if item_type == "attachment":
                        data = item.get("data", {})
                        if data.get("contentType") == "application/pdf" and data.get("parentItem"):
                            parent_key = data["parentItem"]
                            if parent_key not in attachments_by_parent:
                                attachments_by_parent[parent_key] = []
                            attachments_by_parent[parent_key].append(item)
                        continue
                    
                    # Skip notes
                    if item_type == "note":
                        continue
                    
                    # If collections filter is specified, check collections
                    if filter_collections:
                        item_collections = item.get("data", {}).get("collections", [])
                        if not any(col in filter_collections for col in item_collections):
                            continue
                    
                    # This is a paper item
                    papers.append(item)
                
                # Check if there are more items
                total_results = int(response.headers.get("Total-Results", "0"))
                if start + len(batch) >= total_results:
                    break
                
                start += self.ITEMS_PER_PAGE
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
        
        logger.info(f"Fetched {len(papers)} papers and {sum(len(atts) for atts in attachments_by_parent.values())} PDF attachments from {library_id}")
        return papers, attachments_by_parent
    
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
        # Convert empty strings to None for unique fields
        doi = data.get("DOI", "")
        if doi == "":
            doi = None
            
        metadata = {
            "title": data.get("title", ""),
            "authors": authors,
            "abstract": data.get("abstractNote", "") or None,
            "year": self._extract_year(data),
            "journal": data.get("publicationTitle", "") or data.get("bookTitle", "") or None,
            "doi": doi,
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
    
    async def _download_pdf_attachment(self, attachment_item: Dict[str, Any], library_id: str, filename: str) -> Optional[str]:
        """
        Download PDF attachment from Zotero.
        
        Args:
            attachment_item: The attachment item data from Zotero
            library_id: Library ID (e.g., "users/12345" or "groups/67890")
            filename: Filename to save the PDF as
            
        Returns:
            Path to downloaded file or None if failed
        """
        attachment_key = attachment_item.get("key")
        if not attachment_key:
            logger.warning("No key found for attachment item")
            return None
        
        # Download the PDF
        file_url = f"{self.BASE_URL}/{library_id}/items/{attachment_key}/file"
        
        try:
            async with self._session.get(file_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to download PDF for attachment {attachment_key}: {response.status}")
                    return None
                
                # Create temporary file
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, filename)
                
                # Save PDF
                content = await response.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                
                logger.info(f"Downloaded PDF attachment {attachment_key} to {file_path}")
                return file_path
        except Exception as e:
            logger.error(f"Error downloading PDF attachment {attachment_key}: {e}")
            return None
    
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
        
        # Fetch items from Zotero (papers and attachments)
        papers, attachments_by_parent = await self.fetch_library_items(modified_since=last_sync)
        
        # Determine library_id for PDF downloads
        # Use the first selected group or user's personal library
        import json
        selected_groups = []
        if self._config.selected_groups:
            try:
                selected_groups = json.loads(self._config.selected_groups)
            except:
                selected_groups = []
        
        library_id = selected_groups[0] if selected_groups else f"users/{self._config.zotero_user_id}"
        
        for item in papers:
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
                    
                    await self.db.flush()  # Save changes
                    updated_papers += 1
                else:
                    # Check if paper with same DOI already exists
                    existing_paper = None
                    if metadata.get("doi"):
                        result = await self.db.execute(
                            select(Paper).where(Paper.doi == metadata["doi"])
                        )
                        existing_paper = result.scalar_one_or_none()
                    
                    if existing_paper:
                        # Use existing paper and create sync record
                        paper = existing_paper
                        logger.info(f"Found existing paper with DOI {metadata['doi']}, linking to Zotero item {zotero_key}")
                        
                        # Update paper metadata if needed
                        for key, value in metadata.items():
                            if hasattr(paper, key) and value:
                                current_value = getattr(paper, key)
                                # Only update if current value is None or empty
                                if not current_value:
                                    setattr(paper, key, value)
                        
                        await self.db.flush()
                    else:
                        # Create new paper
                        paper = Paper(**metadata)
                        self.db.add(paper)
                        await self.db.flush()  # Get paper ID
                        new_papers += 1
                    
                    # Create sync record
                    sync_record = ZoteroSync(
                        zotero_key=zotero_key,
                        zotero_version=zotero_version,
                        paper_id=paper.id,
                        user_id=self.user_id
                    )
                    self.db.add(sync_record)
                    await self.db.flush()
                
                # Download and process PDF if it's a new paper or newly linked
                if not existing_sync and not paper.file_path:
                    # Check if we have PDF attachments for this paper
                    pdf_attachments = attachments_by_parent.get(zotero_key, [])
                    
                    for pdf_attachment in pdf_attachments:
                        file_path = await self._download_pdf_attachment(
                            pdf_attachment,
                            library_id,
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
                            await self.db.flush()
                            
                            # Only process the first PDF
                            break
                    else:
                        # No PDF attachments found
                        logger.info(f"No PDF attachments found for paper {zotero_key}: {paper.title[:50]}...")
                
                # Commit this item's changes
                await self.db.commit()
                
            except Exception as e:
                logger.error(f"Failed to sync Zotero item {item.get('key')}: {e}")
                failed_papers += 1
                
                # Rollback any changes for this item
                await self.db.rollback()
                continue
        
        # Update last sync time
        if self._config:
            self._config.last_sync = datetime.utcnow()
            self._config.last_sync_status = f"Synced: {new_papers} new, {updated_papers} updated, {failed_papers} failed"
            await self.db.commit()
        
        logger.info(f"Zotero sync complete: {new_papers} new, {updated_papers} updated, {failed_papers} failed")
        logger.info(f"Total attachments available: {sum(len(atts) for atts in attachments_by_parent.values())}")
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
    
    async def fetch_groups(self) -> List[Dict[str, Any]]:
        """
        Fetch all groups the user has access to.
        
        Returns:
            List of group objects with id, name, and type
        """
        groups = []
        
        # First, add the user's personal library
        groups.append({
            "id": f"users/{self._config.zotero_user_id}",
            "name": "My Library",
            "type": "user",
            "owner": None
        })
        
        # Then fetch groups
        url = f"{self.BASE_URL}/users/{self._config.zotero_user_id}/groups"
        
        async with self._session.get(url) as response:
            if response.status == 200:
                group_data = await response.json()
                for group in group_data:
                    data = group.get("data", {})
                    groups.append({
                        "id": f"groups/{data.get('id')}",
                        "name": data.get("name", "Unknown Group"),
                        "type": data.get("type", "Private"),
                        "owner": data.get("owner")
                    })
        
        return groups
    
    async def fetch_collections(self, library_id: str = None) -> List[Dict[str, Any]]:
        """
        Fetch all collections from a library.
        
        Args:
            library_id: Library ID (e.g., "users/12345" or "groups/67890").
                       If None, uses user's personal library.
                       
        Returns:
            List of collection objects with key, name, and parentCollection
        """
        if library_id is None:
            library_id = f"users/{self._config.zotero_user_id}"
        
        collections = []
        url = f"{self.BASE_URL}/{library_id}/collections"
        
        async with self._session.get(url) as response:
            if response.status == 200:
                collection_data = await response.json()
                for collection in collection_data:
                    data = collection.get("data", {})
                    collections.append({
                        "key": data.get("key"),
                        "name": data.get("name", "Unknown Collection"),
                        "parentCollection": data.get("parentCollection"),
                        "libraryId": library_id
                    })
        
        return collections