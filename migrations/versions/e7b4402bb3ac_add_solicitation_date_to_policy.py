"""add solicitation_date to policy

Revision ID: e7b4402bb3ac
Revises: 
Create Date: 2023-04-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7b4402bb3ac'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columna solicitation_date a la tabla policy
    op.add_column('policy', sa.Column('solicitation_date', sa.Date(), nullable=True))


def downgrade():
    # Eliminar columna solicitation_date de la tabla policy
    op.drop_column('policy', 'solicitation_date') 