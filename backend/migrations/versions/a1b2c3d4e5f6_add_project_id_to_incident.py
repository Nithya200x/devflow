"""Add project_id column to incident table and create connected_project table tracking

Revision ID: a1b2c3d4e5f6
Revises: f8b3c2d1e4a6
Create Date: 2026-07-04 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f8b3c2d1e4a6'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    # Add project_id column to incident table (nullable)
    # SQLite requires column to be nullable when adding
    op.add_column('incident', sa.Column('project_id', sa.Integer(), nullable=True))
    
    # Add index on project_id for performance
    op.create_index('idx_incident_project_id', 'incident', ['project_id'])
    
    # connected_project table already created by db.create_all()
    # Ensure it exists and stamp it if not already tracked
    inspector = sa.inspect(conn)
    if 'connected_project' not in inspector.get_table_names():
        op.create_table('connected_project',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('github_owner', sa.String(100), nullable=False),
            sa.Column('github_repo', sa.String(100), nullable=False),
            sa.Column('github_repo_id', sa.BigInteger(), nullable=False),
            sa.Column('full_name', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('html_url', sa.String(255), nullable=True),
            sa.Column('clone_url', sa.String(255), nullable=True),
            sa.Column('default_branch', sa.String(50), nullable=True),
            sa.Column('visibility', sa.String(20), nullable=True),
            sa.Column('language', sa.String(50), nullable=True),
            sa.Column('stars', sa.Integer(), nullable=True),
            sa.Column('forks', sa.Integer(), nullable=True),
            sa.Column('topics', sa.Text(), nullable=True),
            sa.Column('jenkins_job_name', sa.String(100), nullable=True),
            sa.Column('docker_container', sa.String(100), nullable=True),
            sa.Column('docker_image', sa.String(200), nullable=True),
            sa.Column('kubernetes_namespace', sa.String(100), nullable=True),
            sa.Column('kubernetes_deployment', sa.String(100), nullable=True),
            sa.Column('prometheus_labels', sa.Text(), nullable=True),
            sa.Column('grafana_dashboard', sa.String(200), nullable=True),
            sa.Column('status', sa.String(20), nullable=True),
            sa.Column('connected_by', sa.String(80), nullable=False),
            sa.Column('connected_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
    print("Migration a1b2c3d4e5f6 applied: added incident.project_id")


def downgrade():
    op.drop_index('idx_incident_project_id', table_name='incident')
    op.drop_column('incident', 'project_id')
    print("Migration a1b2c3d4e5f6 reverted")
