"""External metadata fetching service for academic papers."""
import re
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Optional, List, Any
from datetime import datetime
import httpx
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

logger = logging.getLogger(__name__)


class ArxivClient:
    """Client for fetching metadata from arXiv API."""
    
    BASE_URL = "https://export.arxiv.org/api/query"
    NAMESPACE = {'atom': 'http://www.w3.org/2005/Atom'}
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    async def fetch_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for a specific arXiv ID.
        
        Args:
            arxiv_id: arXiv identifier (e.g., "2506.06352v1" or "2506.06352")
            
        Returns:
            Dictionary with paper metadata or None if not found
        """
        try:
            # Clean the arXiv ID
            arxiv_id = self._clean_arxiv_id(arxiv_id)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={"id_list": arxiv_id}
                )
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.text)
                
                # Find the entry
                entry = root.find('.//atom:entry', self.NAMESPACE)
                if entry is None:
                    logger.warning(f"No entry found for arXiv ID: {arxiv_id}")
                    return None
                
                # Extract metadata
                metadata = self._extract_metadata_from_entry(entry)
                metadata['arxiv_id'] = arxiv_id
                metadata['source'] = 'arxiv'
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error fetching arXiv metadata for {arxiv_id}: {e}")
            return None
    
    def _clean_arxiv_id(self, arxiv_id: str) -> str:
        """Clean and validate arXiv ID."""
        # Remove common prefixes
        arxiv_id = arxiv_id.replace('arXiv:', '').replace('arxiv:', '')
        arxiv_id = arxiv_id.strip()
        
        # Validate format (YYMM.NNNNN or YYMM.NNNN or older format)
        # Updated to handle both 4 and 5 digit IDs after the dot
        if not re.match(r'^\d{4}\.\d{4,5}(v\d+)?$|^[a-z\-]+/\d{7}(v\d+)?$', arxiv_id):
            logger.warning(f"Invalid arXiv ID format: {arxiv_id}")
        
        return arxiv_id
    
    def _extract_metadata_from_entry(self, entry: ET.Element) -> Dict[str, Any]:
        """Extract metadata from an arXiv entry element."""
        metadata = {}
        
        # Title
        title_elem = entry.find('atom:title', self.NAMESPACE)
        if title_elem is not None and title_elem.text:
            # Clean up title (remove newlines and extra spaces)
            metadata['title'] = ' '.join(title_elem.text.strip().split())
        
        # Authors
        authors = []
        for author_elem in entry.findall('atom:author', self.NAMESPACE):
            name_elem = author_elem.find('atom:name', self.NAMESPACE)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())
        if authors:
            metadata['authors'] = authors
        
        # Abstract
        summary_elem = entry.find('atom:summary', self.NAMESPACE)
        if summary_elem is not None and summary_elem.text:
            metadata['abstract'] = ' '.join(summary_elem.text.strip().split())
        
        # Published date
        published_elem = entry.find('atom:published', self.NAMESPACE)
        if published_elem is not None and published_elem.text:
            try:
                pub_date = datetime.fromisoformat(published_elem.text.replace('Z', '+00:00'))
                metadata['year'] = pub_date.year
                metadata['published_date'] = published_elem.text
            except:
                pass
        
        # DOI if available
        doi_elem = entry.find('.//atom:link[@title="doi"]', self.NAMESPACE)
        if doi_elem is not None:
            doi_url = doi_elem.get('href', '')
            if 'doi.org/' in doi_url:
                metadata['doi'] = doi_url.split('doi.org/')[-1]
        
        # PDF URL
        pdf_elem = entry.find('.//atom:link[@type="application/pdf"]', self.NAMESPACE)
        if pdf_elem is not None:
            metadata['pdf_url'] = pdf_elem.get('href', '')
        
        # Categories
        categories = []
        for cat_elem in entry.findall('atom:category', self.NAMESPACE):
            term = cat_elem.get('term', '')
            if term:
                categories.append(term)
        if categories:
            metadata['categories'] = categories
            # Use first category as venue/journal approximation
            metadata['venue'] = f"arXiv ({categories[0]})"
        
        return metadata


class CrossrefClient:
    """Client for fetching metadata from Crossref API."""
    
    BASE_URL = "https://api.crossref.org"
    
    def __init__(self, email: Optional[str] = None, timeout: int = 30):
        self.email = email
        self.timeout = timeout
        self.headers = {
            'User-Agent': f'AcademicCitationAssistant/1.0 (mailto:{email})' if email else 'AcademicCitationAssistant/1.0'
        }
    
    async def fetch_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for a specific DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            Dictionary with paper metadata or None if not found
        """
        try:
            # Clean DOI
            doi = self._clean_doi(doi)
            
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                response = await client.get(f"{self.BASE_URL}/works/{doi}")
                
                if response.status_code == 404:
                    logger.warning(f"DOI not found: {doi}")
                    return None
                    
                response.raise_for_status()
                
                data = response.json()
                if 'message' not in data:
                    return None
                
                # Extract metadata
                metadata = self._extract_metadata_from_work(data['message'])
                metadata['doi'] = doi
                metadata['source'] = 'crossref'
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error fetching Crossref metadata for {doi}: {e}")
            return None
    
    def _clean_doi(self, doi: str) -> str:
        """Clean and validate DOI."""
        # Remove common prefixes
        doi = doi.replace('https://doi.org/', '')
        doi = doi.replace('http://doi.org/', '')
        doi = doi.replace('doi:', '')
        doi = doi.strip()
        
        return doi
    
    def _extract_metadata_from_work(self, work: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from a Crossref work object."""
        metadata = {}
        
        # Title
        if 'title' in work and work['title']:
            metadata['title'] = work['title'][0]
        
        # Authors
        authors = []
        if 'author' in work:
            for author in work['author']:
                parts = []
                if 'given' in author:
                    parts.append(author['given'])
                if 'family' in author:
                    parts.append(author['family'])
                if parts:
                    authors.append(' '.join(parts))
        if authors:
            metadata['authors'] = authors
        
        # Abstract
        if 'abstract' in work:
            metadata['abstract'] = work['abstract']
        
        # Year
        if 'published-print' in work:
            date_parts = work['published-print'].get('date-parts', [[]])
            if date_parts and date_parts[0]:
                metadata['year'] = date_parts[0][0]
        elif 'published-online' in work:
            date_parts = work['published-online'].get('date-parts', [[]])
            if date_parts and date_parts[0]:
                metadata['year'] = date_parts[0][0]
        
        # Journal/Venue
        if 'container-title' in work and work['container-title']:
            metadata['journal'] = work['container-title'][0]
        
        # Publisher
        if 'publisher' in work:
            metadata['publisher'] = work['publisher']
        
        # URL
        if 'URL' in work:
            metadata['url'] = work['URL']
        
        # Citation count (if available)
        if 'is-referenced-by-count' in work:
            metadata['citation_count'] = work['is-referenced-by-count']
        
        return metadata


class MetadataFetcherService:
    """Service that coordinates metadata fetching from multiple sources."""
    
    def __init__(self, email: Optional[str] = None):
        self.arxiv_client = ArxivClient()
        self.crossref_client = CrossrefClient(email=email)
    
    async def fetch_metadata(self, identifiers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata using available identifiers.
        
        Args:
            identifiers: Dictionary with possible keys: 'arxiv_id', 'doi', 'pmid', etc.
            
        Returns:
            Dictionary with paper metadata or None if not found
        """
        metadata = None
        
        # Try arXiv first if we have an arXiv ID
        if 'arxiv_id' in identifiers and identifiers['arxiv_id']:
            logger.info(f"Trying to fetch metadata from arXiv for ID: {identifiers['arxiv_id']}")
            metadata = await self.arxiv_client.fetch_by_id(identifiers['arxiv_id'])
            if metadata:
                logger.info(f"Successfully fetched metadata from arXiv")
                return metadata
        
        # Try Crossref if we have a DOI
        if 'doi' in identifiers and identifiers['doi']:
            logger.info(f"Trying to fetch metadata from Crossref for DOI: {identifiers['doi']}")
            metadata = await self.crossref_client.fetch_by_doi(identifiers['doi'])
            if metadata:
                logger.info(f"Successfully fetched metadata from Crossref")
                return metadata
        
        # Future: Add more sources (Semantic Scholar, PubMed, etc.)
        
        return None
    
    def extract_identifiers_from_text(self, text: str) -> Dict[str, str]:
        """
        Extract paper identifiers from text content.
        
        Args:
            text: Text content from PDF or other source
            
        Returns:
            Dictionary with found identifiers
        """
        identifiers = {}
        
        # Extract arXiv ID
        # Patterns: arXiv:2506.06352v1, arXiv:2506.06352, 2506.06352v1, DOI with arXiv
        arxiv_patterns = [
            r'arXiv[:\s]+(\d{4}\.\d{4,5}(?:v\d+)?)',
            r'arxiv[:\s]+(\d{4}\.\d{4,5}(?:v\d+)?)',
            r'10\.48550/arXiv\.(\d{4}\.\d{4,5}(?:v\d+)?)',  # DOI pattern for arXiv
            r'/arXiv\.(\d{4}\.\d{4,5}(?:v\d+)?)',  # Anywhere in DOI
            r'\b(\d{4}\.\d{4,5}(?:v\d+)?)\b'  # Just the number pattern
        ]
        
        for pattern in arxiv_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                identifiers['arxiv_id'] = match.group(1)
                break
        
        # Extract DOI
        # Patterns: 10.xxxx/yyyy, doi:10.xxxx/yyyy, https://doi.org/10.xxxx/yyyy
        doi_patterns = [
            r'(?:doi[:\s]+|https?://doi\.org/)(10\.\d{4,}/[-._;()/:\w]+)',
            r'\b(10\.\d{4,}/[-._;()/:\w]+)\b'
        ]
        
        for pattern in doi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doi = match.group(1)
                identifiers['doi'] = doi
                
                # If it's an arXiv DOI and we haven't found an arXiv ID yet, extract it
                if 'arxiv_id' not in identifiers and 'arXiv' in doi:
                    arxiv_match = re.search(r'arXiv\.(\d{4}\.\d{4,5}(?:v\d+)?)', doi, re.IGNORECASE)
                    if arxiv_match:
                        identifiers['arxiv_id'] = arxiv_match.group(1)
                break
        
        # Extract PMID (PubMed ID)
        pmid_pattern = r'(?:PMID|pmid)[:\s]+(\d+)'
        match = re.search(pmid_pattern, text)
        if match:
            identifiers['pmid'] = match.group(1)
        
        # Log what we found for debugging
        if identifiers:
            logger.info(f"Extracted identifiers: {identifiers}")
        
        return identifiers
    
    def parse_bibtex(self, bibtex_string: str) -> Optional[Dict[str, Any]]:
        """
        Parse BibTeX string and extract metadata.
        
        Args:
            bibtex_string: BibTeX formatted string
            
        Returns:
            Dictionary with paper metadata or None if parsing fails
        """
        try:
            parser = BibTexParser()
            parser.customization = convert_to_unicode
            bib_database = bibtexparser.loads(bibtex_string, parser=parser)
            
            if not bib_database.entries:
                return None
            
            # Take the first entry
            entry = bib_database.entries[0]
            metadata = {}
            
            # Map BibTeX fields to our metadata schema
            if 'title' in entry:
                metadata['title'] = entry['title'].strip('{}')
            
            if 'author' in entry:
                # Parse author field (usually "Last, First and Last, First")
                authors = []
                author_string = entry['author']
                # Split by 'and'
                for author in author_string.split(' and '):
                    author = author.strip()
                    # Handle "Last, First" format
                    if ',' in author:
                        parts = author.split(',', 1)
                        author = f"{parts[1].strip()} {parts[0].strip()}"
                    authors.append(author)
                metadata['authors'] = authors
            
            if 'year' in entry:
                try:
                    metadata['year'] = int(entry['year'])
                except:
                    pass
            
            if 'journal' in entry:
                metadata['journal'] = entry['journal'].strip('{}')
            elif 'booktitle' in entry:
                metadata['journal'] = entry['booktitle'].strip('{}')
            
            if 'doi' in entry:
                metadata['doi'] = entry['doi']
            
            if 'abstract' in entry:
                metadata['abstract'] = entry['abstract'].strip('{}')
            
            if 'arxivid' in entry or 'eprint' in entry:
                metadata['arxiv_id'] = entry.get('arxivid', entry.get('eprint', ''))
            
            metadata['source'] = 'bibtex'
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error parsing BibTeX: {e}")
            return None