"""Fix portfolio_snapshots created_at and updated_at missing server_default

Revision ID: fix_snapshot_defaults
Revises: 27e263602ff4
Create Date: 2026-02-19 10:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_snapshot_defaults'
down_revision: Union[str, Sequence[str], None] = 'd669d3fd285d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """created_at, updated_at에 DB 레벨 DEFAULT now() 추가"""
    op.execute(
        "ALTER TABLE portfolio_snapshots "
        "ALTER COLUMN created_at SET DEFAULT now()"
    )
    op.execute(
        "ALTER TABLE portfolio_snapshots "
        "ALTER COLUMN updated_at SET DEFAULT now()"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE portfolio_snapshots "
        "ALTER COLUMN created_at DROP DEFAULT"
    )
    op.execute(
        "ALTER TABLE portfolio_snapshots "
        "ALTER COLUMN updated_at DROP DEFAULT"
    )
