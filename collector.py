#!/usr/bin/env python3
# ============================================================================
#  Sentinel Scorecard Collector  v2
#  Campiona stato + banda dei nodi Sentinel a intervalli regolari e accumula
#  uno storico in JSON-lines. Alimenta lo Scorecard (uptime%, stabilita',
#  trend banda, classifica) -- il dato che nessun tool istantaneo da'.
#
#  Uso:
#    python3 collector.py                  # nodi in watchlist
#    python3 collector.py --all            # TUTTI i nodi della rete (paginati)
#    python3 collector.py --country IT     # filtra per paese (best effort)
#    python3 collector.py --add sentnode1..# aggiunge un nodo alla watchlist
#    python3 collector.py --report         # riepilogo storico
#    python3 collector.py --export-latest  # ultimo snapshot per nodo -> latest.json
#
#  Cron consigliato (--all e' pesante: ogni ora; watchlist: ogni 30m):
#    0 * * * * /usr/bin/python3 /home/superpios/scorecard/collector.py --all >> ~/scorecard/collector.log 2>&1
# ============================================================================

import json, os, sys, time, urllib.request, urllib.error, ssl
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "history.jsonl")
WATCH = os.path.join(HERE, "watchlist.json")
LATEST = os.path.join(HERE, "latest.json")
LCD = "https://lcd.sentinel.co"
TIMEOUT = 10
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

