# ─── ASN TYPE ENRICHMENT (PeeringDB) ───────────────────────────────
# Aggiunge a ogni ASN il tipo ufficiale da PeeringDB, con cache su file.
# info_type possibili: Content, NSP, Cable/DSL/ISP, Enterprise, Educational/Research,
#   Non-Profit, Route Server, Network Services, Government, ecc.
# Mappiamo questi nei badge del sito in modo OGGETTIVO (dato pubblico, non euristica sul nome).
import json, os, time, urllib.request

ASN_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asn-types.json")

def load_asn_cache():
    try:
        with open(ASN_CACHE_FILE) as f: return json.load(f)
    except Exception:
        return {}

def save_asn_cache(cache):
    tmp = ASN_CACHE_FILE + ".tmp"
    with open(tmp, "w") as f: json.dump(cache, f, separators=(",", ":"))
    os.replace(tmp, ASN_CACHE_FILE)

def peeringdb_type(asn_num, cache):
    """Ritorna info_type ufficiale per un numero ASN, con cache. None se ignoto."""
    key = str(asn_num)
    if key in cache:
        return cache[key]
    info_type = None
    try:
        url = "https://www.peeringdb.com/api/net?asn=%s" % asn_num
        req = urllib.request.Request(url, headers={"User-Agent": "node-scorecard/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r).get("data", [])
            if data:
                info_type = data[0].get("info_type") or None
    except Exception:
        info_type = None  # non raggiungibile / non in PeeringDB
    cache[key] = info_type           # cache anche i None (evita ri-tentare ogni giro)
    time.sleep(0.7)                  # rate-limit gentile verso PeeringDB
    return info_type

def asn_num_from_string(asn_str):
    """'AS24940 Hetzner...' -> 24940 ; ritorna None se non parsabile."""
    if not asn_str: return None
    s = asn_str.strip()
    if s.upper().startswith("AS"):
        head = s[2:].split()[0] if len(s) > 2 else ""
        return head if head.isdigit() else None
    return None
