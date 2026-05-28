# Mirago Developer Log

A running, record of what changed in mirago and *why* — the reasoning behind
decisions, not just the diff. Git history tells you *what*; this log tells you *why we chose it*.

This is an open-source project. **Contributors are welcome to add entries.** If you land a
meaningful change — a feature, a design decision, a reversal, a tricky bug — add a short note here
so the next person inherits the context instead of reverse-engineering it.

## How to add an entry

- Newest entries go **at the top** (reverse chronological).
- Use the heading format: `## YYYY-MM-DD — Short title` followed by `**Author:** @your-github-handle`.
- Write prose, not a changelog bullet. Explain the *decision and the reasoning*. Link the PR/issue.
- Keep it honest. "We tried X, it didn't work, here's why" is the most valuable kind of entry.
- This is not the changelog. User-facing release notes live elsewhere; this is for builders.

---

## 2026-05-28 — Phase 0: hexagonal refactor (engine / Registry / verdict model / --json)

**Author:** @ddsyasas

Refactored the internals so the *engine* (pure logic) is separate from the *adapters* (disk,
network, CLI). No user-facing change — default CLI output is byte-identical to before — but the
shape is now ready for everything that comes next (an MCP guardrail, a web playground, CI). PR #1.
The guiding rule was "a seam, not a framework": minimal abstractions that unblock what's coming,
nothing speculative.

Four moves:

- **Pure engine.** `check_source(source, filename)` does the work on a *string*. `extract_imports`
  and `check_file` are now thin wrappers that read from disk and delegate. This matters because the
  next consumers (an editor, an agent hook) need to check code that isn't a file on disk yet.
- **Registry seam.** A `Registry` Protocol with one method, `exists(name) -> bool`. `PyPIRegistry`
  implements it today; a `FakeRegistry` lets the whole test suite run offline; a future npm registry
  drops in without touching the engine. The Python stdlib short-circuit lives in `PyPIRegistry`, not
  the engine, because it's Python-specific.
- **Forward-compatible verdict model.** `Issue` now carries `severity` (default `"error"`) and
  `signals` (default `{}`). They're unused today, but they mean a later risk-grading pass can mark
  something as a *warning* with supporting evidence instead of being limited to a yes/no verdict —
  no model rework required.
- **`--json` output.** `mirago check --json` emits structured results. Anything that consumes mirago
  programmatically (CI, an editor, a hook) should parse JSON, not scrape the formatted text.

Also added: mypy in CI (the source is type-clean — a tool that catches type hallucinations should be
type-clean itself) and Python 3.13 in the test matrix.

## 2026-05-28 — Planned: v0.3 agent-guardrail spike

**Author:** @ddsyasas

Next up is a throwaway spike to validate the project's core strategic bet: that mirago can run
*inside an AI coding agent's write loop* and block a hallucinated import **before** it's written to
disk — not just flag it after the fact like a normal linter.

Two mechanisms will be prototyped:

1. **A Claude Code `PreToolUse` hook (primary).** The harness runs it deterministically before any
   `Write`/`Edit`, so the model can't skip it. It extracts the source about to be written, runs
   mirago's existing checker, and refuses the write (telling the agent which package doesn't exist)
   if a hallucinated import is present. This proves *enforcement*.
2. **An MCP `check_imports(source)` tool (secondary).** A portable tool any agent (Cursor, Codex)
   can call. Weaker guarantee — it relies on the agent choosing to call it — but it's the
   cross-agent story. This proves *portability*.

The one real design wrinkle: every v0.1 entry point reads from a **file path on disk**, but a
guardrail must check a **string the agent hasn't written yet**. The spike bridges this with a small
`check_source(str)` adapter (tempfile today; a first-class core function later). If the spike
confirms the hook can block a write, `check_source` graduates into the core API in a future release.

Success is binary and will be captured in a short screen recording: a fake import gets blocked, a
file of real imports passes untouched. If the hook *can't* block, the "in the workflow" positioning
needs rethinking — which is exactly why we're spiking it cheaply before building on top of it.

## 2026-05-28 — Honest framing: the existence check is a pre-install gate, not slopsquatting armor

**Author:** @ddsyasas

Corrected an overclaim in the project's framing before launch. v0.1 checks whether each imported
package **exists** on PyPI. That catches the *harmless* half of the problem — names the AI invented
that nobody registered (wasted time, broken installs).

It does **not**, on its own, stop a live slopsquatting attack. Once an attacker has registered the
hallucinated name, the package *does* exist, so an existence check stays silent and the malware
sails through. Pretending otherwise would have been the first thing a technical audience caught.

Decisions that followed:
- Reframed v0.1 publicly as a **pre-install gate**: it saves you from installing a name your AI made
  up. Honest and modest.
- Made the **v0.2 metadata tier** the real slopsquatting defense — flag packages that *exist* but
  look suspicious (recently created, very low download count, not already in your lockfile). This is
  where the genuine security value lives, and the hard part is trust (false positives erode it fast).
- Pulled the **agent-guardrail spike forward** in the roadmap, because *position* (being in the
  agent's write loop) is the real differentiator, not the existence check — which any supply-chain
  scanner (pip-audit, OSV-Scanner, Socket.dev, Snyk) could ship in a sprint.
- Re-rated symbol/signature verification as **Hard / Very Hard**, with a plan to *wrap pyright*
  rather than rebuild a type checker — only surfacing the AI-context cases existing tools miss.

## 2026-05-28 — v0.1 scaffolding

**Author:** @ddsyasas

Initial cut of the tool. `mirago check file.py` parses a Python file, finds every import, and asks
PyPI whether each top-level package is real.

Architecture (intentionally small — four modules):
- `parser.py` — an `ast.NodeVisitor` that extracts imports. Collapses dotted imports to the
  top-level package (`import a.b.c` → checks `a`), skips relative imports, and captures the source
  line + line number for readable reports.
- `pypi.py` — existence check against `https://pypi.org/pypi/<name>/json`. Two deliberate choices:
  (1) **stdlib short-circuit** so standard-library modules never hit the network, and (2)
  **fail-open** — a network error or timeout returns "exists" so we never flag a user's real code as
  hallucinated just because PyPI was unreachable. Results cache on disk for 7 days.
- `checker.py` — orchestrates the two, memoizing one PyPI lookup per unique package per run.
- `cli.py` — Typer + rich. Exit code `1` when issues are found (CI-friendly), `2` on a missing file.

11 tests (network tests marked and skipped in CI by default), ruff lint, GitHub Actions CI, MIT.

The fail-open stance is the load-bearing design decision here: a linter that cries wolf when the
network blips would get uninstalled on day one. Better to occasionally miss than to be wrong loudly.
