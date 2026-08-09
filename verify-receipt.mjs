// verify-receipt.mjs — independent, OFFLINE verification of a Route Receipt (no call back to the provider).
// Byte-identical to nodescorecard's receipt.mjs: SAME canonicalization (JCS/RFC-8785 style,
// sorted keys) + resultHash = sha-256 hex, so two agents reproduce the server's hash exactly.
// Handles both the v0.1 receipt (flat hex resultHash) and the v0.2 field (integrity.resultHash,
// optional 'sha256:' prefix) plus v0.2 stale_at.
import { createHash } from "node:crypto";

// --- IDENTICAL to the server's receipt.mjs ---
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
  let obj;
  try { obj = typeof servedBytes === "string" ? JSON.parse(servedBytes) : servedBytes; }
  catch { return { verdict: "REJECT", reasons: ["served bytes are not valid JSON"] }; }

  // 1. independent resultHash (SAME canonicalization as the server)
  const computed = resultHash(obj);
  let claimed = receipt?.resultHash ?? receipt?.integrity?.resultHash;
  if (typeof claimed === "string" && claimed.startsWith("sha256:")) claimed = claimed.slice(7);
  if (!claimed) reasons.push("receipt has no resultHash");
  else if (computed !== claimed) reasons.push(`resultHash mismatch (bytes altered): ${computed} != ${claimed}`);

  // 2. stale_at OFFLINE (v0.2, optional): absolute timestamp
  const staleAt = receipt?.measurement?.stale_at ?? receipt?.stale_at;
  if (staleAt) {
    const ms = Date.parse(staleAt);
    if (!Number.isFinite(ms)) reasons.push(`stale_at is not a valid timestamp: ${staleAt}`);
    else if (now > ms) reasons.push(`quote expired: now > stale_at (${staleAt})`);
  }

  // 3. must be settled
  const ts = receipt?.terminalState;
  if (ts && ts !== "settled") reasons.push(`not settled: terminalState=${ts}`);

  return { verdict: reasons.length ? "REJECT" : "ACCEPT", reasons, computedHash: computed };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const fs = await import("node:fs");
  const [r, b] = process.argv.slice(2);
  if (!r || !b) { console.error("usage: node verify-receipt.mjs <receipt.json> <servedBytes.json>"); process.exit(2); }
  const out = verifyReceipt(JSON.parse(fs.readFileSync(r, "utf8")), fs.readFileSync(b, "utf8"));
  console.log(out.verdict); for (const x of out.reasons) console.log("  - " + x);
  process.exit(out.verdict === "ACCEPT" ? 0 : 1);
}
