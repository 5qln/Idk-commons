# Security Policy

trail-commons moves questions across a privacy membrane. Its security properties
are: (1) no private content from an /idk cycle (α, Z, ∇, B″, the Codex seal,
cycle numbers, identities) may cross into the commons, and (2) the client gate,
the bundle-ingest gate, and the commons-CI gate must agree. A leak, or a way to
bypass any gate, is a security issue.

## Reporting

Email **security@5qln.com** with the repository, commit, and a description or
proof-of-concept. Please do **not** open a public issue for a suspected leak.

- Acknowledgement within **3 business days**.
- Coordinated disclosure; we agree a date before any public note.

## Scope notes

`membrane-spec.json` is the shared source of truth for the forbidden markers and
Codex hash; it is kept byte-identical with the `Questions` repository. The Tor
transport has a documented DNS-resolution limitation on the SSH path — see
`ARCHITECTURE.md` → Known limitations.
