"""create paper chunks table

Revision ID: create_paper_chunks
Revises: 
Create Date: 2025-07-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'create_paper_chunks'
down_revision = '111db885c1f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create paper_chunks table
    op.create_table('paper_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=False),
        sa.Column('end_char', sa.Integer(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('section_title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_paper_chunks_paper_id', 'paper_chunks', ['paper_id'], unique=False)
    op.create_index('idx_paper_chunks_embedding', 'paper_chunks', ['embedding'], unique=False, postgresql_using='ivfflat')


def downgrade() -> None:
    op.drop_index('idx_paper_chunks_embedding', table_name='paper_chunks')
    op.drop_index('idx_paper_chunks_paper_id', table_name='paper_chunks')
    op.drop_table('paper_chunks')