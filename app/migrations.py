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
        ("metric_x", "VARCHAR(100)"),
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
        ("iteration_number", "INTEGER"),
        ("execution_type", "VARCHAR(30)"),
        ("record_name", "VARCHAR(200)"),
        ("publico", "VARCHAR(200)"),
        ("public_id", "INTEGER"),
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

    cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_experiment_records_public_id
        ON experiment_records (public_id)
    """)

    # --- Publics table ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='publics'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE publics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                name_normalized VARCHAR(200) NOT NULL UNIQUE,
                description TEXT,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_publics_name_normalized
            ON publics (name_normalized)
        """)

    # Backfill publics from existing records
    cur.execute("SELECT id, publico FROM experiment_records WHERE publico IS NOT NULL")
    public_rows = cur.fetchall()
    if public_rows:
        cur.execute("SELECT id, name_normalized FROM publics")
        existing = {row[1]: row[0] for row in cur.fetchall()}

        def normalize_public(value: str) -> str:
            return " ".join(value.strip().lower().split())

        def is_unassigned(value: str) -> bool:
            return value in {"sin publico", "sin público", "no asignado", "no asignada"}

        for record_id, publico in public_rows:
            if not publico:
                continue
            normalized = normalize_public(publico)
            if not normalized or is_unassigned(normalized):
                continue
            public_id = existing.get(normalized)
            if not public_id:
                cur.execute(
                    "INSERT INTO publics (name, name_normalized) VALUES (?, ?)",
                    (publico.strip(), normalized),
                )
                public_id = cur.lastrowid
                existing[normalized] = public_id
            cur.execute(
                "UPDATE experiment_records SET public_id = ? WHERE id = ?",
                (public_id, record_id),
            )

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

    # --- Record update audits ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='record_update_audits'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE record_update_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL REFERENCES experiment_records(id),
                source VARCHAR(100) NOT NULL,
                changed_fields TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT (datetime('now'))
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_record_update_audits_record_id
            ON record_update_audits (record_id)
        """)

    # --- Entity files ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entity_files'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE entity_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type VARCHAR(20) NOT NULL,
                entity_id INTEGER NOT NULL,
                display_name VARCHAR(255) NOT NULL,
                stored_name VARCHAR(255) NOT NULL,
                folder VARCHAR(255),
                content_type VARCHAR(100),
                size_bytes INTEGER NOT NULL,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_entity_files_entity
            ON entity_files (entity_type, entity_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_entity_files_folder
            ON entity_files (folder)
        """)

    # --- Chat memory ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_memory'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE chat_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assistant_type VARCHAR(20) NOT NULL DEFAULT 'consult',
                memory_type VARCHAR(30) NOT NULL,
                content TEXT NOT NULL,
                references_json TEXT,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_chat_memory_assistant_type
            ON chat_memory (assistant_type)
        """)
    elif not _column_exists(cur, "chat_memory", "references_json"):
        cur.execute("ALTER TABLE chat_memory ADD COLUMN references_json TEXT")
    if _column_exists(cur, "chat_memory", "assistant_type") is False:
        cur.execute("ALTER TABLE chat_memory ADD COLUMN assistant_type VARCHAR(20) NOT NULL DEFAULT 'consult'")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_chat_memory_assistant_type
            ON chat_memory (assistant_type)
        """)

    # --- Chat messages ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id VARCHAR(100),
                assistant_type VARCHAR(20) NOT NULL DEFAULT 'consult',
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                references_json TEXT,
                created_at DATETIME NOT NULL DEFAULT (datetime('now'))
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_chat_messages_conversation_id
            ON chat_messages (conversation_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_chat_messages_assistant_type
            ON chat_messages (assistant_type)
        """)
    elif not _column_exists(cur, "chat_messages", "references_json"):
        cur.execute("ALTER TABLE chat_messages ADD COLUMN references_json TEXT")
    if _column_exists(cur, "chat_messages", "assistant_type") is False:
        cur.execute("ALTER TABLE chat_messages ADD COLUMN assistant_type VARCHAR(20) NOT NULL DEFAULT 'consult'")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_chat_messages_assistant_type
            ON chat_messages (assistant_type)
        """)

    # --- Assistant drafts ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assistant_drafts'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE assistant_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id VARCHAR(100) NOT NULL,
                assistant_type VARCHAR(20) NOT NULL DEFAULT 'openclaw',
                draft_type VARCHAR(20) NOT NULL,
                payload_json TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_assistant_drafts_conversation_id
            ON assistant_drafts (conversation_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_assistant_drafts_assistant_type
            ON assistant_drafts (assistant_type)
        """)
    if _column_exists(cur, "assistant_drafts", "assistant_type") is False:
        cur.execute("ALTER TABLE assistant_drafts ADD COLUMN assistant_type VARCHAR(20) NOT NULL DEFAULT 'openclaw'")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_assistant_drafts_assistant_type
            ON assistant_drafts (assistant_type)
        """)

    # --- Cloud Drive ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cloud_libraries'")
    if cur.fetchone():
        if not _column_exists(cur, "cloud_libraries", "root_path"):
            cur.execute("ALTER TABLE cloud_libraries ADD COLUMN root_path VARCHAR(500)")
        if not _column_exists(cur, "cloud_libraries", "is_system"):
            cur.execute("ALTER TABLE cloud_libraries ADD COLUMN is_system BOOLEAN DEFAULT 0")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cloud_items'")
    if cur.fetchone():
        if not _column_exists(cur, "cloud_items", "rel_path"):
            cur.execute("ALTER TABLE cloud_items ADD COLUMN rel_path VARCHAR(500)")

    # --- Drive sync paths ---
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experiments'")
    if cur.fetchone():
        if not _column_exists(cur, "experiments", "drive_folder_path"):
            cur.execute("ALTER TABLE experiments ADD COLUMN drive_folder_path VARCHAR(500)")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS ix_experiments_drive_folder_path
                ON experiments (drive_folder_path)
            """)

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experiment_records'")
    if cur.fetchone():
        if not _column_exists(cur, "experiment_records", "drive_folder_path"):
            cur.execute("ALTER TABLE experiment_records ADD COLUMN drive_folder_path VARCHAR(500)")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS ix_experiment_records_drive_folder_path
                ON experiment_records (drive_folder_path)
            """)

    conn.commit()
    conn.close()
