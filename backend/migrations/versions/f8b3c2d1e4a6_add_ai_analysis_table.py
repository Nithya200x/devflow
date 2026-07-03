"""add ai_analysis table for persistent AI analysis storage

Revision ID: f8b3c2d1e4a6
Revises: e7a2b1c3d4f5
Create Date: 2026-07-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f8b3c2d1e4a6'
down_revision = 'e7a2b1c3d4f5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.String(length=50), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('root_cause', sa.String(length=255), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('affected_components_json', sa.Text(), nullable=True),
        sa.Column('possible_causes_json', sa.Text(), nullable=True),
        sa.Column('suggested_fixes_json', sa.Text(), nullable=True),
        sa.Column('preventive_actions_json', sa.Text(), nullable=True),
        sa.Column('similar_patterns_json', sa.Text(), nullable=True),
        sa.Column('risk_assessment', sa.Text(), nullable=True),
        sa.Column('estimated_resolution_time', sa.String(length=100), nullable=True),
        sa.Column('requires_human', sa.Boolean(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('prompt_version', sa.String(length=20), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_ai_analysis_incident_id'),
        'ai_analysis',
        ['incident_id'],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f('ix_ai_analysis_incident_id'), table_name='ai_analysis')
    op.drop_table('ai_analysis')
