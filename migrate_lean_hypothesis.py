"""
Migration script: Add Lean Hypothesis fields to experiments and creative/execution fields to records.

This migration adds columns WITHOUT breaking existing data:
  - experiments: hypothesis_type, independent_variable, primary_metric,
                 validation_threshold, threshold_value, threshold_type, threshold_operator,
                 rate_base_unit, experiment_status, min_volume, volume_min_value, volume_unit
  - experiment_records: execution_type, hook_text, hook_type, cta_text,
                        cta_type, creative_id, record_status, updated_at

Run: python migrate_lean_hypothesis.py
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "experiments.db"


def column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Nothing to migrate.")
        print("The app will create the tables automatically on first run.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # --- Experiment table ---
    experiment_columns = [
        ("hypothesis_type", "VARCHAR(50)"),
        ("independent_variable", "VARCHAR(500)"),
        ("primary_metric", "VARCHAR(100)"),
        ("validation_threshold", "VARCHAR(200)"),
        ("threshold_value", "FLOAT"),
        ("threshold_type", "VARCHAR(30)"),
        ("threshold_operator", "VARCHAR(5)"),
        ("rate_base_unit", "VARCHAR(30)"),
        ("experiment_status", "VARCHAR(30) NOT NULL DEFAULT 'draft'"),
        ("min_volume", "INTEGER"),
        ("volume_min_value", "INTEGER"),
        ("volume_unit", "VARCHAR(30)"),
    ]

    for col_name, col_type in experiment_columns:
        if not column_exists(cur, "experiments", col_name):
            sql = f"ALTER TABLE experiments ADD COLUMN {col_name} {col_type}"
            print(f"  + experiments.{col_name}")
            cur.execute(sql)
        else:
            print(f"  = experiments.{col_name} (already exists)")

    # --- ExperimentRecord table ---
    record_columns = [
        ("execution_type", "VARCHAR(30)"),
        ("record_name", "VARCHAR(200)"),
        ("hook_text", "TEXT"),
        ("hook_type", "VARCHAR(30)"),
        ("cta_text", "TEXT"),
        ("cta_type", "VARCHAR(30)"),
        ("creative_id", "VARCHAR(200)"),
        ("record_status", "VARCHAR(20) NOT NULL DEFAULT 'collecting'"),
        ("updated_at", "DATETIME"),
    ]

    for col_name, col_type in record_columns:
        if not column_exists(cur, "experiment_records", col_name):
            sql = f"ALTER TABLE experiment_records ADD COLUMN {col_name} {col_type}"
            print(f"  + experiment_records.{col_name}")
            cur.execute(sql)
        else:
            print(f"  = experiment_records.{col_name} (already exists)")

    conn.commit()
    conn.close()
    print("\nMigration complete. Existing data preserved.")


if __name__ == "__main__":
    print("=== Lean Hypothesis Migration ===\n")
    migrate()
