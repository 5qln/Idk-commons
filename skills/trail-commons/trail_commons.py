#!/usr/bin/env python3
"""
trail_commons.py — the transport layer for the /idk Question Commons.

WHAT THIS IS
  Three verbs that move *questions* — never trails — between agents over the
  one network that is already installed everywhere: git.

    publish   strip the private phases, content-address, sign with an
              ephemeral identity, stage the question. Nothing leaves the
              machine until the human at the membrane has seen the exact
              bytes and confirmed.
    discover  git pull the commons, list what is new since last time.
    browse    print one question by its content hash (or a short prefix).

WHAT THIS IS NOT
  It is NOT the cycle. The gate machine (xyzab_state.py) runs the cycle and
  decides what is alive. This module only carries the public residue — X and
  ∞0' — across to other people. It judges *form* (did anything private leak?),
  never *life* (was the question genuine?). That attestation is the human's,
  the same membrane the whole system is built to respect.

      Form only. Never life.

THE MEMBRANE, ENFORCED
  Only two things are public: the question (X) and the next question (∞0').
  Everything from G through V — α, {α'}, Z, ∇, B'' — stays private. This is
  not a convention you are trusted to keep. `membrane_check()` reads the bytes
  that are about to leave and *refuses* the publish if any private marker is
  present. The same check runs in CI on the commons repo, so a malformed or
  hostile file cannot land private content even if this client is bypassed.

PRIVACY POSTURE
  - Ephemeral git identity per publish (user.name "trail-commons"), set with
    `-c` so global config is never touched.
  - Commit timestamps coarsened to date granularity by default — exact times
    are a correlation vector across a person's questions.
  - The public file carries NO cycle number and NO author. Sequential cycle
    numbers link a person's questions to each other; that linkage is exactly
    what ephemeral authorship is meant to break. (This is a deliberate
    divergence from the draft file format — see ARCHITECTURE.md, "cycle number
    is a deanonymization vector.")
  - Stylometry is disclosed, not solved. Short text in your own voice can be
    correlated. The preview says so out loud; the human decides.

stdlib only, Python 3.8+. No accounts, no tokens, no blockchain, no server.
"""

import hashlib
import json
import os
import re
import uuid
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

# The commons repo's identity. The default remote; forkable, replaceable.
DEFAULT_REMOTE = "git@github.com:5qln/questions.git"
SPDX = "CC0-1.0"
EPHEMERAL_NAME = "trail-commons"
EPHEMERAL_EMAIL = "anon@commons.idk"  # non-routable on purpose; not a mailbox

# The Codex seal. It must NEVER appear in a public question — its presence
# would mean a private surface leaked into the commons. Listed here so the
# membrane check can forbid it by value.
CODEX_HASH = "feaa46b4147d4e023cdd3fd59c051d063e8ec654ee7b38a481dcd5e4c781859b"


# ── Config ────────────────────────────────────────────────────────────────

def _coerce(v: str):
    s = v.strip().strip('"').strip("'")
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none", "~", ""):
        return None
    if s.isdigit():
        return int(s)
    return s


def _parse_simple_yaml(path: Path) -> dict:
    """A small YAML reader for exactly the shapes this config uses: top-level
    scalars, a top-level list (`remotes:` then `- item` lines), and one-level
    maps (`privacy:` then indented `key: val`). No PyYAML dependency."""
    result: dict = {}
    cur_key = None      # the top-level key whose block we are inside
    cur_kind = None     # "list" | "map" | None (undecided until first child)
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indented = line[:1] in (" ", "\t")
            stripped = line.strip()
            if not indented:
                if stripped.endswith(":"):
                    cur_key = stripped[:-1].strip()
                    cur_kind = None
                    result[cur_key] = None
                else:
                    k, _, v = stripped.partition(":")
                    result[k.strip()] = _coerce(v)
                    cur_key, cur_kind = None, None
            else:
                if cur_key is None:
                    continue
                if stripped.startswith("- "):
                    if cur_kind is None:
                        cur_kind, result[cur_key] = "list", []
                    result[cur_key].append(_coerce(stripped[2:]))
                elif ":" in stripped:
                    if cur_kind is None:
                        cur_kind, result[cur_key] = "map", {}
                    k, _, v = stripped.partition(":")
                    result[cur_key][k.strip()] = _coerce(v)
    return result


