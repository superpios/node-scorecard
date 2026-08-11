# Route Receipt fixtures

Executable checks for the Route Receipt spec — so the spec is testable, not just prose.

## Profile check

```
node ../verify-receipt.mjs receipt.valid.json           served.json   # -> ACCEPT
node ../verify-receipt.mjs receipt.unknown-profile.json served.json   # -> REJECT (unknown canonicalization profile)
```

`receipt.unknown-profile.json` is identical to `receipt.valid.json` except its
`canonicalization` field. Restoring the exact profile (`jcs-strings-v0.2`) makes it pass:
the verifier fails loudly on an unknown profile instead of hashing with its own canonicalizer.

## Drift over time (runtime contract)

The same receipt passes before its `stale_at`, rejects after, and passes again only with a
renewed quote (a fresh `stale_at`). Freshness is a runtime contract, not a one-off parser trick.
`--now` lets you evaluate the verifier at a fixed instant.

```
node ../verify-receipt.mjs receipt.drift.json         served.json --now 2026-08-11T15:00:00Z  # -> ACCEPT (before stale_at)
node ../verify-receipt.mjs receipt.drift.json         served.json --now 2026-08-11T17:00:00Z  # -> REJECT (expired)
node ../verify-receipt.mjs receipt.drift-renewed.json served.json --now 2026-08-11T17:00:00Z  # -> ACCEPT (renewed quote)
```
