"""add name email and created_at to user

Revision ID: 8a3b5c7d9e0f
Revises: 058ef1f6ddb1
Create Date: 2026-07-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '8a3b5c7d9e0f'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=120), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('email', sa.String(length=120), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_unique_constraint('uq_user_email', ['email'])


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_email', type_='unique')
        batch_op.drop_column('created_at')
        batch_op.drop_column('email')
        batch_op.drop_column('name')
