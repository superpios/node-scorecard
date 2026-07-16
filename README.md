# Sentinel Node Scorecard

**Network intelligence & historical diagnostics for Sentinel dVPN nodes.**

The Scorecard answers the question that matters most to a node operator: **how has my node behaved over time, and how does it compare to the rest of the network?**

It samples every node on the Sentinel network on a schedule, builds a historical record measured in hundreds of thousands of samples, and turns it into an actionable reliability score, a country ranking, time-series trends, and a node-by-node diagnostic â€” all from data collected on-device, with no backend.
## Public API

All Scorecard data is available as free JSON endpoints (CORS open, no key,
updated hourly):

    https://superpios.github.io/node-scorecard/latest.json           # current snapshot, ~9000 nodes
    https://superpios.github.io/node-scorecard/history-summary.json  # reliability history per node
    https://superpios.github.io/node-scorecard/trends.json           # network trends over time

Full field-by-field documentation, examples and join patterns: **[API.md](API.md)**
---

## What it does

### ðŸ—ºï¸ Network Explorer
The whole network at a glance. Every node, sortable and filterable by:

- **Score** (computed with real variance â€” see below)
- **Status** (active / inactive) â€” inactive nodes hidden by default, toggle to show
- **Protocol** (V2Ray / WireGuard / OpenVPN / Xray-REALITY / AmneziaWG / Hysteria2) â€” each carries an **anti-censorship level** derived from the protocol
- **Price** (P2P/hr and P2P/GB)
- **Peers**, historical **uptime %**, **country / city**
- **ASN / hosting provider** â€” which network each node runs on, with saturation flags

Search by moniker, address or city. Click any node to open its full diagnostic inline.

### ðŸ”¬ Node diagnostic
Click any node (or paste an address) to deep-dive:

