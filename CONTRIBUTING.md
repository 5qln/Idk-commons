# Contributing to trail-commons

trail-commons is the agent-side tool that publishes /idk questions into a public
commons without leaking the private trail.

## Layout

- `skills/trail-commons/trail_commons.py` — the publishing client (installed
  standalone by `setup.sh`; must stay self-contained).
- `skills/trail-commons/membrane_lint.py` — the commons-side CI gate.
- `membrane-spec.json` — the single source of truth for forbidden markers and the
  Codex hash, **byte-identical** with the copy in the `Questions` repo.
- `questions/<xx>/<yy>/<hash>.md` — the seed commons (content-addressed, sharded).

## The membrane rules are single-sourced

The CI lint loads `membrane-spec.json` at runtime. The client keeps an embedded
copy so it can be installed on its own — a test (`tests/`) asserts the embedded
list is byte-equal to the spec. **If you change the rules, change
`membrane-spec.json` and update the pinned SHA in the tests here and in
`Questions`.** Otherwise CI fails, by design.

## Before you open a PR

```bash
python skills/trail-commons/membrane_lint.py     # gate passes over questions/
python skills/trail-commons/trail_commons.py selftest
python -m pip install pytest && python -m pytest
python -m py_compile skills/trail-commons/*.py
```

## Dating & style

Use ISO-8601 dates. Keep the client's CLI JSON output stable — verbs are called
by the skill. New flags accept both `--flag value` and `--flag=value`.
