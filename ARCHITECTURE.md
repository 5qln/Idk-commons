# Architecture

How the trail-commons transport layer is built, and — just as important —
what was deliberately left out.

This document shows the reasoning. If the reasoning is right, the verbs and the
gate follow from it almost mechanically. If something here is wrong, it is
cheaper to find it now, in prose, than later, in a published question that
cannot be recalled.

---

## 1. The one idea

A finished `/idk` cycle leaves a residue that is safe to share: the question it
opened (**X**) and the question it could not have asked before (**∞0'**).
Everything else the cycle touched — the seed α, the raw material, the click Z,
the direction ∇, the artifact B'' — is the private certificate of authentic
inquiry. It never leaves the machine.

So the transport problem is small and sharp:

> Move **X** and **∞0'** to other people, prove nothing private went with them,
> and do it without building anything that needs to be trusted, funded, or run.

That last clause rules out almost everything one might reach for. No server (it
would have an owner, an IP, an uptime bill). No accounts (they are identity, and
identity is the thing we are protecting). No tokens, no blockchain, no consensus
(a question is not a coin; there is nothing to double-spend). What is left is the
one decentralized, content-addressed, signature-bearing, already-installed
network on every developer's machine: **git**.

Git is the network. Questions are the payload. trail-commons is the thin gate
between a private cycle and that public network.

---

## 2. The membrane, enforced three times

Only X and ∞0' are public. The membrane sits at X|α: the question crosses, the
seed does not. This is the system's central claim, so it is not left to
discipline. It is checked **three times**, in three different trust domains:

1. **Client preview** (`publish`, no `--confirm`). The exact bytes are built and
   gated locally; the human reads them and attests before anything moves.
2. **Steward ingest** (`ingest`). A submitted bundle is never trusted. The gate
   re-runs on every question it carries, server-side.
3. **Commons CI** (`skills/trail-commons/membrane_lint.py`, run by GitHub Actions on
   every changed file). Even a direct push by someone with write access is
   gated before it can land.

A private marker has to defeat all three to reach the public commons. The gate
is a denylist of phase symbols and footer fields (`α`, `{α'}`, `Z:`, `∇`,
`B''`, `φ ⋂ Ω`, `δE`, `δV`, the Codex seal hash, gate-machine JSON, cycle
numbers) plus a positive-form requirement (a real X heading, a CC0 dedication,
a content hash, an ∞0'). It judges **form only**. It cannot tell whether a
question is alive — only whether the bytes are clean. That is why step 1 exists:
the human judges meaning; the machine judges form.

### What the gate cannot do, stated plainly

The gate strips structure. It does not anonymize **voice**. A distinctive way of
phrasing a question, repeated across several published questions, can correlate
them to one author by stylometry alone — no name required. trail-commons
**discloses** this on every preview and refuses to pretend otherwise; it never
silently edits the text, because a silent edit hides what leaked. Stylometric
defense is the human's judgment, informed but not automated. (A future,
opt-in paraphrase pass could raise this floor. It is not in the MVP, because a
paraphrase that changed the question's meaning would be worse than the leak.)

---

## 3. The five open questions, answered

These were the open decisions in the brief. Here is where each one landed, and
why.

### Q1 — Who can push to the commons?

**Answer: nobody needs to. Transport is pluggable, and the anonymous default
needs no write access at all.**

A shared write key in a public repo is a non-answer: GitHub detects and revokes
committed secrets automatically, and a key everyone holds authenticates no one.
So there are two backends instead:

- **`bundle` (default).** The question is committed in a throwaway repo and
  exported as a `git bundle` — a single file carrying a `refs/heads/incoming`
  ref. The human submits that file to a steward through any channel (email,
  paste, dead drop). No account, no key, no server, no link back. This is the
  most anonymous path and the MVP default.
- **`push`.** For a steward, or for someone publishing to their **own** mirror:
  a direct commit-and-push, for whoever legitimately holds write access.

The steward closes the loop with **`ingest`**, which re-runs the membrane gate
on the bundle and merges only clean questions. The end state — most
decentralized of all — is **fork + steward-merge**: anyone forks `questions`,
adds their file, opens a pull request; CI gates it; a maintainer merges. No
privileged client, no shared secret, GitHub's own review as the trust layer.

### Q2 — What if two people surface the same question?

**Answer: they land on the same file, and that is treated as a signal, not a
collision.**

The filename is `sha256(normalize(X))`, where `normalize` is NFC + trim +
internal-whitespace-collapse. Two people who arrive at the same question — no
matter how they spaced or wrapped it — produce identical bytes at an identical
path. Git deduplicates this for free: the second add is a no-op. trail-commons
surfaces it as `already_present` with a deliberate framing: *the question is
alive in more than one person.* Convergence is the propagation signal the
commons exists to reveal, so it is reported as arrival, never as conflict.

### Q3 — Public id: content hash, or cycle number?

**Answer: content hash. Cycle numbers never cross the membrane.**

This is the sharpest privacy decision in the design. A cycle number is
sequential and per-author: questions tagged `cycle: 39`, `cycle: 40`, `cycle:
41` are trivially linked to one person walking one sequence — exactly the
linkage ephemeral authorship exists to break. So the public file carries **no
cycle number** (the gate forbids it by pattern) and **no author**. The content
hash is the only identifier: it is deterministic, collision-addressing (see Q2),
and reveals nothing about who, when, or in what order.

> **Flagged divergence from the brief's file format.** The brief's example
> frontmatter showed `cycle:` and `date:` fields. trail-commons omits `cycle:`
> entirely (a deanonymization vector) and makes `date:` **optional and off by
> default** (`privacy.include_date`). A day-level date plus a writing voice can
> still correlate questions over time; the commons never depends on the field
> for discovery — git commit order does that — so omitting it costs nothing and
> protects the author. Set `include_date: true` to match the documented format
> exactly. This divergence is raised here, and in the config, on purpose: it is
> the one place the implementation chose the brief's stated *priority* (privacy,
> ephemeral authorship) over the brief's example *format*.

### Q4 — How does the commons cold-start?

**Answer: the steward seeds it, and an empty commons says so gracefully.**

The bootstrap repo `github.com/5qln/Questions` ships a README, the CC0 license,
the CI gate, and a small number of seed questions in the fan-out layout, so the
very first `discover` returns something to sit with. When a commons is genuinely
empty, `discover` does not error — it returns a quiet note: *the commons is
quiet; yours could be the first.* The cold-start path is a first-class state,
not an edge case.

### Q5 — What happens as the commons grows?

**Answer: two-level hash fan-out, and discovery by commit range, not by full
scan.**

Files are sharded `questions/<aa>/<bb>/<hash>.md` — the same trick git uses for
its own object store, which scales to millions of objects while keeping any one
directory small. `discover` records the last-seen commit and asks git for the
diff since then (a shallow clone keeps history bounded), so the cost of
discovery is proportional to *what is new*, not to the size of the commons.
Should the single-repo model ever strain, the remotes list is plural and the
repo is forkable: the commons can shard across repositories without any client
change.

---

## 4. Privacy posture, in full

What protects the author, layer by layer:

- **Ephemeral git identity, per publish.** Every commit is authored as
  `trail-commons <anon@commons.idk>` via `GIT_AUTHOR_*` / `GIT_COMMITTER_*`
  environment variables — set on the command, so the machine's global git
  identity is never touched and a commit can never silently fall back to the
  real author. (A stable pen name is available via `pseudonymous` mode; it is a
  deliberately weaker choice, and labeled as such.)
- **Coarsened commit time.** Timestamps are flattened to midnight UTC of the
  publish day by default (`commit_time: date`), or to a fixed constant for
  everyone (`epoch`). Exact times are a correlation vector; `exact` exists but
  is not recommended.
- **No identifiers in the artifact.** No cycle number, no author, no date by
  default. Just the two questions and a hash.
- **Human attestation before transmission.** Nothing leaves on the first
  command. The two-step publish exists so a person sees the exact bytes and says
  yes before they enter the public domain under CC0.
- **Tor, optional.** Git can be routed over a local SOCKS5 proxy to hide the
  author's IP from the remote. It is documented, not required, and it protects
  the *connection*, never the *content* — the gate does that.

What this does **not** defend against, said once more because it matters:
stylometry. The gate cannot launder a voice. The preview says so every time.

---

## 5. What was deliberately left out

- **A server / API.** It would have an owner and a single point of failure and
  control. Git already federates.
- **Accounts and keys.** Identity is the asset under protection. Joining is
  installing; there is nothing to sign up for.
- **A token / ledger / consensus mechanism.** There is no scarcity to enforce
  and no global order to agree on. A question is not a coin.
- **Automatic anonymization of voice.** A paraphrase strong enough to defeat
  stylometry is strong enough to change the question. Disclosure beats silent
  rewriting.
- **A live feed / engagement loop.** `discover` lists what is new and stops.
  The commons is a place to find a question to hold, not a stream to consume —
  the same restraint the cycle itself is built on.

Form only. Never life. Only the question travels. The trail is yours.

## Known limitations

**DNS resolution under Tor.** When `tor: true`, HTTPS remotes are proxied with
`ALL_PROXY=socks5h://127.0.0.1:9050` — the `h` means the remote hostname is
resolved *through* Tor, so there is no DNS leak on that path. The SSH transport,
however, tunnels via `nc -X 5 -x 127.0.0.1:9050`, and whether the hostname is
resolved locally or by the proxy depends on the `netcat` implementation on the
host; some resolve locally, which leaks the remote's DNS query outside Tor. If
anonymity of the *destination* matters, use an HTTPS or `.onion` remote (which
forces resolution through Tor) and verify with a DNS-leak test before relying on
it. This is a documented limitation, not an MVP guarantee.
