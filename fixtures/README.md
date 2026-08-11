# Route Receipt fixtures

Executable checks for the Route Receipt spec — so the spec is testable, not just prose.

Run the reference verifier against these fixtures:

```
node ../verify-receipt.mjs receipt.valid.json           served.json   # -> ACCEPT
node ../verify-receipt.mjs receipt.unknown-profile.json served.json   # -> REJECT (unknown canonicalization profile)
```

`receipt.unknown-profile.json` is identical to `receipt.valid.json` except its
`canonicalization` field. Restoring the exact profile (`jcs-strings-v0.2`) makes it pass:
the verifier fails loudly on an unknown profile instead of hashing with its own canonicalizer.
