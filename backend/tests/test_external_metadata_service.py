"""Tests for external metadata fetching service."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
import xml.etree.ElementTree as ET
from app.services.external_metadata_service import (
    ArxivClient, 
    CrossrefClient, 
    MetadataFetcherService
)


class TestArxivClient:
    """Test ArXiv API client."""
    
    @pytest_asyncio.fixture
    async def client(self):
        return ArxivClient(timeout=5)
    
    @pytest.mark.asyncio
    async def test_clean_arxiv_id(self, client):
        """Test arXiv ID cleaning."""
        assert client._clean_arxiv_id("arXiv:2506.06352v1") == "2506.06352v1"
        assert client._clean_arxiv_id("arxiv:2506.06352") == "2506.06352"
        assert client._clean_arxiv_id("2506.06352v2") == "2506.06352v2"
        assert client._clean_arxiv_id("arXiv: 2506.06352 ") == "2506.06352"
    
    @pytest.mark.asyncio
    async def test_extract_metadata_from_entry(self, client):
        """Test metadata extraction from XML entry."""
        # Mock XML entry
        xml_data = """
        <entry xmlns="http://www.w3.org/2005/Atom">
            <title>Test Paper Title</title>
            <author><name>John Doe</name></author>
            <author><name>Jane Smith</name></author>
            <summary>This is the abstract of the test paper.</summary>
            <published>2024-01-15T00:00:00Z</published>
            <link href="http://dx.doi.org/10.1234/test" title="doi"/>
            <link href="http://arxiv.org/pdf/2401.12345v1" type="application/pdf"/>
            <category term="cs.AI"/>
            <category term="cs.LG"/>
        </entry>
        """
        entry = ET.fromstring(xml_data)
        
        metadata = client._extract_metadata_from_entry(entry)
        
        assert metadata['title'] == "Test Paper Title"
        assert metadata['authors'] == ["John Doe", "Jane Smith"]
        assert metadata['abstract'] == "This is the abstract of the test paper."
        assert metadata['year'] == 2024
        assert metadata['doi'] == "10.1234/test"
        assert metadata['pdf_url'] == "http://arxiv.org/pdf/2401.12345v1"
        assert metadata['categories'] == ["cs.AI", "cs.LG"]
        assert metadata['venue'] == "arXiv (cs.AI)"
    
    @pytest.mark.asyncio
    async def test_fetch_by_id_success(self, client):
        """Test successful fetch by arXiv ID."""
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Real Paper Title</title>
                <author><name>Author Name</name></author>
                <summary>Paper abstract.</summary>
                <published>2023-06-15T00:00:00Z</published>
            </entry>
        </feed>"""
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance
            
            metadata = await client.fetch_by_id("2306.12345")
            
            assert metadata is not None
            assert metadata['title'] == "Real Paper Title"
            assert metadata['authors'] == ["Author Name"]
            assert metadata['arxiv_id'] == "2306.12345"
            assert metadata['source'] == 'arxiv'


