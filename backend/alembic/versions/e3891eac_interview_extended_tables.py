"""Extend interview session table

Revision ID: e3891eac
Revises: d2891eac
Create Date: 2026-08-20 19:28:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3891eac'
down_revision: Union[str, Sequence[str], None] = 'd2891eac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('job_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('mode', sa.String(), nullable=False, server_default='Mixed'))
        batch_op.add_column(sa.Column('difficulty', sa.String(), nullable=False, server_default='Beginner'))
        batch_op.add_column(sa.Column('question_count', sa.Integer(), nullable=False, server_default='5'))
        batch_op.add_column(sa.Column('current_question_index', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('overall_score', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('category_scores', sa.JSON(), nullable=False, server_default='{}'))
        batch_op.add_column(sa.Column('readiness_status', sa.String(), nullable=False, server_default='NEEDS PRACTICE'))
        batch_op.add_column(sa.Column('readiness_explanation', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('weak_areas', sa.JSON(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('questions_data', sa.JSON(), nullable=False, server_default='[]'))

        batch_op.alter_column('question_text', existing_type=sa.VARCHAR(), nullable=True)

        batch_op.create_index(batch_op.f('ix_interview_sessions_job_id'), ['job_id'], unique=False)
        batch_op.create_foreign_key('fk_interview_sessions_job_id', 'jobs', ['job_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_interview_sessions_job_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_interview_sessions_job_id'))
        batch_op.alter_column('question_text', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.drop_column('questions_data')
        batch_op.drop_column('weak_areas')
        batch_op.drop_column('readiness_explanation')
        batch_op.drop_column('readiness_status')
        batch_op.drop_column('category_scores')
        batch_op.drop_column('overall_score')
        batch_op.drop_column('is_completed')
        batch_op.drop_column('current_question_index')
        batch_op.drop_column('question_count')
        batch_op.drop_column('difficulty')
        batch_op.drop_column('mode')
        batch_op.drop_column('job_id')
