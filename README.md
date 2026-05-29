# mirago

> Catch the fake package names AI coding tools make up — before you try to install them.

[![PyPI](https://img.shields.io/pypi/v/mirago.svg)](https://pypi.org/project/mirago/)
[![Python versions](https://img.shields.io/pypi/pyversions/mirago.svg)](https://pypi.org/project/mirago/)
[![CI](https://github.com/ddsyasas/mirago/actions/workflows/ci.yml/badge.svg)](https://github.com/ddsyasas/mirago/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

**Status: 0.1.0 — beta.** It works and it's useful; it's also early, so expect rough edges and
tell us what's missing.

## What it does (in plain words)

When you ask an AI tool (Copilot, Cursor, Claude, and others) to write Python code, it sometimes
`import`s a package that doesn't actually exist — it made the name up. If you try to install it,
you waste time chasing a package that was never real.

mirago reads your code, looks at every package it imports, and checks each one against PyPI (the
official Python package index). It tells you about two kinds of problem:

1. **Doesn't exist** — the AI invented the name. (An error.)
2. **Exists but looks risky** — the name is real, but it was created very recently *and* is barely
   downloaded *and* isn't already used in your project. (A warning — could be a copycat package.)

```bash
mirago check your_file.py
```

If something's fake, you'll see:

```
🚨 1 hallucination in your_file.py

  Line 1: import fastjson_validator
    → Package 'fastjson_validator' does not exist on PyPI
```

If everything looks fine, mirago stays quiet (just a short summary).

## Install

mirago is a command-line tool. The easiest way is [pipx](https://pipx.pypa.io/), which installs
CLI tools in their own isolated environment:

```bash
pipx install mirago
```

Or with plain pip:

```bash
pip install mirago
```

**Requirements:** Python 3.10 or newer. mirago works the same on **Windows, macOS, and Linux**
(it's pure Python).

<details>
<summary>Platform notes</summary>

- **macOS / Linux:** install pipx with `pip install --user pipx` (or `brew install pipx` on macOS),
  then `pipx install mirago`.
- **Windows:** in PowerShell, `py -m pip install --user pipx` then `py -m pipx install mirago`.
  Make sure Python is on your PATH (the official python.org installer has a checkbox for this).

</details>

## Usage

```bash
mirago check your_file.py        # check one file
mirago check .                   # check this folder and everything under it
mirago check src/                # check a folder
```

When you point it at a folder, mirago checks every `.py` file inside it, skipping noise like
`.venv`, `.git`, caches, and `build` folders.

Handy options:

| Option | What it does |
|---|---|
| `--fix` | Offer to fix a misspelled package name (`requets` → `requests`). |
| `--fail-on warning` | Make the run fail (exit `1`) on warnings too, not just errors. |
| `--json` | Print results as JSON, for use by other tools or CI. |
| `--no-cache` | Skip the saved results and re-check against PyPI. |

The exit code is `1` when problems are found and `0` when clean, so mirago drops straight into
automated checks (CI).

## What it catches — and what it doesn't (yet)

**Catches today:**
- Package names that don't exist on PyPI (names an AI made up).
- Real-but-risky packages (brand-new + barely downloaded + not already in your project).
- Common typos of popular packages, with a suggested fix.

**Doesn't catch yet (planned):**
- Fake *function* or method names inside real packages (e.g. a method that doesn't exist).
- Editor / IDE integrations — there are **none yet**; mirago is a command-line tool for now.
- Catching mistakes live, as an AI assistant writes them.

A safety note: if PyPI can't be reached, mirago assumes your packages are fine rather than raising
a false alarm. It would rather miss occasionally than cry wolf.

## Contributing

Issues and pull requests are welcome. To work on mirago locally:

```bash
git clone https://github.com/ddsyasas/mirago
cd mirago

# Install with the developer tools
pip install -e ".[dev]"

# Run the tests (tests needing live PyPI are skipped by default)
pytest

# Try it on the bundled examples
mirago check tests/fixtures/good.py
mirago check tests/fixtures/bad.py
```

See [docs/DEVLOG.md](./docs/DEVLOG.md) for a plain-language history of what changed and why, and
[CHANGELOG.md](./CHANGELOG.md) for the release notes.

## License

MIT. See [LICENSE](./LICENSE).
