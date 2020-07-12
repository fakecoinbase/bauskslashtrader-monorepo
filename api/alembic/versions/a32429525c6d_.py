"""

Revision ID: a32429525c6d
Revises: a35cbd2ae378
Create Date: 2020-07-12 14:22:49.025110

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a32429525c6d'
down_revision = 'a35cbd2ae378'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('strategies', sa.Column('resource_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'strategies', 'resources', ['resource_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'strategies', type_='foreignkey')
    op.drop_column('strategies', 'resource_id')
    # ### end Alembic commands ###
