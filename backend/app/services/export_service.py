"""Export services for documents and papers."""
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.document_paper import DocumentPaper
from app.models.paper import Paper


class ExportService:
    """Service for exporting documents and papers to various formats."""
    
    @staticmethod
    async def export_document_bibtex(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> str:
        """Export all papers assigned to a document as BibTeX."""
        # Get document with papers
        result = await db.execute(
            select(Document)
            .where(Document.id == document_id, Document.owner_id == user_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            raise ValueError("Document not found")
        
        # Get all papers assigned to this document
        result = await db.execute(
            select(DocumentPaper)
            .options(selectinload(DocumentPaper.paper))
            .where(DocumentPaper.document_id == document_id)
            .order_by(DocumentPaper.position)
        )
        doc_papers = result.scalars().all()
        
        if not doc_papers:
            return "% No papers assigned to this document\n"
        
        # Generate BibTeX entries
        bibtex_entries = [
            f"% BibTeX export for document: {document.title}\n",
            f"% Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"% Total papers: {len(doc_papers)}\n\n"
        ]
        
        for doc_paper in doc_papers:
            paper = doc_paper.paper
            entry = ExportService._generate_bibtex_entry(paper)
            if doc_paper.notes:
                entry = f"% Notes: {doc_paper.notes}\n{entry}"
            bibtex_entries.append(entry)
        
        return "\n".join(bibtex_entries)
    
    @staticmethod
    def _generate_bibtex_entry(paper: Paper) -> str:
        """Generate a BibTeX entry for a single paper."""
        # Generate citation key
        citation_key = ExportService._generate_citation_key(paper)
        
        # Determine entry type
        entry_type = "article"  # Default
        if paper.arxiv_id:
            entry_type = "misc"  # ArXiv papers are typically misc
        elif paper.journal and paper.journal.lower() in ["arxiv", "biorxiv", "medrxiv"]:
            entry_type = "misc"
        
        # Start building the entry
        entry_lines = [f"@{entry_type}{{{citation_key},"]
        
        # Required fields
        entry_lines.append(f'  title = {{{paper.title}}},')
        
        # Authors
        if paper.authors:
            authors_str = " and ".join(paper.authors)
            entry_lines.append(f'  author = {{{authors_str}}},')
        
        # Year
        if paper.year:
            entry_lines.append(f'  year = {{{paper.year}}},')
        
        # Journal/venue
        if paper.journal:
            if entry_type == "article":
                entry_lines.append(f'  journal = {{{paper.journal}}},')
            else:
                entry_lines.append(f'  howpublished = {{{paper.journal}}},')
        
        # Identifiers
        if paper.doi:
            entry_lines.append(f'  doi = {{{paper.doi}}},')
        
        if paper.arxiv_id:
            entry_lines.append(f'  eprint = {{{paper.arxiv_id}}},')
            entry_lines.append('  archivePrefix = {arXiv},')
        
        if paper.pubmed_id:
            entry_lines.append(f'  pmid = {{{paper.pubmed_id}}},')
        
        # URL
        if paper.source_url:
            entry_lines.append(f'  url = {{{paper.source_url}}},')
        
        # Abstract
        if paper.abstract:
            # Clean abstract for BibTeX
            abstract_clean = paper.abstract.replace('\n', ' ').replace('"', "''")
            entry_lines.append(f'  abstract = {{{abstract_clean}}},')
        
        # Remove trailing comma from last line
        if entry_lines[-1].endswith(','):
            entry_lines[-1] = entry_lines[-1][:-1]
        
        entry_lines.append("}\n")
        
        return "\n".join(entry_lines)
    
    @staticmethod
    def _generate_citation_key(paper: Paper) -> str:
        """Generate a citation key for a paper."""
        # Basic format: FirstAuthorLastName:Year:FirstWordOfTitle
        key_parts = []
        
        # Author part
        if paper.authors and len(paper.authors) > 0:
            first_author = paper.authors[0]
            # Extract last name (simple approach)
            last_name = first_author.split()[-1] if first_author else "Unknown"
            # Remove special characters
            last_name = re.sub(r'[^a-zA-Z]', '', last_name)
            key_parts.append(last_name)
        else:
            key_parts.append("Unknown")
        
        # Year part
        if paper.year:
            key_parts.append(str(paper.year))
        else:
            key_parts.append("0000")
        
        # Title part
        if paper.title:
            # Get first meaningful word from title
            title_words = paper.title.split()
            for word in title_words:
                # Skip common words
                if word.lower() not in ['a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for']:
                    clean_word = re.sub(r'[^a-zA-Z]', '', word)
                    if clean_word:
                        key_parts.append(clean_word)
                        break
        
        return "".join(key_parts)
    
    @staticmethod
    async def export_document_latex(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        template: str = "article",
        bib_filename: Optional[str] = None
    ) -> str:
        """Export document content to LaTeX format."""
        # Get document
        result = await db.execute(
            select(Document)
            .where(Document.id == document_id, Document.owner_id == user_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            raise ValueError("Document not found")
        
        # Start LaTeX document
        latex_lines = [
            "\\documentclass{article}",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage{hyperref}",
            "\\usepackage{cite}",
            "\\usepackage{graphicx}",
            "\\usepackage{amsmath}",
            "",
            f"\\title{{{ExportService._escape_latex(document.title)}}}",
            "\\author{Academic Citation Assistant}",
            f"\\date{{\\today}}",
            "",
            "\\begin{document}",
            "",
            "\\maketitle",
            ""
        ]
        
        # Add abstract if description exists
        if document.description:
            latex_lines.extend([
                "\\begin{abstract}",
                ExportService._escape_latex(document.description),
                "\\end{abstract}",
                ""
            ])
        
        # Convert document content
        if document.content:
            content_latex = ExportService._convert_lexical_to_latex(document.content)
            latex_lines.append(content_latex)
        elif document.plain_text:
            # Fallback to plain text
            latex_lines.append(ExportService._escape_latex(document.plain_text))
        
        # Add bibliography section if papers are assigned
        result = await db.execute(
            select(DocumentPaper)
            .where(DocumentPaper.document_id == document_id)
            .limit(1)
        )
        has_papers = result.scalar_one_or_none() is not None
        
        if has_papers:
            # Use custom bibliography filename if provided, otherwise use document title
            if bib_filename:
                bibliography_ref = bib_filename
            else:
                bibliography_ref = f"{document.title.replace(' ', '_')}_bibliography"
            
            latex_lines.extend([
                "",
                "\\bibliographystyle{plain}",
                f"\\bibliography{{{bibliography_ref}}}",
                ""
            ])
        
        latex_lines.append("\\end{document}")
        
        return "\n".join(latex_lines)
    
    @staticmethod
    def _escape_latex(text: str) -> str:
        """Escape special LaTeX characters."""
        if not text:
            return ""
        
        # LaTeX special characters
        replacements = {
            '\\': '\\textbackslash{}',
            '{': '\\{',
            '}': '\\}',
            '$': '\\$',
            '&': '\\&',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '~': '\\textasciitilde{}',
            '%': '\\%',
        }
        
        result = text
        for char, replacement in replacements.items():
            result = result.replace(char, replacement)
        
        return result
    
    @staticmethod
    def _convert_lexical_to_latex(content: Dict[str, Any]) -> str:
        """Convert Lexical editor JSON content to LaTeX."""
        # This is a simplified conversion - would need to be more sophisticated
        # to handle all Lexical node types properly
        latex_parts = []
        
        
        if "root" in content and "children" in content["root"]:
            for node in content["root"]["children"]:
                latex_part = ExportService._convert_lexical_node_to_latex(node)
                if latex_part:
                    latex_parts.append(latex_part)
        
        return "\n\n".join(latex_parts)
    
    @staticmethod
    def _convert_child_node_to_latex(node: Dict[str, Any]) -> str:
        """Convert a child node to LaTeX, handling different node types."""
        node_type = node.get("type", "")
        
        if node_type == "text":
            text = node.get("text", "")
            # Handle text formatting
            if node.get("format", 0) & 1:  # Bold
                text = f"\\textbf{{{ExportService._escape_latex(text)}}}"
            elif node.get("format", 0) & 2:  # Italic
                text = f"\\textit{{{ExportService._escape_latex(text)}}}"
            else:
                text = ExportService._escape_latex(text)
            return text
        
        elif node_type == "citation":
            # Handle citation nodes
            # Try different possible field names for the citation key
            citation_key = node.get("citationKey") or node.get("citation_key") or node.get("key") or ""
            if citation_key:
                return f"\\cite{{{citation_key}}}"
            # Fallback to paperId if no citation key
            paper_id = node.get("paperId") or node.get("paper_id") or ""
            if paper_id:
                return f"\\cite{{{paper_id}}}"
            # Last resort - use any available identifier
            return f"\\cite{{unknown}}"
        
        # For other types, try to extract text content
        return ExportService._get_text_from_node(node)
    
    @staticmethod
    def _convert_lexical_node_to_latex(node: Dict[str, Any]) -> str:
        """Convert a single Lexical node to LaTeX."""
        node_type = node.get("type", "")
        
        
        if node_type == "paragraph":
            text_parts = []
            for child in node.get("children", []):
                child_latex = ExportService._convert_child_node_to_latex(child)
                if child_latex:
                    text_parts.append(child_latex)
            return " ".join(text_parts)
        
        elif node_type == "heading":
            level = int(node.get("tag", "h1")[1])  # h1 -> 1, h2 -> 2, etc.
            section_commands = {
                1: "\\section",
                2: "\\subsection",
                3: "\\subsubsection",
                4: "\\paragraph",
                5: "\\subparagraph"
            }
            command = section_commands.get(level, "\\paragraph")
            # Process heading children to preserve citations
            text_parts = []
            for child in node.get("children", []):
                child_latex = ExportService._convert_child_node_to_latex(child)
                if child_latex:
                    text_parts.append(child_latex)
            text = " ".join(text_parts) if text_parts else ExportService._get_text_from_node(node)
            return f"{command}{{{text}}}"
        
        elif node_type == "list":
            list_type = node.get("listType", "bullet")
            env = "itemize" if list_type == "bullet" else "enumerate"
            items = []
            for child in node.get("children", []):
                # List items might be wrapped in listitem nodes
                if child.get("type") == "listitem":
                    # Process listitem's children
                    item_parts = []
                    for grandchild in child.get("children", []):
                        if grandchild.get("type") == "paragraph":
                            # Process paragraph's children
                            for ggchild in grandchild.get("children", []):
                                ggchild_latex = ExportService._convert_child_node_to_latex(ggchild)
                                if ggchild_latex:
                                    item_parts.append(ggchild_latex)
                        else:
                            grandchild_latex = ExportService._convert_child_node_to_latex(grandchild)
                            if grandchild_latex:
                                item_parts.append(grandchild_latex)
                    item_text = " ".join(item_parts)
                else:
                    # Process other types of list children
                    item_parts = []
                    for grandchild in child.get("children", []):
                        grandchild_latex = ExportService._convert_child_node_to_latex(grandchild)
                        if grandchild_latex:
                            item_parts.append(grandchild_latex)
                    item_text = " ".join(item_parts) if item_parts else ExportService._get_text_from_node(child)
                items.append(f"  \\item {item_text}")
            
            return f"\\begin{{{env}}}\n" + "\n".join(items) + f"\n\\end{{{env}}}"
        
        elif node_type == "quote":
            # Process quote children to preserve citations
            text_parts = []
            for child in node.get("children", []):
                child_latex = ExportService._convert_child_node_to_latex(child)
                if child_latex:
                    text_parts.append(child_latex)
            text = " ".join(text_parts) if text_parts else ExportService._escape_latex(ExportService._get_text_from_node(node))
            return f"\\begin{{quote}}\n{text}\n\\end{{quote}}"
        
        elif node_type == "code":
            text = node.get("text", "")
            return f"\\begin{{verbatim}}\n{text}\n\\end{{verbatim}}"
        
        elif node_type == "citation":
            # Handle citation nodes at the root level
            # Try different possible field names for the citation key
            citation_key = node.get("citationKey") or node.get("citation_key") or node.get("key") or ""
            if citation_key:
                return f"\\cite{{{citation_key}}}"
            # Fallback to paperId if no citation key
            paper_id = node.get("paperId") or node.get("paper_id") or ""
            if paper_id:
                return f"\\cite{{{paper_id}}}"
            # Last resort - use any available identifier
            return f"\\cite{{unknown}}"
        
        elif node_type == "listitem":
            # Handle list item nodes specifically
            item_parts = []
            for child in node.get("children", []):
                child_latex = ExportService._convert_lexical_node_to_latex(child)
                if child_latex:
                    item_parts.append(child_latex)
            return " ".join(item_parts)
        
        # For other node types, process children if they exist
        children = node.get("children", [])
        if children:
            child_parts = []
            for child in children:
                child_latex = ExportService._convert_lexical_node_to_latex(child)
                if child_latex:
                    child_parts.append(child_latex)
            return " ".join(child_parts)
        
        return ""
    
    @staticmethod
    def _get_text_from_node(node: Dict[str, Any]) -> str:
        """Extract plain text from a Lexical node."""
        text_parts = []
        
        if "text" in node:
            return node["text"]
        
        for child in node.get("children", []):
            if child.get("type") == "text":
                text_parts.append(child.get("text", ""))
            else:
                # Recursively get text from child nodes
                text_parts.append(ExportService._get_text_from_node(child))
        
        return " ".join(text_parts)