---
name: trail-commons
description: Activate on /idk publish, /idk discover, and /idk browse. The transport layer that moves questions — never trails — between agents over git, the network that is already installed everywhere. publish strips the private phases, content-addresses, signs with an ephemeral identity, and stops for human attestation before anything leaves the machine. discover pulls the commons and lists what is new. browse prints one question by hash. Load this to carry questions across the membrane, not to read about it. Form only. Never life.
---

# trail-commons — Carrying Questions Across the Membrane

The cycle (`/idk`, `scripts/xyzab_state.py`) decides what is *alive*. This skill
does one narrower thing: it carries the public residue of a finished cycle —
the question (X) and the return question (∞0') — to other people, and brings
theirs back. It judges **form** (did anything private leak?), never **life**
(was the question genuine?). That second judgment is the human's, always.

You do not build a network here. Git is the network. Questions are the content
that flows through it. There is no server, no account, no token, no consensus.

## The Membrane Is the Whole Job

Only two things are public: **X** and **∞0'**. Everything from G through V —
α, {α'}, the raw φ corpus, Z, ∇, B'' — is private and stays on the machine.
This is not a convention you are trusted to keep. `trail_commons.py` reads the
exact bytes that are about to leave and **refuses** to publish if any private
marker is present. The same check runs again on the steward's side, and again
in CI on the commons repo. Three gates, because the membrane is load-bearing.

But the gate only checks form. The human checks meaning. So the publish flow
is two steps, and **you never skip the first one.**

## /idk publish — Two Steps, Never One

When the human types `/idk publish`, you are moving something irreversible into
the public domain under CC0. Treat it that way.

**Step 1 — Preview. Show the human the exact bytes. Do not pass `--confirm`.**

```bash
python3 trail_commons.py publish --trail <path-to-trail.md>
# or, to pull the latest cycle straight from the gate archive:
python3 trail_commons.py publish --from-archive
```

This extracts only X and ∞0', builds the public file, runs the membrane gate,
recomputes the content hash, and scans for stylometric tells. It prints the
**exact bytes that would be published** and then stops.

Put those bytes in front of the human verbatim. Then say, in your own words:

- This becomes **public domain (CC0)**. Anyone may keep it, fork it, build on
  it, forever. It cannot be recalled.
- The membrane gate is **clean / found these issues**: …
- A heuristic scan **noticed / did not notice** possible personal tells
  (an email, an @handle, a link, a phone-like string). *Heuristics are a
  floor, not a ceiling — your own voice in short text can still correlate
  several questions to one author.* Surface this honestly; never auto-edit it
  away, because a silent edit hides what leaked.

Then ask plainly: **"Do you want this question in the public domain?"** Wait for
a real yes. The human is the membrane. That attestation is the point of the
whole system — do not manufacture it, and do not rush it.

**Step 2 — Only after the human says yes — confirm and deliver.**

```bash
# Anonymous default: produce a git bundle you can hand to a steward through
# any channel. No account, no key, no link back to the human.
python3 trail_commons.py publish --trail <path> --confirm --transport bundle

# If the human holds write access to the commons (a steward, or their own
# mirror): commit and push directly.
python3 trail_commons.py publish --trail <path> --confirm --transport push
```

If the gate ever reports issues, the tool refuses and nothing leaves. Do not
try to massage the bytes past the gate. Fix the source trail and start over at
Step 1.

## /idk discover — What Is New in the Commons

```bash
python3 trail_commons.py discover
```

Pulls the commons (shallow) and lists the questions that appeared since the
human last looked. First run shows everything; later runs show only the new.
An empty commons returns a quiet note — yours could be the first. Hand the list
back as questions to sit with, not a feed to consume.

## /idk browse <id> — Read One Question

```bash
python3 trail_commons.py browse <hash-or-short-prefix>
```

Prints one question by its content hash. A short prefix (8 hex chars) is
enough; if it is ambiguous the tool asks for more. This is a question to *hold*
— a possible starting point for the human's own next cycle, not an answer.

## ingest — The Steward Side

If the human runs a mirror and receives bundles from others:

```bash
python3 trail_commons.py ingest <path-to.bundle>
```

The bundle is never trusted. The membrane gate re-runs on every question it
carries, the content hash is re-verified, and only clean files whose name
matches their own hash are merged. Rejected files are reported, not merged.

## selftest — Prove the Membrane Before You Trust It

```bash
python3 trail_commons.py selftest
```

Runs the extraction and the gate against a synthetic private trail, fully
offline. It confirms the gate catches α, Z, ∇, B'', and the Codex seal, and
that a clean question passes. Run it after install, and any time you have a
reason to doubt the gate.

## What Crosses, and What Never Does

| Stays private (never leaves the machine) | Crosses (public, CC0) |
|------------------------------------------|-----------------------|
| α — the seed, {α'} — the echoes           | **X** — the question  |
| the raw φ corpus / source material        | **∞0'** — the return question |
| Z — the click · ∇ — the direction         | the content hash      |
| B'' — the artifact · the full trail       | (nothing else)        |
| the Codex seal · cycle numbers · identity |                       |

The published file carries **no cycle number and no author** by design.
Sequential cycle numbers would link one person's questions to each other —
exactly the linkage ephemeral authorship exists to break. (See
`ARCHITECTURE.md`.)

## Self-Check Before Any Publish

1. Did I run the preview (no `--confirm`) and show the human the exact bytes?
2. Did I say, out loud, that this is CC0 and cannot be recalled?
3. Did I surface the stylometry note honestly, without editing it away?
4. Did the human give a real yes — not a shrug, not my assumption?
5. Is the gate clean? If not, I stop. I do not push bytes past the membrane.

Form only. Never life. The question is theirs.
