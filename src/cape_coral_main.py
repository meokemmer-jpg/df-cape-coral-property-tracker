"""
Cape-Coral-Property-Tracker Core-Logic [CRUX-MK]
Sandbox-Default mit Mock-Properties. Real-API ENV-Var-gated.

K_0 Touch: Real-Estate-Investment $300-800k
Q_0 Touch: Familien-Hauptwohnsitz-Wechsel
"""
import os
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class Property:
    """Immutable Property-Listing."""
    listing_id: str
    address: str
    price_usd: int
    bedrooms: int
    bathrooms: float
    sqft: int
    pool: bool
    boat_access: bool
    school_district_score: float  # 0-10
    listed_date: str  # ISO
    source: str  # "mock" | "zillow" | "realtor"


@dataclass
class FamilyMatchScore:
    """Familien-Match-Score nach 4 Kriterien."""
    listing_id: str
    pool_match: bool  # Pflicht
    boat_access_match: bool  # Wunsch (Cape Coral Canal-System)
    school_match: bool  # >=8.0
    bedrooms_match: bool  # >=4
    overall_score: float  # 0.0-1.0
    timestamp: str


# 5 Mock-Properties fuer Sandbox-Default
MOCK_PROPERTIES = [
    Property("MOCK-001", "1234 SE 22nd Ter, Cape Coral FL 33990", 485000, 4, 3.0, 2400, True, True, 8.5, "2026-04-01", "mock"),
    Property("MOCK-002", "5678 SW 31st St, Cape Coral FL 33914", 720000, 5, 4.0, 3200, True, True, 9.2, "2026-04-15", "mock"),
    Property("MOCK-003", "910 NE 15th Pl, Cape Coral FL 33909", 320000, 3, 2.0, 1800, False, False, 7.0, "2026-04-20", "mock"),
    Property("MOCK-004", "2345 SW 47th St, Cape Coral FL 33914", 595000, 4, 3.5, 2800, True, True, 8.8, "2026-05-01", "mock"),
    Property("MOCK-005", "6789 SE 8th Ave, Cape Coral FL 33990", 410000, 4, 2.5, 2200, True, False, 7.5, "2026-05-05", "mock"),
]


class CapeCoralPropertyTracker:
    """Property-Tracker fuer Cape-Coral-FL Listings.

    Sandbox-Default mit 5 Mock-Properties. Real-API via ENV-Var-Gated.
    """

    MIN_BEDROOMS = 4
    MIN_SCHOOL_SCORE = 8.0

    def __init__(self, real_enabled: Optional[bool] = None):
        if real_enabled is None:
            real_enabled = os.environ.get("DF_CAPE_CORAL_REAL_ENABLED", "false").lower() == "true"
        self.real_enabled = real_enabled
        self.phronesis_ticket = os.environ.get("PHRONESIS_TICKET", "MISSING")

        # K_0/Q_0 Pre-Action-Verification (K13 PAV)
        if self.real_enabled and self.phronesis_ticket == "MISSING":
            raise RuntimeError(
                "K13-PAV-VIOLATION: Real-Mode aktiviert ohne PHRONESIS_TICKET. "
                "Cape-Coral-Property-Tracker beruehrt K_0+Q_0. Phronesis Pflicht."
            )

    def fetch_listings(self) -> list[Property]:
        """Fetch Property-Listings. Sandbox-Default = MOCK_PROPERTIES."""
        if not self.real_enabled:
            return list(MOCK_PROPERTIES)
        # Real-API-Call WAERE hier (Zillow/Realtor.com), aber default disabled
        raise NotImplementedError("Real-API-Adapter pending Phronesis-Approval")

    def compute_family_match(self, prop: Property) -> FamilyMatchScore:
        """Berechnet 4-Kriterien-Match."""
        pool_m = prop.pool
        boat_m = prop.boat_access
        school_m = prop.school_district_score >= self.MIN_SCHOOL_SCORE
        bed_m = prop.bedrooms >= self.MIN_BEDROOMS
        score = sum([pool_m, boat_m, school_m, bed_m]) / 4.0
        return FamilyMatchScore(
            listing_id=prop.listing_id,
            pool_match=pool_m,
            boat_access_match=boat_m,
            school_match=school_m,
            bedrooms_match=bed_m,
            overall_score=score,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def detect_price_drops(self, current: list[Property], previous: list[Property]) -> list[dict]:
        """Detect Price-Drops zwischen Run-N und Run-N-1."""
        prev_map = {p.listing_id: p.price_usd for p in previous}
        drops = []
        for p in current:
            if p.listing_id in prev_map and p.price_usd < prev_map[p.listing_id]:
                drops.append({
                    "listing_id": p.listing_id,
                    "old_price": prev_map[p.listing_id],
                    "new_price": p.price_usd,
                    "delta_usd": prev_map[p.listing_id] - p.price_usd,
                    "delta_pct": round((prev_map[p.listing_id] - p.price_usd) / prev_map[p.listing_id] * 100, 2),
                })
        return drops

    def filter_top_matches(self, properties: list[Property], min_score: float = 0.75) -> list[FamilyMatchScore]:
        """Filtert Top-Matches mit Score >= min_score."""
        return [
            self.compute_family_match(p)
            for p in properties
            if self.compute_family_match(p).overall_score >= min_score
        ]

    def to_report(self, properties: list[Property]) -> dict:
        """Generiert Run-Report (idempotent)."""
        matches = [self.compute_family_match(p) for p in properties]
        top = [m for m in matches if m.overall_score >= 0.75]
        return {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_mode": "real-api" if self.real_enabled else "sandbox-mock",
            "phronesis_ticket": self.phronesis_ticket,
            "n_properties": len(properties),
            "n_top_matches": len(top),
            "top_matches": [asdict(m) for m in top],
            "all_matches": [asdict(m) for m in matches],
        }
