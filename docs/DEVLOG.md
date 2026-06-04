# Mirago Developer Log

A running, plain-language record of what changed in mirago and *why*. Git history tells you
*what* changed; this log explains the thinking behind it, so a new contributor can catch up fast.

This is an open-source project. **Contributors are welcome to add entries.** If you make a
meaningful change — a feature, a design decision, a reversal, a tricky bug — add a short note.

## How to add an entry

- Newest entries go **at the top**.
- Heading: `## YYYY-MM-DD — Short title`, then `**Author:** @your-github-handle`.
- Write in plain words. Explain the decision and the reason. Link the PR/issue.
- Honesty helps: "we tried X, it didn't work, here's why" is a great entry.

---

## 2026-06-04 — mirago has a home: mirago.dev

**Author:** @ddsyasas

We registered **mirago.dev** and built a small landing page that explains, in plain words, what
mirago does and why packages an AI invents are a problem worth catching. It's a simple marketing
site — the tool itself stays the focus, and the command line is still where all the work happens.

The site is built and going live at [mirago.dev](https://mirago.dev) shortly. Its source lives in
its own separate project, kept out of this open-source repo so this one stays purely the tool.

## 2026-05-29 — Released: 0.1.0 (first public beta)

**Author:** @ddsyasas

mirago is now installable by anyone:

```bash
pipx install mirago    # or: pip install mirago
```

This is the first public release — version **0.1.0**, marked beta (it works and it's useful, but
it's early). It bundles everything built so far: the existence check, the smarter risk detection,
typo suggestions with `--fix`, `--json` output, and whole-folder checking. Tagged `v0.1.0` with a
matching GitHub Release and a `CHANGELOG.md`.

Honest scope: there are still **no editor/IDE integrations** and no real-time blocking yet — mirago
is a command-line tool for now. Those are next.


**Author:** @ddsyasas

You can now point mirago at a folder instead of naming files one by one:

```bash
mirago check .       # this folder and everything under it
mirago check src/
```

It looks through every `.py` file in the folder and its subfolders. It skips folders that would
be noise or slow to scan — virtual environments (`.venv`, `venv`), caches, `.git`, `build`,
`node_modules`, and similar — so it won't waste time digging through your installed libraries.

Output got tidier for big runs: clean files no longer print a line each. Files *with* problems
still show their details, and there's a single summary at the end (for example, "✓ Checked 87
files, no problems found."). The output for problems is unchanged.

## 2026-05-28 — Shipped: smarter detection (v0.2)

**Author:** @ddsyasas

Merged in PR #2. v0.1 could only tell you whether a package *exists* on PyPI. The gap:
someone can register a fake-sounding name, so it *does* exist and slips past a plain existence
check.

v0.2 adds a second layer. For a package that exists, it looks at a few clues and warns you only
when they line up suspiciously:

- how new the package is (just created?),
- how often it's downloaded (almost never?),
- whether your project already uses it (is it in your requirements / lockfile?).

It warns only when several clues agree, and stays quiet when it isn't sure — so it doesn't cry
wolf. Warnings don't fail your build by default. It also suggests the right name when you mistype
a well-known package (`requets` → `requests`), adds a `--fix` option to apply that suggestion,
and a `--json` option so other tools can read the results.

## 2026-05-28 — Experiment: mirago can stop an AI from writing a fake import, live

**Author:** @ddsyasas

We tested an idea: can mirago sit beside an AI coding assistant and stop it from writing an
import for a package that doesn't exist — *as it tries to write the file*, not after?

It worked. Using a small throwaway script (a "hook" — code that runs automatically just before
the assistant writes a file), we asked an AI assistant to create a file containing a made-up
package. mirago caught it and blocked the write: the file was never created, and the assistant
was told why (it even suggested a real package instead). A normal file with real imports went
through untouched.

This was a quick experiment to prove the idea works, not a finished feature — the throwaway code
lives outside the published tool.

## 2026-05-28 — Internal cleanup (no change to how the tool behaves)

**Author:** @ddsyasas

Reorganized the code so the core logic is separated from the parts that touch the outside world
(reading files, calling PyPI, printing results). Nothing about how the tool behaves changed — the
output is exactly the same as before — but the cleaner shape makes the next features much easier
to add. PR #1. Also switched on a type checker and ran the tests on more Python versions.

## 2026-05-28 — Being honest about what v0.1 catches

**Author:** @ddsyasas

Clarified the tool's promise so it isn't oversold. v0.1 catches package names that **don't
exist** — the kind an AI assistant simply made up. It does **not**, by itself, catch the case
where someone has actually registered a fake-sounding name; that's what the smarter detection in
v0.2 is for. The README now says this plainly.

## 2026-05-28 — v0.1: the first working version

**Author:** @ddsyasas

The starting point. `mirago check file.py` reads a Python file, finds every import, and asks PyPI
whether each package is real. If one isn't, it tells you and exits with an error code (handy for
automation). A deliberate safety choice: if PyPI can't be reached, mirago assumes the package is
fine rather than raising a false alarm — a tool that cries wolf gets uninstalled. Built with a
small test suite and automated checks from day one.
