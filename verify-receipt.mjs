// verify-receipt.mjs — independent, OFFLINE verification of a Route Receipt (no call back to the provider).
// Byte-identical to nodescorecard's receipt.mjs canonicalization. Handles v0.1 (flat hex resultHash)
// and v0.2 (integrity.resultHash, optional 'sha256:' prefix, stale_at).
//
// v0.2 CANONICALIZATION PROFILE: the receipt MUST declare its canonicalization
// profile (e.g. "jcs-strings-v0.2"). A verifier MUST fail loudly on an unknown/missing profile
// instead of hashing with its own canonicalizer and silently agreeing on different bytes.
import { createHash } from "node:crypto";

// Profiles THIS verifier implements. "jcs-strings-v0.2" == sorted-key JCS with amounts as strings.
// "JCS/RFC8785" kept as a transitional alias for receipts already emitted with that label.
const SUPPORTED_PROFILES = new Set(["jcs-strings-v0.2", "JCS/RFC8785"]);

export function canonicalize(v) {
  if (v === null) return "null";
  const t = typeof v;
  if (t === "number") { if (!Number.isFinite(v)) throw new Error("non-finite number"); return JSON.stringify(v); }
  if (t === "boolean" || t === "string") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(canonicalize).join(",") + "]";
  if (t === "object") {
    const keys = Object.keys(v).sort();
    return "{" + keys.map((k) => JSON.stringify(k) + ":" + canonicalize(v[k])).join(",") + "}";
  }
  throw new Error("value is not canonicalizable: " + t);
}
function sha256hex(str) { return createHash("sha256").update(Buffer.from(str, "utf8")).digest("hex"); }
export function resultHash(value) { return sha256hex(canonicalize(value)); }

export function verifyReceipt(receipt, servedBytes, now = Date.now()) {
  const reasons = [];

  // 0. CANONICALIZATION PROFILE — fail loudly on unknown/missing
  const profile = receipt?.canonicalization ?? receipt?.integrity?.canonicalization;
  if (!profile) {
    return { verdict: "REJECT", reasons: ["receipt declares no canonicalization profile (v0.2 requires one, e.g. jcs-strings-v0.2)"] };
  }
  if (!SUPPORTED_PROFILES.has(profile)) {
    return { verdict: "REJECT", reasons: [`unknown canonicalization profile: ${profile}; this verifier supports: ${[...SUPPORTED_PROFILES].join(", ")}`] };
  }

  let obj;
  try { obj = typeof servedBytes === "string" ? JSON.parse(servedBytes) : servedBytes; }
  catch { return { verdict: "REJECT", reasons: ["served bytes are not valid JSON"] }; }

  // 1. independent resultHash (only reached once the profile is known/supported)
  const computed = resultHash(obj);
  let claimed = receipt?.resultHash ?? receipt?.integrity?.resultHash;
  if (typeof claimed === "string" && claimed.startsWith("sha256:")) claimed = claimed.slice(7);
  if (!claimed) reasons.push("receipt has no resultHash");
  else if (computed !== claimed) reasons.push(`resultHash mismatch (bytes altered): ${computed} != ${claimed}`);

  // 2. stale_at OFFLINE (absolute timestamp)
  const staleAt = receipt?.measurement?.stale_at ?? receipt?.stale_at;
  if (staleAt) {
    const ms = Date.parse(staleAt);
    if (!Number.isFinite(ms)) reasons.push(`stale_at is not a valid timestamp: ${staleAt}`);
    else if (now > ms) reasons.push(`quote expired: now > stale_at (${staleAt})`);
  }

  // 3. must be settled
  const ts = receipt?.terminalState;
  if (ts && ts !== "settled") reasons.push(`not settled: terminalState=${ts}`);

  return { verdict: reasons.length ? "REJECT" : "ACCEPT", reasons, computedHash: computed, profile };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const fs = await import("node:fs");
  const args = process.argv.slice(2);
  const nowIdx = args.indexOf("--now");
  let now = Date.now();
  if (nowIdx >= 0) { now = Date.parse(args[nowIdx + 1]); args.splice(nowIdx, 2); }
  const [r, b] = args;
  if (!r || !b) { console.error("usage: node verify-receipt.mjs <receipt.json> <servedBytes.json> [--now <iso8601>]"); process.exit(2); }
  const out = verifyReceipt(JSON.parse(fs.readFileSync(r, "utf8")), fs.readFileSync(b, "utf8"), now);
  console.log(out.verdict); for (const x of out.reasons) console.log("  - " + x);
  process.exit(out.verdict === "ACCEPT" ? 0 : 1);
}
