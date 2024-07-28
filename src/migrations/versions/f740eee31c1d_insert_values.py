"""insert values

Revision ID: f740eee31c1d
Revises: febb240d2824
Create Date: 2024-07-27 21:46:55.002190

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f740eee31c1d"
down_revision: Union[str, None] = "febb240d2824"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO public.user (email, full_name, password, is_admin) \
               VALUES ('user@ex.com', 'User', '17390d628441b6563401867a5628622c', FALSE), \
               ('admin@ex.com', 'Admin', '95f32a3f42136e54e5811807763a34d0', TRUE);"
    )
    op.execute(
        "INSERT INTO account (id, balance, id_user) \
               VALUES ('1', '0', '1');"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM public.user WHERE email IN ('user@ex.com', 'admin@ex.com');"
    )
    op.execute("DELETE FROM account WHERE id IN ('1');")
