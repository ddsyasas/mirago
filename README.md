# mirago

> Catch the fake package names AI coding tools make up — before you try to install them.

## What it does (in plain words)

When you ask an AI tool (Copilot, Cursor, Claude, and others) to write Python code, it
sometimes `import`s a package that doesn't actually exist — it made the name up. If you try to
install it, you waste time chasing a package that was never real.

mirago reads your file, looks at every package it imports, and checks each one against PyPI
(the official Python package index). If a package doesn't exist, mirago tells you — so you can
fix it before running `pip install`.

```bash
mirago check your_file.py
```

If something's fake, you'll see:

```
🚨 1 hallucination in your_file.py

  Line 1: import fastjson_validator
    → Package 'fastjson_validator' does not exist on PyPI
```

If everything is real, mirago stays quiet.

## Where the project is right now

- **v0.1 — works today:** checks whether the packages you import actually exist on PyPI.
- **Internal cleanup — done:** the code was reorganized to make new features easier to add.
  How the tool behaves did not change.
- **Smarter detection (v0.2) — in progress:** also warns about packages that *do* exist but
  look risky (brand-new, almost never downloaded, and not already used in your project). Adds
  "did you mean" suggestions for typos and a `--fix` option.
- **Experiment — done:** we showed mirago can stop an AI assistant from writing a fake import
  the moment it tries, not just after the fact.

## Install (when v0.1 is published)

```bash
pipx install mirago
```

## Usage

```bash
mirago check your_file.py        # check one file
mirago check .                   # check a whole folder (and its subfolders)
mirago check src/                # check a folder
```

When you point it at a folder, mirago checks every `.py` file inside it, skipping noise like
`.venv`, `.git`, caches, and `build` folders.

The exit code is `1` when problems are found, which makes mirago easy to use in automated
checks (CI).

## What v0.1 catches — and what it doesn't (yet)

- **Catches:** package names that don't exist on PyPI (names an AI made up). Works for both
  `import x` and `from x import y`, and for submodules (`import x.y.z` checks `x`).
- **Doesn't catch yet:** a fake-sounding name that someone has *actually registered* on PyPI.
  Because it exists, a simple "does it exist?" check can't see it. Catching this is the job of
  the smarter detection coming in v0.2.

## What's coming next

- Finish v0.2 smarter detection (warn on risky-but-real packages, suggestions, `--fix`).
- Catch fake *function* names inside real packages (e.g. a method that doesn't exist).
- Editor and CI integrations so mirago runs automatically.

## Development

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

See [docs/DEVLOG.md](./docs/DEVLOG.md) for a plain-language history of what changed and why.

## License

MIT. See [LICENSE](./LICENSE).
