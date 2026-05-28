# mirago

> A pre-install gate for AI-generated imports.

**The linter for AI-generated imports.** When Copilot, Cursor, Claude Code, or any other AI assistant invents a package name that doesn't exist on PyPI, mirago flags it before you waste time trying to install a name your AI made up.

## The problem

AI coding tools hallucinate package names. Research at USENIX Security 2025 found AI models invent non-existent packages 5-22% of the time. When attackers register those hallucinated names on PyPI or npm with malicious payloads, the result is a supply chain attack called **slopsquatting**.

That background is *why* hallucinated imports are worth catching. To be precise about what v0.1 actually does: mirago checks whether each imported package exists on PyPI and flags the ones that don't — a **pre-install gate** that stops you wasting time on a name your AI invented.

It does **not**, on its own, stop a slopsquatting attack. Once an attacker has registered the fake name, the package *does* exist, so an existence check stays silent. Closing that gap is the job of the v0.2 metadata tier — see the [Roadmap](#roadmap).

## Status

🚧 **v0.1 in active development.** Star to follow the launch.

## Install (when v0.1 ships)

```bash
pipx install mirago
```

## Usage

```bash
mirago check your_file.py
mirago check src/**/*.py
```

Example output:

```
🚨 2 hallucinations in src/main.py

  Line 4:  import fastjson_validator
    → Package 'fastjson_validator' does not exist on PyPI

  Line 12: from json_super_fast_2026 import parse
    → Package 'json_super_fast_2026' does not exist on PyPI
```

Exit code is `1` when issues are found, perfect for CI.

## What v0.1 catches and does not catch

**Catches:** AI-invented package names that do not exist on PyPI.

- Both `import x` and `from x import y` forms
- Submodule imports (`import x.y.z` checks `x`)

**Does NOT catch yet:** a hallucinated name that an attacker has *already registered* on PyPI — the live slopsquatting case. Because the package exists, an existence check can't see it. This is planned for v0.2 via package age and download-count metadata.

## How mirago relates to existing tools

Supply-chain scanners already exist: [pip-audit](https://github.com/pypa/pip-audit), [OSV-Scanner](https://github.com/google/osv-scanner), [Socket.dev](https://socket.dev), and [Snyk](https://snyk.io). They are mature and well-funded.

Be clear-eyed about it: the existence check is commoditizable — any of those tools could ship it in a single sprint. mirago's durable differentiation is not the check, it's the **position**: living *inside the AI agent workflow*. An MCP server that an agent (Claude Code, Cursor, Codex) consults *before* it writes an import is something the supply-chain incumbents are not structured to do. That is the bet — see v0.3 in the [Roadmap](#roadmap).

## Roadmap

- **v0.2 — Metadata tier (the real slopsquatting defense):** flag packages that *exist* but look suspicious — recently created, very low download count, or not already in your lockfile. Paired with "did you mean" suggestions (Levenshtein against real PyPI names) and a `--fix` flag.
- **v0.3 — MCP server spike (the strategic differentiator):** a throwaway spike proving the end-to-end loop — an AI agent tries to write a hallucinated import, and mirago blocks it before it lands. This is the position the whole project is betting on.
- **v0.4:** Directory recursion, git-diff mode, pre-commit hook, and GitHub Action integrations.
- **v0.5:** npm / JavaScript support.
- **v0.6+ — Symbol & signature verification (Dimensions 2-3, Hard / Very Hard):** e.g. `from requests import nonexistent_func`, or calls with wrong arguments. The plan is to *wrap pyright* rather than rebuild a type checker — focusing only on the AI-context cases existing checkers miss, not reimplementing static analysis.
- **v1.0:** VS Code extension.

## Development

```bash
git clone https://github.com/ddsyasas/mirago
cd mirago

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run the test suite (skips network tests by default in CI)
pytest

# Try it on the bundled fixtures
mirago check tests/fixtures/good.py
mirago check tests/fixtures/bad.py
```

## License

MIT. See [LICENSE](./LICENSE).
