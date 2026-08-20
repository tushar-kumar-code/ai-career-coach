"""Add skill intelligence fields to skills and career_roles tables

Revision ID: f9811eac
Revises: b16bae963666
Create Date: 2026-08-19 17:13:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9811eac'
down_revision: Union[str, Sequence[str], None] = 'b16bae963666'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('skills', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_evaluated_at', sa.DateTime(), nullable=True))

    with op.batch_alter_table('career_roles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('important_skills', sa.JSON(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('optional_skills', sa.JSON(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('recommended_proficiency', sa.JSON(), nullable=False, server_default='{}'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('career_roles', schema=None) as batch_op:
        batch_op.drop_column('recommended_proficiency')
        batch_op.drop_column('optional_skills')
        batch_op.drop_column('important_skills')

    with op.batch_alter_table('skills', schema=None) as batch_op:
        batch_op.drop_column('last_evaluated_at')
