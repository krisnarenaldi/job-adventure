"""Convert is_active field to boolean

Revision ID: 003
Revises: 002
Create Date: 2024-11-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert is_active from String to Boolean for job_descriptions table
    # First, update existing values to proper boolean format
    op.execute("UPDATE job_descriptions SET is_active = 'true' WHERE is_active IS NULL OR is_active = ''")
    
    # Add a temporary boolean column
    op.add_column('job_descriptions', sa.Column('is_active_bool', sa.Boolean(), nullable=True))
    
    # Copy data from string column to boolean column
    op.execute("UPDATE job_descriptions SET is_active_bool = CASE WHEN is_active = 'true' THEN true ELSE false END")
    
    # Set default value for new rows
    op.execute("ALTER TABLE job_descriptions ALTER COLUMN is_active_bool SET DEFAULT true")
    
    # Make the column non-nullable
    op.execute("UPDATE job_descriptions SET is_active_bool = true WHERE is_active_bool IS NULL")
    op.alter_column('job_descriptions', 'is_active_bool', nullable=False)
    
    # Drop the old string column
    op.drop_column('job_descriptions', 'is_active')
    
    # Rename the new boolean column to is_active
    op.alter_column('job_descriptions', 'is_active_bool', new_column_name='is_active')
    
    # Create index on is_active for filtering
    op.create_index('idx_job_is_active', 'job_descriptions', ['is_active'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_job_is_active', table_name='job_descriptions')
    
    # Rename column back
    op.alter_column('job_descriptions', 'is_active', new_column_name='is_active_bool')
    
    # Add string column
    op.add_column('job_descriptions', sa.Column('is_active', sa.String(length=10), nullable=True))
    
    # Copy data back to string format
    op.execute("UPDATE job_descriptions SET is_active = CASE WHEN is_active_bool = true THEN 'true' ELSE 'false' END")
    
    # Drop boolean column
    op.drop_column('job_descriptions', 'is_active_bool')
