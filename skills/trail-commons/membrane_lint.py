#!/usr/bin/env python3
"""
membrane_lint.py — the commons-side privacy gate.

This is the third and final check on the membrane (the others run in the
publishing client and in the steward's ingest). It runs in CI on every changed
question file, so that NOTHING private can land in the public commons even if a
file was crafted by hand, submitted through a fork, or pushed directly by
someone with write access. It trusts no client.

It is intentionally self-contained — stdlib only, no import of the publishing
tool — because it must run in the commons repo, which carries only questions.
The rules here are kept byte-for-byte identical to the client's membrane_check
so the three gates never disagree.

Usage:
    membrane_lint.py [FILE ...]      # check the named files
    membrane_lint.py                 # check every questions/**/*.md

Exit 0 if all clean; exit 1 (with a report) if any file would leak.

      Form only. Never life.
"""

import hashlib
import re
import sys
import unicodedata
from pathlib import Path

SPDX = "CC0-1.0"
CODEX_HASH = "feaa46b4147d4e023cdd3fd59c051d063e8ec654ee7b38a481dcd5e4c781859b"

# Private phase markers. Presence of any one means a private surface leaked.
FORBIDDEN = [
    (r"α", "alpha (α) — the private seed"),
    (r"\{α'\}", "echoes {α'}"),
    (r"\bALPHA:", "ALPHA: footer field"),
    (r"\bSEEKS:", "SEEKS: footer field"),
    (r"\bPHI:", "PHI: footer field"),
    (r"\bOMEGA:", "OMEGA: footer field"),
    (r"\bALIGNMENT:", "ALIGNMENT: footer field"),
    (r"\bEXTENT:", "EXTENT: footer field"),
    (r"^\s*Z:", "Z: (the click) footer field"),
    (r"\bVALUE_MAX:", "VALUE_MAX: footer field"),
    (r"\bENERGY:", "ENERGY: footer field"),
    (r"\bB2:", "B2: (artifact) footer field"),
    (r"\bLIVENESS:", "LIVENESS: footer field"),
    (r"^\s*L:\s", "L: (what crystallized) footer field"),
    (r"φ\s*⋂\s*Ω", "Q-phase formula φ ⋂ Ω"),
    (r"δE", "P-phase energy term δE"),
    (r"δV", "P-phase value term δV"),
    (r"∇", "gradient ∇ — the private direction"),
    (r"B''", "B'' — the private artifact"),
    (r"##\s*α", "α section heading"),
    (r"##\s*Z\b", "Z section heading"),
    (r"##\s*∇", "∇ section heading"),
    (r"##\s*Raw Material", "raw-material section (the φ corpus)"),
    (r"##\s*The Field Condition", "field-condition section"),
    (re.escape(CODEX_HASH), "the Codex seal hash (a private surface leaked)"),
    (r'"(?:opened|pending|gate_violations)"', "gate-machine JSON"),
    (r"^cycle:\s*\d", "cycle number in frontmatter (deanonymization vector)"),
    (r"#\s*Cycle\s+\d", "Cycle-N heading (deanonymization vector)"),
]


def normalize_question(text: str) -> str:
    t = unicodedata.normalize("NFC", text)
    t = t.strip()
    return re.sub(r"\s+", " ", t)


def content_hash(x: str) -> str:
    return hashlib.sha256(normalize_question(x).encode("utf-8")).hexdigest()


def heading_of(text: str):
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1) if m else None


def check(text: str, relname: str):
    """Return a list of problems for one question file. Empty list = clean."""
    problems = []
    for pat, label in FORBIDDEN:
        if re.search(pat, text, re.M):
            problems.append(f"private content present: {label}")
    # Positive form: a public question is two questions plus its dedication.
    if "# " not in text:
        problems.append("no question heading (#) — there is no X")
    if f"spdx: {SPDX}" not in text:
        problems.append(f"missing SPDX dedication: {SPDX}")
    head = heading_of(text)
    fm = re.search(r"content_hash:\s*sha256:([0-9a-f]{64})", text)
    if not fm:
        problems.append("missing content_hash")
    if "∞0'" not in text:
        problems.append("missing ∞0' — a published question must open a return question")
    # Hash integrity: the frontmatter hash must equal the hash of the heading.
    if head and fm:
        want = content_hash(head)
        if want != fm.group(1):
            problems.append(
                f"hash mismatch: heading hashes to {want[:16]}…, "
                f"frontmatter says {fm.group(1)[:16]}…")
        # Filename integrity: the file must be named for its own content hash,
        # so no question can be smuggled in under another's address.
        stem = Path(relname).stem
        if stem != want:
            problems.append(
                f"filename does not match content hash (expected {want[:16]}….md)")
    return problems


def iter_targets(argv):
    if argv:
        for a in argv:
            yield Path(a)
    else:
        root = Path("questions")
        if root.is_dir():
            yield from sorted(root.rglob("*.md"))


def main(argv):
    targets = [p for p in iter_targets(argv) if p.suffix == ".md"]
    if not targets:
        print("membrane_lint: no question files to check.")
        return 0
    failed = {}
    for p in targets:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:  # unreadable file is itself a failure
            failed[str(p)] = [f"could not read: {e}"]
            continue
        problems = check(text, p.name)
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
