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

from app.models import Paper, User, ZoteroSync, ZoteroConfig, PaperChunk
from app.services.paper_processor import PaperProcessorService
from app.core.config import settings
from app.utils.logging_utils import log_async_info, log_async_error
from app.models.system_log import LogCategory

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
        self._sync_progress: Dict[str, Any] = {
            "status": "idle",
            "current": 0,
            "total": 0,
            "message": "",
            "libraries_processed": 0,
            "libraries_total": 0
        }
    
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
                success = response.status == 200
                if success:
                    await log_async_info(
                        self.db,
                        LogCategory.ZOTERO_SYNC,
                        "Zotero connection test successful",
                        user_id=self.user_id
                    )
                else:
                    await log_async_error(
                        self.db,
                        LogCategory.ZOTERO_SYNC,
                        f"Zotero connection test failed with status {response.status}",
                        Exception(f"HTTP {response.status}"),
                        user_id=self.user_id
                    )
                return success
        except Exception as e:
            logger.error(f"Zotero connection test failed: {e}")
            await log_async_error(
                self.db,
                LogCategory.ZOTERO_SYNC,
                "Zotero connection test failed",
                e,
                user_id=self.user_id
            )
            return False
    
    def get_sync_progress(self) -> Dict[str, Any]:
        """Get current sync progress."""
        return self._sync_progress.copy()
    
    def _update_sync_progress(self, **kwargs) -> None:
        """Update sync progress."""
        self._sync_progress.update(kwargs)
    
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
        selected_collections_by_library = {}  # Map library_id -> [collection_keys]
        has_old_format_collections = False
        
        if self._config.selected_groups:
            try:
                selected_groups = json.loads(self._config.selected_groups)
            except:
                selected_groups = []
                
        if self._config.selected_collections:
            try:
                collections_data = json.loads(self._config.selected_collections)
                # Handle both old format (list of keys) and new format (list of {key, libraryId})
                for collection in collections_data:
                    if isinstance(collection, dict) and 'key' in collection and 'libraryId' in collection:
                        # New format with library ID
                        lib_id = collection['libraryId']
                        key = collection['key']
                        if lib_id not in selected_collections_by_library:
                            selected_collections_by_library[lib_id] = []
                        selected_collections_by_library[lib_id].append(key)
                        selected_collections.append(key)  # Keep for backward compatibility
                    else:
                        # Old format - just collection key
                        selected_collections.append(collection)
                        has_old_format_collections = True
            except:
                selected_collections = []
        
        logger.info(f"Selected collections: {selected_collections}")
        logger.info(f"Collections by library: {selected_collections_by_library}")
        logger.info(f"Has old format collections: {has_old_format_collections}")
        
        # Determine which libraries to fetch from
        libraries_to_fetch = set(selected_groups)
        
        # Add libraries that contain selected collections (new format)
        libraries_to_fetch.update(selected_collections_by_library.keys())
        
        # If we have old-format collections, we need to search all libraries
        if has_old_format_collections:
            logger.info("Old format collections detected - will search all available libraries")
            # First, always check user's personal library
            personal_library = f"users/{self._config.zotero_user_id}"
            libraries_to_fetch.add(personal_library)
            
            # Then add all groups the user has access to
            try:
                groups = await self.fetch_groups()
                for group in groups:
                    if group["type"] != "user":  # Skip the personal library entry
                        libraries_to_fetch.add(group["id"])
                logger.info(f"Will search {len(libraries_to_fetch)} libraries for collections: {selected_collections}")
            except Exception as e:
                logger.error(f"Failed to fetch groups for collection search: {e}")
                logger.warning("Will only search personal library for collections")
        
        # If no specific selections, fetch from user's personal library
        if not libraries_to_fetch and not selected_collections:
            libraries_to_fetch.add(f"users/{self._config.zotero_user_id}")
            logger.info("No specific groups or collections selected - fetching from personal library")
        
        logger.info(f"Will fetch from {len(libraries_to_fetch)} libraries: {list(libraries_to_fetch)}")
        
        # Update progress
        self._update_sync_progress(
            status="fetching",
            libraries_total=len(libraries_to_fetch),
            libraries_processed=0,
            message="Starting to fetch items from Zotero..."
        )
        
        # For old format collections, we need to discover which library contains them
        collection_to_library_map = {}
        if has_old_format_collections:
            logger.info("Discovering library locations for old format collections...")
            for library_id in libraries_to_fetch:
                try:
                    collections = await self.fetch_collections(library_id)
                    for col in collections:
                        if col['key'] in selected_collections:
                            collection_to_library_map[col['key']] = library_id
                            logger.info(f"Found collection {col['key']} ({col['name']}) in library {library_id}")
                except Exception as e:
                    logger.warning(f"Failed to fetch collections from {library_id}: {e}")
            
            # Log collections not found in any library
            not_found = [c for c in selected_collections if c not in collection_to_library_map and not isinstance(c, dict)]
            if not_found:
                logger.warning(f"Collections not found in any library: {not_found}")
        
        # Fetch items from each library
        library_count = 0
        for library_id in libraries_to_fetch:
            # Determine which collections to filter for this library
            library_collections = []
            
            # Add collections explicitly assigned to this library (new format)
            if library_id in selected_collections_by_library:
                library_collections.extend(selected_collections_by_library[library_id])
            
            # Add old format collections that we found in this library
            if has_old_format_collections:
                for col_key, lib_id in collection_to_library_map.items():
                    if lib_id == library_id and col_key not in library_collections:
                        library_collections.append(col_key)
            
            # Skip this library if:
            # 1. We have selected collections AND
            # 2. This library has no collections to filter
            # This prevents fetching entire libraries when looking for specific collections
            if selected_collections and not library_collections:
                logger.info(f"Skipping {library_id} - no selected collections in this library")
                continue
            
            # Only apply collection filter if we have collections for this library
            filter_collections = library_collections if library_collections else None
            
            logger.info(f"Fetching from {library_id} with collection filter: {filter_collections}")
            
            papers, attachments = await self._fetch_items_from_library(
                library_id, 
                modified_since, 
                filter_collections
            )
            
            if papers:
                logger.info(f"Found {len(papers)} papers in {library_id}")
            
            all_papers.extend(papers)
            # Merge attachments dictionaries
            for key, value in attachments.items():
                if key not in all_attachments:
                    all_attachments[key] = []
                all_attachments[key].extend(value)
            
            # Update progress
            library_count += 1
            self._update_sync_progress(
                libraries_processed=library_count,
                message=f"Fetched items from {library_count}/{len(libraries_to_fetch)} libraries"
            )
        
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
                        else:
                            logger.debug(f"Item {item.get('key')} matches collection filter - collections: {item_collections}")
                    
                    # This is a paper item
                    papers.append(item)
                
                # Check if there are more items
                total_results = int(response.headers.get("Total-Results", "0"))
                if start + len(batch) >= total_results:
                    break
                
                start += self.ITEMS_PER_PAGE
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
        
        attachment_count = sum(len(atts) for atts in attachments_by_parent.values())
        logger.info(f"Library {library_id}: Found {len(papers)} papers and {attachment_count} PDF attachments")
        
        if filter_collections and papers:
            logger.info(f"Collection filter applied: {len(papers)} papers match collections {filter_collections}")
        elif filter_collections and not papers:
            logger.warning(f"No papers found in collections {filter_collections} for library {library_id}")
            
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
                await log_async_info(
                    self.db,
                    LogCategory.PDF_PROCESSING,
                    f"Downloaded PDF attachment {attachment_key}",
                    user_id=self.user_id,
                    entity_type="attachment",
                    entity_id=attachment_key,
                    details={"file_path": file_path, "size": len(content)}
                )
                return file_path
        except Exception as e:
            logger.error(f"Error downloading PDF attachment {attachment_key}: {e}")
            await log_async_error(
                self.db,
                LogCategory.PDF_PROCESSING,
                f"Failed to download PDF attachment {attachment_key}",
                e,
                user_id=self.user_id,
                entity_type="attachment",
                entity_id=attachment_key
            )
            return None
    
    async def sync_library(self, force_full_sync: bool = False) -> Tuple[int, int, int]:
        """
        Sync entire Zotero library.
        
        Args:
            force_full_sync: If True, sync all items regardless of last sync time
            
        Returns:
            Tuple of (new_papers, updated_papers, failed_papers)
        """
        new_papers = 0
        updated_papers = 0
        failed_papers = 0
        
        logger.info(f"Starting Zotero sync (force_full_sync={force_full_sync})")
        
        # Log sync start
        await log_async_info(
            self.db,
            LogCategory.ZOTERO_SYNC,
            f"Starting Zotero sync (force_full_sync={force_full_sync})",
            user_id=self.user_id,
            details={"force_full_sync": force_full_sync}
        )
        
        # Initialize progress
        self._update_sync_progress(
            status="starting",
            current=0,
            total=0,
            message="Preparing to sync with Zotero...",
            libraries_processed=0,
            libraries_total=0
        )
        
        # Get last sync time (only use if not forcing full sync)
        last_sync = None if force_full_sync else (self._config.last_sync if self._config else None)
        
        if force_full_sync:
            logger.info("Force full sync enabled - ignoring last sync timestamp")
        elif last_sync:
            logger.info(f"Incremental sync - fetching items modified since {last_sync}")
        else:
            logger.info("No previous sync found - performing full sync")
        
        # Fetch items from Zotero (papers and attachments)
        papers, attachments_by_parent = await self.fetch_library_items(modified_since=last_sync)
        
        logger.info(f"Fetched {len(papers)} papers from Zotero")
        if not papers:
            logger.warning("No papers found to sync. Check your Zotero library and collection settings.")
        
        # Update progress
        self._update_sync_progress(
            status="processing",
            current=0,
            total=len(papers),
            message=f"Processing {len(papers)} papers..."
        )
        
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
        
        paper_count = 0
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
                    logger.debug(f"Skipping paper {zotero_key} - already up to date (version {zotero_version})")
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
                
                # Download and process PDF if:
                # 1. It's a new paper or newly linked (not existing_sync)
                # 2. Paper doesn't have a file yet (not paper.file_path)
                # 3. Paper isn't processed yet (not paper.is_processed)
                should_process_pdf = not existing_sync and (not paper.file_path or not paper.is_processed)
                
                if should_process_pdf:
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
                            
                            # Save to get paper ID if needed
                            await self.db.flush()
                            
                            logger.info(f"Processing PDF for paper {paper.id}: {paper.title[:50]}...")
                            
                            # Process the paper asynchronously (chunks and embeddings)
                            try:
                                await PaperProcessorService.process_paper(
                                    str(paper.id),
                                    file_path
                                )
                                logger.info(f"Successfully processed PDF for paper {paper.id}")
                            except Exception as process_error:
                                logger.error(f"Failed to process PDF for paper {paper.id}: {process_error}")
                                paper.processing_error = str(process_error)
                                paper.is_processed = False
                            
                            await self.db.flush()
                            
                            # Only process the first PDF
                            break
                    else:
                        # No PDF attachments found
                        logger.info(f"No PDF attachments found for paper {zotero_key}: {paper.title[:50]}...")
                elif existing_sync and paper.file_path and not paper.is_processed:
                    # Paper exists with file but wasn't processed - process it now
                    logger.info(f"Reprocessing existing PDF for paper {paper.id}: {paper.title[:50]}...")
                    try:
                        await PaperProcessorService.process_paper(
                            str(paper.id),
                            paper.file_path
                        )
                        logger.info(f"Successfully reprocessed PDF for paper {paper.id}")
                    except Exception as process_error:
                        logger.error(f"Failed to reprocess PDF for paper {paper.id}: {process_error}")
                        paper.processing_error = str(process_error)
                        paper.is_processed = False
                
                # Commit this item's changes
                await self.db.commit()
                
            except Exception as e:
                logger.error(f"Failed to sync Zotero item {item.get('key')}: {e}", exc_info=True)
                failed_papers += 1
                
                # Rollback any changes for this item
                await self.db.rollback()
                continue
            
            # Update progress
            paper_count += 1
            self._update_sync_progress(
                current=paper_count,
                message=f"Processed {paper_count}/{len(papers)} papers ({new_papers} new, {updated_papers} updated, {failed_papers} failed)"
            )
        
        # Update last sync time and final progress
        if self._config:
            self._config.last_sync = datetime.utcnow()
            self._config.last_sync_status = f"Synced: {new_papers} new, {updated_papers} updated, {failed_papers} failed"
            await self.db.commit()
        
        # Update final progress
        self._update_sync_progress(
            status="completed",
            current=len(papers),
            message=f"Sync complete: {new_papers} new, {updated_papers} updated, {failed_papers} failed"
        )
        
        # Log processing status
        await self._log_processing_status()
        
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
    
    async def _log_processing_status(self):
        """Log the processing status of all papers."""
        # Count papers by processing status
        result = await self.db.execute(
            select(Paper)
            .join(ZoteroSync)
            .where(ZoteroSync.user_id == self.user_id)
        )
        papers = result.scalars().all()
        
        total_papers = len(papers)
        processed_papers = sum(1 for p in papers if p.is_processed)
        papers_with_files = sum(1 for p in papers if p.file_path)
        papers_with_errors = sum(1 for p in papers if p.processing_error)
        
        logger.info(f"\nPaper Processing Status:")
        logger.info(f"  Total papers: {total_papers}")
        logger.info(f"  Papers with files: {papers_with_files}")
        logger.info(f"  Successfully processed: {processed_papers}")
        logger.info(f"  Processing errors: {papers_with_errors}")
        logger.info(f"  Not processed yet: {total_papers - processed_papers - papers_with_errors}")
        
        # Log papers with errors for debugging
        if papers_with_errors > 0:
            logger.warning("Papers with processing errors:")
            for paper in papers:
                if paper.processing_error:
                    logger.warning(f"  - {paper.title[:50]}...: {paper.processing_error}")
    
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
    
    async def migrate_collection_format(self) -> bool:
        """
        Migrate old format collections (just keys) to new format (with library IDs).
        
        Returns:
            True if migration was performed, False if no migration needed
        """
        if not self._config or not self._config.selected_collections:
            return False
            
        import json
        try:
            collections_data = json.loads(self._config.selected_collections)
            needs_migration = False
            migrated_collections = []
            
            # Check if any collections are in old format
            for collection in collections_data:
                if isinstance(collection, str):
                    needs_migration = True
                    break
                elif isinstance(collection, dict) and 'key' in collection and 'libraryId' in collection:
                    # Already in new format
                    migrated_collections.append(collection)
                    
            if not needs_migration:
                logger.info("Collections already in new format - no migration needed")
                return False
                
            logger.info("Migrating collections from old format to new format...")
            
            # Get all available collections from all libraries
            collection_map = {}  # key -> {libraryId, name}
            
            # Fetch from all libraries
            groups = await self.fetch_groups()
            for group in groups:
                library_id = group['id']
                try:
                    collections = await self.fetch_collections(library_id)
                    for col in collections:
                        key = col['key']
                        if key not in collection_map:
                            collection_map[key] = {
                                'key': key,
                                'libraryId': library_id,
                                'name': col['name']
                            }
                except Exception as e:
                    logger.warning(f"Failed to fetch collections from {library_id}: {e}")
                    
            # Migrate old format collections
            for collection in collections_data:
                if isinstance(collection, str):
                    # Old format - find library
                    if collection in collection_map:
                        migrated = collection_map[collection]
                        migrated_collections.append({
                            'key': migrated['key'],
                            'libraryId': migrated['libraryId']
                        })
                        logger.info(f"Migrated collection {collection} ({migrated['name']}) to library {migrated['libraryId']}")
                    else:
                        logger.warning(f"Collection {collection} not found in any library - skipping")
                        
            # Update configuration
            self._config.selected_collections = json.dumps(migrated_collections)
            await self.db.commit()
            
            logger.info(f"Migration complete - migrated {len(migrated_collections)} collections")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate collections: {e}")
            return False