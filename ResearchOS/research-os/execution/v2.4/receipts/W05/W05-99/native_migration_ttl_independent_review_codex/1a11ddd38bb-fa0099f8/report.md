## Security Audit Report

### Summary
- Critical: 0
- High: 0
- Medium: 0
- Low: 0

Scope: only the two credential TTL expressions in native_migration_authority_harness_windows_test.go, lines 466 and 470, compared with the actual formatted T5 compiler input. This is a source review; no native run or runtime acceptance is claimed.

### Findings
No exploitable security issue introduced by this delta. Both IssueCredential calls change time.Hour to 15*time.Minute. Reversing exactly these two expressions recovers every baseline byte. Production auth.go still checks 0 < ttl <= 15*time.Minute and rejects time.Now() >= expires_at. The change does not grant extra permissions or extend the production limit.

Trust boundaries and STRIDE: Root configuration and explicit approvals remain the source of execution decisions; the real issuance API supplies Owner/executor credentials in memory; the broker transmits them through its private stdin pipe; production authentication enforces expiry. Spoofing, tampering, repudiation, disclosure, denial of service, and elevation paths in those boundaries are unchanged by the byte-exact delta. The unchanged nine cases, replay rejection, whole-state assertions, raw pin checks, Job closure and explicit fixture release remain required. OWASP authentication/access-control/injection/misconfiguration/integrity/logging coverage is bounded to this delta. No dependencies, lockfiles or third-party installers changed; no fresh CVE sweep or full-system audit was performed. LLM-specific categories are not applicable to this credential expression change.

### Positive Observations
- Production expiry and maximum TTL remain code-enforced.
- The two issued credentials remain in process and do not gain a refresh or retry path.
- Four-minute migration grants and all original rejection assertions are preserved.
- Original failure 820 and orchestration diagnostic 822 remain immutable inputs.

### Recommendations
Root may compose a fresh isolated T7 build and fresh case/config. Complete every credential-dependent operation, including native invocation and replay, within the initial 15-minute credential interval and the unchanged grant interval. Review holds do not extend validity. An expired attempt must remain a recorded failure and cannot be silently refreshed or retried.

Independent review tooling diagnostics 824 and 825 are separately retained with actual outer exit 1 and Python/native exits null. They do not describe harness failures. Counter reset is false.

Decision: TTL_MINIMAL_SOURCE_ACCEPTED_FRESH_ISOLATED_BUILD_REQUIRED. Authority NONE; formal/native/Owner/original-business acceptance false. Stop after sealing this review.

