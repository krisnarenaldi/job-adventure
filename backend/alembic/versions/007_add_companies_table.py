"""add companies table

Revision ID: 007
Revises: 006
Create Date: 2024-11-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create index on company name
    op.create_index('idx_company_name', 'companies', ['name'])
    
    # Set all existing company_id values to NULL before adding foreign key
    # This ensures no orphaned references exist
    op.execute("UPDATE users SET company_id = NULL WHERE company_id IS NOT NULL")
    
    # Add foreign key constraint to users table
    op.create_foreign_key(
        'fk_users_company_id',
        'users', 'companies',
        ['company_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_users_company_id', 'users', type_='foreignkey')
    
    # Drop index
    op.drop_index('idx_company_name', table_name='companies')
    
    # Drop companies table
    op.drop_table('companies')
