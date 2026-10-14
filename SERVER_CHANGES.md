# Server changes for nodescorecard.xyz

**Inferred. The Express/x402 server is not in this repository.**

Checked on 2026-10-14:

- This repo (`superpios/node-scorecard`) has the collector, the static Pages site, and the receipt verifier. It has no Express app, no x402 middleware, and no MCP handler.
- `gh repo list superpios` showed no other public repository that contains the API server. A code search for `sentinel_network_overview` was rate-limited, so a private repo is still possible. Nothing below was applied to a server tree, because there is no server tree here.

Do not change prices, paid route paths, or the x402 `402` payment flow. The paid routes stay:

| Route | Price |
|---|---|
| `GET /scorecard/network-stats` | $0.010 |
| `GET /scorecard/recommend` | $0.010 |
| `GET /scorecard/nodes` | $0.005 |
| `GET /scorecard/nodes/top` | $0.005 |
| `GET /scorecard/node/:address` | $0.003 |

Apply the edits on the Pi that runs the process behind `https://nodescorecard.xyz`, then restart that process. Commands at the bottom are the operational steps. The file paths are inferred from the live responses, not from a checkout.

## What is still free, and must stay

Keep these working and unpaid:

- `GET /scorecard/health`
- `GET /llms.txt`
- `GET /developers`
- `GET /about`
- `GET /privacy`
- Discovery: `GET /`, `GET /manifest`, `GET /openapi.json`, `GET /sitemap.xml`, `GET /auth.md`, `GET /.well-known/api-catalog`, `GET /.well-known/agent-skills/index.json`, `GET /.well-known/mcp/server-card.json`

Keep these agent-readiness behaviors. They were live on 2026-10-14:

- `Vary: Accept` on `/`, `/llms.txt`, `/developers`, `/about`, `/privacy`
- Homepage JSON-LD (`application/ld+json` with `SoftwareApplication` and `Organization`)
- `GET /` negotiates HTML, JSON (`Accept: application/json`), and Markdown (`Accept: text/markdown`)
- Markdown 404 for an unknown path, with links to the sitemap, `llms.txt`, OpenAPI, and `/developers`
- JSON 404 body containing `error.code`, `error.message`, `error.hint`, and `error.links`
- Sitemap lists `/developers`, `/about`, and `/privacy`
- `llms.txt` keeps a `## Quick links` section and a `## When to use this` section

`/developers`, fetched 2026-10-14 as HTML (it ignores `Accept` and returns `text/html`), does **not** contain `superpios.github.io/node-scorecard` or a "Free data" section. After the copy changes below, confirm it still does not.

`openapi.json`, fetched the same day, lists only `/scorecard/network-stats`, `/scorecard/recommend`, `/scorecard/nodes`, `/scorecard/nodes/top`, `/scorecard/node/{address}`, and `/scorecard/health`. It does not mention GitHub Pages or the three free MCP tools. Leave those paths and prices as they are. If any description string is generated from the same source as `llms.txt`, re-check the file after editing that source.

## Remove the free data copy

Observed `GET /llms.txt` (200, `text/plain`). Delete the whole `## Free vs Paid` block, including the blank heading and the two bullets that follow `## When to use this`. The live text is:

```
## Free vs Paid

## When to use this
- Use the paid API when an agent needs a ranked, anti-concentrated recommendation or a single-node scorecard with verifiable receipt before spending.
- Use the free GitHub Pages data for bulk exploration, historical analysis, or when no payment is desired.
- Prefer /scorecard/recommend or /scorecard/nodes/top over raw node lists when the goal is a decision.

- **Free data** (GitHub Pages): full hourly snapshots at https://superpios.github.io/node-scorecard/ — use for exploration and historical analysis.
- **Paid API** (this service): decision endpoints (recommend, top nodes with anti-concentration, verifiable receipts, Akash trends). Pay only for the call you need; errors are never charged.
```

Replace that region with:

```
## When to use this
- Use the paid API when an agent needs a ranked, anti-concentrated recommendation, a network report, or a single-node scorecard with a verifiable receipt.
- Prefer /scorecard/recommend or /scorecard/nodes/top over a raw node list when the goal is a decision.
- Node snapshots and scores are not available without payment.
```

Keep `## Quick links` as it is (Developers, OpenAPI, Auth, Sitemap, Health).

In `## Free endpoints`, this line currently advertises the free tools:

```
- POST /mcp - Model Context Protocol server (stateless, 2026-07-28 and 2025-11-25). Free tools: sentinel_network_overview, sentinel_node_lookup, sentinel_top_nodes.
```

Remove that line. Do not replace it with a free sample. The same sentence is rendered into:

- `GET /` HTML, inside `<h2>Free endpoints</h2>`
- `GET /` JSON (`Accept: application/json`), `free_endpoints` entry for `POST /mcp`
- `GET /` Markdown (`Accept: text/markdown`)
- `GET /manifest` (same JSON body and etag as `GET /` with `Accept: application/json` on 2026-10-14: `W/"1d9e-q7JDUSgHrKL0JaVuBBdpnl7uDu4"`)

`GET /` JSON also includes `chain_registry_example` with a live `active_on_chain` count (observed `1864` at `2026-10-14T08:09:59Z`). That is the number `sentinel_network_overview` exists to give away. Drop `chain_registry_example` from the unauthenticated homepage and manifest. The paid `GET /scorecard/network-stats` response can keep returning `chain_registry`.

`GET /about` HTML contains:

```html
<p>Free hourly snapshots of the full network are published at <a href="https://superpios.github.io/node-scorecard/">superpios.github.io/node-scorecard</a>.</p>
```

