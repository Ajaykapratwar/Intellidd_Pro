"""
persistence/db.py — SQLite database setup and connection management.

Responsibilities:
  - Create the database file on first run
  - Enable WAL mode for concurrent read safety
  - Create all tables (migrations)
  - Provide get_connection() for all queries

Schema:
  research_runs   — one row per pipeline execution
  company_tags    — user-defined tags for runs (many-to-one)

Usage:
    from persistence.db import get_connection, init_db
    init_db()   # call once at app startup
    conn = get_connection()
"""

import sqlite3
from pathlib import Path

import config


def get_connection() -> sqlite3.Connection:
    """
    Returns a SQLite connection with:
      - WAL mode enabled (safe concurrent reads)
      - Row factory set to sqlite3.Row (access columns by name)
      - Foreign keys enforced

    Always use as a context manager:
        with get_connection() as conn:
            conn.execute(...)
    """
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """
    Initialize the database — create tables if they don't exist.
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
    Call this once at app startup in main.py.
    """
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        # ── research_runs ─────────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS research_runs (
                -- Identity
                run_id              TEXT PRIMARY KEY,
                company_name        TEXT NOT NULL,
                company_url         TEXT NOT NULL,
                company_slug        TEXT NOT NULL,

                -- Timing
                created_at          TEXT NOT NULL,   -- ISO 8601 timestamp
                duration_seconds    REAL DEFAULT 0,

                -- Status
                pipeline_status     TEXT DEFAULT 'completed',
                sector_detected     TEXT DEFAULT '',
                errors_json         TEXT DEFAULT '[]',

                -- Core research outputs (stored as JSON strings)
                seed_data_json          TEXT DEFAULT '{}',
                team_data_json          TEXT DEFAULT '{}',
                investor_data_json      TEXT DEFAULT '{}',
                press_data_json         TEXT DEFAULT '{}',
                financials_data_json    TEXT DEFAULT '{}',
                tech_stack_data_json    TEXT DEFAULT '{}',
                social_data_json        TEXT DEFAULT '{}',
                competitor_data_json    TEXT DEFAULT '{}',
                validation_notes_json   TEXT DEFAULT '{}',
                risk_scorecard_json     TEXT DEFAULT '{}',

                -- Final outputs
                report_markdown     TEXT DEFAULT '',
                output_dir          TEXT DEFAULT '',

                -- RAG metadata
                documents_uploaded  INTEGER DEFAULT 0,   -- count of docs
                doc_names_json      TEXT DEFAULT '[]',   -- list of filenames

                -- Observability
                langsmith_trace_url TEXT DEFAULT '',

                -- User metadata
                notes               TEXT DEFAULT '',
                is_starred          INTEGER DEFAULT 0    -- 0=no, 1=yes
            )
        """)

        # ── company_tags ──────────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS company_tags (
                tag_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      TEXT NOT NULL REFERENCES research_runs(run_id) ON DELETE CASCADE,
                tag         TEXT NOT NULL,
                UNIQUE(run_id, tag)
            )
        """)

        # ── Indexes for fast lookups ──────────────────────────────────────────
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_company_slug
            ON research_runs(company_slug)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_created_at
            ON research_runs(created_at DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_company_name
            ON research_runs(company_name)
        """)

        conn.commit()

    print(f"  ✅ [DB] Database initialized: {config.DB_PATH}")


def get_db_stats() -> dict:
    """
    Returns basic stats about the database for display in UI.
    """
    try:
        with get_connection() as conn:
            total_runs = conn.execute(
                "SELECT COUNT(*) FROM research_runs"
            ).fetchone()[0]

            unique_companies = conn.execute(
                "SELECT COUNT(DISTINCT company_slug) FROM research_runs"
            ).fetchone()[0]

            latest = conn.execute(
                "SELECT created_at FROM research_runs ORDER BY created_at DESC LIMIT 1"
            ).fetchone()

            db_size_bytes = Path(config.DB_PATH).stat().st_size \
                if Path(config.DB_PATH).exists() else 0

            return {
                "total_runs":        total_runs,
                "unique_companies":  unique_companies,
                "latest_run":        latest[0] if latest else "Never",
                "db_size_kb":        round(db_size_bytes / 1024, 1),
            }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Quick test — run: uv run python persistence/db.py
    print("Initializing database...")
    init_db()
    stats = get_db_stats()
    print(f"✅ DB ready. Stats: {stats}")