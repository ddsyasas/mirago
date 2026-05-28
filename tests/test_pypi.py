"""Tests for the PyPI existence checker."""

import pytest

from mirago.pypi import package_exists_on_pypi


def test_stdlib_short_circuits_without_network() -> None:
    # No httpx call needed: stdlib modules return True immediately.
    assert package_exists_on_pypi("os") is True
    assert package_exists_on_pypi("json") is True


@pytest.mark.network
def test_real_package_exists() -> None:
    assert package_exists_on_pypi("requests", use_cache=False) is True


@pytest.mark.network
def test_hallucinated_package_does_not_exist() -> None:
    fake = "this-package-definitely-does-not-exist-mirago-test-xyz123"
    assert package_exists_on_pypi(fake, use_cache=False) is False
