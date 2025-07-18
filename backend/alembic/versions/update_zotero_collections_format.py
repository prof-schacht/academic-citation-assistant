"""Update zotero collections to include library ID

Revision ID: update_zotero_collections_format
Revises: add_zotero_groups_collections
Create Date: 2025-07-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'update_zotero_collections_format'
down_revision: Union[str, None] = 'fix_doi_null_constraint'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The existing column can store the new format (JSON with library IDs)
    # No schema change needed, just a data format change
    # Users will need to re-select their collections to get the new format
    pass


def downgrade() -> None:
    # No schema change to revert
    pass