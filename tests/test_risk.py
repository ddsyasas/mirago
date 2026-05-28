"""Tests for the risk scorer. Pure/offline — synthetic PackageInfo + Lockfile."""

from mirago.lockfile import Lockfile
from mirago.registry import PackageInfo
from mirago.risk import assess

NO_LOCK = Lockfile(exists=False)


def info(
    *, exists: bool = True, age: int | None = None, downloads: int | None = None
) -> PackageInfo:
    return PackageInfo(exists=exists, age_days=age, downloads_last_month=downloads)


def test_nonexistent_is_error() -> None:
    v = assess("fastjson_validator", info(exists=False), NO_LOCK)
    assert v is not None
    assert v.severity == "error"
    assert "does not exist" in v.message
    assert v.signals["risk_factors"] == ["not_on_pypi"]


def test_recent_and_low_downloads_is_warning() -> None:
    v = assess("sketchy", info(age=3, downloads=10), NO_LOCK)
    assert v is not None
    assert v.severity == "warning"
    assert v.signals["risk_factors"] == ["recently_created", "low_downloads"]


def test_recent_but_popular_is_safe() -> None:
    assert assess("x", info(age=3, downloads=10_000), NO_LOCK) is None


def test_old_but_obscure_is_safe() -> None:
    assert assess("x", info(age=4000, downloads=5), NO_LOCK) is None


def test_unknown_age_fails_safe() -> None:
    # low downloads but unknown age -> not both signals -> safe
    assert assess("x", info(age=None, downloads=5), NO_LOCK) is None


def test_unknown_downloads_fails_safe() -> None:
    assert assess("x", info(age=2, downloads=None), NO_LOCK) is None


def test_in_lockfile_suppresses_warning() -> None:
    lock = Lockfile(exists=True, packages={"sketchy"})
    assert assess("sketchy", info(age=3, downloads=10), lock) is None


def test_not_in_lockfile_added_as_factor() -> None:
    lock = Lockfile(exists=True, packages={"something-else"})
    v = assess("sketchy", info(age=3, downloads=10), lock)
    assert v is not None
    assert v.severity == "warning"
    assert "not_in_lockfile" in v.signals["risk_factors"]


def test_lockfile_membership_is_canonicalized() -> None:
    lock = Lockfile(exists=True, packages={"foo-bar"})
    assert assess("Foo_Bar", info(age=1, downloads=1), lock) is None
