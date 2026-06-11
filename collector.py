#!/usr/bin/env python3
# Sentinel Scorecard Collector v3.6 (active-first)
# v3.6: la chain ha 76k+ registrazioni storiche (per lo piu' morte). Ora scarichiamo
#       SOLO gli attivi (status=1, ~8 pagine) + scriviamo un record leggero "inactive"
#       per i nodi tracciati che escono dalla lista attivi (li segue la purga 30gg).
#       export_latest applica lo stesso taglio 30gg.
# v3: aggiunge price_hr/price_gb (da LCD), protocol/peers/version/banda (da API locale)
# v3.1: retry API nodo (2 tentativi) per ridurre nodi con moniker/peers None
# v3.2: ASN enrichment con cache su file (lookup IP->ASN via ip-api, 1 call per IP nuovo)
# v3.4: enrich_asn solo nodi attivi (status==active) - meno lookup, piu utile
# v3.5: aggiunge campo hosting (datacenter true/false) da ip-api; cache come dict {asn,hosting}
import json, os, sys, time, urllib.request, urllib.parse, ssl, socket
from datetime import datetime, timezone
HERE=os.path.dirname(os.path.abspath(__file__))
DATA=os.path.join(HERE,"history.jsonl"); WATCH=os.path.join(HERE,"watchlist.json"); LATEST=os.path.join(HERE,"latest.json")
ASNCACHE=os.path.join(HERE,"asn_cache.json")
LCD="https://lcd.sentinel.co"; TIMEOUT=10
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
def now_iso(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def fetch(url,timeout=TIMEOUT):
    req=urllib.request.Request(url,headers={"User-Agent":"scorecard/3.4"})
    with urllib.request.urlopen(req,timeout=timeout,context=CTX) as r: return json.loads(r.read().decode())
def _cache_get(cache, ip):
    # Cache entries can be legacy strings (asn only) or dicts {asn,hosting}.
    v=cache.get(ip)
    if v is None: return None
    if isinstance(v,str): return {"asn":v,"hosting":None}  # legacy entry, hosting unknown
    return v
def lookup_asn(remote, cache):
    # remote = 'host:port' o 'ip:port' -> dict {asn,hosting} (cache su IP, 1 call per IP nuovo)
    if not remote: return None
    host=remote.split(":")[0].strip()
    if not host: return None
    try: ip=socket.gethostbyname(host)
    except Exception: return None
    cached=_cache_get(cache, ip)
    if cached is not None and cached.get("hosting") is not None: return cached  # full entry
    try:
        d=fetch(f"http://ip-api.com/json/{ip}?fields=status,as,isp,hosting",timeout=8)
        if d.get("status")=="success":
            entry={"asn":d.get("as") or d.get("isp"),"hosting":bool(d.get("hosting"))}
            cache[ip]=entry; return entry
    except Exception: pass
    if cached is not None:
        cache[ip]=cached; return cached  # keep legacy asn, hosting stays None
    cache[ip]={"asn":None,"hosting":None}
    return cache[ip]
def load_watch():
    if os.path.exists(WATCH):
        try: return json.load(open(WATCH))
        except: return {"nodes":[]}
    return {"nodes":[]}
def save_watch(w): json.dump(w,open(WATCH,"w"),indent=2)
def add_node(a):
    w=load_watch()
    if a not in w["nodes"]: w["nodes"].append(a); save_watch(w); print(f"Aggiunto {a}")
    else: print("Gia' presente")
def all_nodes(lim=200,maxp=40,status=None):
    out=[]; key=None
    for p in range(maxp):
        url=f"{LCD}/sentinel/node/v3/nodes?pagination.limit={lim}"
        if status is not None: url+=f"&status={status}"
        if key: url+=f"&pagination.key={urllib.parse.quote(key)}"
        try: d=fetch(url,timeout=15)
        except Exception as e: print(f"  ! pagina {p}: {e}"); break
        ns=d.get("nodes",[])
        for n in ns: out.append(n.get("address"))
        key=(d.get("pagination") or {}).get("next_key")
        print(f"  pagina {p+1}: +{len(ns)} (tot {len(out)})")
        if not key or not ns: break
        time.sleep(0.5)
    return out
def price_udvpn(arr):
    for p in (arr or []):
        if p.get("denom")=="udvpn":
            try: return round(int(p["quote_value"])/1e6,2)
            except: return None
    return None
def sample(addr):
    rec={"ts":now_iso(),"addr":addr,"status":None,"inactive_at":None,"remote":None,"moniker":None,
         "dl_mbps":None,"ul_mbps":None,"api_ok":False,"gb_tokens":0,
         "price_hr":None,"price_gb":None,"protocol":None,"peers":None,"version":None,"country":None,"city":None,"asn":None,"hosting":None}
    try:
        n=fetch(f"{LCD}/sentinel/node/v3/nodes/{addr}").get("node",{})
        rec["status"]=n.get("status"); rec["inactive_at"]=n.get("inactive_at")
        ra=n.get("remote_addrs") or []; rec["remote"]=ra[0] if ra else None
        rec["moniker"]=n.get("moniker")
        gp=n.get("gigabyte_prices") or []; hp=n.get("hourly_prices") or []
        rec["gb_tokens"]=len(gp)
        rec["price_gb"]=price_udvpn(gp)
        rec["price_hr"]=price_udvpn(hp)
    except Exception as e: rec["error"]=str(e); return rec
    if rec["remote"]:
        api=None
        for attempt,to in enumerate((7,12)):
            try:
                api=fetch(f"https://{rec['remote']}/",timeout=to); break
            except Exception:
                if attempt==0: time.sleep(1)
                api=None
        if api is not None:
            try:
                res=api.get("result",api)
                rec["api_ok"]=True
                if res.get("downlink"):
                    try: rec["dl_mbps"]=round(int(res["downlink"])*8/1e6,2)
                    except: pass
                if res.get("uplink"):
                    try: rec["ul_mbps"]=round(int(res["uplink"])*8/1e6,2)
                    except: pass
                rec["peers"]=res.get("peers")
                rec["protocol"]=res.get("service_type")
                ver=res.get("version") or {}
                rec["version"]=ver.get("tag") if isinstance(ver,dict) else ver
                if not rec["moniker"]: rec["moniker"]=res.get("moniker")
                loc=res.get("location") or {}
                if loc.get("country"): rec["country"]=loc["country"]
                if loc.get("city"): rec["city"]=loc["city"]
            except Exception: rec["api_ok"]=False
        else:
            rec["api_ok"]=False
    return rec
def export_latest():
    if not os.path.exists(DATA): print("Nessuno storico."); return
    from datetime import timedelta
    cut=(datetime.now(timezone.utc)-timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    latest={}
    for l in open(DATA):
        if l.strip():
            try: r=json.loads(l); latest[r["addr"]]=r
            except: pass
    before=len(latest)
    latest={a:r for a,r in latest.items() if (r.get("ts") or "")>=cut}
    json.dump(list(latest.values()),open(LATEST,"w"))
    print(f"Esportati {len(latest)} nodi in {LATEST} ({before-len(latest)} oltre 30gg esclusi)")
def enrich_asn():
    # v3.4: ASN enrichment solo nodi ATTIVI. Salva cache ogni 40 lookup (a prova di interruzione),
    # stampa progresso, riprende dalla cache se rilanciato. Rate-limit ip-api 45/min.
    if not os.path.exists(LATEST): print("Nessun latest.json."); return
    cache=json.load(open(ASNCACHE)) if os.path.exists(ASNCACHE) else {}
    nodes=json.load(open(LATEST))
    todo=[n for n in nodes if n.get("remote") and n.get("status")=="active" and (not n.get("asn") or n.get("hosting") is None)]
    print(f"[{now_iso()}] ASN enrich: {len(todo)} nodi ATTIVI da risolvere (cache: {len(cache)} IP)")
    new_lookups=0; done=0
    for n in nodes:
        # process active nodes missing asn OR missing hosting (so legacy entries get hosting filled)
        if not n.get("remote") or n.get("status")!="active": continue
        if n.get("asn") and n.get("hosting") is not None: continue
        host=n["remote"].split(":")[0].strip()
        try: ip=socket.gethostbyname(host)
        except Exception: ip=None
        if not ip: continue
        cached=_cache_get(cache, ip)
        if cached is not None and cached.get("hosting") is not None:
            n["asn"]=cached.get("asn"); n["hosting"]=cached.get("hosting")
        else:
            entry=lookup_asn(n["remote"],cache); new_lookups+=1
            if entry: n["asn"]=entry.get("asn"); n["hosting"]=entry.get("hosting")
            if new_lookups%40==0:
                json.dump(cache,open(ASNCACHE,"w"))
                json.dump(nodes,open(LATEST,"w"))
                print(f"  ...{new_lookups} nuovi lookup, cache {len(cache)} IP - pausa 62s")
                time.sleep(62)
        done+=1
    json.dump(cache,open(ASNCACHE,"w"))
    json.dump(nodes,open(LATEST,"w"))
    withasn=sum(1 for n in nodes if n.get("asn"))
    print(f"[{now_iso()}] ASN done: {new_lookups} nuovi lookup, {withasn}/{len(nodes)} nodi con ASN, cache {len(cache)} IP")
def report():
    if not os.path.exists(DATA): print("Nessuno storico."); return
    rows=[json.loads(l) for l in open(DATA) if l.strip()]; by={}
    for r in rows: by.setdefault(r["addr"],[]).append(r)
    print(f"\n{len(rows)} campioni su {len(by)} nodi\n")
    for a,recs in sorted(by.items(),key=lambda x:-sum(1 for r in x[1] if r.get('status')=='active')/len(x[1])):
        n=len(recs); up=round(sum(1 for r in recs if r.get("status")=="active")/n*100,1)
        mon=(recs[-1].get("moniker") or a[:20])[:22]; print(f"  {mon:<24} {n:>4}smp {up:>5}%")
def main():
    a=sys.argv[1:]
    if "--add" in a: add_node(a[a.index("--add")+1]); return
    if "--report" in a: report(); return
    if "--export-latest" in a: export_latest(); return
    if "--asn" in a: enrich_asn(); return
    tracked_inactive=[]
    if "--all" in a:
        print(f"[{now_iso()}] Scarico nodi ATTIVI dalla chain (status=1)...")
        t=all_nodes(status=1)
        if not t:
            print("! lista attivi vuota (LCD giu'?), esco senza scrivere"); return
        # nodi che tracciavamo come attivi e ora non sono piu' nella lista: un record
        # leggero li marca inactive; poi smettiamo di campionarli (purge 30gg li elimina)
        act_set=set(t)
        if os.path.exists(LATEST):
            try:
                for n in json.load(open(LATEST)):
                    if n.get("status")=="active" and n["addr"] not in act_set:
                        tracked_inactive.append(n["addr"])
            except Exception: pass
        print(f"[{now_iso()}] {len(t)} attivi on-chain | {len(tracked_inactive)} tracked diventati inattivi")
    else:
        t=load_watch()["nodes"]
        if not t: print("Vuoto. Usa --add o --all"); return
        print(f"[{now_iso()}] Campiono {len(t)} nodi watchlist")
    w=0; act=0; done=0; total=len(t)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with open(DATA,"a") as f:
        with ThreadPoolExecutor(max_workers=60) as ex:
            futs={ex.submit(sample,addr):addr for addr in t}
            for fut in as_completed(futs):
                try: rec=fut.result()
                except Exception as e: rec={"ts":now_iso(),"addr":futs[fut],"error":str(e)}
                f.write(json.dumps(rec)+"\n"); w+=1; done+=1
                if rec.get("status")=="active": act+=1
                if "--all" in a and done%200==0: print(f"  ...{done}/{total} ({act} active)")
        for a2 in tracked_inactive:
            f.write(json.dumps({"ts":now_iso(),"addr":a2,"status":"inactive","inactive_at":None,"remote":None,
                "moniker":None,"dl_mbps":None,"ul_mbps":None,"api_ok":False,"gb_tokens":0,"price_hr":None,
                "price_gb":None,"protocol":None,"peers":None,"version":None,"country":None,"city":None,
                "asn":None,"hosting":None})+"\n")
    print(f"[{now_iso()}] {w} campioni attivi + {len(tracked_inactive)} transizioni inactive")
    export_latest()
    enrich_asn()   # v3.4: aggiunge ASN dopo l'export
if __name__=="__main__": main()
