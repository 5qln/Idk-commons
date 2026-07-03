# AGENTS.md — working *on* `trail-commons`

> For an AI agent modifying, extending, or maintaining **this repository**.
> This is not the file that publishes a question. If a human ran `/idk publish`,
> load [`skills/trail-commons/SKILL.md`](skills/trail-commons) instead.

Two different jobs, don't confuse them:

| Job | You are… | Load |
| --- | --- | --- |
| **Carry a question out** | running `publish` / `discover` / `browse` / `ingest` | `skills/trail-commons/` |
| **Maintain the repo** | editing the gate, the skill, docs, tests | **this file** |

---

## What this repo is

`Idk-commons` ships **trail-commons**, the transport layer of the Question
Commons: the tool that carries **X** and **∞0′** — and nothing else — from a
finished `/idk` cycle into the public commons, over git, only after a human sees
the exact bytes and attests. One repo of three; see [`SYSTEM.md`](https://github.com/5qln/Idk/blob/main/SYSTEM.md).

Read [`ARCHITECTURE.md`](ARCHITECTURE.md) first. It records the five design
decisions (who can push, hash vs. cycle number, cold start, growth, dedup) and
the privacy posture in full. Most changes here have a privacy consequence — the
architecture doc is where that reasoning lives.

## The hard rules

1. **The gate is sacred, and it is form-only.** The membrane gate is a denylist
   of private phase symbols/footer fields plus a positive-form requirement. It
   judges **bytes, never life** — it can tell if content is clean, never if a
   question is alive. Do not add "smart" semantic judgement to it; that is the
   human's job at the preview step.

2. **`membrane-spec.json` is a shared, sealed contract.** It must stay
   **byte-identical** with the copy in [`5qln/questions`](https://github.com/5qln/questions).
   A change here MUST land in both repos in lockstep; the pinned-SHA sync test
   exists to stop them drifting. Never edit one side alone.

3. **Never weaken the three-times enforcement.** The membrane is checked in three
   trust domains — client preview, steward ingest, commons CI. Do not collapse
   these into one, and never make `publish` a single step: nothing may leave on
   the first command. The two-step attestation is load-bearing, not friction.

4. **Never silently edit a human's question text.** The gate strips *structure*;
   it must not paraphrase *voice*. If content leaks stylometrically, the tool
   **discloses** — it never quietly rewrites, because a silent edit hides the
   leak. (An opt-in paraphrase pass is a possible future; it is not the default,
   and it must never change a question's meaning.)

5. **Protect anonymity by construction.** Ephemeral git identity per publish,
   coarsened commit time, no cycle number / author / date by default. Any change
   that could attach identity to an outgoing question is a regression — treat it
   as one.

## Layout

| Path | What it is | Touch it when… |
| --- | --- | --- |
| `skills/trail-commons/` | the one skill: the three verbs + `ingest` / `selftest` | changing transport behavior |
| `skills/trail-commons/membrane_lint.py` | the gate | changing form checks (mirror in `questions`) |
| `membrane-spec.json` | shared sealed contract | **only** together with `questions` |
| `setup.sh` | prereq check + self-test + skill install | changing install (self-test is a refusal gate — keep it) |
| `tests/` | membrane + client tests | always, with any behavior change |

## Conventions

- **Python: stdlib only**, no server, no accounts, no tokens. Git is the network.
  If a change reaches for any of those, it contradicts the architecture — stop
  and check with the human (see `ARCHITECTURE.md` §5, "left out").
- **`setup.sh` self-test is a refusal gate.** If it fails, install refuses. Never
  route around a refusal; surface it.
- **Voice**: spare, precise, privacy-first. Match the existing docs.

## Before you finish

```bash
bash setup.sh                     # runs the membrane self-test (refusal gate)
python3 -m pytest -q              # membrane + client tests pass
```

Confirm `membrane-spec.json` still matches `questions` byte-for-byte and the
sync test passes. Reconcile any cross-repo wording against
[`SYSTEM.md`](https://github.com/5qln/Idk/blob/main/SYSTEM.md).

---

*Form only. Never life. Only the question travels. The trail is yours.*