- **Historical uptime timeline** â€” a visual active/inactive bar for every sample collected over time
- **Measured uptime %** and **stability** (how often it flaps offline)
- **Country ranking** â€” "#12 of 47 in Italy", not a meaningless absolute number
- **Detected problems** â€” 16 rule-based diagnostics: inactive, low uptime, unstable, API unreachable, stale heartbeat, zero peers, price outliers (per hr **and** per GB vs network median), very low bandwidth, outdated version, saturated ASN, crowded country, young node, missing speedtest â€” plus a **historical uptime trend** check (declining / recovering, computed from the node's own timeline), a **lease check** that catches the most frustrating case â€” a perfectly healthy node that gets *no client traffic* because it isn't whitelisted for plans (peers â‰ˆ 0 across recent history) â€” and an **elite badge** for top-20 ranked nodes
- **Reliability grade** â€” an A+/A/B/C/D/E letter from the historical score, with a global rank ("#12 of 1,594 active nodes")
- **Anti-censorship level** â€” derived objectively from the node's protocol: **High** (Xray/REALITY â€” anti-active-probing, resists state-level censorship), **Medium** (AmneziaWG / Hysteria2 â€” obfuscated transport, evades DPI), **Basic** (V2Ray â€” encrypted but detectable) or **Minimal** (WireGuard / OpenVPN â€” recognizable & blockable). Surfaced as a badge so operators and privacy-focused users can pick censorship-resistant nodes at a glance
- **Score breakdown** â€” how each weighted component contributes
- **Generate support report** â€” a ready-to-paste summary for the Sentinel support Telegram or a GitHub issue, so a node's problems actually reach the people who can help

### ðŸ’¬ NodeAdvisor â€” community feedback
The data tells you how a node *behaves*; NodeAdvisor tells you how it *feels to use*. On any node, anyone can leave structured feedback:

- **Quick tags** â€” positive (fast, stable, good uptime, good value, connects first try) and negative (drops often, high latency, slow, hard to reach)
- **Optional comment** (up to 500 chars)
- **Aggregated view** â€” feedback is shown as tag counts ("12 Â· fast connection Â· 3 Â· high latency"), not a single falsifiable star rating
- **Light anti-abuse** â€” one vote per node per browser, plus server-side de-duplication. Not bulletproof (nothing browser-side is), but it keeps casual self-voting down, and comments can be moderated.

Feedback is stored in a free Supabase table read directly from the static page â€” still no server of your own to run.

### ðŸŒ ASN Intelligence â€” "Where to host"
A dedicated view for deciding **where to put a new node**: it groups active nodes by hosting provider (ASN), counts how many run on each, and flags the saturated ones â€” and now tells you, honestly, *which providers are even worth considering*.

- **Per-ASN node counts & saturation flags** â€” ASNs over the PlanWizard whitelist limit are marked `SATURATED`; nodes there rarely get leased
- **Least crowded vs most crowded** â€” every country below the free-slot threshold, ranked, so you can spot genuine opportunities
- **Lease %** per ASN â€” not just how many nodes, but how many are *actually earning* a lease there
- **Provider honesty badges** â€” recommended hosts (verified on their official site) get a direct link; **major clouds** (AWS, Oracle, Alibabaâ€¦) carry a *may-not-be-whitelisted* warning per the Sentinel docs; **national ISPs / telecoms** are flagged as *not a hosting provider*; everything else is marked *unverified â€” check before use*. "Free slots" no longer misleads you toward a phone company or a reseller
- **Lease uptime (historical)** â€” for each node, the % of the last 7 days it actually held an on-chain lease â€” the real "am I earning?" signal, distinct from a one-off snapshot
- **Hosting column + diagnostic** â€” every node shows its ASN in the table, and a node on a saturated ASN gets a clear warning in its diagnostic ("may not get leased/earn")
- **Pick a clean ASN** â€” low-count, non-saturated providers are the smart choice for a new node
- **Clickable ASN drill-down** â€” search a country or provider, then click any ASN box to instantly see every node running on it, ranked by score

This turns a painful, learned-the-hard-way lesson (datacenter ASNs like IONOS, Oracle and OVH are saturated; residential ASNs are not) into something you can *see* before spending a cent. The same view doubles as a **node placement advisor**: search an ASN or a country and get an instant verdict (â›” saturated / âš ï¸ filling up / âœ… room available) with capacity-used %, plus the least- and most-crowded countries.

### ðŸ† Top Reliable
The 25 most reliable active nodes ranked by **historical** uptime, stability and track record â€” not by who happens to be online right now. A node only ranks here by being consistently up across many samples.

### ðŸ“ˆ Trends â€” the network over time
The Scorecard records a snapshot of the network every 2 hours and shows how it **moves over time**:

- **Network Pulse** â€” active-node count over time
- **ASNs gaining / losing nodes** â€” watch providers fill up or empty out (IONOS went 285 â†’ 188 active nodes in two days; this view catches that)
- **Node movers** â€” nodes whose 7-day uptime improved or declined the most vs their own history

### ðŸ§Š Time Capsule â€” on Walrus (Sui)
The Scorecard's historical snapshot is archived on **Walrus**, the decentralized storage protocol on Sui. Each capsule is an immutable, content-addressed blob with a verifiable hash and a public link shown in the Trends tab. The history of a decentralized VPN, stored on decentralized storage.

The Scorecard itself is also published as a **Walrus Site** â€” the static page lives on Walrus, fully decentralized, with no central server hosting it. A planned next step is integrating **Walrus Memory** to give an AI agent persistent, verifiable memory of node history â€” an assistant that remembers how the network and individual nodes have behaved over time.

---

### Official SLA test results

Every hour the collector merges the results of Sentinel's **official SLA test runs**
([test.sentinel.co](https://test.sentinel.co)): a real tunnel is opened through each
node and its actual speed is measured - the strongest possible signal that a node
**actually serves clients**, not just that its API answers.

Each tested node carries four extra fields in `latest.json`:

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

A 0â€“100 score built to have real variance (no more "everyone gets 90"):

| Component | Weight | Source |
|-----------|--------|--------|
| Uptime | 32% | measured % active over collected history |
| Longevity | 25% | history samples / network max (proven track record) |
| Stability | 15% | penalizes frequent activeâ†”inactive flips |
| Freshness | 13% | recency of the on-chain heartbeat |
| API health | 10% | node API reachable + active on-chain |
| Payment tokens | 5% | number of accepted denoms |

New nodes start lower on longevity and climb as they build a track record â€” exactly how trust works.

---

## Architecture

Everything runs on a single always-on device (e.g. a Raspberry Pi). No server, no database, no cost.

```
collector.py     -> samples every node from the Sentinel LCD (status, price, protocol,
                    peers, bandwidth), appends to history.jsonl. Retries each node's
                    API twice to minimise blank fields from transient timeouts.
                    Enriches active nodes with their ASN (IP->ASN lookup, cached on
                    disk so each IP is resolved only once).
make-summary.py  -> aggregates history.jsonl into history-summary.json (uptime %,
                    stability, longevity + a compact per-node timeline). Soft-purges
                    nodes not seen for 30+ days to keep the files lean.
make-trends.py   -> appends a network snapshot per run (active count, per-ASN and
                    per-country totals) and computes node movers (7d uptime vs prior)
                    from raw history. Writes + publishes trends.json.
walrus-capsule.py-> once a day, archives trends.json on Walrus and publishes
                    capsule.json with the blob ID, hash and verification link.
push-latest.sh   -> publishes latest.json + history-summary.json to this repo
index.html       -> static UI, fetches the two JSON files and renders everything
                    client-side. Community feedback (NodeAdvisor) is read/written
                    directly to a free Supabase table from the browser.
```

The UI is a single static HTML file â€” host it on GitHub Pages or any static host. It reads the published JSON directly. The only external dependency is a free Supabase project for NodeAdvisor feedback (optional â€” the rest works without it).

---

## API / Data access (for developers & white-label apps)

All Scorecard data is served as plain JSON over HTTPS â€” no key, no auth, no rate limit. White-label apps, dashboards, or bots can consume it directly. These are **read-only** endpoints.

### Per-node current snapshot â€” `latest.json`
The most recent sample of every node on the network.

```
GET https://superpios.github.io/node-scorecard/latest.json
```

Returns an array of node objects:

| Field | Type | Meaning |
|-------|------|---------|
| `addr` | string | Node address (`sentnode1â€¦`) |
| `moniker` | string\|null | Node name (null if its API didn't answer at sample time) |
| `status` | string | `active` / `inactive` (on-chain) |
| `ts` | string | ISO timestamp of this sample |
| `inactive_at` | string | On-chain heartbeat-expiry timestamp |
| `remote` | string\|null | Announced `host:port` |
| `protocol` | string\|null | `v2ray` / `wireguard` / `openvpn` / `xray` / `amneziawg` / `hysteria2` |
| `peers` | int\|null | Connected peers at sample time |
| `price_hr` / `price_gb` | number\|null | Price in P2P per hour / per GB |
| `dl_mbps` / `ul_mbps` | number\|null | Measured bandwidth |
| `version` | string\|null | Node software version |
| `country` / `city` | string\|null | Geolocation |
| `asn` | string\|null | Hosting ASN + provider (e.g. `AS8560 IONOS SE`); active nodes only |
| `gb_tokens` | int | Number of accepted payment denoms |
| `api_ok` | bool | Whether the node's API answered the collector |

### Per-node historical summary â€” `history-summary.json`
Aggregated history + a compact uptime timeline per node.

```
GET https://superpios.github.io/node-scorecard/history-summary.json
```

| Field | Type | Meaning |
|-------|------|---------|
| `a` | string | Node address |
| `mon` | string | Moniker (or address if unnamed) |
| `n` | int | Number of samples collected |
| `uptime` | number | % active across all samples |
| `stab` | number | Stability score (0â€“100) |
| `trans` | int | Count of activeâ†”inactive transitions |
| `ul` | number\|null | Average upload Mbps |
| `country` | string\|null | Country |
| `sc` | int | Rough composite score |
| `tl` | string | Compact timeline: `1`=active, `0`=inactive, oldestâ†’newest |
| `tl_from` / `tl_to` | string | Timeline start / end timestamps |
| `stale` | bool | Last sample older than 24h |
| `age_h` | number\|null | Hours since last sample |

> The on-page score uses a richer weighting than the `sc` field above; `sc` is a lightweight pre-computed approximation. To reproduce the full score, see the weights table under [The score](#the-score).

### Network time series â€” `trends.json`
One snapshot every ~3 hours: `{ts,total,active,stale,api_ok,asn:{...},country:{...}}` per point, plus `movers_up`/`movers_down` (nodes whose 7-day uptime changed most vs their prior history).

```
GET https://superpios.github.io/node-scorecard/trends.json
```

### Walrus archive index â€” `capsule.json`
The latest and last 30 daily Walrus capsules: `{date,blobId,sha256,bytes,url,network}`. Fetch the `url` to retrieve the archived snapshot from a Walrus aggregator and verify its `sha256`.

```
GET https://superpios.github.io/node-scorecard/capsule.json
```

### Community feedback (NodeAdvisor)
Feedback is stored in Supabase and is **readable** via its auto-generated REST API (read policy only). Example â€” fetch visible feedback for one node:

```
GET https://<project>.supabase.co/rest/v1/node_feedback?node_addr=eq.<addr>&hidden=eq.false&select=tags,comment,created_at
Header: apikey: <publishable-key>
```

Feedback **writing** goes through the web UI, which applies anti-abuse measures (one vote per device, de-duplication). Writing directly via API bypasses those, so it isn't documented here by design.

### Notes for integrators
- Data refreshes roughly every 2 hours; cache accordingly.
- Fields can be `null` for nodes whose API was unreachable at sample time (~half the network at any moment) â€” handle nulls gracefully.
- This is a community project; endpoints may evolve. Open an issue if you build on it and need stability guarantees.

---

## Data sources & honest limits

- **test.sentinel.co** - official Sentinel SLA runs, merged hourly into `latest.json` (fields `sla_*`).

- **Prices, status, heartbeat** come from the Sentinel LCD and are available for **every** node.
- **Protocol, peers, bandwidth, version** come from each node's local API â€” available only for nodes that expose it publicly, so these fields are blank for unreachable nodes (roughly half the network at any moment). This is a limit of public data, not a bug.
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
0 */2 * * * /usr/bin/python3 /path/to/collector.py --all >> collector.log 2>&1 && \
            /usr/bin/python3 /path/to/make-summary.py >> collector.log 2>&1 && \
            /usr/bin/python3 /path/to/make-trends.py >> collector.log 2>&1 && \
            /bin/bash /path/to/push-latest.sh >> collector.log 2>&1

# daily Walrus capsule (optional)
50 23 * * * /usr/bin/python3 /path/to/walrus-capsule.py >> capsule.log 2>&1
```

Then publish `latest.json` and `history-summary.json` to the repo (see `push-latest.sh`) and open `index.html`.

---

## Roadmap

- âœ… Public read-only JSON API (done â€” see API section)
- âœ… ASN intelligence â€” per-provider saturation + placement advisor (done)
- âœ… Reliability grade + global rank, Top Reliable leaderboard (done)
- âœ… Trends â€” network time series, ASN movers, node movers (done â€” accumulating history)
- âœ… Walrus Time Capsule on Sui (done)
- âœ… Published as a fully decentralized Walrus Site (done)
- âœ… "Where to host" â€” provider honesty badges, lease %, per-country opportunity (done)
- âœ… Multi-protocol awareness + anti-censorship level per node (done â€” V2Ray/WireGuard/OpenVPN/Xray-REALITY/AmneziaWG/Hysteria2)
- On-chain earnings trend per node â†’ ROI calculator (opt-in, by wallet)
- Objective ASN classification via PeeringDB (hosting / ISP / enterprise)
- Walrus Memory integration â€” persistent memory for an AI node-advisor agent
- Clean versioned API endpoint with developer-friendly field names
- Multi-network support (agnostic core - Sentinel first, others later)
- Alerting hooks for operators

---

## Ecosystem

Friends & complementary tools: [BlueFrens Hub](https://hub.bluefrens.xyz) Â· [SentNodes](https://sentnodes.com) Â· [SuchNode](https://nodes.suchnode.net) Â· [p2pscan](https://p2pscan.com) Â· [stats.sentinel.co](https://stats.sentinel.co)

---

*Built by a node operator, for node operators. Not affiliated with the Sentinel Foundation.*
