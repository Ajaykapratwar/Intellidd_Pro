"""
monitoring/scheduler.py — APScheduler singleton for company monitoring.

Design decisions:
  - Monitor configs are stored in SQLite (our DB), not APScheduler's job store
  - On startup, all active monitors are loaded from DB and re-registered
  - This means monitors survive app restarts correctly
  - APScheduler runs in a BackgroundScheduler (non-blocking thread)
  - Each job: run pipeline → detect changes → save events → send alerts

Usage:
    from monitoring.scheduler import get_scheduler
    sched = get_scheduler()
    sched.add_monitor(company_url, ...)
    sched.start()
"""

import time
import threading
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import config

# ── Frequency config ──────────────────────────────────────────────────────────

FREQUENCY_OPTIONS = {
    "daily": {"hours", 24},
    "weekly": {"weeks": 1},
    "monthly": {"weeks": 4},
}

FREQUENCY_LABELS = {
    "daily": "Every 24 hours",
    "weekly": "Every 7 days",
    "monthly": "Every 30 days",
}

# ── Job Function ──────────────────────────────────────────────────────────

def _run_monitor_job(monitor_id: str) -> None:
    """
    The function APScheduler calls for each scheduled monitor.

    Steps:
      1. Load monitor config from DB
      2. Run full due diligence pipeline
      3. Get previous run for this company from DB
      4. Detect changes between new and previous run
      5. Save change events to DB
      6. Send alerts if significant changes found
      7. Update monitor's last_run timestamp
    """

    from persistence.db import init_db
    from persistence import queries
    from monitoring.change_detector import detect_changes, has_significant_changes
    from monitoring.alerting import send_alerts

    init_db()

    monitor = queries.get_monitor(monitor_id)
    if not monitor or not monitor.get("is_Active"):
        print(f"  ⚠️  [Scheduler] Monitor {monitor_id} not found or inactive — skipping")
        return

    company_url = monitor["company_URL"]
    company_name = monitor["company_name"]
    alert_email = monitor.get("alert_email", "")
    alert_slack = monitor.get("alert_slack", "")

    print(f"\n{'='*60}")
    print(f"  ⏰ [Scheduler] Running scheduled monitor: {company_name}")
    print(f"  Monitor ID: {monitor_id}")
    print(f"{'='*60}")

    try:
        # Step 1: Run pipeline
        from pipeline.runner import run_due_diligence
        final_state = run_due_diligence(company_url)
        new_run_id = final_state.get("run_id", "")

        # Step 2: Get previous run (exclude the one we just created)
        company_slug = company_url.replace("https://", "").replace("http://", "").replace("www.", "").split("/").split(".")[0].lower()
        all_runs = queries.get_runs_for_company(company_slug)
        prev_runs = [r for r in all_runs if r.run_id != new_run_id]

        if not prev_runs:
            print(f"  🔍 No previous runs found for {company_name} — skipping change detection")
            queries.update_monitor_last_run(monitor_id, datetime.utcnow())
            return
        
        new_run = queries.get_run(new_run_id)
        prev_runs = prev_runs[0]

        if not new_run:
            print(f"  ⚠️  New run {new_run_id} not found in DB — skipping change detection")
            queries.update_monitor_last_run(monitor_id, datetime.utcnow())
            return
        
        # Step 3: Detect changes
        events = detect_changes(new_run, prev_runs, use_llm=True)

        # Step 4: Save change events
        for event in events:
            queries.save_change_event(
                monitor_id=monitor_id,
                new_run_id=new_run_id,
                old_run_id = prev_runs.run_id
                event=event,
            )
        
        # Step 5: Send alerts if significant
        if has_significant_changes(events):
            send_alerts(company_name, company_url, events, alert_email or None, alert_slack or None)
        else:
            print(f"  ℹ️  [Scheduler] No significant changes — alerts not sent")

        # Step 6: Update last_run
        queries.update_monitor_last_run(monitor_id, datetime.utcnow())

        print(f"  ✅ [Scheduler] Monitor job complete: {company_name}")
        print(f"     Changes: {len(events)} | Significant: {has_significant_changes(events)}")
        
    except Exception as e:
        print(f"  ❌ [Scheduler] Error running monitor job {monitor_id}: {e}")
        import traceback
        traceback.print_exc()


# ── Scheduler singleton ───────────────────────────────────────────────────────

