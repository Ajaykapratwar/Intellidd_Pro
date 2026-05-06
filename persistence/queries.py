"""
persistence/queries.py — All database query functions.

Every interaction with SQLite goes through these functions.
No raw SQL outside this file.

Usage:
    from persistence.queries import save_run, list_runs, get_run
"""

import json
from datetime import datetime
from typing import Optional

from persistence.db import get_connection
from persistence.models import ResearchRun


# ── Write operations ──────────────────────────────────────────────────────────

def save_run(final_state: dict) -> bool:
    """
    Persist a completed pipeline run to the database.

    Args:
        final_state: The DDState dict returned by dd_graph.invoke()

    Returns:
        True on success, False on failure.
    """
    try:
        seed_data    = final_state.get("seed_data", {})
        company_name = seed_data.get("company_name", "Unknown")
        company_url  = final_state.get("company_url", "")
        run_id       = final_state.get("run_id", "")

        # Derive slug from URL
        company_slug = (
            company_url
            .replace("https://", "").replace("http://", "")
            .replace("www.", "").split("/")[0].split(".")[0].lower()
        )

        # Detect sector label from seed data
        try:
            from prompts.sectors import detect_sector, get_sector_label
            sector = detect_sector(seed_data)
            sector_detected = get_sector_label(sector)
        except Exception:
            sector_detected = ""

        # Count uploaded documents
        uploaded_files = final_state.get("uploaded_files", [])
        doc_names = [str(f).split("/")[-1].split("\\")[-1] for f in uploaded_files]

        with get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO research_runs (
                    run_id, company_name, company_url, company_slug,
                    created_at, duration_seconds, pipeline_status,
                    sector_detected, errors_json,
                    seed_data_json, team_data_json, investor_data_json,
                    press_data_json, financials_data_json, tech_stack_data_json,
                    social_data_json, competitor_data_json,
                    validation_notes_json, risk_scorecard_json,
                    report_markdown, output_dir,
                    documents_uploaded, doc_names_json,
                    langsmith_trace_url, notes, is_starred
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?
                )
            """, (
                run_id,
                company_name,
                company_url,
                company_slug,
                datetime.now().isoformat(),
                float(final_state.get("duration_seconds", 0)),
                final_state.get("pipeline_status", "completed"),
                sector_detected,
                json.dumps(final_state.get("errors", [])),
                json.dumps(seed_data),
                json.dumps(final_state.get("team_data", {})),
                json.dumps(final_state.get("investor_data", {})),
                json.dumps(final_state.get("press_data", {})),
                json.dumps(final_state.get("financials_data", {})),
                json.dumps(final_state.get("tech_stack_data", {})),
                json.dumps(final_state.get("social_data", {})),
                json.dumps(final_state.get("competitor_data", {})),
                json.dumps(final_state.get("validation_notes", {})),
                json.dumps(final_state.get("risk_scorecard", {})),
                final_state.get("report_markdown", ""),
                final_state.get("output_dir", ""),
                len(uploaded_files),
                json.dumps(doc_names),
                final_state.get("langsmith_trace_url", ""),
                "",    # notes — empty by default
                0,     # is_starred — false by default
            ))
            conn.commit()

        print(f"  💾 [DB] Run saved: {run_id} ({company_name})")
        return True

    except Exception as e:
        print(f"  ❌ [DB] Failed to save run: {e}")
        return False


def update_run_notes(run_id: str, notes: str) -> bool:
    """Update the user notes for a run."""
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE research_runs SET notes = ? WHERE run_id = ?",
                (notes, run_id)
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"  ❌ [DB] Failed to update notes: {e}")
        return False


def toggle_star(run_id: str) -> bool:
    """Toggle the starred status of a run. Returns new star state."""
    try:
        with get_connection() as conn:
            current = conn.execute(
                "SELECT is_starred FROM research_runs WHERE run_id = ?",
                (run_id,)
            ).fetchone()
            if not current:
                return False
            new_state = 0 if current["is_starred"] else 1
            conn.execute(
                "UPDATE research_runs SET is_starred = ? WHERE run_id = ?",
                (new_state, run_id)
            )
            conn.commit()
        return bool(new_state)
    except Exception as e:
        print(f"  ❌ [DB] Failed to toggle star: {e}")
        return False


def add_tag(run_id: str, tag: str) -> bool:
    """Add a tag to a run. Silently ignores duplicates."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO company_tags (run_id, tag) VALUES (?, ?)",
                (run_id, tag.strip().lower())
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"  ❌ [DB] Failed to add tag: {e}")
        return False