def load_config() -> dict:
    """Read ~/.5qln/trails/config.yaml, defaulting anything missing."""
    home = Path.home()
    defaults = {
        "remotes": [DEFAULT_REMOTE],
        "branch": "main",
        "commons_dir": str(home / ".5qln" / "trails" / "commons"),
        "state_dir": str(home / ".5qln" / "trails"),
        "archive": str(home / ".5qln" / "cycles.jsonl"),
        "privacy_mode": "ephemeral",   # or "pseudonymous"
        "pseudonym": None,
        "commit_time": "date",         # date | exact | epoch
        "include_date": False,         # day-level date in the file (off: privacy)
        "tor": False,
    }
    env = os.environ.get("TRAIL_COMMONS_CONFIG")
    cp = Path(env) if env else (home / ".5qln" / "trails" / "config.yaml")
    if cp.is_file():
        try:
            loaded = _parse_simple_yaml(cp)
            rc = loaded.get("remotes")
            if isinstance(rc, list) and rc:
                defaults["remotes"] = rc
            for k in ("commons_dir", "state_dir", "archive"):
                if k in loaded.get("paths", {}):
                    defaults[k] = os.path.expanduser(
                        os.path.expandvars(str(loaded["paths"][k])))
            priv = loaded.get("privacy", {})
            for k_yaml, k_cfg in (("mode", "privacy_mode"),
                                  ("commit_time", "commit_time"),
                                  ("include_date", "include_date")):
                if k_yaml in priv:
                    defaults[k_cfg] = priv[k_yaml]
            if "pseudonym" in loaded:
                p = loaded["pseudonym"]
                defaults["pseudonym"] = p if p not in ("", []) else None
            if "tor" in loaded:
                defaults["tor"] = loaded["tor"]
            if isinstance(loaded.get("branch"), str) and loaded["branch"].strip():
                defaults["branch"] = loaded["branch"].strip()
        except Exception as exc:
            sys.stderr.write(f"warning: config parse failed, using defaults: {exc}\n")
            # a broken config must not strand a publish; fall back to defaults
    return defaults


def _state_file(cfg: dict) -> Path:
    d = Path(cfg["state_dir"])
    d.mkdir(parents=True, exist_ok=True)
    return d / "state.json"


def _load_state(cfg: dict) -> dict:
    sf = _state_file(cfg)
    if sf.is_file():
        try:
            return json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_seen_commit": None}


def _save_state(cfg: dict, state: dict) -> None:
    _state_file(cfg).write_text(json.dumps(state, indent=2), encoding="utf-8")


# ── Content addressing ──────────────────────────────────────────────────────

def normalize_question(text: str) -> str:
    """Canonical form for hashing: NFC, trimmed, internal whitespace collapsed.
    Two people who surface the same question — however they spaced or wrapped
    it — land on the same hash, and so on the same file. The collision IS the
    point: it means a question is alive in more than one person."""
    t = unicodedata.normalize("NFC", text)
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    text = text.translate({ord(c): None for c in _ZERO_WIDTH})
    return t


def content_hash(x: str) -> str:
    return hashlib.sha256(normalize_question(x).encode("utf-8")).hexdigest()


def fanout_path(commons_dir: Path, h: str) -> Path:
    """questions/<aa>/<bb>/<hash>.md — two levels of fan-out so no directory
    grows unbounded. Git itself shards its object store this way; it scales to
    millions of files and keeps any single directory small."""
    return commons_dir / "questions" / h[:2] / h[2:4] / f"{h}.md"


# ── Extraction (private trail / archive  →  X, ∞0') ─────────────────────────

_HEAD = re.compile(r"^#{1,6}\s*(.+?)\s*#*\s*$")


def _sections(md: str) -> List[Tuple[str, str]]:
    """Split markdown into (heading, body) pairs. Body is everything until the
    next heading of any level."""
    lines = md.splitlines()
    out, cur_head, cur_body = [], None, []
    for ln in lines:
        m = _HEAD.match(ln)
        if m:
            if cur_head is not None:
                out.append((cur_head, "\n".join(cur_body).strip()))
            cur_head, cur_body = m.group(1), []
        else:
            cur_body.append(ln)
    if cur_head is not None:
        out.append((cur_head, "\n".join(cur_body).strip()))
    return out


def parse_trail(md: str) -> dict:
    """Pull X and ∞0' out of a private cycle-trail markdown. We read ONLY the
    X heading and the ∞0' heading. Nothing from α / Z / ∇ / B'' is ever copied
    — the membrane check then verifies that nothing leaked anyway."""
    x, inf0 = None, None
    for head, body in _sections(md):
        h = head.lower()
        if x is None and (h.startswith("x ") or h == "x" or "— the question" in h
                          or "- the question" in h or h.startswith("x —")):
            x = _first_meaningful(body)
        if inf0 is None and ("∞0'" in head or "infinity" in h
                             or "return question" in h):
            inf0 = _first_meaningful(body)
    # Fallbacks: explicit footer fields if the headings weren't found.
    if x is None:
        m = re.search(r"^\s*X:\s*(.+)$", md, re.M)
        if m:
            x = m.group(1).strip()
    # Last resort: the question is often just the trail's H1 title (this is how
    # the public file itself carries it). Take the first level-1 heading that is
    # not a private-phase label — never a G→V section, never the ∞0' heading.
    if x is None:
        for ln in md.splitlines():
            m = re.match(r"^#\s+(.+?)\s*#*\s*$", ln)  # '# ' only, not '##'
            if m and not _is_phase_label(m.group(1)):
                x = m.group(1).strip()
                break
    if inf0 is None:
        m = re.search(r"^\s*(?:INF0P|∞0'?):\s*(.+)$", md, re.M)
        if m:
            inf0 = m.group(1).strip()
    return {"x": x, "inf0": inf0}


