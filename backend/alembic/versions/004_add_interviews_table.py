"""Add interviews table

Revision ID: 004
Revises: 003
Create Date: 2024-11-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types for interview (check if they exist first)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE interviewtype AS ENUM ('phone', 'video', 'in-person');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE interviewstatus AS ENUM ('scheduled', 'completed', 'cancelled', 'rescheduled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create interviews table
    op.create_table(
        'interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('match_result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('interview_type', postgresql.ENUM('phone', 'video', 'in-person', name='interviewtype', create_type=False), 
              nullable=False, server_default=sa.text("'video'")),
        sa.Column('status', postgresql.ENUM('scheduled', 'completed', 'cancelled', 'rescheduled', name='interviewstatus', create_type=False), 
              nullable=False, server_default=sa.text("'scheduled'")),
        sa.Column('meeting_link', sa.String(500), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('invitation_sent', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invitation_opened', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invitation_clicked', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_interviews_match_result_id',
        'interviews', 'match_results',
        ['match_result_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_interviews_job_id',
        'interviews', 'job_descriptions',
        ['job_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_interviews_created_by',
        'interviews', 'users',
        ['created_by'], ['id']
    )
    
    op.create_foreign_key(
        'fk_interviews_cancelled_by',
        'interviews', 'users',
        ['cancelled_by'], ['id']
    )
    
    # Create indexes
    op.create_index('idx_interview_match_result', 'interviews', ['match_result_id'], unique=False)
    op.create_index('idx_interview_job', 'interviews', ['job_id'], unique=False)
    op.create_index('idx_interview_scheduled_time', 'interviews', ['scheduled_time'], unique=False)
    op.create_index('idx_interview_status', 'interviews', ['status'], unique=False)
    op.create_index('idx_interview_created_by', 'interviews', ['created_by'], unique=False)
    op.create_index('idx_interview_job_status', 'interviews', ['job_id', 'status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_interview_job_status', table_name='interviews')
    op.drop_index('idx_interview_created_by', table_name='interviews')
    op.drop_index('idx_interview_status', table_name='interviews')
    op.drop_index('idx_interview_scheduled_time', table_name='interviews')
    op.drop_index('idx_interview_job', table_name='interviews')
    op.drop_index('idx_interview_match_result', table_name='interviews')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_interviews_cancelled_by', 'interviews', type_='foreignkey')
    op.drop_constraint('fk_interviews_created_by', 'interviews', type_='foreignkey')
    op.drop_constraint('fk_interviews_job_id', 'interviews', type_='foreignkey')
    op.drop_constraint('fk_interviews_match_result_id', 'interviews', type_='foreignkey')
    
    # Drop table
    op.drop_table('interviews')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS interviewstatus')
    op.execute('DROP TYPE IF EXISTS interviewtype')
