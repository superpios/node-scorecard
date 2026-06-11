#!/usr/bin/env python3
# walrus-capsule v1 — Sentinel Time Capsule
# Once a day, archives the network's historical snapshot (trends.json) on
# Walrus decentralized storage (Sui ecosystem). Keeps a local ledger of blob
# IDs (walrus-capsule.jsonl), writes capsule.json for the site and pushes it
# to GitHub reusing the token already in push-latest.sh.
# TESTNET for now: free, public publisher. Mainnet would need own publisher + WAL.
import json, os, re, base64, urllib.request, hashlib
from datetime import datetime, timezone

HERE=os.path.dirname(os.path.abspath(__file__)) or "."
TRENDS=os.path.join(HERE,"trends.json")
LEDGER=os.path.join(HERE,"walrus-capsule.jsonl")
OUT=os.path.join(HERE,"capsule.json")
PUSH_SH=os.path.join(HERE,"push-latest.sh")
REPO="superpios/node-scorecard"; BRANCH="main"
EPOCHS=30   # testnet epochs to keep the blob

PUBLISHERS=[
 "https://publisher.walrus-testnet.walrus.space",
 "https://walrus-testnet-publisher.nodes.guru",
 "https://walrus-testnet-publisher.stakin-nodes.com",
]
AGGREGATOR="https://aggregator.walrus-testnet.walrus.space"

NOW=datetime.now(timezone.utc)
today=NOW.strftime("%Y-%m-%d")

# skip if already archived today (idempotent for cron retries)
if os.path.exists(LEDGER):
    for l in open(LEDGER):
        try:
            if json.loads(l).get("date")==today:
                print(f"capsule: già archiviato oggi ({today}), esco"); raise SystemExit
        except SystemExit: raise
        except Exception: pass

data=open(TRENDS,"rb").read()
sha256=hashlib.sha256(data).hexdigest()

blob_id=None; used=None
for pub in PUBLISHERS:
    try:
        req=urllib.request.Request(f"{pub}/v1/blobs?epochs={EPOCHS}",data=data,method="PUT",
                                   headers={"Content-Type":"application/octet-stream"})
        resp=json.loads(urllib.request.urlopen(req,timeout=120).read())
        info=resp.get("newlyCreated",{}).get("blobObject") or resp.get("alreadyCertified") or {}
        blob_id=info.get("blobId")
        if blob_id: used=pub; break
    except Exception as e:
        print(f"  publisher {pub} fallito: {e}")
if not blob_id:
    print("capsule: nessun publisher raggiungibile, riproverò domani"); raise SystemExit(1)

entry={"date":today,"ts":NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),"blobId":blob_id,
       "sha256":sha256,"bytes":len(data),"publisher":used,
       "url":f"{AGGREGATOR}/v1/blobs/{blob_id}","network":"walrus-testnet"}
with open(LEDGER,"a") as f: f.write(json.dumps(entry,separators=(",",":"))+"\n")

# site file: last 30 capsules
caps=[]
for l in open(LEDGER):
    try: caps.append(json.loads(l))
    except Exception: pass
json.dump({"latest":caps[-1],"capsules":caps[-30:]},open(OUT,"w"),separators=(",",":"))
print(f"capsule: {today} -> blobId {blob_id} ({len(data)}B, sha256 {sha256[:12]}…)")

# push capsule.json to GitHub (same token-reuse pattern as make-trends)
try:
    tok=re.search(r'(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})',open(PUSH_SH).read()).group(1)
    api=f"https://api.github.com/repos/{REPO}/contents/capsule.json"
    def gh(url,data=None,method="GET"):
        req=urllib.request.Request(url,data=data,method=method,
            headers={"Authorization":f"token {tok}","User-Agent":"scorecard","Accept":"application/vnd.github+json"})
        return json.loads(urllib.request.urlopen(req,timeout=30).read())
    sha=None
    try: sha=gh(api+f"?ref={BRANCH}").get("sha")
    except Exception: pass
    body={"message":"daily Walrus capsule","branch":BRANCH,
          "content":base64.b64encode(open(OUT,"rb").read()).decode()}
    if sha: body["sha"]=sha
    gh(api,json.dumps(body).encode(),"PUT")
    print("OK capsule.json pushed")
except Exception as e:
    print(f"push capsule fallito: {e}")
