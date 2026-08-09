# Route Receipt — v0.1 (draft, open)

A small, provider-agnostic receipt schema for x402 APIs. Goal: an agent should be able
to pay any provider and get back the **same shaped** receipt — comparable across providers,
verifiable without turning each `402` into a custom parser.

This is an open proposal, not an authority-blessed standard. `nodescorecard.xyz` is the
reference implementation. Anyone may adopt it; feedback welcome.

---

## 1. The quote (what the `402` advertises)

An agent needs to compare routes before paying. Each `402` response lists `accepts[]`,
one entry per payable route, with these comparable fields:

| field | meaning |
| --- | --- |
| `scheme` | payment scheme, e.g. `exact` |
| `network` | chain in CAIP-2, e.g. `eip155:8453`, `solana:5eykt4…`, `sui:mainnet` |
| `asset` | token identifier on that chain (contract / mint / coin-type) |
| `maxAmountRequired` | atomic amount (string) the route will charge at most |
| `payTo` | recipient address on that chain |
| `maxTimeoutSeconds` | how long the quote is valid |

A provider MAY expose the same list at a stable discovery path (`/manifest`,
`/.well-known/x402`) so agents can plan before hitting the endpoint.

## 2. Unsupported-network refusal (fail-closed)

If an agent tries to pay on a network the provider does not accept, the provider MUST
refuse **fail-closed** — never silently succeed or 500. Documented shape:

```json
{ "error": "unsupported_network", "network": "eip155:1", "accepted": ["eip155:8453","solana:5eykt4…","sui:mainnet"] }
```

So the agent immediately knows to pick another route rather than debugging a stall.

## 3. The Route Receipt (after payment)

Retrievable at `GET /receipt/{requestId}` (deterministic, idempotent). Shape:

```json
{
  "version": 1,
  "requestId": "req_…",                       // globally unique at the resource server
  "route":   { "resource": "https://…/scorecard/nodes", "method": "GET" },
  "selected":{ "network": "eip155:8453", "asset": "0x8335…", "amount": "5000" },
  "requirementHash": "…",                      // sha-256 of the chosen quote (network,asset,amount,payTo,scheme)
  "resultHash": "…",                           // sha-256 of the exact bytes served
  "hashAlgorithm": "sha-256",
  "canonicalization": "JCS/RFC8785",
  "settlement": {
    "tx": "0x… | sig…",                        // on-chain settlement reference
    "finalitySource": "eip155:8453:finalized | solana:finalized | sui:checkpoint",
    "status": "settled"                        // settled | pending | rejected | not_found
  },
  "terminalState": "settled",                  // derived from ON-CHAIN FINALITY, not facilitator ack
  "ts": 1723200000000,
  "receiptUrl": "https://…/receipt/req_…"
}
```

### Field rules
- **`requestId`** is unique at the resource server (not scoped to network+payer), so a
  multi-network retry dedups to the same receipt.
- **`requirementHash`** binds the receipt to the exact quote, so a retry can't resolve a
  *different* quote after the fact.
- **`resultHash`** is computed over the **unchanged** response body, canonicalized with
  JCS (RFC 8785) then SHA-256. The bytes you pay for are the bytes you get.
- **`terminalState` / `settlement.status`** are derived from **on-chain finality**, not
  from the facilitator's `/settle` acknowledgement — this closes the duplicate-settle race
  (a facilitator can ack twice; finality is observed once). Values:
  `settled` · `pending` · `rejected` · `not_found`.
- Unknown `requestId` → `404` with `{ "requestId": "…", "terminalState": "not_found" }`.

## 4. How an agent verifies (no trust in the server)

1. Recompute `resultHash` from the bytes it received (JCS canonical → SHA-256) and compare
   to `receipt.resultHash`. Mismatch → the data was altered; reject.
2. Check `terminalState === "settled"` (and `settlement.tx` present).
3. Check `requirementHash` matches the quote it actually paid.

All three pass → the agent has cryptographic proof it paid for, and received, exactly
these bytes on exactly this route. Fail-closed on any missing field.

## 5. Cross-chain note

The schema is chain-agnostic: `network`/`asset`/`finalitySource` carry the chain-specific
detail, everything else is uniform. An agent comparing an EVM, a Solana and a Sui provider
reads the **same** receipt shape from each.

---

*Reference implementation: nodescorecard.xyz (`/receipt/{requestId}`). v0.1 — subject to
change with community input.*
