# Contributing to mirago

Thanks for your interest! mirago is early (0.1.0 beta), so there's plenty of useful work to do —
see [ROADMAP.md](./ROADMAP.md) for what's next, and the open issues.

## Get set up

Requires Python 3.10 or newer.

```bash
git clone https://github.com/ddsyasas/mirago
cd mirago
pip install -e ".[dev]"
```

## Run the checks (all should pass before you open a PR)

```bash
ruff check src tests          # lint
mypy                          # type check
pytest -m "not network"       # tests, offline (this is what CI runs by default)
pytest                        # full suite, including a few that hit live PyPI
```

CI runs lint + types + tests on Python 3.10–3.13.

## How the code is organized

mirago separates the "thinking" (the engine) from the "plumbing" (files, network, output) so each
part is small and easy to test:

- **`parser.py`** — reads a Python file's imports, using Python's built-in `ast`.
- **`checker.py`** — the engine: `check_source(...)` decides what's a problem. It works on a *string*,
  so it doesn't need a file on disk (handy for editors and the future guardrail).
- **`registry.py`** — the seam to a package index: `Registry` (an interface) and `PyPIRegistry`.
  Tests use a `FakeRegistry`, which is why the suite runs without the network. A future npm registry
  plugs in here.
- **`risk.py`** — the risk scorer: turns age + downloads + lockfile membership into
  error / warning / fine.
- **`lockfile.py`** — finds and reads your project's dependency list (the "this is trusted" signal).
- **`suggest.py`** — "did you mean" suggestions from a bundled list of popular packages.
- **`discovery.py`** — finds the `.py` files to check when you point mirago at a folder.
- **`cli.py`** — the command-line interface (formatting, options, exit codes).

## Conventions

- **Fail open.** When we can't be sure (a network error, missing data), treat it as fine — never
  raise a false alarm. A tool that cries wolf gets uninstalled.
- **Tests run offline.** Anything that needs the network goes behind the `network` marker so it's
  skipped by default.
- **Keep it lint-clean and type-clean.** A tool that catches type mistakes should be type-clean
  itself.
- **Plain language in docs.** `README.md` and `docs/` are for everyone — keep them simple.
- **Small, focused PRs** with a clear description and green tests are easiest to review.

## Picking something up

Start from [ROADMAP.md](./ROADMAP.md) or the issues. If you're planning something larger, open an
issue first so we can agree on the approach before you write a lot of code.
