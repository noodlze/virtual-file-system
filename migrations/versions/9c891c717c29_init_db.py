"""init_db

Revision ID: 9c891c717c29
Revises:
Create Date: 2020-12-02 13:28:51.922988

"""
from alembic import op
from datetime import datetime
import sqlalchemy as sa
# from sqlalchemy.schema import Sequence, CreateSequence


# revision identifiers, used by Alembic.
revision = '9c891c717c29'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    item_table = op.create_table('item',
                                 sa.Column('id', sa.Integer(), nullable=False,
                                           autoincrement=True),
                                 sa.Column('name', sa.String(),
                                           nullable=True),
                                 sa.Column('created_at',
                                           sa.DateTime(), nullable=False),
                                 sa.Column('updated_at',
                                           sa.DateTime(), nullable=False),
                                 sa.Column('size', sa.Integer(),
                                           nullable=False),
                                 sa.Column('is_dir', sa.Boolean(),
                                           default=False),
                                 sa.PrimaryKeyConstraint('id'),
                                 )

    op.create_table('file',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('data', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.ForeignKeyConstraint(['id'], ['item.id'])
                    )

    ancestors_table = op.create_table('ancestors',
                                      sa.Column(
                                          'parent_id', sa.Integer(), nullable=False),
                                      sa.Column(
                                          'child_id', sa.Integer(), nullable=False),
                                      sa.Column('depth', sa.Integer(),
                                                nullable=False),
                                      sa.Column('rank', sa.Text(),
                                                nullable=False),
                                      sa.PrimaryKeyConstraint(
                                          'rank'),
                                      sa.ForeignKeyConstraint(
                                          ['parent_id'], ['item.id']),
                                      sa.ForeignKeyConstraint(['child_id'], ['item.id']))
    # insert /
    op.bulk_insert(item_table,
                   [{"id": 0, "name": "/", "created_at": datetime.now(), "updated_at": datetime.now(), "size": 0, "is_dir": True}])

    op.bulk_insert(ancestors_table,
                   [{"parent_id": 0, "child_id": 0, "depth": 0, "rank": "0"}])


def downgrade():
    op.drop_table('item')
    op.drop_table('file')
    op.drop_table('Ancestors')
