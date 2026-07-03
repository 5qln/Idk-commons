# trail-commons

The transport layer of the Question Commons: the agent-side tool that carries
**questions — and only questions** — from a finished `/idk` cycle into the
public commons, over git, with a human attestation before anything leaves the
machine.

A cycle touches far more than its question — a seed, raw material, a click, a
direction, an artifact — and all of that is **private**. It never leaves the
machine. Only two things cross the membrane:

- **X** — the question that opened the cycle
- **∞0'** — the return question the cycle could not have asked before it began

> One person's published question becomes another person's starting point.
> The work that connects them stays private. Only the questions are public.

There is no server, no account, no token, no consensus. Git is the network;
questions are the payload; this tool is the thin gate between a private cycle
and that public network.

## The three verbs

- **`/idk publish`** — strips a finished cycle down to X and ∞0', runs the
  membrane gate, shows the human the **exact bytes**, and only after a real
  yes delivers them — as an anonymous `git bundle` handed to a steward
  (default; no account, no key, no link back), or as a direct push for those
  with write access. Two steps, never one: nothing leaves on the first command.
- **`/idk discover`** — pulls the commons and lists what is new since the
  human last looked. Questions to sit with, not a feed to consume.
- **`/idk browse <id>`** — prints one question by its content hash. A possible
  starting point for the human's own next cycle, not an answer.

Plus, for stewards: **`ingest`** re-runs the gate on every question a
submitted bundle carries and merges only clean files. And **`selftest`**
proves the gate offline — run it after install, and any time you doubt.

## The membrane, enforced three times

Only X and ∞0' are public. This is not a convention anyone is trusted to
keep — it is checked in three different trust domains:

1. **Client preview** — `publish` gates the exact bytes locally before the
   human ever attests.
2. **Steward ingest** — a bundle is never trusted; the gate re-runs on
   everything it carries.
3. **Commons CI** — [`skills/trail-commons/membrane_lint.py`](skills/trail-commons/membrane_lint.py)
   runs on every push and pull request to the commons, so even a direct push
   by someone with write access is gated.

A file carrying any private marker — or whose name does not match its own
content hash — fails the gate and cannot land. The gate judges **form only**.
It cannot tell whether a question is alive; the human judges meaning. That is
why the preview step exists and is never skipped.

The rules live in [`membrane-spec.json`](membrane-spec.json) — a single
source of truth kept byte-identical with the commons repo, with a pinned-SHA
sync test so the gates cannot silently disagree. See
[`ARCHITECTURE.md`](ARCHITECTURE.md) for the full reasoning, the privacy
posture (ephemeral identity, coarsened commit time, no cycle numbers), and
what the gate honestly cannot do (stylometry).

## Install

You usually don't install this directly. The staged path: install
[`/idk`](https://github.com/5qln/Idk) first and walk cycles; the first time
you type `/idk publish`, your agent installs this repo at that moment — the
transport arrives exactly when a finished cycle wants to cross.

To install it explicitly, send one message to your Hermes agent:

> Clone `https://github.com/5qln/Idk-commons` into `~/idk-commons`, run
> `bash ~/idk-commons/setup.sh`, then load the `trail-commons` skill. If any
> check fails, stop and show me the output — don't work around it.

Or by hand:

```bash
git clone https://github.com/5qln/Idk-commons.git
cd Idk-commons && bash setup.sh
```

`setup.sh` checks the prerequisites (python3, git), runs the membrane
self-test, and installs the one skill into your Hermes agent
(`~/.hermes/skills`; if your `HERMES_HOME` lives elsewhere, run
`HERMES_SKILLS=$HERMES_HOME/skills bash setup.sh`).

The self-test is a **refusal gate**, not a formality: setup refuses to
install a gate that fails to catch private content. A refusal is a stop, not
an obstacle to route around.

The commons repo itself is never installed — the tool clones
[5qln/questions](https://github.com/5qln/questions) on its own at the first
`discover` or `publish`.

## What a published question looks like

```markdown
---
spdx: CC0-1.0
content_hash: sha256:<64 hex chars>
---

# <the question that opened the cycle>

*Published to the Question Commons. CC0 — public domain. Make it yours.*

## ∞0' — The Return Question

<the question that could not have been asked before>

---

*Originated from an /idk creative cycle. The trail is private. The question is yours.*
```

The file is named for the SHA-256 of its own question text and stored under a
two-level fan-out (`questions/<aa>/<bb>/<hash>.md`). If two people arrive at
the same question, they land on the same file — that convergence is the whole
point, and it is reported as arrival, never as conflict.

## The commons of record

Published questions live at
**[github.com/5qln/questions](https://github.com/5qln/questions)** — that
repo, not this one, is the commons. The `questions/` directory here carries a
copy of the seed questions as the gate's own CI fixtures: the membrane lint
refuses to pass an empty or missing commons (fail-closed, guarding against
silent deletion), so this repo keeps a small sharded set for its gate and
tests to run against.

## The three repositories

One membrane, three repos — each holds one part and only that part:

| Repo | Role |
| --- | --- |
| [5qln/Idk](https://github.com/5qln/Idk) | **The practice.** `/idk` — the gate-enforced cycle a human walks with an agent. Trails stay there, private. |
| [5qln/Idk-commons](https://github.com/5qln/Idk-commons) | **The transport.** This repo — strips, gates, and carries X and ∞0' after the human attests. |
| [5qln/questions](https://github.com/5qln/questions) | **The commons of record.** Questions only, CC0, no authors. |

For the full picture — how a question moves through all three and what never
crosses the membrane — see [`SYSTEM.md`](https://github.com/5qln/Idk/blob/main/SYSTEM.md).
Maintaining this repo? Read [`AGENTS.md`](AGENTS.md) first.

## Naming

Three names show up around the commons. They are not one thing said three
ways — they name three different layers, and each is used deliberately:

- **The Question Commons** — the *product*: the public, CC0 collection of
  questions, published at [`5qln/questions`](https://github.com/5qln/questions).
  It is what you join.
- **trail-commons** — the *tool*: the agent-side skill in
  `skills/trail-commons/` (plus the shared membrane gate) that strips a finished
  `/idk` cycle down to its two public questions and delivers them to the
  commons. The name describes the job — it carries the public residue of a
  private **trail** into the **commons**. It is what you install.
- **Idk-commons** — the *repository*: this repo, which ships that tool. It is
  where the tool lives.

Product, tool, repo. Nothing to reconcile.

## License

Everything here is dedicated to the public domain under
[CC0 1.0](LICENSE) — the tool, and every question it carries. You may copy,
modify, build upon, and republish any of it, for any purpose, without asking.
Make it yours.

---

*Form only. Never life. The trail is private. The question is yours.*
