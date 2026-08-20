"""Add roadmap system fields to roadmaps table

Revision ID: a1791eac
Revises: f9811eac
Create Date: 2026-08-19 17:24:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1791eac'
down_revision: Union[str, Sequence[str], None] = 'f9811eac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('roadmaps', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_outdated', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('hours_per_day', sa.Integer(), server_default='1', nullable=False))
        batch_op.add_column(sa.Column('days_per_week', sa.Integer(), server_default='5', nullable=False))
        batch_op.add_column(sa.Column('preferred_learning_style', sa.String(), server_default='Hands-on', nullable=False))
        batch_op.add_column(sa.Column('total_estimated_weeks', sa.Integer(), server_default='8', nullable=False))
        batch_op.add_column(sa.Column('completed_task_ids', sa.JSON(), server_default='[]', nullable=False))
        batch_op.add_column(sa.Column('completed_milestone_ids', sa.JSON(), server_default='[]', nullable=False))
        batch_op.add_column(sa.Column('completed_project_ids', sa.JSON(), server_default='[]', nullable=False))
        batch_op.create_index(batch_op.f('ix_roadmaps_target_role'), ['target_role'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('roadmaps', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_roadmaps_target_role'))
        batch_op.drop_column('completed_project_ids')
        batch_op.drop_column('completed_milestone_ids')
        batch_op.drop_column('completed_task_ids')
        batch_op.drop_column('total_estimated_weeks')
        batch_op.drop_column('preferred_learning_style')
        batch_op.drop_column('days_per_week')
        batch_op.drop_column('hours_per_day')
        batch_op.drop_column('is_outdated')