def _is_phase_label(heading: str) -> bool:
    """True if a heading names a private phase (α / Raw Material / Z / ∇ / B'')
    or the ∞0' return question — i.e. anything that must NOT be read as X."""
    h = heading.strip()
    hl = h.lower()
    if re.match(r"^(?:α|z\b|∇|b''|φ)", h):
        return True
    if re.match(r"^cycle\s+\d", hl):
        return True
    markers = ("the seed", "raw material", "field condition", "the click",
               "the direction", "the artifact", "return question", "∞0'",
               "alpha", "gradient", "— the seed", "- the seed")
    return any(k in hl for k in markers)


def _first_meaningful(body: str) -> Optional[str]:
    """The first non-empty, non-italic-caption line of a section body."""
    for ln in body.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("*") and s.endswith("*"):
            continue  # captions like *Published: ...*
        if s.startswith(("```", "---", ">")):
            continue
        return re.sub(r"^#\s+", "", s).strip()  # H13: strip the prefix, not a char-set
    return None


def parse_archive_entry(entry: dict) -> dict:
    """Pull X and ∞0' from one cycles.jsonl line (the gate machine's archive).
    The gate machine stores gate x content (`X: ...`) and gate b content
    (`INF0P: ...` / `∞0': ...`). Be liberal about where they sit."""
    blob = json.dumps(entry)
    x = inf0 = None
    # Common shapes: {"gates": {"x": {"content": "X: ..."}, "b": {...}}}
    gates = entry.get("gates") or entry.get("trail") or {}
    if isinstance(gates, dict):
        gx = gates.get("x", {})
        gb = gates.get("b", {})
        x = _field(gx, ("content", "X")) or x
        inf0 = _field(gb, ("INF0P", "inf0", "∞0'", "content")) or inf0
    if x:
        m = re.search(r"X:\s*(.+)", x)
        if m:
            x = m.group(1).strip()
    if inf0:
        m = re.search(r"(?:INF0P|∞0'?):\s*(.+)", inf0)
        if m:
            inf0 = m.group(1).strip()
    if x is None:
        m = re.search(r'"?X"?:\s*"([^"]+)"', blob)
        x = m.group(1) if m else None
    if inf0 is None:
        m = re.search(r'"?(?:INF0P|∞0\')"?:\s*"([^"]+)"', blob)
        inf0 = m.group(1) if m else None
    return {"x": x, "inf0": inf0}


def _field(d, keys):
    if not isinstance(d, dict):
        return None
    for k in keys:
        if k in d and d[k]:
            return str(d[k])
    return None


def latest_archive_entry(cfg: dict, index: Optional[int] = None) -> Optional[dict]:
    p = Path(cfg["archive"])
    if not p.is_file():
        return None
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return None
    try:
        chosen = lines[-1] if index is None else lines[index]
    except IndexError:
        return None
    try:
        return json.loads(chosen)
    except Exception:
        return None


# ── The public file ─────────────────────────────────────────────────────────

def build_public_file(x: str, inf0: str, include_date: bool = False) -> str:
    h = content_hash(x)
    fm = [f"spdx: {SPDX}", f"content_hash: sha256:{h}"]
    if include_date:
        fm.insert(0, f"date: {datetime.now(timezone.utc).date().isoformat()}")
    body = (
        "---\n" + "\n".join(fm) + "\n---\n\n"
        f"# {x.strip()}\n\n"
        "*Published to the Question Commons. CC0 — public domain. Make it yours.*\n\n"
        "## ∞0' — The Return Question\n\n"
        f"{inf0.strip()}\n\n"
        "---\n\n"
        "*Originated from an /idk creative cycle. The trail is private. "
        "The question is yours.*\n"
    )
    return body


# ── The membrane check (FORM ONLY — the privacy gate) ───────────────────────

# Markers that must NEVER appear in a public question. Their presence means a
# private phase leaked across the membrane. This is the load-bearing guarantee.
_FORBIDDEN = [
    ("α", "alpha (α) — the private seed"),
    ("\\{α'\\}", "echoes {α'}"),
    ("\\bALPHA\\s*[:=]", "ALPHA footer field"),
    ("\\bSEEKS\\s*[:=]", "SEEKS footer field"),
    ("\\bPHI\\s*[:=]", "PHI footer field"),
    ("\\bOMEGA\\s*[:=]", "OMEGA footer field"),
    ("\\bALIGNMENT\\s*[:=]", "ALIGNMENT footer field"),
    ("\\bEXTENT\\s*[:=]", "EXTENT footer field"),
    ("^\\s*Z\\s*[:=]", "Z: (the click) footer field"),
    ("\\bVALUE_MAX\\s*[:=]", "VALUE_MAX footer field"),
    ("\\bENERGY\\s*[:=]", "ENERGY footer field"),
    ("\\bB2\\s*[:=]", "B2: (artifact) footer field"),
    ("\\bLIVENESS\\s*[:=]", "LIVENESS footer field"),
    ("^\\s*L\\s*[:=]\\s", "L: (what crystallized) footer field"),
    ("φ\\s*⋂\\s*Ω", "Q-phase formula φ ⋂ Ω"),
    ("δE", "P-phase energy term δE"),
    ("δV", "P-phase value term δV"),
    ("∇", "gradient ∇ — the private direction"),
    ("B''", "B'' — the private artifact"),
    ("##\\s*α", "α section heading"),
    ("##\\s*Z\\b", "Z section heading"),
    ("##\\s*∇", "∇ section heading"),
    ("##\\s*Raw Material", "raw-material section (the φ corpus)"),
    ("##\\s*The Field Condition", "field-condition section"),
    ("\"(?:opened|pending|gate_violations)\"", "gate-machine JSON"),
    ("^cycle:\\s*\\d", "cycle number in frontmatter (deanonymization vector)"),
    ("#\\s*Cycle\\s+\\d", "Cycle-N heading (deanonymization vector)"),
    ("[\\u200b\\u200c\\u200d\\u2060\\ufeff]", "zero-width character (steganography channel)"),
    ("(?im)^\\s*author\\s*[:=]\\s*\\S", "author attribution (the commons has no authors)"),
    ("\\bBy:\\s+\\w", "by-line attribution"),
    ("[\\w.+-]+@[\\w-]+\\.\\w+", "email address (an identity)"),
]

