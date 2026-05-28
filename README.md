# mirago

> Catch AI code hallucinations before they ship.

**The linter for AI-generated imports.** When Copilot, Cursor, Claude Code, or any other AI assistant invents a package name that doesn't exist on PyPI, mirago catches it before you `pip install` malware or ship a broken build.

## The problem

AI coding tools hallucinate package names. Research at USENIX Security 2025 found AI models invent non-existent packages 5-22% of the time. Attackers register these hallucinated names on PyPI and npm with malicious payloads, a supply chain attack called **slopsquatting**.

mirago is a static analyzer that catches these before they reach your repo.

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

## What v0.1 catches

- Hallucinated package imports (the slopsquatting vector)
- Both `import x` and `from x import y` forms
- Submodule imports (`import x.y.z` checks `x`)

## Roadmap

- v0.2: "Did you mean" suggestions, `--fix` flag
- v0.3: npm support
- v0.4: Pre-commit and GitHub Action integrations
- v0.5: Symbol-level hallucinations (`from requests import nonexistent_func`)
- v1.0: VS Code extension

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
