"""Add status field to match_results

Revision ID: 002
Revises: 001
Create Date: 2024-11-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for candidate status
    op.execute("CREATE TYPE candidatestatus AS ENUM ('pending', 'shortlisted', 'rejected', 'maybe')")
    
    # Add status column with default value 'pending'
    op.add_column('match_results', 
        sa.Column('status', sa.Enum('pending', 'shortlisted', 'rejected', 'maybe', name='candidatestatus'), 
                  nullable=False, server_default='pending')
    )
    
    # Add status_updated_at column
    op.add_column('match_results',
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Add status_updated_by column
    op.add_column('match_results',
        sa.Column('status_updated_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add foreign key constraint for status_updated_by
    op.create_foreign_key(
        'fk_match_results_status_updated_by',
        'match_results', 'users',
        ['status_updated_by'], ['id']
    )
    
    # Create index on status for filtering
    op.create_index('idx_match_status', 'match_results', ['status'], unique=False)
    
    # Create composite index for job_id and status
    op.create_index('idx_match_job_status', 'match_results', ['job_id', 'status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_match_job_status', table_name='match_results')
    op.drop_index('idx_match_status', table_name='match_results')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_match_results_status_updated_by', 'match_results', type_='foreignkey')
    
    # Drop columns
    op.drop_column('match_results', 'status_updated_by')
    op.drop_column('match_results', 'status_updated_at')
    op.drop_column('match_results', 'status')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS candidatestatus')
