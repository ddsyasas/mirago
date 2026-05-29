# Mirago Roadmap

Where mirago is, where it's going, and why — in plain language. Priorities can shift; if you want
to work on something or suggest a direction, open an issue.

## The goal

AI coding tools confidently make things up. mirago's job is to **catch what the AI invented before
it causes problems** — starting with fake package names, and growing to the other things AI gets
wrong. The aim is for mirago to become a normal part of the toolchain (like a linter), available
wherever code gets written: your terminal, your CI, your editor, and eventually inside the AI
assistants themselves.

## The five levels of checking (the long-term shape)

Each level is deeper and more valuable than the one before:

1. **Does the package exist?** — e.g. `import fastjson_validator` when there's no such package.
   *(Shipped in 0.1.0.)*
2. **Does the imported name exist in the package?** — e.g. `from requests import get_json` when
   `requests` has no `get_json`.
3. **Does the function call match the real function?** — e.g. an argument that doesn't exist.
4. **Does the code do what its comment claims?** — e.g. a "sort descending" that sorts ascending.
5. *(We deliberately skip team-style/convention checks — other tools already cover that.)*

0.1.0 nails level 1 and adds a risk check for real-but-suspicious packages. The plan is to grow into
levels 2 → 3 → 4 over time.

## Where we are: 0.1.0 (beta, shipped)

- Checks a single file or a whole folder (`mirago check .`).
- Flags packages that don't exist on PyPI (level 1).
- Warns about real-but-risky packages (brand-new **and** barely downloaded **and** not already in
  your project's lockfile).
- Suggests fixes for typos of popular packages; `--fix` applies them.
- `--json` output and a CI-friendly exit code.
- Command-line only (no editor integration yet).

## What's next (roughly in priority order)

1. **Run automatically** — a pre-commit hook and a GitHub Action, so mirago runs on every commit and
   pull request without anyone remembering to. (High value now that it's installable.)
2. **Only check what changed** — a git-diff mode and glob patterns, so it stays fast on big repos.
3. **Config file** — `.mirago.toml` to tune the risk thresholds and add allowlists for internal /
   private packages.
4. **Deeper detection (level 2)** — catch fake function and method names inside real packages. The
   plan is to lean on an existing type-checker (pyright) rather than rebuild one.
5. **Editor integrations** — VS Code, plus a language server so other editors work too, for
   real-time underlines as you type.
6. **Catch mistakes as the AI writes them** — we've prototyped a guardrail that blocks an AI
   assistant from writing a fake import in real time (see [docs/DEVLOG.md](./docs/DEVLOG.md)).
   Turning that prototype into a real feature is a later step.
7. **Other languages** — JavaScript / npm support, reusing the same core engine.

## How the pieces fit

For how the code is organized and how to pick something up, see [CONTRIBUTING.md](./CONTRIBUTING.md).
