"""add orchestration engine tables (event_store, incident_evidence, incident_timeline)

Revision ID: e7a2b1c3d4f5
Revises: cb20543ff394
Create Date: 2026-06-26 09:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7a2b1c3d4f5'
down_revision = 'cb20543ff394'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('event_store',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('incident_evidence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.String(length=50), nullable=False),
        sa.Column('evidence_id', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('evidence_type', sa.String(length=100), nullable=True, server_default='generic'),
        sa.Column('data_json', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('collected_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('incident_timeline',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True, server_default=''),
        sa.Column('description', sa.Text(), nullable=True, server_default=''),
        sa.Column('metadata_json', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('incident_timeline')
    op.drop_table('incident_evidence')
    op.drop_table('event_store')
