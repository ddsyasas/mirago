# Changelog

All notable changes to mirago are recorded here. This project uses
[semantic versioning](https://semver.org/) (loosely, while pre-1.0).

## [0.1.0] - 2026-05-29 (beta)

First public release. mirago checks the packages your Python code imports and flags the ones an AI
assistant likely made up.

### Added
- `mirago check <file>` — flags imports of packages that don't exist on PyPI (the core check).
- `mirago check <folder>` — checks every `.py` file in a folder and its subfolders, skipping noise
  directories (`.venv`, `.git`, caches, `build`, `node_modules`, ...).
- **Smarter detection:** for packages that *do* exist, warns when they look risky — created very
  recently **and** barely downloaded — and treats a package already in your lockfile as trusted.
  Warnings are non-fatal by default; use `--fail-on warning` to make them fail the run.
- **"Did you mean" suggestions** for misspelled popular packages (`requets` → `requests`).
- `--fix` to interactively apply a suggestion.
- `--json` for machine-readable output (used by CI and other tools).
- On-disk caching of PyPI lookups (7 days) so repeated runs are fast.

### Notes
- Exit code is `1` when problems are found (handy for CI), `0` when clean.
- **Fail-open by design:** if PyPI can't be reached, mirago assumes the package is fine rather than
  raising a false alarm.
- Requires Python 3.10+. Works on Windows, macOS, and Linux.
- Not in this release (planned): catching fake *function* names inside real packages, editor/IDE
  integrations, and the real-time agent guardrail.

[0.1.0]: https://github.com/ddsyasas/mirago/releases/tag/v0.1.0