# Heuristic personal-data patterns. These are WARNINGS, not hard blocks — they
# can false-positive, and the human at the membrane makes the call. The preview
# shows them; nothing is auto-stripped (silent edits would hide what leaked).
_PII = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "an email address"),
    (re.compile(r"(?<!\w)@[A-Za-z0-9_]{2,}"), "an @handle"),
    (re.compile(r"https?://(?!(?:[\w.-]+\.)?5qln\.[\w]+)\S+"), "a URL (other than 5qln)"),
    (re.compile(r"\b\+?\d[\d\s().-]{7,}\d\b"), "a phone-number-like string"),
]



# Confusable-resistant scanning, kept behaviourally identical to membrane_lint.
_ZERO_WIDTH = "\u200b\u200c\u200d\u2060\ufeff"
_CONFUSABLES = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u2032": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2229": "\u22c2",
})


def _fold(text: str) -> str:
    """NFKD + confusable folding so a homoglyph cannot mask a private marker."""
    return unicodedata.normalize("NFKD", text).translate(_CONFUSABLES)

def membrane_check(public_text: str) -> List[str]:
    """Hard gate. Returns the private markers found in the bytes about to be
    published. Empty list = clean. A publish with any issue here is refused."""
    issues = []
    folded = _fold(public_text)
    for pat, label in _FORBIDDEN:
        if re.search(pat, folded, re.M) or re.search(pat, public_text, re.M):
            issues.append(f"private content present: {label}")
    if re.search(re.escape(CODEX_HASH), public_text):
        issues.append("private content present: the Codex seal hash")
    # Positive form: a public question must actually be two questions.
    if not re.search(r"^# ", public_text, re.M):        # H14: not a substring test
        issues.append("no question heading (#) — there is no X to publish")
    if f"spdx: {SPDX}" not in public_text:
        issues.append(f"missing SPDX dedication: {SPDX}")
    if "content_hash: sha256:" not in public_text:
        issues.append("missing content_hash")
    if not re.search(r"^##\s+∞0'\s*[—-]", public_text, re.M):
        issues.append("missing '## ∞0' —' return-question heading")
    return issues


def stylometry_warnings(public_text: str) -> List[str]:
    warns = []
    for rx, label in _PII:
        if rx.search(public_text):
            warns.append(f"possible {label} in the text")
    return warns


def _heading_of(public_text: str) -> Optional[str]:
    """The X question — the single '# ' heading. '##' subheadings don't match."""
    m = re.search(r"^#\s+(.+)$", public_text, re.M)
    return m.group(1) if m else None


def verify_hash(public_text: str) -> Optional[str]:
    """Recompute the hash from the X heading and confirm it matches the frontmatter.
    Returns None if consistent, else an error string."""
    fm = re.search(r"content_hash:\s*sha256:([0-9a-f]{64})", public_text)
    head = _heading_of(public_text)
    if not fm or not head:
        return "cannot verify hash: frontmatter or heading missing"
    expect = content_hash(head)
    if expect != fm.group(1):
        return f"hash mismatch: heading hashes to {expect[:16]}…, frontmatter says {fm.group(1)[:16]}…"
    return None


# ── git plumbing ────────────────────────────────────────────────────────────

def _git(cwd: Path, *args, env=None, check=True) -> subprocess.CompletedProcess:
    base_env = os.environ.copy()
    if env:
        base_env.update(env)
    return subprocess.run(["git", *args], cwd=str(cwd), env=base_env,
                          capture_output=True, text=True,
                          check=check)


