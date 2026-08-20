"""Create job intelligence tables

Revision ID: d2891eac
Revises: c1891eac
Create Date: 2026-08-20 19:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2891eac'
down_revision: Union[str, Sequence[str], None] = 'c1891eac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('provider_id', sa.String(), nullable=True),
        sa.Column('provider_name', sa.String(), nullable=False, server_default='catalog'),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('company', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=False, server_default='Remote'),
        sa.Column('is_remote', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('employment_type', sa.String(), nullable=False, server_default='Full-time'),
        sa.Column('experience_level', sa.String(), nullable=False, server_default='Mid Level'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('required_skills', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('preferred_skills', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('education_requirements', sa.String(), nullable=False, server_default="Bachelor's degree or equivalent experience"),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('salary_currency', sa.String(), nullable=False, server_default='USD'),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('posted_date', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_company'), 'jobs', ['company'], unique=False)
    op.create_index(op.f('ix_jobs_location'), 'jobs', ['location'], unique=False)
    op.create_index(op.f('ix_jobs_provider_id'), 'jobs', ['provider_id'], unique=False)
    op.create_index(op.f('ix_jobs_provider_name'), 'jobs', ['provider_name'], unique=False)
    op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'], unique=False)

    op.create_table(
        'saved_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('saved_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_jobs_job_id'), 'saved_jobs', ['job_id'], unique=False)
    op.create_index(op.f('ix_saved_jobs_user_id'), 'saved_jobs', ['user_id'], unique=False)

    op.create_table(
        'job_applications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='Applied'),
        sa.Column('applied_date', sa.String(), nullable=True),
        sa.Column('interview_date', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_applications_job_id'), 'job_applications', ['job_id'], unique=False)
    op.create_index(op.f('ix_job_applications_status'), 'job_applications', ['status'], unique=False)
    op.create_index(op.f('ix_job_applications_user_id'), 'job_applications', ['user_id'], unique=False)

    op.create_table(
        'application_status_histories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('application_id', sa.String(), nullable=False),
        sa.Column('from_status', sa.String(), nullable=True),
        sa.Column('to_status', sa.String(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_application_status_histories_application_id'), 'application_status_histories', ['application_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_application_status_histories_application_id'), table_name='application_status_histories')
    op.drop_table('application_status_histories')
    op.drop_index(op.f('ix_job_applications_user_id'), table_name='job_applications')
    op.drop_index(op.f('ix_job_applications_status'), table_name='job_applications')
    op.drop_index(op.f('ix_job_applications_job_id'), table_name='job_applications')
    op.drop_table('job_applications')
    op.drop_index(op.f('ix_saved_jobs_user_id'), table_name='saved_jobs')
    op.drop_index(op.f('ix_saved_jobs_job_id'), table_name='saved_jobs')
    op.drop_table('saved_jobs')
    op.drop_index(op.f('ix_jobs_title'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_provider_name'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_provider_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_location'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_company'), table_name='jobs')
    op.drop_table('jobs')
