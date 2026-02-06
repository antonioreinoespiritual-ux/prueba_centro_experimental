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
    ]

    for col_name, col_type in experiment_columns:
        if not _column_exists(cur, "experiments", col_name):
            cur.execute(f"ALTER TABLE experiments ADD COLUMN {col_name} {col_type}")

    record_columns = [
        ("execution_type", "VARCHAR(30)"),
        ("hook_text", "TEXT"),
        ("hook_type", "VARCHAR(30)"),
        ("cta_text", "TEXT"),
        ("cta_type", "VARCHAR(30)"),
        ("creative_id", "VARCHAR(200)"),
        ("record_status", "VARCHAR(20) NOT NULL DEFAULT 'collecting'"),
        ("updated_at", "DATETIME"),
    ]

    for col_name, col_type in record_columns:
        if not _column_exists(cur, "experiment_records", col_name):
            cur.execute(f"ALTER TABLE experiment_records ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
