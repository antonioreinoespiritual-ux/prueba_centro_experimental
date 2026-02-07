# app/migrations.py
from __future__ import annotations

import sqlite3
from pathlib import Path

from .database import DATABASE_URL


def _column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def ensure_schema() -> None:
    """Ensure new columns exist for lean hypothesis upgrades."""
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_file = Path(db_path)
    if not db_file.exists():
        return

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experiments'")
    if not cur.fetchone():
        conn.close()
        return

    experiment_columns = [
        ("hypothesis_type", "VARCHAR(50)"),
        ("independent_variable", "VARCHAR(500)"),
        ("primary_metric", "VARCHAR(100)"),
        ("validation_threshold", "VARCHAR(200)"),
        ("threshold_value", "FLOAT"),
        ("threshold_type", "VARCHAR(30)"),
        ("threshold_operator", "VARCHAR(5)"),
        ("experiment_status", "VARCHAR(30) NOT NULL DEFAULT 'draft'"),
        ("min_volume", "INTEGER"),
        ("volume_min_value", "INTEGER"),
        ("volume_unit", "VARCHAR(30)"),
        ("updated_at", "DATETIME"),
    ]

    for col_name, col_type in experiment_columns:
        if not _column_exists(cur, "experiments", col_name):
            cur.execute(f"ALTER TABLE experiments ADD COLUMN {col_name} {col_type}")

    record_columns = [
        ("execution_type", "VARCHAR(30)"),
        ("record_name", "VARCHAR(200)"),
        ("publico", "VARCHAR(200)"),
        ("hook_text", "TEXT"),
        ("hook_type", "VARCHAR(30)"),
        ("cta_text", "TEXT"),
        ("cta_type", "VARCHAR(30)"),
        ("creative_id", "VARCHAR(200)"),
        ("record_status", "VARCHAR(20) NOT NULL DEFAULT 'collecting'"),
        ("updated_at", "DATETIME"),
        ("views_profile", "INTEGER"),
        ("inicia_test", "INTEGER"),
    ]

    for col_name, col_type in record_columns:
        if not _column_exists(cur, "experiment_records", col_name):
            cur.execute(f"ALTER TABLE experiment_records ADD COLUMN {col_name} {col_type}")

    # --- Documentation tables ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documentation'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE documentation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type VARCHAR(20) NOT NULL,
                entity_id INTEGER NOT NULL,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME,
                UNIQUE(entity_type, entity_id)
            )
        """)

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documentation_note'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE documentation_note (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                documentation_id INTEGER NOT NULL REFERENCES documentation(id),
                body TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME
            )
        """)

    # --- AI Analysis table ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_analysis'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type VARCHAR(20) NOT NULL,
                entity_id INTEGER NOT NULL,
                analysis_type VARCHAR(20) NOT NULL,
                model VARCHAR(100) NOT NULL,
                prompt_version VARCHAR(50) NOT NULL,
                input_snapshot TEXT NOT NULL,
                output TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT (datetime('now'))
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_ai_analysis_entity
            ON ai_analysis (entity_type, entity_id, analysis_type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_ai_analysis_created
            ON ai_analysis (created_at)
        """)

    conn.commit()
    conn.close()
