"""normalize company names

Revision ID: 008
Revises: 007
Create Date: 2024-11-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Normalize existing company names to lowercase
    op.execute("""
        UPDATE companies 
        SET name = LOWER(TRIM(REGEXP_REPLACE(name, '\s+', ' ', 'g')))
        WHERE name IS NOT NULL
    """)
    
    # Add unique constraint on lowercase company name
    # This prevents duplicate companies with different cases
    op.create_index(
        'idx_company_name_lower_unique',
        'companies',
        [sa.text('LOWER(name)')],
        unique=True
    )


def downgrade() -> None:
    # Drop the unique constraint
    op.drop_index('idx_company_name_lower_unique', table_name='companies')
