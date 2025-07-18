"""Add selected groups and collections to zotero_config

Revision ID: add_zotero_groups_collections
Revises: create_paper_chunks_table
Create Date: 2025-01-15 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_zotero_groups_collections'
down_revision: Union[str, None] = 'add_zotero_integration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add selected_groups and selected_collections columns to zotero_config table
    op.add_column('zotero_config', sa.Column('selected_groups', sa.String(500), nullable=True))
    op.add_column('zotero_config', sa.Column('selected_collections', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('zotero_config', 'selected_collections')
    op.drop_column('zotero_config', 'selected_groups')