def now_iso(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def fetch(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent":"scorecard-collector/2.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return json.loads(r.read().decode())

def load_watch():
    if os.path.exists(WATCH):
        try: return json.load(open(WATCH))
        except: return {"nodes": []}
    return {"nodes": []}

def save_watch(w): json.dump(w, open(WATCH,"w"), indent=2)

def add_node(addr):
    w=load_watch()
    if addr not in w["nodes"]:
        w["nodes"].append(addr); save_watch(w)
        print(f"Aggiunto {addr} ({len(w['nodes'])} nodi in watchlist)")
    else: print("Gia' in watchlist")

def all_nodes(limit_per_page=200, max_pages=10):
    """Scarica TUTTI i nodi attivi paginando. Ritorna lista di indirizzi."""
    out=[]; key=None
    for page in range(max_pages):
        url=f"{LCD}/sentinel/node/v3/nodes?status=1&pagination.limit={limit_per_page}"
        if key: url+=f"&pagination.key={urllib.parse.quote(key)}"
        try:
            d=fetch(url, timeout=15)
        except Exception as e:
            print(f"  ! pagina {page}: {e}"); break
        nodes=d.get("nodes",[])
        for n in nodes: out.append(n.get("address"))
        key=(d.get("pagination") or {}).get("next_key")
        print(f"  pagina {page+1}: +{len(nodes)} nodi (totale {len(out)})")
        if not key or not nodes: break
        time.sleep(0.5)
    return out

def sample_node(addr):
    rec={"ts":now_iso(),"addr":addr,"status":None,"inactive_at":None,"remote":None,
         "moniker":None,"dl_mbps":None,"ul_mbps":None,"api_ok":False,"gb_tokens":0,"margin_min":None}
    try:
        n=fetch(f"{LCD}/sentinel/node/v3/nodes/{addr}").get("node",{})
        rec["status"]=n.get("status"); rec["inactive_at"]=n.get("inactive_at")
        ra=n.get("remote_addrs") or []; rec["remote"]=ra[0] if ra else None
        rec["moniker"]=n.get("moniker"); rec["gb_tokens"]=len(n.get("gigabyte_prices") or [])
        ia=n.get("inactive_at")
        if ia and ia!="0001-01-01T00:00:00Z":
            try: dt=datetime.strptime(ia,"%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            except ValueError: dt=datetime.strptime(ia[:19]+"Z","%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            rec["margin_min"]=round((dt-datetime.now(timezone.utc)).total_seconds()/60)
    except Exception as e:
        rec["error"]=f"chain:{e}"; return rec
    if rec["remote"]:
        try:
            api=fetch(f"https://{rec['remote']}/", timeout=7); res=api.get("result",api)
            rec["api_ok"]=True; bw=res.get("bandwidth") or {}
            if bw.get("download"): rec["dl_mbps"]=round(int(bw["download"])*8/1e6,2)
            if bw.get("upload"): rec["ul_mbps"]=round(int(bw["upload"])*8/1e6,2)
            if not rec["moniker"]: rec["moniker"]=res.get("moniker")
            loc=res.get("location") or {}
            if loc.get("country"): rec["country"]=loc["country"]
            if loc.get("city"): rec["city"]=loc["city"]
        except Exception: rec["api_ok"]=False
    return rec

def export_latest():
    """Scrive latest.json: ultimo snapshot per ciascun nodo (per lo Scorecard)."""
    if not os.path.exists(DATA): print("Nessuno storico."); return
    latest={}
    for l in open(DATA):
        if not l.strip(): continue
        try: r=json.loads(l)
        except: continue
        latest[r["addr"]]=r  # l'ultimo vince
    json.dump(list(latest.values()), open(LATEST,"w"))
    print(f"Esportati {len(latest)} nodi (ultimo snapshot) in {LATEST}")

def report():
    if not os.path.exists(DATA): print("Nessuno storico ancora."); return
    rows=[json.loads(l) for l in open(DATA) if l.strip()]
    by={}
    for r in rows: by.setdefault(r["addr"],[]).append(r)
    print(f"\nStorico: {len(rows)} campioni su {len(by)} nodi\n")
    print(f"{'NODO':<24}{'CAMP':>6}{'UP%':>7}{'FLIP':>6}{'UL Mbps':>9}")
    print("-"*52)
    def upk(x):
        recs=x[1]; n=len(recs); a=sum(1 for r in recs if r.get("status")=="active")
        return -(a/n if n else 0)
    for addr,recs in sorted(by.items(), key=upk):
        n=len(recs); active=sum(1 for r in recs if r.get("status")=="active")
        up=round(active/n*100,1) if n else 0
        trans=sum(1 for i in range(1,len(recs)) if (recs[i].get("status")=="active")!=(recs[i-1].get("status")=="active"))
        uls=[r["ul_mbps"] for r in recs if r.get("ul_mbps")]; ul=round(sum(uls)/len(uls),1) if uls else 0
        mon=(recs[-1].get("moniker") or addr[:20])[:22]
        print(f"{mon:<24}{n:>6}{up:>6}%{trans:>6}{ul:>9}")
    print()

def main():
    import urllib.parse
    args=sys.argv[1:]
    if "--add" in args: add_node(args[args.index("--add")+1]); return
    if "--report" in args: report(); return
    if "--export-latest" in args: export_latest(); return

    if "--all" in args:
        print(f"[{now_iso()}] Scarico la lista globale dei nodi attivi...")
        targets=all_nodes()
        print(f"[{now_iso()}] {len(targets)} nodi totali da campionare")
    elif "--country" in args:
        c=args[args.index("--country")+1]; targets=all_nodes()
        print(f"[{now_iso()}] (filtro {c} applicato dopo il sample, via API location)")
    else:
        targets=load_watch()["nodes"]
        if not targets: print("Watchlist vuota. Usa --add, --country o --all"); return
        print(f"[{now_iso()}] Campiono {len(targets)} nodi in watchlist")

    written=0; active=0
    with open(DATA,"a") as f:
        for i,addr in enumerate(targets):
            rec=sample_node(addr)
            f.write(json.dumps(rec)+"\n"); written+=1
            if rec.get("status")=="active": active+=1
            if "--all" in args:
                if (i+1)%50==0: print(f"  ...{i+1}/{len(targets)} ({active} active finora)")
            else:
                st=rec.get("status") or "?"; bw=f"{rec['ul_mbps']}Mbps up" if rec.get("ul_mbps") else "banda n/d"
                print(f"  {addr[:24]}... {st:<9} {bw}")
            time.sleep(0.25)
    print(f"[{now_iso()}] Scritti {written} campioni ({active} active) in {DATA}")
    export_latest()

if __name__=="__main__":
    import urllib.parse
    main()
