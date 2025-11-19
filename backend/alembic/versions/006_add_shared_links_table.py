"""add shared links table

Revision ID: 006
Revises: 005
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create shared_links table
    op.create_table(
        'shared_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('share_token', sa.String(64), unique=True, nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('recipient_email', sa.String(255), nullable=True),
        sa.Column('custom_message', sa.String(1000), nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('view_count', sa.Integer, default=0, nullable=False),
        sa.Column('last_viewed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()'))
    )
    
    # Create indexes
    op.create_index('idx_shared_links_token', 'shared_links', ['share_token'])
    op.create_index('idx_shared_links_job_id', 'shared_links', ['job_id'])
    op.create_index('idx_shared_links_created_by', 'shared_links', ['created_by'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_shared_links_created_by', 'shared_links')
    op.drop_index('idx_shared_links_job_id', 'shared_links')
    op.drop_index('idx_shared_links_token', 'shared_links')
    
    # Drop table
    op.drop_table('shared_links')
