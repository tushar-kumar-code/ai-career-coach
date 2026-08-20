"""Add extended fields to roadmaps table

Revision ID: c1891eac
Revises: a1791eac
Create Date: 2026-08-20 18:47:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1891eac'
down_revision: Union[str, Sequence[str], None] = 'a1791eac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('roadmaps', schema=None) as batch_op:
        batch_op.add_column(sa.Column('target_career_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('user_level', sa.String(), server_default='Beginner', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('roadmaps', schema=None) as batch_op:
        batch_op.drop_column('user_level')
        batch_op.drop_column('target_career_id')
