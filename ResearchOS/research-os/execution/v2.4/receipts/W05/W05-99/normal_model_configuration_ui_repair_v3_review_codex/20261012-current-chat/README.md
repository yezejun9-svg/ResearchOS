# UI repair v3 independent review

**REQUEST_CHANGES** for `2f48ad7d4cd3cececf06a2a9a059a36ba157032c`.

The v2 asynchronous remount defect is repaired on the same host. Independent execution passes 17 selected boundary tests and the five frozen author DOM cases. Two new, independently authored actual-DOM counterexamples show a remaining P1: a configuration started on Host A finishes after discovery has changed to Host B; terminal reconciliation reads B and shows saved if B has matching configuration fields/revision. The STALE_RESPONSE case even accepts a different model_config_ref. B receives no configure request.

`independent-review.json` gives the source lines and repair requirement. `host-race-results.json`, the two DOM captures and `host-race-http/` retain actual public request/response bytes and validator child output. The immutable origin must survive through terminal reconciliation; same fields do not establish the original host's identity.

1112 input checks passed. These tests use v3 source components and the frozen v2 Go validator. They are explicitly not a v3 full build-input binding, normal Electron/Core flow or formal acceptance. There were zero actual model or external calls, and no modifications outside this review directory.