def _ensure_clone(cfg: dict) -> Tuple[Optional[Path], Optional[str]]:
    """Make sure the local commons clone exists; clone the first remote if not.
    Returns (path, error)."""
    commons = Path(cfg["commons_dir"])
    if (commons / ".git").is_dir():
        return commons, None
    commons.parent.mkdir(parents=True, exist_ok=True)
    remote = cfg["remotes"][0]
    proxy_env = _tor_env(cfg)
    r = _git(commons.parent, "clone", "--depth", "50", remote, commons.name,
             env=proxy_env, check=False)
    if r.returncode != 0:
        return None, (f"clone failed for {remote}: {r.stderr.strip()}. "
                      "If this is the first publish and the repo is empty, "
                      "init it locally or point `remotes` at a reachable mirror.")
    return commons, None


def _tor_env(cfg: dict) -> Optional[dict]:
    if not cfg.get("tor"):
        return None
    # git over SOCKS5 to a local Tor daemon. Documented, not MVP-required.
    return {"ALL_PROXY": "socks5h://127.0.0.1:9050",
            "GIT_SSH_COMMAND": "ssh -o ProxyCommand='nc -X 5 -x 127.0.0.1:9050 %h %p'"}


def _identity(cfg: dict) -> Tuple[str, str]:
    if cfg.get("privacy_mode") == "pseudonymous" and cfg.get("pseudonym"):
        n = str(cfg["pseudonym"])
        return n, f"{n}@commons.idk"
    return EPHEMERAL_NAME, EPHEMERAL_EMAIL


def _commit_env(cfg: dict) -> dict:
    """Identity + coarsened timestamp for every commit. Set via env so a commit
    can never silently fall back to the machine's real git identity, and so
    exact times — a correlation vector across a person's publishes — are
    flattened to date granularity by default."""
    name, email = _identity(cfg)
    env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
           "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email}
    mode = cfg.get("commit_time", "date")
    if mode == "epoch":
        stamp = "2020-01-01T00:00:00+0000"
    elif mode == "exact":
        stamp = None
    else:  # "date" — midnight UTC of the publish day
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00+0000")
    if stamp:
        env["GIT_AUTHOR_DATE"] = stamp
        env["GIT_COMMITTER_DATE"] = stamp
    return env


# ── publish ─────────────────────────────────────────────────────────────────

