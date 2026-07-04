"""Apply the project_id column to incident table directly"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'app.db')
print(f"Database path: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(incident)")
columns = [col[1] for col in cursor.fetchall()]

if 'project_id' not in columns:
    cursor.execute("ALTER TABLE incident ADD COLUMN project_id INTEGER REFERENCES connected_project(id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incident_project_id ON incident(project_id)")
    print("Added project_id column to incident table")
else:
    print("project_id column already exists in incident table")

# Update alembic version stamp
cursor.execute("SELECT version_num FROM alembic_version")
current = cursor.fetchone()
if current and current[0] != 'a1b2c3d4e5f6':
    cursor.execute("UPDATE alembic_version SET version_num = 'a1b2c3d4e5f6'")
    print(f"Updated alembic version from {current[0]} to a1b2c3d4e5f6")

conn.commit()
conn.close()
print("Migration applied successfully")

# Verify
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(incident)")
print("Incident columns:", [col[1] for col in cursor.fetchall()])
cursor.execute("SELECT version_num FROM alembic_version")
print("Alembic version:", cursor.fetchone())
conn.close()
