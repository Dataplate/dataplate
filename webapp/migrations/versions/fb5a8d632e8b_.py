"""empty message

Revision ID: fb5a8d632e8b
Revises: 087fbdf452da
Create Date: 2020-12-17 14:11:51.728231

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb5a8d632e8b'
down_revision = '087fbdf452da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    #op.add_column('global_config', sa.Column('output_path', sa.String(length=250), nullable=True))
    pass
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('global_config', 'output_path')
    # ### end Alembic commands ###
