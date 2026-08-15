#!/usr/bin/env python3
# make-akash-trends.py - builds per-provider historical trends from akash-history.jsonl.
# Output: latest-akash-trends.json (per-provider score/uptime/gpu time series + deltas).
# Schema-robust: handles either one-snapshot-per-line {ts,providers:[...]} or one-record-per-line {ts,id,...}.
import json, sys, os, time
BASE = os.path.dirname(os.path.abspath(__file__))
HIST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "akash-history.jsonl")
OUT  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "latest-akash-trends.json")
if not os.path.exists(HIST): print("NO HISTORY FILE:", HIST); sys.exit(1)

series = {}
def pick(rec, *keys):
    for k in keys:
        if rec.get(k) is not None: return rec.get(k)
    return None

def add(ts, rec):
    pid = pick(rec, "id", "provider", "owner")
    if not pid: return
    gpu = rec.get("gpu")
    if isinstance(gpu, dict): gfree, gtot = gpu.get("available"), gpu.get("total")
    else: gfree, gtot = pick(rec, "gf", "gpu_free"), pick(rec, "gt", "gpu_total")
    series.setdefault(pid, []).append({"ts": ts,
        "score": pick(rec, "s", "score"),
        "uptime": pick(rec, "u", "uptime", "uptime30d"),
        "gpu_free": gfree, "gpu_total": gtot})

n_lines = 0
for line in open(HIST, encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line: continue
    try: obj = json.loads(line)
    except Exception: continue
    n_lines += 1
    plist = None
    if isinstance(obj, dict):
        for key in ("p", "providers", "nodes"):
            if isinstance(obj.get(key), list): plist = obj[key]; break
    if plist is not None:
        ts = obj.get("ts") or obj.get("time") or obj.get("updated_at")
        for rec in plist:
            if isinstance(rec, dict): add(ts, rec)
    elif isinstance(obj, dict):
        add(obj.get("ts") or obj.get("time"), obj)
    elif isinstance(obj, list):
        for rec in obj:
            if isinstance(rec, dict): add(rec.get("ts"), rec)

def trend(vals):
    v = [x for x in vals if isinstance(x, (int, float))]
    if not v: return {"samples": 0, "first": None, "last": None, "delta": None, "direction": "n/a"}
    if len(v) < 2: return {"samples": len(v), "first": v[0], "last": v[0], "delta": 0, "direction": "flat", "min": v[0], "max": v[0]}
    d = round(v[-1] - v[0], 3)
    return {"samples": len(v), "first": v[0], "last": v[-1], "delta": d,
            "direction": "up" if d > 0 else "down" if d < 0 else "flat", "min": min(v), "max": max(v)}

if not series:
    print("NO USABLE RECORDS in", HIST, "- nothing written"); sys.exit(2)

out = {"updated_at": int(time.time()), "source_lines": n_lines, "providers_tracked": len(series), "providers": {}}
for pid, samples in series.items():
    samples.sort(key=lambda x: x.get("ts") or 0)
    out["providers"][pid] = {"samples": len(samples), "first_seen": samples[0].get("ts"), "last_seen": samples[-1].get("ts"),
        "score": trend([s["score"] for s in samples]),
        "uptime": trend([s["uptime"] for s in samples]),
        "gpu_free": trend([s["gpu_free"] for s in samples])}
tmp = OUT + ".tmp"
with open(tmp, "w", encoding="utf-8") as fh:
    json.dump(out, fh, separators=(",", ":"))
os.replace(tmp, OUT)  # atomic: never leaves a half-written file
print("TRENDS WRITTEN:", OUT, "| providers:", len(series), "| source lines:", n_lines)
