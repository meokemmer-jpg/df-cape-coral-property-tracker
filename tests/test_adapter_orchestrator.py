"""Tests fuer AdapterOrchestrator [CRUX-MK]."""
import json
import tempfile
from pathlib import Path
import pytest
from src.adapter_orchestrator import AdapterOrchestrator


@pytest.fixture
def tmp_state_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_should_run_default_ok(tmp_state_dir):
    """Ohne STOP.flag laeuft."""
    o = AdapterOrchestrator(state_dir=tmp_state_dir)
    ok, reason = o.should_run()
    assert ok is True
    assert reason == "ok"


def test_should_run_blocked_by_stop_flag(tmp_state_dir):
    """STOP.flag blockt Run."""
    o = AdapterOrchestrator(state_dir=tmp_state_dir)
    o.stop_flag.write_text("manual halt")
    ok, reason = o.should_run()
    assert ok is False
    assert "STOP.flag" in reason


def test_run_daily_persists_report(tmp_state_dir):
    """Daily-Run produziert Report-File."""
    o = AdapterOrchestrator(state_dir=tmp_state_dir)
    result = o.run_daily()
    assert result["status"] == "ok"
    assert "run_id" in result
    report = json.loads(Path(result["report_path"]).read_text())
    assert report["n_properties"] == 5
    assert report["source_mode"] == "sandbox-mock"


def test_run_daily_skipped_with_stop_flag(tmp_state_dir):
    """Run skipped wenn STOP.flag."""
    o = AdapterOrchestrator(state_dir=tmp_state_dir)
    o.stop_flag.write_text("halt")
    result = o.run_daily()
    assert result["status"] == "skipped"
