"""Risk scoring: turn existence + metadata into a graded verdict.

Conservative by design. A package is only flagged 'suspicious' (a warning) when it EXISTS
but combines positive risk evidence on multiple axes. Every missing/unknown signal is
treated as safe (fail-open), so a network or stats outage never manufactures a warning.

Thresholds are provisional (see pdocs/v0.2-plan.md calibration); user-tunable config is v0.5.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mirago.lockfile import Lockfile
from mirago.registry import PackageInfo

AGE_DAYS_THRESHOLD = 30
MIN_DOWNLOADS_THRESHOLD = 100


@dataclass
class Verdict:
    severity: str  # "error" | "warning"
    message: str
    signals: dict[str, object] = field(default_factory=dict)


def assess(name: str, info: PackageInfo, lockfile: Lockfile) -> Verdict | None:
    """Grade a single package. Returns None when it looks fine.

    - does not exist            -> error (a hallucination)
    - exists and in the lockfile -> None (a trusted dependency; never warn)
    - exists, recent AND low-downloads -> warning (a possible slopsquat)
    - otherwise                 -> None
    """
    in_lockfile = lockfile.has(name) if lockfile.exists else None
    signals: dict[str, object] = {
        "exists": info.exists,
        "age_days": info.age_days,
        "downloads_last_month": info.downloads_last_month,
        "lockfile_present": lockfile.exists,
        "in_lockfile": in_lockfile,
        "risk_factors": [],
    }

    if not info.exists:
        signals["risk_factors"] = ["not_on_pypi"]
        return Verdict(
            severity="error",
            message=f"Package '{name}' does not exist on PyPI",
            signals=signals,
        )

    # Trusted: a package you already declare as a dependency is never suspicious.
    if in_lockfile:
        return None

    recently_created = info.age_days is not None and info.age_days < AGE_DAYS_THRESHOLD
    low_downloads = (
        info.downloads_last_month is not None
        and info.downloads_last_month < MIN_DOWNLOADS_THRESHOLD
    )

    # Conservative AND: both registry signals must fire. not_in_lockfile alone never warns.
    if not (recently_created and low_downloads):
        return None

    risk: list[str] = ["recently_created", "low_downloads"]
    detail = [f"created {info.age_days}d ago", f"{info.downloads_last_month} downloads/month"]
    if lockfile.exists and in_lockfile is False:
        risk.append("not_in_lockfile")
        detail.append("not in your lockfile")

    signals["risk_factors"] = risk
    return Verdict(
        severity="warning",
        message=f"Package '{name}' exists but looks suspicious ({', '.join(detail)})",
        signals=signals,
    )
