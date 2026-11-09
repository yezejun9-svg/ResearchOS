# Native migration harness credential TTL revision

Status: SOURCE_ONLY_PENDING_ROOT_INDEPENDENT_REVIEW_AND_FRESH_ISOLATED_BUILD.

This package replaces only candidate-root/internal/domain/native_migration_authority_harness_windows_test.go.
Its base is the actual formatted T5 source, verified against T5's selected tagged
compiler input inventory. The accepted e57c Source, contract and handoff remain
inputs. No Main, T5, previous package, production auth, native binary, broker or
controller is modified.

Exactly two arguments change: owner and executor IssueCredential calls use
15*time.Minute instead of time.Hour. The actual production auth.go accepts
strictly positive TTL up to and including 15*time.Minute and authenticates only
while time.Now().Before(stored expires_at). There is no smaller cap in this API.
Production rules are unchanged. Credentials still come from the existing real
public issuance APIs, are issued before backup and retained only in process.

The inverse two replacements recover every byte of the formatted T5 baseline.
All assertions, nine cases, schema/whole-row invariants, exact error matching,
true Owner source, native authority/channel inputs, four-minute grant interval,
nonce, replay, Job ownership and cleanup remain unchanged.

Root must complete all operations requiring these credentials, including the
actual native invocation and planned positive replay, within 15 minutes of
the initial issuance of each credential. The 20-minute review hold/controller
lifetime does not guarantee that Owner stays valid. Root must inspect the
existing absolute expiries and budget both review/sign/publish pauses within
the original credential TTL and the unchanged grant validity. This package
adds no Owner refresh, reissuance, retry, deadline extension or automatic
approval. If time expires, preserve the actual failure and obtain the required
Root decision for any fresh isolated attempt; do not mutate the old case.

Failure 820 remains the original real single-positive Go exit 1:
PID 53352, creation FILETIME 134359747687806045, exact error
INVALID_REQUEST: credential TTL must be at most 15 minutes at original line 468.
Its actual closed invocation, stdout and Root's closed-qualified failure record
are pinned. Source author did not repeat the run, read the retained DB, or
perform native signing. Root reported prior fixture inspection/release; the
author only verifies the public invocation's actual Job closure and the
failure record's zero signatures/grants.

Diagnostic 822 is a separate functions.exec orchestration failure before any
exec_command or process launch; outer/Python/native exits are null, not 1.
Its complete original input and returned error are retained.

Root next independently reviews this minimal delta, composes a fresh isolated
T7, builds/freezes its actual compiler inputs and creates a fresh case/config.
No Go/native/SQL/private/model execution, production acceptance or retry is
claimed by this Source-only package. The prior e57c execution contract otherwise
remains applicable without relaxation.
