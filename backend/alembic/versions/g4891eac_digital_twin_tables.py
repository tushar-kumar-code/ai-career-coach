"""Add digital twin and readiness tracking tables

Revision ID: g4891eac
Revises: e3891eac
Create Date: 2026-08-21 18:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g4891eac'
down_revision: Union[str, Sequence[str], None] = 'e3891eac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. career_digital_twins
    op.create_table(
        'career_digital_twins',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('overall_readiness_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('readiness_label', sa.String(), nullable=False, server_default='Not Started'),
        sa.Column('skill_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('resume_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('interview_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('roadmap_progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('job_match_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('portfolio_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('target_career', sa.String(), nullable=True),
        sa.Column('primary_archetype', sa.String(), nullable=True),
        sa.Column('experience_level', sa.String(), nullable=False, server_default='Beginner'),
        sa.Column('top_strengths', sa.JSON(), nullable=False),
        sa.Column('priority_gaps', sa.JSON(), nullable=False),
        sa.Column('critical_missing_skills', sa.JSON(), nullable=False),
        sa.Column('next_action', sa.JSON(), nullable=False),
        sa.Column('evidence_summary', sa.JSON(), nullable=False),
        sa.Column('last_computed_at', sa.DateTime(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_career_digital_twins_user_id', 'career_digital_twins', ['user_id'])

    # 2. readiness_snapshots
    op.create_table(
        'readiness_snapshots',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('overall_readiness_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skill_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('resume_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('interview_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('roadmap_progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('job_match_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('portfolio_readiness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_readiness_snapshots_user_id', 'readiness_snapshots', ['user_id'])
    op.create_index('ix_readiness_snapshots_snapshot_date', 'readiness_snapshots', ['snapshot_date'])

    # 3. user_achievements
    op.create_table(
        'user_achievements',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('achievement_key', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('icon', sa.String(), nullable=False, server_default='trophy'),
        sa.Column('category', sa.String(), nullable=False, server_default='General'),
        sa.Column('evidence_description', sa.String(), nullable=True),
        sa.Column('earned_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_user_achievements_user_id', 'user_achievements', ['user_id'])
    op.create_index('ix_user_achievements_achievement_key', 'user_achievements', ['achievement_key'])

    # 4. weekly_career_reports
    op.create_table(
        'weekly_career_reports',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('week_start_date', sa.Date(), nullable=False),
        sa.Column('week_end_date', sa.Date(), nullable=False),
        sa.Column('overall_score_delta', sa.String(), nullable=False, server_default='0'),
        sa.Column('skill_score_delta', sa.String(), nullable=False, server_default='0'),
        sa.Column('resume_score_delta', sa.String(), nullable=False, server_default='0'),
        sa.Column('interview_score_delta', sa.String(), nullable=False, server_default='0'),
        sa.Column('roadmap_delta', sa.String(), nullable=False, server_default='0'),
        sa.Column('tasks_completed', sa.String(), nullable=False, server_default='0'),
        sa.Column('interviews_completed', sa.String(), nullable=False, server_default='0'),
        sa.Column('applications_submitted', sa.String(), nullable=False, server_default='0'),
        sa.Column('skills_verified', sa.String(), nullable=False, server_default='0'),
        sa.Column('improvements', sa.JSON(), nullable=False),
        sa.Column('achievements_earned', sa.JSON(), nullable=False),
        sa.Column('biggest_weakness', sa.String(), nullable=True),
        sa.Column('recommended_focus', sa.String(), nullable=True),
        sa.Column('ai_narrative', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_weekly_career_reports_user_id', 'weekly_career_reports', ['user_id'])
    op.create_index('ix_weekly_career_reports_week_start_date', 'weekly_career_reports', ['week_start_date'])


def downgrade() -> None:
    op.drop_table('weekly_career_reports')
    op.drop_table('user_achievements')
    op.drop_table('readiness_snapshots')
    op.drop_table('career_digital_twins')
