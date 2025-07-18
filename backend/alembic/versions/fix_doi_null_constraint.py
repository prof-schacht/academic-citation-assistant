"""Fix DOI null constraint to allow NULL instead of empty strings

Revision ID: fix_doi_null_constraint
Revises: add_zotero_groups_collections
Create Date: 2025-07-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_doi_null_constraint'
down_revision: Union[str, Sequence[str], None] = 'add_zotero_groups_collections'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update empty DOI strings to NULL and ensure proper handling"""
    # First, update any existing empty DOI strings to NULL
    op.execute("UPDATE papers SET doi = NULL WHERE doi = ''")
    
    # Same for other ID fields that might have empty strings
    op.execute("UPDATE papers SET arxiv_id = NULL WHERE arxiv_id = ''")
    op.execute("UPDATE papers SET pubmed_id = NULL WHERE pubmed_id = ''")
    op.execute("UPDATE papers SET semantic_scholar_id = NULL WHERE semantic_scholar_id = ''")
    
    # Add a check constraint to prevent empty strings in the future
    op.create_check_constraint(
        'ck_papers_doi_not_empty',
        'papers',
        "doi IS NULL OR doi != ''"
    )
    op.create_check_constraint(
        'ck_papers_arxiv_id_not_empty',
        'papers',
        "arxiv_id IS NULL OR arxiv_id != ''"
    )
    op.create_check_constraint(
        'ck_papers_pubmed_id_not_empty',
        'papers',
        "pubmed_id IS NULL OR pubmed_id != ''"
    )
    op.create_check_constraint(
        'ck_papers_semantic_scholar_id_not_empty',
        'papers',
        "semantic_scholar_id IS NULL OR semantic_scholar_id != ''"
    )


def downgrade() -> None:
    """Remove check constraints"""
    op.drop_constraint('ck_papers_doi_not_empty', 'papers')
    op.drop_constraint('ck_papers_arxiv_id_not_empty', 'papers')
    op.drop_constraint('ck_papers_pubmed_id_not_empty', 'papers')
    op.drop_constraint('ck_papers_semantic_scholar_id_not_empty', 'papers')