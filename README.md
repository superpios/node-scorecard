# Sentinel Node Scorecard

**Network intelligence & historical diagnostics for Sentinel dVPN nodes.**

The Scorecard answers the question that matters most to a node operator: **how has my node behaved over time, and how does it compare to the rest of the network?**

It samples every node on the Sentinel network on a schedule, builds a historical record measured in hundreds of thousands of samples, and turns it into an actionable reliability score, a country ranking, time-series trends, and a node-by-node diagnostic. Those results stay on the collector and are served by the paid API. The GitHub Pages site does not render them.
## Data access

Node snapshots and scores are not published from this repository. GitHub Pages
does not serve them. Agents and apps get that data only from the paid API:

    https://nodescorecard.xyz

Prices, routes, and the x402 payment flow: **[API.md](API.md)** and the [Paid API](#paid-api-for-ai-agents-x402) section below.

<!-- STATS:BEGIN -->
<!-- generated hourly by update-stats.py — do not edit by hand -->

Latest snapshot: **4,081 nodes tracked**, **1,804 active**, **1,772** of those with a responding API. Those 1,772 span **252 autonomous systems**, and **285** (16.1%) pass verified-residential checks (geo-IP flag *and* a non-hosting ASN).

<!-- STATS:END -->

## What it does

### 🗺️ Network Explorer
The whole network at a glance. Every node, sortable and filterable by:

- **Score** (computed with real variance — see below)
- **Status** (active / inactive) — inactive nodes hidden by default, toggle to show
- **Protocol** (V2Ray / WireGuard / OpenVPN / Xray-REALITY / AmneziaWG / Hysteria2) — each carries an **anti-censorship level** derived from the protocol
- **Price** (P2P/hr and P2P/GB)
- **Peers**, historical **uptime %**, **country / city**
- **ASN / hosting provider** — which network each node runs on, with saturation flags

Search by moniker, address or city. Click any node to open its full diagnostic inline.

### 🔬 Node diagnostic
Click any node (or paste an address) to deep-dive:

- **Historical uptime timeline** — a visual active/inactive bar for every sample collected over time
- **Measured uptime %** and **stability** (how often it flaps offline)
- **Country ranking** — "#12 of 47 in Italy", not a meaningless absolute number
- **Detected problems** — 16 rule-based diagnostics: inactive, low uptime, unstable, API unreachable, stale heartbeat, zero peers, price outliers (per hr **and** per GB vs the SLA limit — 50 P2P/hr, 40 P2P/GB), very low bandwidth, outdated version, saturated ASN, crowded country, young node, missing speedtest — plus a **historical uptime trend** check (declining / recovering, computed from the node's own timeline), a **lease check** that catches the most frustrating case — a perfectly healthy node that gets *no client traffic* because it isn't whitelisted for plans (peers ≈ 0 across recent history) — and an **elite badge** for top-20 ranked nodes
- **Reliability grade** — an A+/A/B/C/D/E letter from the historical score, with a global rank ("#12 of 1,594 active nodes")
- **Anti-censorship level** — derived objectively from the node's protocol: **High** (Xray/REALITY — anti-active-probing, resists state-level censorship), **Medium** (AmneziaWG / Hysteria2 — obfuscated transport, evades DPI), **Basic** (V2Ray — encrypted but detectable) or **Minimal** (WireGuard / OpenVPN — recognizable & blockable). Surfaced as a badge so operators and privacy-focused users can pick censorship-resistant nodes at a glance
- **Score breakdown** — how each weighted component contributes
- **Generate support report** — a ready-to-paste summary for the Sentinel support Telegram or a GitHub issue, so a node's problems actually reach the people who can help

### 💬 NodeAdvisor — community feedback
The data tells you how a node *behaves*; NodeAdvisor tells you how it *feels to use*. On any node, anyone can leave structured feedback:

- **Quick tags** — positive (fast, stable, good uptime, good value, connects first try) and negative (drops often, high latency, slow, hard to reach)
- **Optional comment** (up to 500 chars)
- **Aggregated view** — feedback is shown as tag counts ("12 · fast connection · 3 · high latency"), not a single falsifiable star rating
- **Light anti-abuse** — one vote per node per browser, plus server-side de-duplication. Not bulletproof (nothing browser-side is), but it keeps casual self-voting down, and comments can be moderated.

Feedback is stored in a free Supabase table read directly from the static page — still no server of your own to run.

### 🌐 ASN Intelligence — "Where to host"
A dedicated view for deciding **where to put a new node**: it groups active nodes by hosting provider (ASN), counts how many run on each, and flags the saturated ones — and now tells you, honestly, *which providers are even worth considering*.

- **Per-ASN node counts & saturation flags** — ASNs over the PlanWizard whitelist limit are marked `SATURATED`; nodes there rarely get leased
- **Least crowded vs most crowded** — every country below the free-slot threshold, ranked, so you can spot genuine opportunities
- **Lease %** per ASN — not just how many nodes, but how many are *actually earning* a lease there
- **Provider honesty badges** — recommended hosts (verified on their official site) get a direct link; **major clouds** (AWS, Oracle, Alibaba…) carry a *may-not-be-whitelisted* warning per the Sentinel docs; **national ISPs / telecoms** are flagged as *not a hosting provider*; everything else is marked *unverified — check before use*. "Free slots" no longer misleads you toward a phone company or a reseller
- **Lease uptime (historical)** — for each node, the % of the last 7 days it actually held an on-chain lease — the real "am I earning?" signal, distinct from a one-off snapshot
- **Hosting column + diagnostic** — every node shows its ASN in the table, and a node on a saturated ASN gets a clear warning in its diagnostic ("may not get leased/earn")
- **Pick a clean ASN** — low-count, non-saturated providers are the smart choice for a new node
- **Clickable ASN drill-down** — search a country or provider, then click any ASN box to instantly see every node running on it, ranked by score

This turns a painful, learned-the-hard-way lesson (datacenter ASNs like IONOS, Oracle and OVH are saturated; residential ASNs are not) into something you can *see* before spending a cent. The same view doubles as a **node placement advisor**: search an ASN or a country and get an instant verdict (⛔ saturated / ⚠️ filling up / ✅ room available) with capacity-used %, plus the least- and most-crowded countries.

### 🏆 Top Reliable
The 25 most reliable active nodes ranked by **historical** uptime, stability and track record — not by who happens to be online right now. A node only ranks here by being consistently up across many samples.

### 📈 Trends — the network over time
The Scorecard records a snapshot of the network every hour and shows how it **moves over time**:

- **Network Pulse** — active-node count over time
- **ASNs gaining / losing nodes** — watch providers fill up or empty out (IONOS went 285 → 188 active nodes in two days; this view catches that)
- **Node movers** — nodes whose 7-day uptime improved or declined the most vs their own history

### Official SLA test results

Every hour the collector merges the results of Sentinel's **official SLA test runs**
([test.sentinel.co](https://test.sentinel.co)): a real tunnel is opened through each
node and its actual speed is measured - the strongest possible signal that a node
**actually serves clients**, not just that its API answers.

Each tested node carries four extra fields in the collector's local snapshot (kept on the device, not published):

| field | meaning |
|---|---|
| `sla_pass` | `true` if the official test opened a working tunnel |
| `sla_mbps` | measured real throughput |
| `sla_baseline` | tester's baseline speed for comparison |
| `sla_err` | error code when the test failed (`TIMEOUT`, `OTHER`, ...) |

In the UI: an **SLA pass/fail badge** next to each node's status, a dedicated row in
the node inspector, and a diagnostics warning when a node failed its last official
test. Nodes not included in the latest run simply have no SLA fields (untested is
not the same as failed).

## The score

A 0–100 score built to have real variance (no more "everyone gets 90"):

| Component | Weight | Source |
|-----------|--------|--------|
| Uptime | 32% | measured % active over collected history |
| Longevity | 25% | history samples / network max (proven track record) |
| Stability | 15% | penalizes frequent active↔inactive flips |
| Freshness | 13% | recency of the on-chain heartbeat |
| API health | 10% | node API reachable + active on-chain |
| Payment tokens | 5% | number of accepted denoms |

New nodes start lower on longevity and climb as they build a track record — exactly how trust works.

---

## Architecture

Everything runs on a single always-on device (e.g. a Raspberry Pi). The collector writes local files there. A separate process on that device serves the paid API. GitHub Pages hosts only the static page.

```
collector.py     -> samples every node from the Sentinel LCD (status, price, protocol,
                    peers, bandwidth), appends to history.jsonl. Retries each node's
                    API twice to minimise blank fields from transient timeouts.
                    Enriches active nodes with their ASN (IP->ASN lookup, cached on
                    disk so each IP is resolved only once).
make-summary.py  -> aggregates history.jsonl into a local history-summary.json (uptime %,
                    stability, longevity + a compact per-node timeline). Soft-purges
                    nodes not seen for 30+ days to keep the files lean. Not published.
make-trends.py   -> appends a network snapshot per run (active count, per-ASN and
                    per-country totals) and computes node movers (7d uptime vs prior)
                    from raw history. Writes local trends.json only. Does not upload it.
index.html       -> static page on GitHub Pages. It does not fetch or render node
                    snapshots. Community feedback (NodeAdvisor) is read/written
                    directly to a free Supabase table from the browser.
```

The collector files (`latest.json`, `history-summary.json`, `trends.json`, `latest-akash.json`, `latest-akash-trends.json`, and the `*.jsonl` logs) stay on the device that runs the collector. They are the input the paid API reads. They are gitignored and excluded from the GitHub Pages build. Do not upload them with `push-latest.sh` or any other GitHub Contents API script.

The UI is a single static HTML file on GitHub Pages. The only external dependency is a free Supabase project for NodeAdvisor feedback (optional).

---

## API / Data access (for developers & white-label apps)

Node snapshots and scores are served only by the paid API at
[`https://nodescorecard.xyz`](https://nodescorecard.xyz). There is no public JSON
snapshot on GitHub Pages. Field lists, prices, and call examples are in
**[API.md](API.md)** and in the [Paid API](#paid-api-for-ai-agents-x402) section below.

### Community feedback (NodeAdvisor)
Feedback is stored in Supabase and is **readable** via its auto-generated REST API (read policy only). Example — fetch visible feedback for one node:

```
GET https://<project>.supabase.co/rest/v1/node_feedback?node_addr=eq.<addr>&hidden=eq.false&select=tags,comment,created_at
Header: apikey: <publishable-key>
```

Feedback **writing** goes through the web UI, which applies anti-abuse measures (one vote per device, de-duplication). Writing directly via API bypasses those, so it isn't documented here by design. NodeAdvisor comments are community notes, not the scorecard snapshot.

### Notes for integrators
- Paid responses refresh from an hourly collector snapshot and are cached for 10 minutes.
- Fields can be `null` for nodes whose API was unreachable at sample time — handle nulls gracefully.
- This is a community project; endpoints may evolve. Open an issue if you build on it and need stability guarantees.

---

## Data sources & honest limits

- **test.sentinel.co** - official Sentinel SLA runs, merged hourly into the local collector snapshot (fields `sla_*`). That snapshot is not published.

- **Prices, status, heartbeat** come from the Sentinel LCD and are available for **every** node.
- **Protocol, peers, bandwidth, version** come from each node's local API — available only for nodes that expose it publicly, so these fields are blank for unreachable nodes (roughly half the network at any moment). This is a limit of public data, not a bug.
- **Historical metrics improve the longer the collector runs.** A fresh install needs a few days of samples before uptime/timeline are meaningful.
- The diagnostic's optional **live peer fetch** hits a node's API directly from your browser; nodes use self-signed certs, so most browsers block it and the value falls back to the last collector reading. Expected behaviour, not an error.

---

## Setup

```bash
# on the always-on device
git clone https://github.com/superpios/node-scorecard   # or download the scripts
cd node-scorecard

# first manual run (takes ~10 min for the full network)
python3 collector.py --all
python3 make-summary.py

# schedule collection (crontab -e) - every 2 hours
# Do not append push-latest.sh or any script that uploads JSON to this repo.
0 */2 * * * /usr/bin/python3 /path/to/collector.py --all >> collector.log 2>&1 && \
            /usr/bin/python3 /path/to/make-summary.py >> collector.log 2>&1 && \
            /usr/bin/python3 /path/to/make-trends.py >> collector.log 2>&1

```

Leave `latest.json`, `history-summary.json`, and `trends.json` on the device. The paid API reads them there. Do not commit or upload them.

---

## Roadmap

- Public snapshot files were removed from GitHub Pages. Data access is the paid API (see API section)
- ✅ ASN intelligence — per-provider saturation + placement advisor (done)
- ✅ Reliability grade + global rank, Top Reliable leaderboard (done)
- ✅ Trends — network time series, ASN movers, node movers (done — accumulating history)
- ✅ "Where to host" — provider honesty badges, lease %, per-country opportunity (done)
- ✅ Multi-protocol awareness + anti-censorship level per node (done — V2Ray/WireGuard/OpenVPN/Xray-REALITY/AmneziaWG/Hysteria2)
- ✅ Multi-protocol collector: per-protocol peer counts from the v9+ node API, with legacy fallback (done)
- ✅ Granular API failure reasons (`api_status`) instead of a single ok/failed flag (done)
- ✅ Verified-residential detection: geo-IP hosting flag cross-checked against the ASN (done — the flag alone over-reports by ~3.4x)
- ✅ Paid x402 API for AI agents, pay-per-call in USDC on Base (done — see Paid API section)
- On-chain earnings trend per node → ROI calculator (opt-in, by wallet)
- Objective ASN classification via PeeringDB (hosting / ISP / enterprise)
- Clean versioned API endpoint with developer-friendly field names
- Multi-network support (agnostic core - Sentinel first, others later)
- Alerting hooks for operators

---

## Ecosystem

Friends & complementary tools: [BlueFrens Hub](https://hub.bluefrens.xyz) · [SentNodes](https://sentnodes.com) · [SuchNode](https://nodes.suchnode.net) · [p2pscan](https://p2pscan.com) · [stats.sentinel.co](https://stats.sentinel.co)

Also by the same operator: **[Node Dash](https://superpios.github.io/sentinel-node-dash/)** — an arcade game that teaches how the Sentinel network actually works.

---

*Built by a node operator, for node operators. Not affiliated with the Sentinel Foundation.*

### Paid API for AI agents (x402)

**Live at [`https://nodescorecard.xyz`](https://nodescorecard.xyz)**

The Node Scorecard data is available as a machine-payable HTTP API. There is no
account, no API key, no sign-up and no OAuth. An agent calls an endpoint, receives
`402 Payment Required`, signs a USDC payment on one of the five chains, retries, and gets the data.

Requests that fail (HTTP >= 400) are never settled — errors are not charged.

| | |
|---|---|
| Base URL | `https://nodescorecard.xyz` |
| Protocol | x402 v2, scheme `exact` |
| Chains | **Base**, **Polygon**, **Arbitrum**, **Avalanche** and **Solana** — the `402` lists all five, the agent picks one |
| Base | `eip155:8453` · USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| Polygon | `eip155:137` · USDC `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359` |
| Arbitrum | `eip155:42161` · USDC `0xaf88d065e77c8cC2239327C5EDb3A432268e5831` |
| Avalanche | `eip155:43114` · USDC `0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E` |
| Solana | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` · USDC `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |
| Facilitator | `https://facilitator.payai.network` |

On Solana the facilitator sponsors the transaction fee, so an agent needs USDC
only — no SOL.

#### Verifiable receipts

Every paid response carries an `X-Receipt-Id` header. `GET /receipt/{requestId}`
returns a receipt binding the payment to a SHA-256 hash (JCS/RFC-8785 canonical) of
the exact bytes served — the bytes you pay for are the bytes you get. Verify by
recomputing the hash from the response you received; no trust in the server required.

#### Provider trends (Akash)

Akash provider snapshots are archived hourly, so every provider carries a history the
upstream console does not expose. `make-akash-trends.py` writes a local
`latest-akash-trends.json` (per provider: score, uptime and free-GPU series with
direction and delta). That file stays on the collector. It is not committed and
GitHub Pages does not serve it. The paid API serves it:
`/scorecard/node/:id?network=akash` returns a `trends` block for that provider,
and `/scorecard/network-stats?network=akash` returns `trends_summary` with how
many providers are improving or declining.

#### Networks

Scoring is multi-network: pass `network=akash` to the node endpoints for independently scored Akash DePIN compute providers (GPU availability, uptime, audit), online-only and ranked.

The receipt format is published as an open, provider-agnostic spec — see [route-receipt-spec.md](route-receipt-spec.md) — with an independent offline verifier ([verify-receipt.mjs](verify-receipt.mjs)) that recomputes the hash from the served bytes and rejects an expired quote, altered bytes, or an unknown canonicalization profile without calling back to the server. Every receipt declares a versioned canonicalization profile (`jcs-strings-v0.2`) so two agents reach the same verdict from the receipt alone.

#### Free discovery endpoints

No payment, no headers, nothing required.

| Endpoint | Returns |
|---|---|
| `GET /` | Documentation. HTML for browsers, JSON for agents, Markdown with `Accept: text/markdown` |
| `GET /manifest` | Machine-readable service manifest |
| `GET /openapi.json` | OpenAPI 3.1 description with `x-x402` price extensions |
| `GET /llms.txt` | Plain-text summary for LLM crawlers |
| `GET /auth.md` | How agent authentication works |
| `GET /.well-known/api-catalog` | RFC 9727 catalog (`application/linkset+json`) |
| `GET /.well-known/agent-skills/index.json` | Agent Skills discovery index |
| `GET /scorecard/health` | Liveness and configuration |
| `POST /mcp` | **Model Context Protocol server** — see below |
| `GET /.well-known/mcp/server-card.json` | MCP server card |

#### Paid endpoints

| Endpoint | Price | Returns |
|---|---|---|
| `GET /scorecard/network-stats` | $0.010 | Network-wide health report |
| `GET /scorecard/recommend` | $0.010 | Ranked recommendations for a stated need |
| `GET /scorecard/nodes` | $0.005 | Full node snapshot |
| `GET /scorecard/nodes/top` | $0.005 | Top nodes by composite score |
| `GET /scorecard/node/:address` | $0.003 | Single node scorecard |

##### `GET /scorecard/network-stats` — $0.010

No parameters. Returns ASN concentration and HHI index, verified residential share,
protocol mix, censorship-resistance mix, country distribution, SLA speed percentiles
and P2P price percentiles, measured from a live snapshot.

##### `GET /scorecard/recommend` — $0.010

| Parameter | Type | Default | Description |
|---|---|---|---|
| `need` | string | — | Free text, e.g. `privacy residential` or `speed europe`. Case-insensitive. |
| `country` | string | any | Restrict candidates to one country, exact name, case-insensitive. |

Returns one recommendation plus up to three alternatives, diversified across ASNs
and countries so the result is not concentrated on a single provider.

##### `GET /scorecard/nodes` — $0.005

| Parameter | Type | Default | Description |
|---|---|---|---|
| `all` | `1` | — | Return every tracked node instead of only the active ones. |

##### `GET /scorecard/nodes/top` — $0.005

| Parameter | Type | Default | Description |
|---|---|---|---|
| `n` | integer | `5` | How many nodes to return. Clamped to 1–50. |
| `max_per_asn` | integer | `2` | Anti-concentration cap: max nodes sharing one ASN. |
| `min_score` | number | `0` | Minimum composite score, 0–100. |
| `country` | string | — | Exact country name, case-insensitive. |
| `protocol` | string | — | `v2ray`, `wireguard`, `xray`, `openvpn`, `hysteria2`, `amneziawg`. Also matches multi-protocol nodes. |
| `sla_only` | `true` | — | Only nodes that passed the SLA speed test. |

`max_per_asn=1` guarantees every returned node sits on a different autonomous
system. This is the parameter that matters for real redundancy: without it, a
"top 10" list can be ten nodes inside the same datacenter.

```
GET /scorecard/nodes/top?n=10&sla_only=true&min_score=80&max_per_asn=1
```

##### `GET /scorecard/node/:address` — $0.003

Full scorecard for one node, addressed by its `sentnode1...` bech32 address.
No query parameters.

#### MCP server

`https://nodescorecard.xyz/mcp` is a stateless Streamable HTTP MCP endpoint
(`2026-07-28` and `2025-11-25`). It must not return node snapshots or scores
without the same x402 payment as the paid routes above. The Express server that
implements it is not in this repository. The inferred edits are in
[SERVER_CHANGES.md](SERVER_CHANGES.md).

#### Calling it

Probe first — this costs nothing and tells you the exact price:

```bash
curl -s -D - -o /dev/null https://nodescorecard.xyz/scorecard/network-stats
```

You get `402 Payment Required` and a `PAYMENT-REQUIRED` header containing
base64-encoded JSON with `payTo`, `network`, `amount`, `asset` and
`maxTimeoutSeconds`. Decode it, sign with your wallet, and retry the identical
request with the `PAYMENT` header.

Any x402 v2 client library handles this automatically. With
[`@x402/fetch`](https://www.npmjs.com/package/@x402/fetch):

```js
import { wrapFetchWithPayment } from '@x402/fetch';

const fetchWithPay = wrapFetchWithPayment(fetch, wallet);

const res = await fetchWithPay(
  'https://nodescorecard.xyz/scorecard/nodes/top?n=5&sla_only=true&max_per_asn=1'
);
const { nodes } = await res.json();
```

#### Where the data comes from

An independent collector polls every active node's API directly and cross-checks
on-chain state. Nothing here is self-reported by node operators. The snapshot is
refreshed hourly; API responses are cached for 10 minutes.

The service runs on a residential Raspberry Pi behind a Cloudflare Tunnel, with
no inbound ports open and the origin address never exposed. The process that
serves paid requests holds no private keys: settlement is delegated to a remote
facilitator, and only the public receiving address is configured.

`https://nodescorecard.xyz` is the canonical origin. The x402 payload served there
advertises that URL as the resource, and the parameters documented above are the
ones implemented by it.
