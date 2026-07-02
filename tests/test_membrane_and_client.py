"""Idk-commons gate tests: lint hardening (C5-C9,H8,H11), the client (H12-H18),
and the client<->spec sync (H19)."""
import hashlib
import json
from pathlib import Path

import membrane_lint as ml
import trail_commons as tc

REPO = Path(ml.__file__).resolve().parents[2]
SPEC = json.loads((REPO / "membrane-spec.json").read_text(encoding="utf-8"))
PINNED_SPEC_SHA = "10637382597e85eac82d30848a4582cee16cc6094b3a316f04f17f5b28d2e35b"


def _lint_labels(text, rel="questions/xx/yy/f.md"):
    return " | ".join(ml.check(text, rel))


# ---- H19: the client, the lint, and the spec agree ----
def test_spec_sha_is_pinned_and_matches_questions_repo():
    got = hashlib.sha256((REPO / "membrane-spec.json").read_bytes()).hexdigest()
    assert got == PINNED_SPEC_SHA  # byte-identical to the Questions copy


def test_client_forbidden_list_equals_spec():
    assert [list(t) for t in tc._FORBIDDEN] == SPEC["forbidden"]


def test_codex_hash_agrees_everywhere():
    assert ml.CODEX_HASH == SPEC["codex_hash"] == tc.CODEX_HASH


# ---- lint hardening (same guarantees as the Questions gate) ----
def test_lint_catches_math_bold_alpha():
    assert "alpha" in _lint_labels("# Q\n\n\U0001D6FC\n")


def test_lint_catches_zero_width_and_author():
    assert "zero-width" in _lint_labels("# Q\u200b\n\n## ∞0' — R\n\nWho?\n")
    assert "author attribution" in _lint_labels("# Q\n\nAuthor: X\n")


def test_lint_rejects_non_md(tmp_path):
    j = tmp_path / "x.json"; j.write_text("{}", encoding="utf-8")
    assert ml.main([str(j)]) == 1


# ---- H11: an ancestor dir named "questions" must not break the shard check ----
def test_ancestor_dir_named_questions_does_not_break_shard():
    heading_text = "Does the shard survive an ancestor of the same name?"
    want = ml.content_hash(heading_text)
    body = (f"---\nspdx: CC0-1.0\ncontent_hash: sha256:{want}\n---\n\n"
            f"# {heading_text}\n\n*CC0*\n\n## ∞0' — R\n\nWho?\n")
    relname = f"/home/user/questions/questions/{want[:2]}/{want[2:4]}/{want}.md"
    assert ml.check(body, relname) == []


# ---- client gate (H14 + folding) is as strong as the lint ----
def test_client_membrane_check_folds_confusables():
    # math-bold alpha must be caught by the CLIENT too, not just CI
    assert any("alpha" in p for p in tc.membrane_check("# Q\n\n\U0001D6FC\n"))


def test_client_membrane_check_requires_real_heading():
    # H14: a '# ' appearing mid-line is not a level-1 heading
    problems = tc.membrane_check("no heading here # not a title\n\n## ∞0' — R\n\nWho?\n")
    assert any("no question heading" in p for p in problems)


# ---- CLI robustness (M12) ----
def test_help_returns_zero():
    assert tc.main(["trail_commons.py", "--help"]) == 0


def test_bad_cycle_is_a_clean_error_not_a_crash():
    assert tc.main(["trail_commons.py", "publish", "--cycle", "notanint"]) == 1


def test_selftest_passes():
    assert tc.main(["trail_commons.py", "selftest"]) == 0
