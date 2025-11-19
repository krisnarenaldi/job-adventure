"""Initial migration with all core models

Revision ID: 001
Revises: 
Create Date: 2024-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('RECRUITER', 'HIRING_MANAGER', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create job_descriptions table
    op.create_table('job_descriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('salary_range', sa.String(length=100), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=True),
        sa.Column('experience_level', sa.String(length=50), nullable=True),
        sa.Column('skills_required', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(384), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_descriptions_company'), 'job_descriptions', ['company'], unique=False)
    op.create_index(op.f('ix_job_descriptions_id'), 'job_descriptions', ['id'], unique=False)
    op.create_index(op.f('ix_job_descriptions_title'), 'job_descriptions', ['title'], unique=False)
    op.create_index('idx_job_created_by', 'job_descriptions', ['created_by'], unique=False)
    op.create_index('idx_job_created_at', 'job_descriptions', ['created_at'], unique=False)
    op.create_index('idx_job_title_company', 'job_descriptions', ['title', 'company'], unique=False)
    op.create_index('idx_job_embedding', 'job_descriptions', ['embedding'], unique=False, postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'})

    # Create resumes table
    op.create_table('resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_type', sa.String(length=10), nullable=True),
        sa.Column('sections', sa.JSON(), nullable=True),
        sa.Column('extracted_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('experience_years', sa.String(length=20), nullable=True),
        sa.Column('education_level', sa.String(length=100), nullable=True),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(384), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_processed', sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_candidate_name'), 'resumes', ['candidate_name'], unique=False)
    op.create_index(op.f('ix_resumes_email'), 'resumes', ['email'], unique=False)
    op.create_index(op.f('ix_resumes_id'), 'resumes', ['id'], unique=False)
    op.create_index('idx_resume_candidate_name', 'resumes', ['candidate_name'], unique=False)
    op.create_index('idx_resume_email', 'resumes', ['email'], unique=False)
    op.create_index('idx_resume_uploaded_at', 'resumes', ['uploaded_at'], unique=False)
    op.create_index('idx_resume_processed', 'resumes', ['is_processed'], unique=False)
    op.create_index('idx_resume_embedding', 'resumes', ['embedding'], unique=False, postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'})

    # Create match_results table
    op.create_table('match_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('key_strengths', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('missing_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('skill_matches', sa.JSON(), nullable=True),
        sa.Column('experience_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('skills_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('education_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('processing_time_ms', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['job_descriptions.id'], ),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_match_results_id'), 'match_results', ['id'], unique=False)
    op.create_index(op.f('ix_match_results_job_id'), 'match_results', ['job_id'], unique=False)
    op.create_index(op.f('ix_match_results_match_score'), 'match_results', [sa.text('match_score DESC')], unique=False)
    op.create_index(op.f('ix_match_results_resume_id'), 'match_results', ['resume_id'], unique=False)
    op.create_index('idx_match_job_id', 'match_results', ['job_id'], unique=False)
    op.create_index('idx_match_resume_id', 'match_results', ['resume_id'], unique=False)
    op.create_index('idx_match_score', 'match_results', [sa.text('match_score DESC')], unique=False)
    op.create_index('idx_match_created_at', 'match_results', ['created_at'], unique=False)
    op.create_index('idx_match_job_score', 'match_results', ['job_id', sa.text('match_score DESC')], unique=False)
    op.create_index('idx_match_unique', 'match_results', ['job_id', 'resume_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('match_results')
    op.drop_table('resumes')
    op.drop_table('job_descriptions')
    op.drop_table('users')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS userrole')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS vector')