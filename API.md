# Node Scorecard — API

Node snapshots and scores are served only by the paid API:

    https://nodescorecard.xyz

GitHub Pages no longer publishes `latest.json`, `history-summary.json`,
`trends.json`, `latest-akash.json`, or `latest-akash-trends.json`. Those files
remain on the collector host for the paid API. They are not a public endpoint.

There is no API key and no account. A call to a paid route returns `402 Payment
Required`. The agent pays in USDC over x402 (version 2) and retries the same
request. Failed requests (HTTP >= 400) are not settled. Prices and routes below
match the live service. This document does not change them.

<!-- STATS:BEGIN -->
<!-- generated hourly by update-stats.py — do not edit by hand -->

Latest snapshot: **4,341 nodes tracked**, **1,846 active**, **1,811** of those with a responding API. Those 1,811 span **247 autonomous systems**, and **272** (15.0%) pass verified-residential checks (geo-IP flag *and* a non-hosting ASN).

<!-- STATS:END -->

## Paid endpoints

| Endpoint | Price | Returns |
|---|---|---|
| `GET /scorecard/network-stats` | $0.010 | Network-wide health report |
| `GET /scorecard/recommend` | $0.010 | Ranked recommendations for a stated need |
| `GET /scorecard/nodes` | $0.005 | Node snapshot |
| `GET /scorecard/nodes/top` | $0.005 | Top nodes by composite score |
| `GET /scorecard/node/:address` | $0.003 | Single node scorecard |

Base URL: `https://nodescorecard.xyz`

Chains, pay-to addresses, query parameters, and receipt verification are
documented in [README.md](README.md#paid-api-for-ai-agents-x402) and by the live
discovery documents:

| Endpoint | Returns |
|---|---|
| `GET /` | Documentation. HTML for browsers, JSON for agents, Markdown with `Accept: text/markdown` |
| `GET /manifest` | Machine-readable service manifest |
| `GET /openapi.json` | OpenAPI 3.1 description with `x-x402` price extensions |
| `GET /llms.txt` | Plain-text summary for LLM crawlers |
| `GET /auth.md` | How agent authentication works |
| `GET /.well-known/api-catalog` | RFC 9727 catalog |
| `GET /scorecard/health` | Liveness and configuration |
| `GET /developers` | Developer quickstart |
| `GET /about` | About this service |
| `GET /privacy` | Privacy notes |

Those discovery routes do not return node snapshots or scores.

Probe a paid route first. The `402` response carries the price:

```bash
curl -s -D - -o /dev/null https://nodescorecard.xyz/scorecard/network-stats
```

## Collector files (not public)

`collector.py`, `make-summary.py`, `make-trends.py`, and `make-akash-trends.py`
still write their JSON on the machine that runs them. `make-trends.py` does not
upload `trends.json`. Do not put these files back on `main`:

- `latest.json`
- `history-summary.json`
- `trends.json`
- `latest-akash.json`
- `latest-akash-trends.json`

The Express server that serves `nodescorecard.xyz` is not in this repository.
Inferred edits for its free MCP tools and docs are in [SERVER_CHANGES.md](SERVER_CHANGES.md).