class IntelliDDScheduler:
    """
    Singleton wrapper around APScheduler's BackgroundScheduler.
    Manages all company monitoring jobs.
    """

    def __init__(self):
        self._scheduler = BackgroundScheduler(
            job_defaults = {
                "coalesce": True,
                "max_instances": 1,
            }
        )
        self._started = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the scheduler and reload all active monitors from DB."""
        with self._lock:
            if self._started:
                return
            try:
                self._scheduler.start()
                self._started = True
                print("  🚀 [Scheduler] Scheduler started successfully")
                self._reload_monitors()
            except Exception as e:
                print(f"  ❌ [Scheduler] Failed to start scheduler: {e}")

    def stop(self) -> None:
        """Gracefully stops the scheduler"""
        with self._lock:
            if self._started:
                self._scheduler.shutdown(wait=False)
                self._started = False
                print("  🛑 [Scheduler] Scheduler stopped")
    
    def _reload_monitors(self) -> None:
        """Load all active monitors from DB and register their jobs."""
        try:
            from persistence.db import init_db
            from persistence import queries

            init_db()

            monitors = queries.list_monitors(active_only=True)
            for m in monitors:
                self._register_job(m)
            print(f"  🔄 [Scheduler] Reloaded {len(monitors)} active monitors")

        except Exception as e:
            print(f"  ❌ [Scheduler] Failed to reload monitors: {e}")
    
    def _register_job(self, monitor: dict) -> None:
        """Register a single monitor job with APScheduler."""

        monitor_id = monitor["monitor_id"]
        frequency = monitor.get("frequency", "weekly")
        interval = FREQUENCY_OPTIONS.get(frequency, FREQUENCY_OPTIONS["weekly"])

        job_id = f"monitor_{monitor_id}"

        # Remove existing job if it exists
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)

        self._scheduler.add_job(
            func=_run_monitor_job,
            trigger=IntervalTrigger(**interval),
            id=job_id,
            args=[monitor_id],
            name=f"Monitor {monitor.get('company_name', monitor_id)}",
            replace_existing=True,
        )

        print(f"  📅 [Scheduler] Registered job: {monitor.get('company_name')} ({frequency})")
    
    def add_monitor(self, company_url: str, company_name: str, frequency: str="weekly", alert_email: Optional[str]=None, alert_slack_webhook: Optional[str]=None) -> Optional[str]:
        """
        Add a new company monitor.

        Args:
            company_url:         URL to monitor
            company_name:        Display name
            frequency:           "daily" | "weekly" | "monthly"
            alert_email:         Optional email for alerts
            alert_slack_webhook: Optional Slack webhook URL

        Returns:
            monitor_id string on success, None on failure.
        """
        from persistence import queries

        monitor_id = queries.save_monitor(
            company_url=company_url,
            company_name=company_name,
            frequency=frequency,
            alert_email=alert_email or "",
            alert_slack_webhook=alert_slack_webhook or "",
        )

        if monitor_id and self._started:
            monitor = queries.get_monitor(monitor_id)
            if monitor:
                self._register_job(monitor)

        return monitor_id
    
    def remove_monitor(self, monitor_id: str) -> bool:
        """Remove a monitor by ID."""
        from persistence import queries

        job_id = f"monitor_{monitor_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            print(f"  🗑️  [Scheduler] Removed job: {job_id}")

        return queries.delete_monitor(monitor_id)

    def toggle_monitor(self, monitor_id: str, active: bool) -> bool:
        """Enable/disable a monitor by ID."""
        from persistence import queries

        success = queries.toogle_monitor_Active(monitor_id, active)
        if success:
            monitor = queries.get_monitor(monitor_id)
            if monitor:
                job_id = f"monitor_{monitor_id}"
                if active:
                    self._register_job(monitor)
                else:
                    if self._scheduler.get_job(job_id):
                        self._scheduler.remove_job(job_id)
        return success
    
    def run_now(self, monitor_id: str) -> bool:
        """Execute a monitor job immediately."""
        from persistence import queries
        monitor = queries.get_monitor(monitor_id)
        if not monitor:
            return False

        thread = threading.Thread(
            target=_run_monitor_job,
            args=[monitor_id],
            daemon=True,
        )
        thread.start()
        print(f"  ▶️  [Scheduler] Manual run triggered: {monitor.get('company_name')}")
        return True

    def get_job_status(self, monitor_id: str) -> dict:
        """Get APScheduler job status for a monitor."""
        job_id = f"monitor_{monitor_id}"
        job    = self._scheduler.get_job(job_id)

        if not job:
            return {"registered": False, "next_run": None}

        return {
            "registered": True,
            "next_run":   job.next_run_time.isoformat() if job.next_run_time else None,
            "job_id":     job_id,
        }

    @property
    def is_running(self) -> bool:
        return self._started and self._scheduler.running


# ── Module-level singleton ────────────────────────────────────────────────────

_scheduler_instance: Optional[IntelliDDScheduler] = None
_scheduler_lock = threading.Lock()


def get_scheduler() -> IntelliDDScheduler:
    """
    Get the global scheduler singleton.
    Creates and starts it on first call.
    """
    global _scheduler_instance
    with _scheduler_lock:
        if _scheduler_instance is None:
            _scheduler_instance = IntelliDDScheduler()
        return _scheduler_instance