class TestCrossrefClient:
    """Test Crossref API client."""
    
    @pytest_asyncio.fixture
    async def client(self):
        return CrossrefClient(email="test@example.com", timeout=5)
    
    @pytest.mark.asyncio
    async def test_clean_doi(self, client):
        """Test DOI cleaning."""
        assert client._clean_doi("https://doi.org/10.1234/test") == "10.1234/test"
        assert client._clean_doi("http://doi.org/10.1234/test") == "10.1234/test"
        assert client._clean_doi("doi:10.1234/test") == "10.1234/test"
        assert client._clean_doi("10.1234/test") == "10.1234/test"
        assert client._clean_doi(" 10.1234/test ") == "10.1234/test"
    
    @pytest.mark.asyncio
    async def test_extract_metadata_from_work(self, client):
        """Test metadata extraction from Crossref work object."""
        work = {
            'title': ['Test Paper Title'],
            'author': [
                {'given': 'John', 'family': 'Doe'},
                {'given': 'Jane', 'family': 'Smith'}
            ],
            'abstract': 'This is the paper abstract.',
            'published-print': {'date-parts': [[2024, 3, 15]]},
            'container-title': ['Journal of Testing'],
            'publisher': 'Test Publisher',
            'URL': 'https://example.com/paper',
            'is-referenced-by-count': 42
        }
        
        metadata = client._extract_metadata_from_work(work)
        
        assert metadata['title'] == 'Test Paper Title'
        assert metadata['authors'] == ['John Doe', 'Jane Smith']
        assert metadata['abstract'] == 'This is the paper abstract.'
        assert metadata['year'] == 2024
        assert metadata['journal'] == 'Journal of Testing'
        assert metadata['publisher'] == 'Test Publisher'
        assert metadata['url'] == 'https://example.com/paper'
        assert metadata['citation_count'] == 42
    
    @pytest.mark.asyncio
    async def test_fetch_by_doi_success(self, client):
        """Test successful fetch by DOI."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={
            'message': {
                'title': ['Paper Title'],
                'author': [{'given': 'A', 'family': 'Author'}],
                'published-online': {'date-parts': [[2023, 12, 1]]}
            }
        })
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance
            
            metadata = await client.fetch_by_doi("10.1234/test")
            
            assert metadata is not None
            assert metadata['title'] == 'Paper Title'
            assert metadata['doi'] == '10.1234/test'
            assert metadata['source'] == 'crossref'


class TestMetadataFetcherService:
    """Test unified metadata fetching service."""
    
    @pytest_asyncio.fixture
    async def service(self):
        return MetadataFetcherService(email="test@example.com")
    
    @pytest.mark.asyncio
    async def test_extract_identifiers_from_text(self, service):
        """Test identifier extraction from text."""
        text = """
        This paper is available at arXiv:2306.12345v1.
        You can also find it at https://doi.org/10.1234/example.
        The PubMed ID is PMID: 12345678.
        """
        
        identifiers = service.extract_identifiers_from_text(text)
        
        assert identifiers['arxiv_id'] == '2306.12345v1'
        assert identifiers['doi'] == '10.1234/example'
        assert identifiers['pmid'] == '12345678'
    
    @pytest.mark.asyncio
    async def test_parse_bibtex(self, service):
        """Test BibTeX parsing."""
        bibtex = """
        @article{test2024,
            title = {Test Paper Title},
            author = {Doe, John and Smith, Jane},
            year = {2024},
            journal = {Journal of Testing},
            doi = {10.1234/test},
            abstract = {This is the abstract.}
        }
        """
        
        metadata = service.parse_bibtex(bibtex)
        
        assert metadata is not None
        assert metadata['title'] == 'Test Paper Title'
        assert metadata['authors'] == ['John Doe', 'Jane Smith']
        assert metadata['year'] == 2024
        assert metadata['journal'] == 'Journal of Testing'
        assert metadata['doi'] == '10.1234/test'
        assert metadata['abstract'] == 'This is the abstract.'
        assert metadata['source'] == 'bibtex'
    
    @pytest.mark.asyncio
    async def test_fetch_metadata_arxiv_first(self, service):
        """Test that arXiv is tried first when available."""
        identifiers = {
            'arxiv_id': '2306.12345',
            'doi': '10.1234/test'
        }
        
        # Mock successful arXiv response
        arxiv_metadata = {'title': 'From arXiv', 'source': 'arxiv'}
        service.arxiv_client.fetch_by_id = AsyncMock(return_value=arxiv_metadata)
        service.crossref_client.fetch_by_doi = AsyncMock()
        
        result = await service.fetch_metadata(identifiers)
        
        assert result == arxiv_metadata
        service.arxiv_client.fetch_by_id.assert_called_once_with('2306.12345')
        service.crossref_client.fetch_by_doi.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fetch_metadata_fallback_to_crossref(self, service):
        """Test fallback to Crossref when arXiv fails."""
        identifiers = {
            'arxiv_id': '2306.12345',
            'doi': '10.1234/test'
        }
        
        # Mock failed arXiv, successful Crossref
        crossref_metadata = {'title': 'From Crossref', 'source': 'crossref'}
        service.arxiv_client.fetch_by_id = AsyncMock(return_value=None)
        service.crossref_client.fetch_by_doi = AsyncMock(return_value=crossref_metadata)
        
        result = await service.fetch_metadata(identifiers)
        
        assert result == crossref_metadata
        service.arxiv_client.fetch_by_id.assert_called_once_with('2306.12345')
        service.crossref_client.fetch_by_doi.assert_called_once_with('10.1234/test')