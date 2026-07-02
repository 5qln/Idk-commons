#!/usr/bin/env python3
"""
membrane_lint.py — the commons-side privacy gate (third of three).

Runs in CI on every changed question so NOTHING private can land in the public
commons even if a file was crafted by hand, submitted through a fork, or pushed
directly by someone with write access. It trusts no client.

The rules (the forbidden markers, the Codex hash, the SPDX id) are loaded from
membrane-spec.json — the single source of truth shared byte-for-byte with the
publishing client, so the gates cannot silently disagree.

Usage:
    membrane_lint.py [FILE ...]      # check the named files
    membrane_lint.py                 # check every file under questions/

Exit 0 if all clean; exit 1 (with a report) if any file would leak, if a
non-question file appears under questions/, or if there is nothing to check.

      Form only. Never life.
"""

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO / "membrane-spec.json"

# Zero-width / BOM code points, stripped before hashing and forbidden outright.
_ZERO_WIDTH = "\u200b\u200c\u200d\u2060\ufeff"
# Confusable folding: curly quotes/prime -> ASCII apostrophe; intersection
# look-alike -> the sealed one. Applied on top of NFKD compatibility folding.
_CONFUSABLES = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u2032": "'",   # ' ' ′  -> '
    "\u201c": '"', "\u201d": '"',                   # " "    -> "
    "\u2229": "\u22c2",                              # ∩ -> ⋂
})


def _load_spec():
    try:
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"membrane_lint: cannot load {SPEC_PATH.name}: {e}\n")
        raise SystemExit(2)
    codex = spec["codex_hash"]
    spdx = spec["spdx"]
    forbidden = [(re.compile(pat, re.M), label) for pat, label in spec["forbidden"]]
    # The Codex seal itself is a private surface — derive it from the spec.
    forbidden.append((re.compile(re.escape(codex)),
                      "the Codex seal hash (a private surface leaked)"))
    return codex, spdx, forbidden


CODEX_HASH, SPDX, FORBIDDEN = _load_spec()


def _fold(text: str) -> str:
    """Compatibility-fold + normalize confusables so a homoglyph cannot mask a
    private marker (mathematical alpha, fullwidth letters, curly quotes, ∩)."""
    return unicodedata.normalize("NFKD", text).translate(_CONFUSABLES)


def normalize_heading(text: str) -> str:
    """Normalize an H1 for hashing: NFC, drop zero-width, collapse whitespace."""
    t = unicodedata.normalize("NFC", text)
    t = t.translate({ord(c): None for c in _ZERO_WIDTH})
    return re.sub(r"\s+", " ", t.strip())


def content_hash(x: str) -> str:
    return hashlib.sha256(normalize_heading(x).encode("utf-8")).hexdigest()


def heading_of(text: str):
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1) if m else None


def _frontmatter(text: str) -> str:
    """Return the YAML frontmatter block, or '' if there isn't a proper one."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    return m.group(1) if m else ""


def check(text: str, relname: str):
    """Return a list of problems for one question file. Empty list = clean."""
    problems = []
    folded = _fold(text)
    for pat, label in FORBIDDEN:
        if pat.search(folded) or pat.search(text):
            problems.append(f"private content present: {label}")

    # Positive form: a public question is two questions plus its CC0 dedication.
    if not re.search(r"^# ", text, re.M):
        problems.append("no level-1 question heading (#) — there is no X")

    fm = _frontmatter(text)
    if not re.search(r"^spdx:\s*" + re.escape(SPDX) + r"\s*$", fm, re.M):
        problems.append(f"missing SPDX dedication in frontmatter: {SPDX}")

    hashm = re.search(r"^content_hash:\s*sha256:([0-9a-f]{64})\s*$", fm, re.M)
    if not hashm:
        problems.append("missing/invalid content_hash in frontmatter")

    if not re.search(r"^##\s+∞0'\s*[—-]", text, re.M):
        problems.append("missing '## ∞0' —' return-question heading")

    head = heading_of(text)
    if head and hashm:
        want = content_hash(head)
        if want != hashm.group(1):
            problems.append(
                f"hash mismatch: heading hashes to {want[:16]}…, "
                f"frontmatter says {hashm.group(1)[:16]}…")
        # Filename + shard integrity: questions/<w[:2]>/<w[2:4]>/<w>.md
        parts = Path(relname).parts
        if "questions" in parts:
            # Anchor to the LAST "questions" segment. A checkout directory (or any
            # ancestor) literally named "questions" must not be mistaken for the
            # commons questions/ subdir — the shard tail is always the final three
            # segments (<xx>/<yy>/<hash>.md), so the last occurrence is the gate.
            i = len(parts) - 1 - parts[::-1].index("questions")
            tail = parts[i + 1:]
            if len(tail) != 3:
                problems.append(
                    "wrong shard depth (expected questions/<xx>/<yy>/<hash>.md)")
            else:
                s1, s2, fname = tail
                if s1 != want[:2] or s2 != want[2:4]:
                    problems.append(
                        f"shard path does not match content hash "
                        f"(expected {want[:2]}/{want[2:4]}/)")
                if Path(fname).stem != want:
                    problems.append(
                        f"filename does not match content hash "
                        f"(expected {want[:16]}….md)")
        else:
            if Path(relname).stem != want:
                problems.append(
                    f"filename does not match content hash "
                    f"(expected {want[:16]}….md)")
    return problems


def iter_all_files():
    root = REPO / "questions"
    if not root.is_dir():
        return None  # signal: no commons directory at all
    return sorted(p for p in root.rglob("*") if p.is_file())


def main(argv):
    if argv:
        # A directory argument means "everything under it" — same treatment
        # the no-argument scan gives questions/ (non-.md files still rejected).
        targets = []
        for a in argv:
            p = Path(a)
            if p.is_dir():
                targets.extend(sorted(q for q in p.rglob("*") if q.is_file()))
            else:
                targets.append(p)
        if not targets:
            print("✗ membrane gate: the named director(y/ies) contain no files.")
            return 1
    else:
        found = iter_all_files()
        if found is None:
            print("✗ membrane gate: no questions/ directory — nothing to verify.")
            return 1
        targets = found
        if not targets:
            print("✗ membrane gate: questions/ is empty. Refusing to pass an "
                  "empty commons (guards against silent deletion).")
            return 1

    # C7: only .md question files may live under questions/. A non-.md file is
    # never scanned by the positive checks, so it is a leak vector — reject it.
    non_md = [str(p) for p in targets if p.suffix != ".md"]
    if non_md:
        print("✗ membrane gate: non-question files under questions/:")
        for p in non_md:
            print(f"     - {p}")
        return 1

    failed = {}
    for p in targets:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:  # unreadable file is itself a failure
            failed[str(p)] = [f"could not read: {e}"]
            continue
        problems = check(text, str(p))
        if problems:
            failed[str(p)] = problems

    if failed:
        print("✗ membrane gate: private content would enter the commons.\n")
        for fname, probs in failed.items():
            print(f"  {fname}")
            for pr in probs:
                print(f"     - {pr}")
        print("\nThese files were NOT clean. Only X and ∞0' may cross the "
              "membrane. Nothing from α / Z / ∇ / B'' may appear.")
        return 1
    print(f"✓ membrane gate: {len(targets)} question(s) clean. "
          "Only X and ∞0' present.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
