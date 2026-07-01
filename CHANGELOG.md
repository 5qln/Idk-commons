# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Fixed / Hardened
- **Membrane gate** hardened to match the commons gate: NFKD + confusable folding
  (math-alpha, curly-quote B″, ∩-vs-⋂), zero-width rejection, structural
  heading/frontmatter/∞0' checks, non-`.md` rejection, fail-closed on an
  empty/missing commons, and full shard-path verification.
- Client `membrane_check`: level-1 heading is now a structural check (not the
  substring `"# "`), the return heading is matched structurally, and confusable
  folding is applied so the client is as strict as CI.
- `_git()` honoured `check=` (it previously always passed `check=False`).
- Trail heading extraction stripped a character-set (`lstrip("# ")`) instead of
  the `# ` prefix — corrupted headings starting with the letters h/#/space.
- Ingest ref is now collision-proof (`uuid4`), and ingest distinguishes
  `merged` / `no_op` / `rejected` instead of reporting no-ops as accepted.
- PII URL heuristic is hostname-scoped (a path containing `5qln` no longer
  whitelists an unrelated host).
- Config parse failures now warn on stderr instead of failing silently.

### Changed
- Forbidden markers + Codex hash extracted to `membrane-spec.json` (shared with
  `Questions`), with a pinned-SHA sync test asserting the client copy matches.
- Commit branch is configurable (`branch:` in config; defaults to `main`).
- CLI supports `--help` and `--flag=value`; a non-integer `--cycle` is a clean
  error instead of a traceback.

### Fixed (repo structure)
- CI workflow moved from repo root to `.github/workflows/membrane.yml` and points
  at `skills/trail-commons/membrane_lint.py`.
- Seed questions moved into the sharded `questions/<xx>/<yy>/` layout.
- Repo URLs corrected to `github.com/5qln/Idk-commons`; doc paths corrected.
- `setup.sh`: colours guarded behind a TTY check; selftest output uses `mktemp`.

### Added
- Test suite (`tests/`), SHA-pinned multi-version CI, and standard community files.

### Deferred
- Full package split of `trail_commons.py` into a multi-module package (M11): the
  file installs standalone, so a split must move `setup.sh`/skill paths in
  lockstep and be tested end-to-end. The underlying concern (rule duplication) is
  resolved via the shared spec + sync test; the file is now covered by tests.
