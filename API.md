# Node Scorecard — Public API

The Scorecard's data is served as static JSON over GitHub Pages. CORS is open
(`Access-Control-Allow-Origin: *`), so you can call these endpoints from any
browser app, backend, script, or AI agent. No key, no auth, no rate limit
beyond GitHub's generous CDN.

> Context: the official `api.health.sentinel.co/v1/records` has been down for a
> long time. These endpoints cover node status, reliability history and network
> intelligence, collected independently by sampling the whole Sentinel network
> on a schedule.

## Endpoints

### 1. Current network snapshot

    GET https://superpios.github.io/node-scorecard/latest.json

Updated **every hour**. Array of ~9000 node objects (all nodes ever seen;
filter by `status` for active ones).

| Field | Type | Meaning |
|---|---|---|
| `ts` | string (ISO) | When this node was last sampled |
| `addr` | string | Node address (`sentnode1...`) — primary key |
| `status` | string | `active` or `inactive` (on-chain status) |
| `inactive_at` | string/null | On-chain heartbeat deadline |
| `remote` | string/null | Public endpoint `IP:port` of the node API |
| `moniker` | string/null | Operator-set name |
| `dl_mbps` / `ul_mbps` | number/null | Last reported speedtest |
| `api_ok` | bool | Node API reachable from the collector |
| `gb_tokens` | number | Accepted payment denoms (0–3) |
| `price_hr` / `price_gb` | number/null | Price in P2P per hour / per GB |
| `protocol` | string/null | `v2ray`, `wireguard`, `openvpn` |
| `peers` | number/null | Connected clients at sample time |
| `version` | string/null | Node software version |
| `country` / `city` | string/null | IP geolocation |
| `asn` | string/null | Hosting network, e.g. `AS24940 Hetzner` |
| `hosting` | bool/null | true = datacenter, false = residential |

Example — active German WireGuard nodes:

```js
const nodes = await (await fetch(
  "https://superpios.github.io/node-scorecard/latest.json")).json();
const de = nodes.filter(n =>
  n.status === "active" && n.country === "Germany" && n.protocol === "wireguard");
```

### 2. Reliability history

    GET https://superpios.github.io/node-scorecard/history-summary.json

Updated **every hour**. Array of per-node reliability summaries computed from
weeks of continuous hourly sampling.

| Field | Type | Meaning |
|---|---|---|
| `a` | string | Node address — join key with `latest.json` `addr` |
| `mon` | string | Moniker (or address if unnamed) |
| `n` | number | Samples collected (track record length) |
| `uptime` | number | % of samples the node was active |
| `trans` | number | Active/inactive transitions (flaps) |
| `stab` | number | Stability 0–100 (100 = never flapped) |
| `ul` | number/null | Median upload Mbps |
| `country` | string/null | Country |
| `sc` | number | Composite reliability score 0–100 |
| `tl` | string | Uptime timeline, one char per sample (`1`=up `0`=down) |
| `tl_from` / `tl_to` | string | Timeline window |
| `stale` | bool | true = not seen for >24h |
| `age_h` | number | Hours since last seen |
| `p_pos` | number/null | % of recent samples with peers > 0 |
| `p_avg` | number/null | Average peers when present |
| `l_pos` | number/null | % of recent days holding an on-chain lease |
| `l_now` | number/null | Simultaneous on-chain leases right now |

### 3. Network trends over time

    GET https://superpios.github.io/node-scorecard/trends.json

Object with:
- `series` — hourly snapshots. Each: `ts`, `total`, `active`, `stale`,
  `api_ok`, `asn` (per-ASN node counts), `country` (per-country node counts)
- `movers_up` / `movers_down` — nodes whose 7-day uptime is improving or
  declining. Each: `a` (address), `mon` (moniker), `d7` (recent uptime %),
  `prev` (prior uptime %), `delta`
- `generated` — when the file was built

## Joining the two datasets

`latest.json` tells you who is good **now**; `history-summary.json` tells you
who has been reliable **over time**. Join on address:

```js
const [latest, hist] = await Promise.all([
  fetch("https://superpios.github.io/node-scorecard/latest.json").then(r=>r.json()),
  fetch("https://superpios.github.io/node-scorecard/history-summary.json").then(r=>r.json()),
]);
const H = Object.fromEntries(hist.map(h => [h.a, h]));
const reliable = latest.filter(n =>
  n.status === "active" && H[n.addr] && !H[n.addr].stale &&
  H[n.addr].uptime >= 90 && H[n.addr].stab >= 80 && H[n.addr].n >= 12);
```

This is exactly what the
[sentinel-connection-planner](https://github.com/superpios/sentinel-connection-planner)
does — use it directly if you want ready-made node selection with censorship-aware
protocol strategy and live verification.

## Data collection & honesty notes

- Collector samples the whole network on a fixed schedule from independent
  infrastructure; scores are computed from measurements, not self-reports.
- Geolocation and ASN come from IP lookups and can be imperfect.
- A node missing from history is new or unmeasured, not necessarily bad.
- Data is provided as-is for research and operational use.

## Fair use

Free for any use. If you build something on it, a link back to
`https://superpios.github.io/node-scorecard` is appreciated. For issues or
field requests, open an issue on the repo.
