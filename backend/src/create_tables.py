import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from extensions import db
import sqlite3

app = create_app()
with app.app_context():
    db.create_all()
    conn = sqlite3.connect('../database/app.db')
    cursor = conn.cursor()

    migrations = [
        ("ALTER TABLE event_store ADD COLUMN project_id INTEGER REFERENCES connected_project(id)",
         "event_store", "project_id"),
        ("ALTER TABLE incident_evidence ADD COLUMN project_id INTEGER REFERENCES connected_project(id)",
         "incident_evidence", "project_id"),
        ("ALTER TABLE incident_timeline ADD COLUMN project_id INTEGER REFERENCES connected_project(id)",
         "incident_timeline", "project_id"),
        ("ALTER TABLE ai_analysis ADD COLUMN project_id INTEGER REFERENCES connected_project(id)",
         "ai_analysis", "project_id"),
        ("ALTER TABLE ai_analysis_cache ADD COLUMN project_id INTEGER REFERENCES connected_project(id)",
         "ai_analysis_cache", "project_id"),
        ("ALTER TABLE incident ADD COLUMN incident_id VARCHAR(50)",
         "incident", "incident_id"),
        ("ALTER TABLE incident ADD COLUMN description TEXT DEFAULT ''",
         "incident", "description"),
        ("ALTER TABLE incident ADD COLUMN source VARCHAR(100) DEFAULT ''",
         "incident", "source"),
        ("ALTER TABLE incident ADD COLUMN evidence_json TEXT DEFAULT '[]'",
         "incident", "evidence_json"),
        ("ALTER TABLE incident ADD COLUMN timeline_json TEXT DEFAULT '[]'",
         "incident", "timeline_json"),
        ("ALTER TABLE incident ADD COLUMN ai_analysis_id INTEGER REFERENCES ai_analysis(id)",
         "incident", "ai_analysis_id"),
        ("ALTER TABLE incident ADD COLUMN resolved_at DATETIME",
         "incident", "resolved_at"),
    ]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in cursor.fetchall()]
    for sql, table, col in migrations:
        if table in tables:
            try:
                cursor.execute(f"SELECT {col} FROM {table} LIMIT 0")
            except sqlite3.OperationalError:
                try:
                    cursor.execute(sql)
                    print(f"MIGRATED: added {col} to {table}")
                except Exception as e:
                    print(f"SKIP: {table}.{col} — {e}")

    conn.commit()
    conn.close()
    print(f"Tables: {tables}")
    if 'connected_project' in tables:
        print("SUCCESS: connected_project table created")
    else:
        print("ERROR: connected_project table NOT found")
