"""
LaunchAgent-Entry fuer df-cape-coral-property-tracker [CRUX-MK]
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone


class AdapterOrchestrator:
    """Orchestriert daily-run + persistiert State."""

    def __init__(self, state_dir: Optional[str] = None):
        self.state_dir = Path(state_dir or Path.home() / ".df-state" / "cape-coral-property-tracker")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.stop_flag = self.state_dir / "STOP.flag"

    def should_run(self) -> tuple[bool, str]:
        """Pre-Run-Check (K11 + K16)."""
        if self.stop_flag.exists():
            return False, "STOP.flag set (manual halt)"
        return True, "ok"

    def run_daily(self) -> dict:
        """Daily-Run-Pipeline."""
        from .cape_coral_main import CapeCoralPropertyTracker
        from .audit_logger import AuditLogger

        ok, reason = self.should_run()
        if not ok:
            return {"status": "skipped", "reason": reason}

        tracker = CapeCoralPropertyTracker()
        properties = tracker.fetch_listings()
        report = tracker.to_report(properties)

        # Persist Run-Report
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = self.state_dir / f"run-{run_id}.json"
        report_path.write_text(json.dumps(report, indent=2))

        # Audit-Log
        audit = AuditLogger(state_dir=self.state_dir)
        audit.append_event({
            "event": "daily_run_complete",
            "run_id": run_id,
            "n_properties": report["n_properties"],
            "n_top_matches": report["n_top_matches"],
            "source_mode": report["source_mode"],
        })

        return {"status": "ok", "run_id": run_id, "report_path": str(report_path)}


# Type alias for stub annotation in main module
from typing import Optional


if __name__ == "__main__":
    orchestrator = AdapterOrchestrator()
    result = orchestrator.run_daily()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") in ("ok", "skipped") else 1)
