"""add contacts table

Revision ID: 009
Revises: 008
Create Date: 2024-11-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_data', sa.Text(), nullable=True),  # Base64 encoded image
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_contacts_id', 'contacts', ['id'])
    op.create_index('ix_contacts_email', 'contacts', ['email'])
    op.create_index('ix_contacts_user_id', 'contacts', ['user_id'])
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_contacts_user_id',
        'contacts', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_contacts_user_id', 'contacts', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_contacts_user_id', table_name='contacts')
    op.drop_index('ix_contacts_email', table_name='contacts')
    op.drop_index('ix_contacts_id', table_name='contacts')
    
    # Drop contacts table
    op.drop_table('contacts')

