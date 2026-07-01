# The Question Commons

A public, CC0 collection of **questions** — and only questions.

Each file here is one question that opened a creative cycle, paired with the
question that cycle could not have asked before it began. Nothing else. No
answers, no authors, no analysis, no identities. Just questions, offered into
the public domain for anyone to pick up and start from.

> One person's published question becomes another person's starting point.
> The work that connects them stays private. Only the questions are public.

## What a question looks like

```markdown
---
spdx: CC0-1.0
content_hash: sha256:<64 hex chars>
---

# <the question that opened the cycle>

*Published to the Question Commons. CC0 — public domain. Make it yours.*

## ∞0' — The Return Question

<the question that could not have been asked before>
```

The file is named for the SHA-256 of its own question text and stored under a
two-level fan-out (`questions/<aa>/<bb>/<hash>.md`). If two people arrive at the
same question, they land on the same file — that convergence is the whole point.

## The membrane

These questions come from `/idk` creative cycles. A cycle touches far more than
its question — a seed, raw material, a turn, a direction, an artifact — and all
of that is **private** and never appears here. Only the question (**X**) and the
return question (**∞0'**) cross.

This is enforced, not requested. Every file is checked by
[`skills/trail-commons/membrane_lint.py`](skills/trail-commons/membrane_lint.py) in CI on every push and pull
request. A file carrying any private marker — or whose name does not match its
own content hash — fails the gate and cannot be merged.

## How questions get here

You do not need an account. Joining the commons is installing the tool.

- **[trail-commons](https://github.com/5qln/Idk-commons)** is the agent-side
  tool that strips a finished cycle down to its two public questions, signs the
  result with an ephemeral identity, and — only after the human has seen the
  exact bytes and agreed — delivers it here, either as a direct push (for those
  with write access) or as an anonymous `git bundle` a maintainer ingests.
- Or, by hand: fork this repo, add a question in the format above at its
  fan-out path, and open a pull request. CI runs the membrane gate on it.

## License

Every question here is dedicated to the public domain under
[CC0 1.0](LICENSE). You may copy, modify, build upon, and republish any of it,
for any purpose, without asking. Make it yours.

---

*The trail is private. The question is yours.*
