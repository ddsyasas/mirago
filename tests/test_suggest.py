"""Tests for did-you-mean suggestions (pure matching, no network)."""

from mirago.suggest import did_you_mean

CORPUS = ["requests", "flask", "django", "numpy", "pandas", "httpx", "pydantic"]


def test_suggests_close_match() -> None:
    assert did_you_mean("requets", CORPUS) == "requests"


def test_suggests_for_transposition() -> None:
    assert did_you_mean("pydnatic", CORPUS) == "pydantic"


def test_no_suggestion_for_gibberish() -> None:
    assert did_you_mean("zzqqxywv", CORPUS) is None


def test_empty_corpus_returns_none() -> None:
    assert did_you_mean("requests", []) is None


def test_bundled_corpus_suggests_popular_package() -> None:
    # Uses the real bundled popular-packages list (no network).
    assert did_you_mean("requets") == "requests"


def test_bundled_corpus_ignores_gibberish() -> None:
    # A hallucinated name unlike any popular package gets no suggestion.
    assert did_you_mean("fastjson_validator") is None
    assert did_you_mean("notarealmodule_xyz_mirago") is None
