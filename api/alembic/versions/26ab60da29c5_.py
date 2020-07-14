"""

Revision ID: 26ab60da29c5
Revises: c1cf8d0f73e5
Create Date: 2020-07-14 22:53:34.215413

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26ab60da29c5'
down_revision = 'c1cf8d0f73e5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('resources_live_session_id_fkey', 'resources', type_='foreignkey')
    op.drop_column('resources', 'live_session_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('resources', sa.Column('live_session_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('resources_live_session_id_fkey', 'resources', 'live_sessions', ['live_session_id'], ['id'])
    # ### end Alembic commands ###