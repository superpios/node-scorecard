# Sentinel Node Scorecard

**Network intelligence & historical diagnostics for [Sentinel dVPN](https://sentinel.co) nodes.**

Most node explorers (SentNodes, suchnode, the official explorer) show you a *snapshot*: is the node active right now, what's its price, how many peers. Useful — but they can't tell you the thing that actually matters to a node operator: **how has this node behaved over time, and how does it compare to the rest of the network?**

The Scorecard fills that gap. It samples every node on the network on a schedule, builds a historical record, and turns it into an actionable score, a country ranking, and a node-by-node diagnostic — the data the other tools don't give you.

---

## What it does

### 🗺️ Network Explorer
The whole network at a glance. Every node, sortable and filterable by:
- **Score** (computed with real variance — see below)
- **Status** (active / inactive)
- **Protocol** (V2Ray / WireGuard / OpenVPN)
- **Price** (P2P/hr and P2P/GB)
- **Peers**, **historical uptime %**, **country / city**

Search by moniker, address or city. Click any node to open it in the Inspector.

### 🔬 Node Inspector
Deep-dive a single node — paste an address or click one from the Explorer:
- **Historical uptime timeline** — a visual active/inactive bar for every sample collected over time
- **Measured uptime %** and **stability** (how often it flaps offline)
- **Country ranking** — *"#12 of 47 in Italy"*, not a meaningless absolute number
- **Detected problems** — rule-based diagnostics (inactive, low uptime, unstable, API unreachable, stale heartbeat, zero peers)
- **Score breakdown** — how each weighted component contributes
- **Generate support report** — a ready-to-paste summary for the Sentinel support Telegram / a GitHub issue, so a node's problems actually reach the people who can help

---

## The score

A 0–100 score built to have **real variance** (no more "everyone gets 90"):

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

Everything runs on a single always-on device (e.g. a Raspberry Pi). No server, no database, no cost.

```
collector.py     → samples every node from the Sentinel LCD (status, price, protocol,
                    peers, bandwidth) on an hourly cron, appends to history.jsonl
make-summary.py  → aggregates history.jsonl into history-summary.json
                    (uptime %, stability, longevity + a compact per-node timeline)
push-latest.sh   → publishes latest.json + history-summary.json to this repo
index.html       → static UI, fetches the two JSON files and renders everything
                    client-side (no backend)
```

The UI is a single static HTML file — host it on GitHub Pages or any static host. It reads the published JSON directly.

---

## Data sources & honest limits

- **Prices, status, heartbeat** come from the Sentinel LCD and are available for **every** node.
- **Protocol, peers, bandwidth, version** come from each node's local API — available only for nodes that expose it publicly, so these fields are blank for unreachable nodes. This is a limit of public data, not a bug.
- **Historical metrics** improve the longer the collector runs. A fresh install needs a few days of samples before uptime/timeline are meaningful.

---

## Setup

```bash
# on the always-on device
git clone https://github.com/superpios/node-scorecard   # or download the scripts
cd node-scorecard

# first manual run (takes ~10 min for the full network)
python3 collector.py --all
python3 make-summary.py

# schedule hourly collection (crontab -e)
0 * * * * /usr/bin/python3 /path/to/collector.py --all >> collector.log 2>&1
```

Then publish `latest.json` and `history-summary.json` to the repo (see `push-latest.sh`) and open `index.html`.

---

## Roadmap

- On-chain earnings trend per node
- Multi-network support (agnostic core — Sentinel first, others later)
- Alerting hooks for operators
- Integration with the Sentinel Scout / AI data layer

---

*Built by a node operator, for node operators. Not affiliated with the Sentinel Foundation.*
