"""add page numbers to paper chunks

Revision ID: 50b417d3ec67
Revises: 33509915dce8
Create Date: 2025-07-19 15:49:26.875203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50b417d3ec67'
down_revision: Union[str, Sequence[str], None] = '33509915dce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add page number columns to paper_chunks table
    op.add_column('paper_chunks', sa.Column('page_start', sa.Integer(), nullable=True))
    op.add_column('paper_chunks', sa.Column('page_end', sa.Integer(), nullable=True))
    op.add_column('paper_chunks', sa.Column('page_boundaries', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove page number columns from paper_chunks table
    op.drop_column('paper_chunks', 'page_boundaries')
    op.drop_column('paper_chunks', 'page_end')
    op.drop_column('paper_chunks', 'page_start')