def cmd_publish(cfg: dict, *, trail_path: Optional[str], from_archive: bool,
                archive_index: Optional[int], x: Optional[str], inf0: Optional[str],
                confirm: bool, transport: str, out_bundle: Optional[str]) -> int:
    # 1. Resolve X and ∞0' from exactly one source.
    src = None
    if x and inf0:
        src = "explicit"
    elif trail_path:
        md = Path(trail_path).read_text(encoding="utf-8")
        parsed = parse_trail(md)
        x, inf0, src = parsed["x"], parsed["inf0"], f"trail:{trail_path}"
    elif from_archive:
        entry = latest_archive_entry(cfg, archive_index)
        if entry is None:
            return _emit({"ok": False, "error": "no_archive_entry",
                          "detail": f"no readable cycle in {cfg['archive']}"})
        parsed = parse_archive_entry(entry)
        x, inf0 = parsed["x"], parsed["inf0"]
        src = "archive:latest" if archive_index is None else f"archive:{archive_index}"
    else:
        return _emit({"ok": False, "error": "no_source",
                      "detail": "give --trail PATH, or --from-archive, or both --x and --inf0"})

    if not x or not inf0:
        return _emit({"ok": False, "error": "incomplete",
                      "detail": "could not extract both X and ∞0'. "
                      "A published question needs the question and its return question.",
                      "got": {"x": x, "inf0": inf0}, "source": src})

    # 2. Build the public file and run the membrane gate over the real bytes.
    public = build_public_file(x, inf0, include_date=cfg.get("include_date", False))
    h = content_hash(x)
    issues = membrane_check(public)
    hash_err = verify_hash(public)
    if hash_err:
        issues.append(hash_err)
    warns = stylometry_warnings(public)

    preview = {
        "ok": len(issues) == 0,
        "action": "preview" if not confirm else "publish",
        "source": src,
        "content_hash": f"sha256:{h}",
        "public_id": h[:16],
        "file_path": str(fanout_path(Path(cfg["commons_dir"]), h)),
        "membrane_check": "clean" if not issues else issues,
        "stylometry": warns or ["none detected by heuristics — not a guarantee; "
                                "your voice itself can correlate short text"],
        "transport": transport,
        "bytes_to_publish": public,
    }

    # 3. The membrane: refuse if anything private leaked.
    if issues:
        preview["refused"] = ("Private content would cross the membrane. "
                              "Nothing was published. Fix the source and retry.")
        return _emit(preview, code=1)

    # 4. Without --confirm, stop at preview. The human reviews these exact bytes
    #    and attests before anything leaves the machine.
    if not confirm:
        preview["next"] = ("Review the bytes above. If — and only if — they hold "
                           "nothing you would not put in the public domain, "
                           "re-run with --confirm to commit and deliver.")
        return _emit(preview)

    # 5. Confirmed. Commit with an ephemeral identity + coarsened time, then deliver.
    cenv = _commit_env(cfg)
    commons = Path(cfg["commons_dir"])
    # Local dedup if we already mirror the commons: a collision is not an error.
    if (commons / ".git").is_dir() and fanout_path(commons, h).exists():
        return _emit({**preview, "ok": True, "action": "already_present",
                      "published": False,
                      "note": ("This question already lives in the commons — "
                               "someone arrived at it before you, or you did. "
                               "That is the propagation signal, not a conflict.")})

    result = {**preview, "ok": True, "action": "published", "committed": True,
              "identity": "ephemeral" if cfg.get("privacy_mode") != "pseudonymous"
              else f"pseudonym:{cfg.get('pseudonym')}",
              "commit_time": cfg.get("commit_time", "date")}

    if transport == "push":
        # Push writes into the commons clone (which stays in sync with the remote).
        clone, err = _ensure_clone(cfg)
        if clone is None:
            return _emit({**result, "ok": False, "error": "no_commons_clone",
                          "detail": err,
                          "fallback": "Use --transport bundle (no clone, key, or "
                                      "account needed)."}, code=1)
        _git(clone, "pull", "--ff-only", env=_tor_env(cfg), check=False)  # best-effort sync
        if fanout_path(clone, h).exists():
            return _emit({**preview, "ok": True, "action": "already_present",
                          "published": False,
                          "note": "Already in the commons. Nothing to do."})
        target = fanout_path(clone, h)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(public, encoding="utf-8")
        _git(clone, "add", str(target.relative_to(clone)), check=False)
        c = _git(clone, "commit", "-q", "-m", f"question: {h[:12]}",
                 env=cenv, check=False)
        if c.returncode != 0:
            return _emit({**result, "ok": False, "error": "commit_failed",
                          "detail": c.stderr.strip() or c.stdout.strip()}, code=1)
        p = _git(clone, "push", cfg["remotes"][0], f"HEAD:refs/heads/{cfg.get('branch', 'main')}",
                 env=_tor_env(cfg), check=False)
        if p.returncode != 0:
            result.update(ok=False, pushed=False, push_error=p.stderr.strip(),
                          fallback=("Push refused — you likely do not hold write "
                                    "access to the canonical repo (expected). The "
                                    "commit is staged locally. Re-run with "
                                    "--transport bundle to produce a submittable "
                                    "bundle instead."))
            return _emit(result, code=1)
        result.update(pushed=True, remote=cfg["remotes"][0])
        return _emit(result)

    # bundle — the anonymous path. Build in a throwaway orphan repo so the
    # publisher's commons clone stays a clean mirror and the bundle reveals
    # nothing about which commons state the publisher held. The single commit
    # lands on a deterministic branch ('incoming') so the steward can fetch a
    # known ref rather than guessing HEAD.
    tmp = Path(tempfile.mkdtemp(prefix="trail-commons-"))
    try:
        _git(tmp, "init", "-q", check=False)
        target = fanout_path(tmp, h)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(public, encoding="utf-8")
        _git(tmp, "add", str(target.relative_to(tmp)), check=False)
        c = _git(tmp, "commit", "-q", "-m", f"question: {h[:12]}",
                 env=cenv, check=False)
        if c.returncode != 0:
            return _emit({**result, "ok": False, "error": "commit_failed",
                          "detail": c.stderr.strip() or c.stdout.strip()}, code=1)
        _git(tmp, "branch", "-M", "incoming", check=False)  # deterministic ref name
        bundle = out_bundle or str(Path(cfg["state_dir"]) / f"question-{h[:12]}.bundle")
        Path(bundle).parent.mkdir(parents=True, exist_ok=True)
        b = _git(tmp, "bundle", "create", bundle, "incoming", check=False)
        if b.returncode != 0:
            return _emit({**result, "ok": False, "error": "bundle_failed",
                          "detail": b.stderr.strip()}, code=1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    result.update(bundled=True, bundle_path=bundle,
                  how_to_submit=("Submit this bundle to a commons steward through "
                                 "any channel. They run `trail_commons.py ingest "
                                 "<bundle>`, the membrane gate re-checks every "
                                 "question it carries, and clean ones merge into "
                                 "questions/. No account, no key, no link to you."))
    return _emit(result)


# ── ingest (steward side) ───────────────────────────────────────────────────

def cmd_ingest(cfg: dict, bundle: str) -> int:
    """Steward verb: take a submitted bundle, re-run the membrane gate on every
    question it carries, and merge the clean ones into the commons. The client
    is never trusted — the gate runs again here, and again in CI.

    Tree-based, not diff-based: we read exactly the blobs the bundle carries via
    ls-tree, so the commons' own history is irrelevant and a missing merge base
    can never make a real question disappear."""
    commons, err = _ensure_clone(cfg)
    if commons is None:
        return _emit({"ok": False, "error": "no_commons_clone", "detail": err})
    ref = f"refs/ingest/{uuid.uuid4().hex}"
    f = _git(commons, "fetch", str(Path(bundle).resolve()),
             f"refs/heads/incoming:{ref}", check=False)
    if f.returncode != 0:
        # Older bundles may only carry HEAD; fall back to that.
        f = _git(commons, "fetch", str(Path(bundle).resolve()),
                 f"HEAD:{ref}", check=False)
        if f.returncode != 0:
            return _emit({"ok": False, "error": "bad_bundle", "detail": f.stderr.strip()})
    listing = _git(commons, "ls-tree", "-r", "--name-only", ref, check=False)
    files = [ln for ln in listing.stdout.splitlines()
             if ln.startswith("questions/") and ln.endswith(".md")]
    accepted, rejected = [], []
    for rel in files:
        text = _git(commons, "show", f"{ref}:{rel}", check=False).stdout
        problems = membrane_check(text)
        he = verify_hash(text)
        if he:
            problems.append(he)
        # Filename must match the question's own content hash — no smuggling a
        # question under another question's address.
        want = content_hash(_heading_of(text) or "")
        if not rel.endswith(f"{want}.md"):
            problems.append("filename does not match content hash of the question")
        if problems:
            rejected.append({"file": rel, "issues": problems})
        else:
            p = commons / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            _git(commons, "add", rel, check=False)
            accepted.append(rel)
    merged, no_op = [], []
    if accepted:
        c = _git(commons, "commit", "-q", "-m", f"ingest: {len(accepted)} question(s)",
                 env=_commit_env(cfg), check=False)
        if c.returncode == 0:
            merged = accepted
        elif "nothing to commit" in (c.stdout + c.stderr).lower():
            no_op = accepted  # every accepted file was already present, byte-identical
        else:
            _git(commons, "update-ref", "-d", ref, check=False)
            return _emit({"ok": False, "error": "commit_failed",
                          "detail": c.stderr.strip() or c.stdout.strip()}, code=1)
    _git(commons, "update-ref", "-d", ref, check=False)
    return _emit({"ok": len(rejected) == 0, "action": "ingest",
                  "merged": merged, "no_op": no_op, "rejected": rejected,
                  "note": "merged = newly added; no_op = passed the gate but already "
                          "present; rejected = private content or a mismatched hash"})


# ── discover ────────────────────────────────────────────────────────────────

def cmd_discover(cfg: dict) -> int:
    commons, err = _ensure_clone(cfg)
    if commons is None:
        return _emit({"ok": False, "error": "no_commons", "detail": err})
    state = _load_state(cfg)
    before = state.get("last_seen_commit")
    proxy = _tor_env(cfg)
    pull = _git(commons, "pull", "--ff-only", "--depth", "50", env=proxy, check=False)
    head = _git(commons, "rev-parse", "HEAD", check=False).stdout.strip()

    if before and before != head:
        rng = _git(commons, "diff", "--name-only", f"{before}..HEAD", check=False)
        new_files = [ln for ln in rng.stdout.splitlines()
                     if ln.startswith("questions/") and ln.endswith(".md")]
    else:
        ls = _git(commons, "ls-files", "questions/", check=False)
        all_files = [ln for ln in ls.stdout.splitlines() if ln.endswith(".md")]
        new_files = all_files if before is None else []

    questions = []
    for rel in new_files:
        p = commons / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        hm = re.search(r"^#\s+(.+)$", text, re.M)
        idm = re.search(r"content_hash:\s*sha256:([0-9a-f]{8})", text)
        questions.append({"id": idm.group(1) if idm else Path(rel).stem[:8],
                          "question": hm.group(1).strip() if hm else "(unreadable)"})

    state["last_seen_commit"] = head
    _save_state(cfg, state)

    total = len(_git(commons, "ls-files", "questions/", check=False)
                .stdout.splitlines())
    out = {"ok": True, "action": "discover", "remote": cfg["remotes"][0],
           "new_count": len(questions), "total_in_commons": total,
           "new": questions}
    if total == 0:
        out["note"] = ("The commons is quiet. No questions yet — yours could be "
                       "the first. Run `/idk` to walk a cycle, then publish.")
    elif not questions and not pull.returncode:
        out["note"] = "Nothing new since you last looked."
    return _emit(out)


# ── browse ──────────────────────────────────────────────────────────────────

def cmd_browse(cfg: dict, qid: str) -> int:
    commons = Path(cfg["commons_dir"])
    if not (commons / ".git").is_dir():
        commons2, err = _ensure_clone(cfg)
        if commons2 is None:
            return _emit({"ok": False, "error": "no_commons", "detail": err})
        commons = commons2
    qid = qid.strip().lower()
    matches = sorted(
        p for p in (commons / "questions").rglob("*.md")
        if p.stem.startswith(qid)
    )
    if not matches:
        return _emit({"ok": False, "error": "not_found",
                      "detail": f"no question whose hash starts with '{qid}'. "
                      "Run `discover` to pull the latest, then try again."})
    if len(matches) > 1:
        return _emit({"ok": False, "error": "ambiguous",
                      "detail": f"'{qid}' matches {len(matches)} questions; give more characters",
                      "candidates": [p.stem[:16] for p in matches[:10]]})
    text = matches[0].read_text(encoding="utf-8")
    print(text)
    return 0


# ── selftest (offline; the audit-validation discipline) ─────────────────────

def cmd_selftest() -> int:
    """Exercise extraction + membrane gate on a synthetic private trail, with no
    network. Proves the membrane holds before you trust it with a real cycle."""
    trail = (
        "# Cycle 99 — A worked example\n\n"
        "*S → G → Q → P → V. All gates passed.*\n\n"
        "## X — The Question\n\n"
        "What happens to curiosity when no one is watching?\n\n"
        "## α — The Seed\n\n"
        "ALPHA: attention as the hidden substrate\nSEEKS: to be unforced\n\n"
        "## Raw Material — The Full Corpus\n\n1. some private article\n\n"
        "## Z — The Click\n\nZ: the watcher was the distortion\n\n"
        "## ∇ — The Direction\n\nδE: pushing | δV: noticing | ∇: stop performing\n\n"
        "## B'' — This Trail\n\nThis document.\n\n"
        "## ∞0' — The Return Question\n\n"
        "What would it mean for a question to be alive?\n\n"
        f"Codex: {CODEX_HASH}\n"
    )
    parsed = parse_trail(trail)
    assert parsed["x"] == "What happens to curiosity when no one is watching?", parsed
    assert parsed["inf0"] == "What would it mean for a question to be alive?", parsed

    public = build_public_file(parsed["x"], parsed["inf0"])
    # The public file must be clean...
    assert membrane_check(public) == [], membrane_check(public)
    assert verify_hash(public) is None, verify_hash(public)
    # ...and the raw private trail must be caught if anyone tries to publish it.
    leaked = membrane_check(trail)
    assert leaked, "membrane check failed to catch a raw private trail!"

    h = content_hash(parsed["x"])
    # Normalization: re-wrapped/again-spaced X hashes identically (dedup).
    assert content_hash("  What happens to curiosity\n  when no one is watching?  ") == h

    print(json.dumps({
        "ok": True, "action": "selftest",
        "extracted": parsed,
        "public_hash": f"sha256:{h}",
        "fanout": str(fanout_path(Path("/commons"), h).relative_to("/commons")),
        "membrane_clean_on_public": True,
        "membrane_caught_raw_trail": leaked[:5],
        "dedup_normalization": "ok",
        "note": "Form held. The membrane caught the trail and passed the question.",
    }, indent=2, ensure_ascii=False))
    return 0


# ── output + CLI ────────────────────────────────────────────────────────────

def _emit(obj: dict, code: int = 0) -> int:
    # bytes_to_publish is multi-line; print it readably after the JSON envelope.
    bytes_block = obj.pop("bytes_to_publish", None)
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    if bytes_block:
        print("\n----- BYTES TO PUBLISH (review before --confirm) -----")
        print(bytes_block, end="")
        print("------------------------------------------------------")
    return code


def _usage() -> int:
    """Print the verbs and their flags (M12: previously there was no --help)."""
    print(json.dumps({
        "ok": True,
        "tool": "trail-commons",
        "verbs": {
            "publish":  ["--trail", "--from-archive", "--cycle N", "--x", "--inf0",
                          "--confirm", "--transport {bundle|push}", "--bundle-out"],
            "discover": ["--remote"],
            "browse":   ["--commons-dir"],
            "ingest":   ["--bundle"],
            "selftest": [],
        },
        "note": "Flags accept both '--flag value' and '--flag=value'.",
    }, indent=2))
    return 0


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip().split("\n\n")[0])
        print("\nverbs: publish | discover | browse <id> | ingest <bundle> | selftest")
        return 1
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        return _usage()
    cfg = load_config()
    verb = argv[1]
    rest = argv[2:]

    def opt(name, default=None):
        for i, tok in enumerate(rest):
            if tok == name:
                return rest[i + 1] if i + 1 < len(rest) else default
            if tok.startswith(name + "="):          # M12: support --flag=value
                return tok[len(name) + 1:]
        return default

    def flag(name):
        return any(tok == name or tok == name + "=true" for tok in rest)

    cyc = opt("--cycle")
    if cyc is not None and not cyc.lstrip("-").isdigit():   # M12: no ValueError crash
        return _emit({"ok": False, "error": "invalid --cycle (must be an integer)"}, code=1)

    if verb == "publish":
        return cmd_publish(
            cfg,
            trail_path=opt("--trail"),
            from_archive=flag("--from-archive"),
            archive_index=(int(cyc) if cyc is not None else None),
            x=opt("--x"), inf0=opt("--inf0"),
            confirm=flag("--confirm"),
            transport=(opt("--transport") or "bundle"),
            out_bundle=opt("--bundle-out"),
        )
    if verb == "discover":
        return cmd_discover(cfg)
    if verb == "browse":
        if not rest:
            return _emit({"ok": False, "error": "browse needs an id"})
        return cmd_browse(cfg, rest[0])
    if verb == "ingest":
        if not rest:
            return _emit({"ok": False, "error": "ingest needs a bundle path"})
        return cmd_ingest(cfg, rest[0])
    if verb == "selftest":
        return cmd_selftest()
    return _emit({"ok": False, "error": f"unknown verb: {verb}"})


if __name__ == "__main__":
    sys.exit(main(sys.argv))