Delete that paragraph. The GitHub source link in the next paragraph can stay. It does not serve the snapshot.

`GET /privacy` HTML contains:

```html
<p>The free data published on GitHub Pages is public network measurement. Paid responses include a verifiable receipt so you can confirm the bytes you paid for are the bytes you received.</p>
```

Replace with a sentence that only mentions the paid receipt, for example: "Paid responses include a verifiable receipt so you can confirm the bytes you paid for are the bytes you received."

Search the server tree for `superpios.github.io/node-scorecard`, `Free data`, `Free vs Paid`, and `free GitHub Pages` and remove every remaining hit.

## Remove the free MCP tools

`POST /mcp` with `tools/list` returned HTTP 200 and these tools, with no `402`:

- `sentinel_network_overview`
- `sentinel_node_lookup` (requires `address`)
- `sentinel_top_nodes` (description says the free tier returns 3 nodes and cannot be filtered)

`GET /.well-known/mcp/server-card.json` lists the same three tools, and its `authentication.note` says "MCP tools are free and return a limited sample."

Remove all three tools from the tool registry and from the server card. `tools/list` must not return them. `tools/call` for those names must not return node status, location, uptime, speed, ASN stats, or scores. A JSON-RPC "unknown tool" error is enough. Do not add a new price and do not change the existing paid HTTP routes to make this work.

Leave the MCP endpoint able to answer protocol housekeeping (`initialize`, empty `tools/list`) if clients need discovery. It must not be a free data path.

## Pi commands

Inferred from this repo and from commit messages on `main` (`update latest.json`, `update history-summary.json`, `update trends.json`, `update latest-akash.json`, `update latest-akash-trends.json`). `push-latest.sh` is not in the repo. `make-trends.py` used to read a GitHub token out of that script and upload `trends.json`. An Akash publisher on the Pi uploads the two Akash files. `update-stats.py` only rewrites the `STATS` blocks in `README.md` and `API.md`.

On the Pi, from the collector checkout:

```bash
cd /path/to/node-scorecard
git pull origin main

# Stop the hourly GitHub uploads. Keep the local JSON; the paid API reads it.
crontab -l
# Edit the crontab so it no longer runs push-latest.sh or any Akash upload.
# Collection itself can stay, for example:
# 0 */2 * * * /usr/bin/python3 /path/to/collector.py --all >> collector.log 2>&1 && \
#             /usr/bin/python3 /path/to/make-summary.py >> collector.log 2>&1 && \
#             /usr/bin/python3 /path/to/make-trends.py >> collector.log 2>&1

# If the upload scripts are still on disk, disable them without deleting local data.
chmod -x push-latest.sh 2>/dev/null || true
# Find the Akash uploader (name is not in this repo) and disable it the same way.
grep -l -E 'latest-akash|api.github.com' ./*.sh ./*.py 2>/dev/null || true

# Confirm the paid server is a different process, then restart it after the copy/MCP edits.
# The unit name is not in this repo. Typical checks:
systemctl list-units --type=service | grep -Ei 'scorecard|x402|node'
# then, for whatever unit that is:
# sudo systemctl restart <that-unit>
```

`make-trends.py` in the pulled commit no longer uploads `trends.json`. If the Pi runs an old copy of that file, the pull is what stops the trends upload.

## Checks after the server restart

These must not return node snapshots or scores:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://superpios.github.io/node-scorecard/latest.json
curl -sS -o /dev/null -w '%{http_code}\n' https://superpios.github.io/node-scorecard/history-summary.json
curl -sS -o /dev/null -w '%{http_code}\n' https://superpios.github.io/node-scorecard/trends.json
curl -sS -o /dev/null -w '%{http_code}\n' https://superpios.github.io/node-scorecard/latest-akash.json
curl -sS -o /dev/null -w '%{http_code}\n' https://superpios.github.io/node-scorecard/latest-akash-trends.json
curl -sS -o /dev/null -w '%{http_code}\n' https://raw.githubusercontent.com/superpios/node-scorecard/main/latest.json

curl -sS https://nodescorecard.xyz/llms.txt | grep -E 'github.io/node-scorecard|Free data|Free vs Paid|sentinel_network_overview|sentinel_node_lookup|sentinel_top_nodes' && echo LEAK || echo 'llms.txt clean'

curl -sS https://nodescorecard.xyz/ | grep -E 'github.io/node-scorecard|Free data|sentinel_network_overview|sentinel_node_lookup|sentinel_top_nodes' && echo LEAK || echo 'homepage html clean'

curl -sS -H 'Accept: application/json' https://nodescorecard.xyz/ | grep -E 'github.io/node-scorecard|sentinel_network_overview|chain_registry_example' && echo LEAK || echo 'homepage json clean'

curl -sS https://nodescorecard.xyz/about | grep 'github.io/node-scorecard' && echo LEAK || echo 'about clean'
curl -sS https://nodescorecard.xyz/privacy | grep -i 'free data' && echo LEAK || echo 'privacy clean'
curl -sS https://nodescorecard.xyz/developers | grep -E 'github.io/node-scorecard|Free data' && echo LEAK || echo 'developers clean'

curl -sS -X POST https://nodescorecard.xyz/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: tools/list' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

curl -sS https://nodescorecard.xyz/.well-known/mcp/server-card.json
```

`tools/list` and the server card must not include the three removed tools. A paid route with no `PAYMENT` header must still return `402`, not a body of node data:

```bash
curl -sS -D - -o /dev/null https://nodescorecard.xyz/scorecard/nodes/top
curl -sS https://nodescorecard.xyz/scorecard/health
```

Health stays `200` with `ok: true`. The `402` from `/scorecard/nodes/top` must still be the existing payment challenge.
