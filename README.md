# Node Scorecard

**Real reliability scoring for Sentinel dVPN nodes.**

A transparent, open-source tool that scores any Sentinel dVPN node on the signals
that actually matter — live on-chain status, heartbeat margin, historical uptime,
stability, and a network-wide leaderboard.

🔗 **Live tool:** https://superpios.github.io/node-scorecard/

---

## Why it exists

dVPN apps pick which nodes to put in their subscription plans from the public node
list — but there's **no transparent tool** that tells an operator *why* their node is
or isn't reliable, or that helps apps tell solid nodes from flaky ones at a glance.

Existing monitors say "your node is up/down right now." None of them score a node's
**reputation over time**. Node Scorecard fills that gap: same metrics, same criteria,
visible to everyone.

## What it does

**🔴 Live snapshot** — paste any `sentnode1...` address and get an instant 0–100 score
from on-chain data: active status, heartbeat margin vs the 60-min window, advertised
address, payment tokens, and a live reachability check. Includes a plain-language
diagnosis and a copy-paste report for Telegram / GitHub issues.

**📊 Historical score** — feed it the history collected by the companion collector and
see real uptime %, stability (active⇄inactive flips), bandwidth trend, and an uptime
timeline. This is the reliability that apps actually care about.

**🏆 Leaderboard** — a network-wide ranking of all nodes, filterable by country and
sortable by score, uptime, or bandwidth. Auto-loads fresh data when published.

## How the scoring works

**Live (100 pts):** on-chain status (35) · heartbeat margin (30) · external
reachability (25) · payment tokens (10).

**Historical:** uptime % (60%) · stability (30%) · bandwidth availability (10%).

Bands: **85+** reliable · **65–84** good · **45–64** unstable · **<45** at risk.

## The collector

`collector.py` runs on your node (or any always-on machine) and samples the network
on a schedule, building the history that powers the Historical and Leaderboard views.

```bash
python3 collector.py --add sentnode1...   # track a specific node
python3 collector.py --all                # sample the whole network
python3 collector.py --report             # print an uptime summary
python3 collector.py --export-latest      # write latest.json for the web tool
```

Run it hourly via cron to accumulate real uptime history:

```cron
0 * * * * /usr/bin/python3 ~/scorecard/collector.py --all >> ~/scorecard/collector.log 2>&1
```

## Honest limitations

- The **live reachability** check can fail from a browser due to CORS/TLS even when the
  node is perfectly reachable — it's shown as "unverified," not as a fault.
- **Historical** metrics need a few days of collected samples to be meaningful.
- Many nodes don't expose live bandwidth via their API, so that field is often "n/d."

## Tech

Single-file HTML/JS (no build, no dependencies) + a small Python collector. Reads
public data from `lcd.sentinel.co` and node APIs. Host it anywhere static — GitHub
Pages works great.

## License

MIT — free to use, modify, and share.

---

*Community tool, not officially affiliated with Sentinel.*
