"""Tests fuer CapeCoralPropertyTracker [CRUX-MK]."""
import os
import pytest
from src.cape_coral_main import CapeCoralPropertyTracker, MOCK_PROPERTIES, Property, FamilyMatchScore


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("DF_CAPE_CORAL_REAL_ENABLED", raising=False)
    monkeypatch.delenv("PHRONESIS_TICKET", raising=False)


def test_default_sandbox_mode():
    """Default ist Sandbox (Real disabled)."""
    t = CapeCoralPropertyTracker()
    assert t.real_enabled is False


def test_real_mode_requires_phronesis(monkeypatch):
    """Real-Mode ohne PHRONESIS_TICKET wirft K13-PAV-VIOLATION."""
    monkeypatch.setenv("DF_CAPE_CORAL_REAL_ENABLED", "true")
    with pytest.raises(RuntimeError, match="K13-PAV-VIOLATION"):
        CapeCoralPropertyTracker()


def test_real_mode_with_phronesis_ok(monkeypatch):
    """Real-Mode mit PHRONESIS_TICKET ist erlaubt."""
    monkeypatch.setenv("DF_CAPE_CORAL_REAL_ENABLED", "true")
    monkeypatch.setenv("PHRONESIS_TICKET", "PT-2026-05-11-001")
    t = CapeCoralPropertyTracker()
    assert t.real_enabled is True
    assert t.phronesis_ticket == "PT-2026-05-11-001"


def test_fetch_listings_sandbox():
    """Sandbox liefert MOCK_PROPERTIES (5 Stueck)."""
    t = CapeCoralPropertyTracker()
    listings = t.fetch_listings()
    assert len(listings) == 5
    assert all(isinstance(p, Property) for p in listings)


def test_compute_family_match_perfect():
    """Property MOCK-002 hat perfekten Match (4/4)."""
    t = CapeCoralPropertyTracker()
    perfect = MOCK_PROPERTIES[1]  # MOCK-002 5br/pool/boat/9.2-school
    score = t.compute_family_match(perfect)
    assert score.overall_score == 1.0
    assert score.pool_match and score.boat_access_match
    assert score.school_match and score.bedrooms_match


def test_compute_family_match_partial():
    """MOCK-003 ist 0/4 Match (3br/no-pool/no-boat/7.0-school)."""
    t = CapeCoralPropertyTracker()
    bad = MOCK_PROPERTIES[2]
    score = t.compute_family_match(bad)
    assert score.overall_score == 0.0


def test_filter_top_matches():
    """Top-Matches mit Score >= 0.75."""
    t = CapeCoralPropertyTracker()
    top = t.filter_top_matches(MOCK_PROPERTIES, min_score=0.75)
    # MOCK-001/002/004 = 1.0, MOCK-005 = 0.75 (pool+bed+school7.5<8 fail+no-boat) = 0.5
    assert len(top) >= 2  # MOCK-001 + MOCK-002 + MOCK-004 perfekt
    assert all(m.overall_score >= 0.75 for m in top)


def test_detect_price_drops():
    """Price-Drop-Detection."""
    t = CapeCoralPropertyTracker()
    previous = list(MOCK_PROPERTIES)
    # Simuliere Preis-Drop bei MOCK-001
    current = list(MOCK_PROPERTIES)
    current[0] = Property(
        listing_id="MOCK-001", address=current[0].address,
        price_usd=460000,  # was 485000
        bedrooms=4, bathrooms=3.0, sqft=2400, pool=True, boat_access=True,
        school_district_score=8.5, listed_date="2026-04-01", source="mock",
    )
    drops = t.detect_price_drops(current, previous)
    assert len(drops) == 1
    assert drops[0]["listing_id"] == "MOCK-001"
    assert drops[0]["delta_usd"] == 25000


def test_detect_price_drops_no_change():
    """Keine Drops bei identischen Preisen."""
    t = CapeCoralPropertyTracker()
    drops = t.detect_price_drops(list(MOCK_PROPERTIES), list(MOCK_PROPERTIES))
    assert drops == []


def test_to_report_structure():
    """Report enthaelt Pflicht-Felder."""
    t = CapeCoralPropertyTracker()
    report = t.to_report(t.fetch_listings())
    assert "run_timestamp" in report
    assert report["source_mode"] == "sandbox-mock"
    assert report["n_properties"] == 5
    assert "top_matches" in report
    assert "all_matches" in report


def test_real_api_raises_not_implemented(monkeypatch):
    """Real-API-Branch ist nicht implementiert (skeleton)."""
    monkeypatch.setenv("DF_CAPE_CORAL_REAL_ENABLED", "true")
    monkeypatch.setenv("PHRONESIS_TICKET", "PT-001")
    t = CapeCoralPropertyTracker()
    with pytest.raises(NotImplementedError):
        t.fetch_listings()


def test_phronesis_ticket_default_missing():
    """Default PHRONESIS_TICKET = MISSING."""
    t = CapeCoralPropertyTracker()
    assert t.phronesis_ticket == "MISSING"
