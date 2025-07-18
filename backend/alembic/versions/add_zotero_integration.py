"""add zotero integration

Revision ID: add_zotero_integration
Revises: create_paper_chunks
Create Date: 2025-07-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_zotero_integration'
down_revision = 'create_paper_chunks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create zotero_config table
    op.create_table('zotero_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('api_key', sa.String(100), nullable=False),
        sa.Column('zotero_user_id', sa.String(50), nullable=False),
        sa.Column('auto_sync_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sync_interval_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('last_sync_status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create zotero_sync table
    op.create_table('zotero_sync',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('zotero_key', sa.String(50), nullable=False),
        sa.Column('zotero_version', sa.Integer(), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('last_synced', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(50), nullable=False, server_default='synced'),
        sa.Column('sync_error', sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'zotero_key', name='_user_zotero_key_uc')
    )
    
    # Add zotero_key column to papers table
    op.add_column('papers', sa.Column('zotero_key', sa.String(50), nullable=True))
    op.create_index('idx_papers_zotero_key', 'papers', ['zotero_key'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_papers_zotero_key', table_name='papers')
    op.drop_column('papers', 'zotero_key')
    op.drop_table('zotero_sync')
    op.drop_table('zotero_config')