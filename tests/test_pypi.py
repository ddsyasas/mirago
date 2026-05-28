"""Tests for the PyPI existence checker."""

import pytest

from mirago.pypi import fetch_metadata, package_exists_on_pypi


def test_stdlib_short_circuits_without_network() -> None:
    # No httpx call needed: stdlib modules return True immediately.
    assert package_exists_on_pypi("os") is True
    assert package_exists_on_pypi("json") is True


def test_fetch_metadata_stdlib_short_circuits() -> None:
    meta = fetch_metadata("os")
    assert meta == {"exists": True, "age_days": None, "downloads_last_month": None}


@pytest.mark.network
def test_real_package_exists() -> None:
    assert package_exists_on_pypi("requests", use_cache=False) is True


@pytest.mark.network
def test_hallucinated_package_does_not_exist() -> None:
    fake = "this-package-definitely-does-not-exist-mirago-test-xyz123"
    assert package_exists_on_pypi(fake, use_cache=False) is False


@pytest.mark.network
def test_fetch_metadata_real_package_is_old() -> None:
    meta = fetch_metadata("requests", use_cache=False)
    assert meta["exists"] is True
    # requests is years old; well clear of the 30-day "recently created" threshold.
    assert meta["age_days"] is not None
    assert meta["age_days"] > 365


@pytest.mark.network
def test_fetch_metadata_nonexistent() -> None:
    fake = "this-package-definitely-does-not-exist-mirago-test-xyz123"
    meta = fetch_metadata(fake, use_cache=False)
    assert meta["exists"] is False