def remove_tag(run_id: str, tag: str) -> bool:
    """Remove a tag from a run."""
    try:
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM company_tags WHERE run_id = ? AND tag = ?",
                (run_id, tag.strip().lower())
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"  ❌ [DB] Failed to remove tag: {e}")
        return False


def delete_run(run_id: str) -> bool:
    """Permanently delete a run and its tags."""
    try:
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM research_runs WHERE run_id = ?", (run_id,)
            )
            conn.commit()
        print(f"  🗑️  [DB] Run deleted: {run_id}")
        return True
    except Exception as e:
        print(f"  ❌ [DB] Failed to delete run: {e}")
        return False


# ── Read operations ───────────────────────────────────────────────────────────

def _get_tags_for_run(conn, run_id: str) -> list[str]:
    """Internal helper: fetch tags for a single run."""
    rows = conn.execute(
        "SELECT tag FROM company_tags WHERE run_id = ? ORDER BY tag",
        (run_id,)
    ).fetchall()
    return [r["tag"] for r in rows]


def get_run(run_id: str) -> Optional[ResearchRun]:
    """
    Fetch a single run by ID with full data.

    Returns:
        ResearchRun object or None if not found.
    """
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM research_runs WHERE run_id = ?",
                (run_id,)
            ).fetchone()
            if not row:
                return None
            tags = _get_tags_for_run(conn, run_id)
            return ResearchRun.from_row(dict(row), tags)
    except Exception as e:
        print(f"  ❌ [DB] Failed to get run {run_id}: {e}")
        return None


def list_runs(
    limit: int = 50,
    offset: int = 0,
    company_slug: Optional[str] = None,
    starred_only: bool = False,
    status_filter: Optional[str] = None,
) -> list[ResearchRun]:
    """
    List runs ordered by most recent first.

    Args:
        limit:         Max number to return
        offset:        Pagination offset
        company_slug:  Filter to a specific company slug
        starred_only:  Only return starred runs
        status_filter: Filter by pipeline_status ('completed', 'failed')

    Returns:
        List of ResearchRun objects (full data).
    """
    try:
        conditions = []
        params = []

        if company_slug:
            conditions.append("company_slug = ?")
            params.append(company_slug)
        if starred_only:
            conditions.append("is_starred = 1")
        if status_filter:
            conditions.append("pipeline_status = ?")
            params.append(status_filter)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params += [limit, offset]

        with get_connection() as conn:
            rows = conn.execute(f"""
                SELECT * FROM research_runs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, params).fetchall()

            runs = []
            for row in rows:
                tags = _get_tags_for_run(conn, row["run_id"])
                runs.append(ResearchRun.from_row(dict(row), tags))
            return runs

    except Exception as e:
        print(f"  ❌ [DB] Failed to list runs: {e}")
        return []


def search_runs(query: str, limit: int = 20) -> list[ResearchRun]:
    """
    Full-text search across company names and report markdown.

    Args:
        query: Search string
        limit: Max results

    Returns:
        List of matching ResearchRun objects.
    """
    try:
        search_term = f"%{query.lower()}%"
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM research_runs
                WHERE LOWER(company_name) LIKE ?
                   OR LOWER(company_url)  LIKE ?
                   OR LOWER(report_markdown) LIKE ?
                   OR LOWER(sector_detected)  LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (search_term, search_term, search_term, search_term, limit)
            ).fetchall()

            runs = []
            for row in rows:
                tags = _get_tags_for_run(conn, row["run_id"])
                runs.append(ResearchRun.from_row(dict(row), tags))
            return runs

    except Exception as e:
        print(f"  ❌ [DB] Failed to search runs: {e}")
        return []


def get_runs_for_company(company_slug: str) -> list[ResearchRun]:
    """
    Get all runs for a specific company, ordered by date.
    Used for the comparison feature.
    """
    return list_runs(limit=20, company_slug=company_slug)


def get_all_company_slugs() -> list[dict]:
    """
    Returns list of all unique companies with run counts.
    Used to populate company selector in History page.
    """
    try:
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT
                    company_slug,
                    company_name,
                    COUNT(*) as run_count,
                    MAX(created_at) as latest_run
                FROM research_runs
                GROUP BY company_slug
                ORDER BY latest_run DESC
            """).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"  ❌ [DB] Failed to get companies: {e}")
        return []


def count_runs(company_slug: Optional[str] = None) -> int:
    """Return total run count, optionally filtered by company."""
    try:
        with get_connection() as conn:
            if company_slug:
                result = conn.execute(
                    "SELECT COUNT(*) FROM research_runs WHERE company_slug = ?",
                    (company_slug,)
                ).fetchone()
            else:
                result = conn.execute(
                    "SELECT COUNT(*) FROM research_runs"
                ).fetchone()
            return result[0]
    except Exception:
        return 0