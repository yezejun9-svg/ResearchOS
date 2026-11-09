# W05 strict-loopback source and development review

Decision: **SOURCE_AND_DEVELOPMENT_COMPONENT_ACCEPTED**.
Actual non-author reviewer: `/root/w09_header_gate_review`.
Author: `/root/w05_main24`. Exact candidate commit:
`2825d2aad972c435268f29349a1e649605be347e`, direct parent
`549ad6924ad43d27bbe533f4ba020ef383a0888f`.
Manifest SHA-256: `d48a3181350ed1bf54960c99a685889feba1de1e6b2d61a4ebdd74e77424cfdd`.

No blocking defect found in the bounded source change. All nine manifest file
hashes match the exact commit and clean candidate worktree; the diff contains
only five production files and four test files, with no schema or threshold edits.
The original fixed JSONL has ten distinct top-level test passes, package PASS,
no failure/skip events, and matches the manifest hash. Original exit 0 is recorded
by the manifest and is consistent with the raw package lifecycle; a separate
structured original invocation receipt is not included in that three-file handoff.

## Contract and code boundaries

The frozen v2.4 `client.protocol.schema.json:345,1204` specifies URI base URLs;
`:353,1212` permits null credential refs. `22_CLIENT_INTERFACE_DETAILS.md:55`
requires credential import only when the supplier requires it. A11-04 at
`contracts/acceptance.json:2878` protects remote communication with TLS/authenticated
encryption. The new strict local HTTP exception does not relax remote TLS or
ResearchOS client-to-host authentication, identity, CAS or session authority.

- `client_protocol_configuration.go:426-503` centralizes lexical validation. HTTP
  permits exactly `127.0.0.1` and `[::1]`, optional valid numeric port, and no
  credential ref. Hostnames, alternate numeric spellings, other loopback addresses,
  IPv4-mapped IPv6, zone IDs, userinfo, percent encoding, query/fragment, path dot
  segments and doubled slashes cannot enter this LIVE local model exception.
  `client_configuration.go` now uses this same check for persistence/read validation.
- `runtime_sessions_windows.go:74-114` preserves stored Owner/provider/model/API/
  endpoint/model-config matching and project/runtime/route/purpose matching.
  Credential-free configurations additionally require the exact local endpoint,
  profile/route credential revision `none`, empty actual credential ref and Bearer.
  Existing configuration references continue to encode revision and original
  command/config identity. No new session ownership or configuration-switch shortcut
  was introduced.
- `runtime_broker_windows.go:43-70,85-136` retains frozen route ID, capability,
  upper-bound, credential revision, model config and admission mode checks. LIVE
  local MODEL is the only new HTTP allowance; external LIVE MODEL retains protected
  credential ref/revision equality, resolver availability and empty preloaded Bearer.
  Existing non-MODEL/FIXTURE policy remains unchanged.
- `runtime_model_windows.go:69-97` rejects credential-bearing local LIVE routes
  before resolver/request construction. Empty refs do not call the vault callback.
  The existing broker constructs fresh HTTP requests from the frozen endpoint and
  validated body, has no cookie jar, uses `Proxy:nil`, denies redirects, and adds
  Authorization only for a deliberately resolved/nonempty route credential.
  The unchanged worker sends only the bounded model body to the broker, discarding
  SDK request headers. Its SDK placeholder key is not an upstream credential.
- Existing UNKNOWN/no-auto-retry, missing-credential NOT_APPLIED, SSE quarantine,
  budget reservation and late-response authority checks remain unchanged.
  The literal revision `none` satisfies a nonempty version identifier; it is not
  persisted as `credential_ref`, inserted into Bearer or treated as secret material.

## Independent supplemental evidence

Two reviewer-only tests ran from a separate copy of the exact committed source,
using the existing SDK bundle and locked Go/Node pins recorded in the invocation.
No original ten-test suite rerun was performed.

1. Actual SDK-to-broker-to-loopback fixture transport returned HTTP 307. It made
   one provider call, zero redirect-target calls, zero proxy calls, zero vault calls,
   and sent none of Authorization/Cookie/Proxy-Authorization/X-Api-Key/Idempotency-Key.
   Host proxy environment variables and an inherited synthetic API key were present.
   The result stayed UNKNOWN and a second RunAdmitted was denied without another
   provider request. The common transport has explicit `Proxy:nil`; loopback proxy
   bypass alone is not used as the source-level proof for that setting.
2. LIVE route predicates accept the exact no-vault local route and reject domain
   lookalikes, trailing-dot hosts, hexadecimal/octal/alternate loopback forms,
   alternate IPv6 spelling and query/fragment variants. Remote HTTPS still requires
   a resolver and exact protected credential binding, and rejects inherited Bearer.

The first reviewer probe copy omitted committed `ops/supervisor` and failed before
tests. Its original exit 1/stdout/invocation are retained. Attempt 002 added committed
ops dependencies, ran only the two previously unexecuted reviewer tests, and passed.
The disposable copy was deleted after verifying its absolute boundary. Candidate
sources, Main and Canon were untouched; the candidate remained clean after testing.

## Acceptance limits

This is source and local-development-component acceptance only. The actual SDK
transport tests run with admission mode FIXTURE; LIVE local predicates are unit
checked and statically traced. No real qwen/Ollama model was called or qualified,
no paid request was made, and no W05/A04 formal acceptance was issued. Existing
HTTPS actual-SDK fixture coverage remains included in the ten original tests.

`apps/cli/cli_contract.go:583` remains HTTPS-only, so this candidate does not complete
the normal CLI set-model product flow. The UI/CLI path, actual local model availability,
model behavior, live provider qualification and complete coding/continuation use
case remain separate work. No frozen spec change, TLS bridge or replacement of
remote security requirements is needed for the scoped source integration.
