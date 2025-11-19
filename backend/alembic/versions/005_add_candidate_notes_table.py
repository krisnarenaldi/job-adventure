"""Add candidate_notes table

Revision ID: 005
Revises: 004
Create Date: 2024-11-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create candidate_notes table
    op.create_table(
        'candidate_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('match_result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_candidate_notes_match_result_id',
        'candidate_notes', 'match_results',
        ['match_result_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_candidate_notes_user_id',
        'candidate_notes', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes
    op.create_index('idx_note_match_result', 'candidate_notes', ['match_result_id'], unique=False)
    op.create_index('idx_note_user', 'candidate_notes', ['user_id'], unique=False)
    op.create_index('idx_note_created_at', 'candidate_notes', ['created_at'], unique=False, postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_note_match_created', 'candidate_notes', ['match_result_id', 'created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_note_match_created', table_name='candidate_notes')
    op.drop_index('idx_note_created_at', table_name='candidate_notes')
    op.drop_index('idx_note_user', table_name='candidate_notes')
    op.drop_index('idx_note_match_result', table_name='candidate_notes')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_candidate_notes_user_id', 'candidate_notes', type_='foreignkey')
    op.drop_constraint('fk_candidate_notes_match_result_id', 'candidate_notes', type_='foreignkey')
    
    # Drop table
    op.drop_table('candidate_notes')
