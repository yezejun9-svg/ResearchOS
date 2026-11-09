# Python broker exact four-key isolated temporary environment

Status: SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL.
Authority: NONE. Formal acceptance: false.
One candidate broker Source plus synthetic public boundary test Source.
No Main, canonical, T* worktree, earlier Source, or historical failure is modified.

## Actual cause retained

The original failure868 public receipt is copied byte for byte.
The pinned base broker demanded only SystemRoot/WINDIR, while the Go broker
request correctly supplied SystemRoot/WINDIR/TEMP/TMP.
That request was rejected before private pipe read, helper import, or native child.
Root's existing receipt records closed Root/Go Jobs and specific release.
Those historical observations are preserved; this author did not repeat or accept them.
Old two-key requests are still rejected by the new exact four-key contract.

## Candidate behavior

main calls require_public_environment once in place of the original pair check.
The call precedes output directory creation, helper spec/import, private pipe read,
and child invocation. RawPin verification stays at its original earlier location.

Only the exact dictionary keys SystemRoot, WINDIR, TEMP, TMP are allowed.
Each value must be a nonempty non-whitespace string without NUL.
Proof-key, provider/secret/profile keys, and every extra or missing key are rejected.
TEMP must equal TMP literally. No os.environ inheritance is added.

TEMP must be absolute, canonical, existing, and strictly below
D:/作品集/ResearchOS/research-os/.local.
The original trial root
D:/作品集/ResearchOS/research-os/.local/mu-sdk-isolated-project-ed84838046934329a76733a005c9b162
and its containing ancestors/descendants are rejected lexically before proof-path
resolution/stat. The local root itself is also rejected.
Resolved aliases/escape/noncanonical paths are rejected after Windows case folding.
The physical directory must remain below canonical .local and cannot overlap
the trial namespace or existing canonical SystemRoot/WINDIR in either direction.
Only directory metadata is queried. No directory listing, file contents, private
resource, ExecuteClaim, original database, or DPAPI material is opened by the guard.

Schema, CWD, RawPins, public Arguments, PrivateStdinHelper, timeout,
private input size/read/wipe, owned helper, child result/closure, return exit,
error text suppression, and publisher retain their original Source/AST.
Four other definitions remain byte-identical and AST-identical.
Undoing the single call replacement and helper insertion recovers all 6201 base bytes.

## Boundary Source and Root execution

broker_temp_environment_boundary_test.py contains 17 public unittest methods.
They create only fresh synthetic public directories below fixed .local when Root
actually runs them. Alias/escape resolution negatives use synthetic metadata mocks,
not a claim about a real Windows junction. Trial negatives forbid resolution/stat
through mocks and touch no trial resource. No private pipe/helper/child is invoked.
All Source boundary results in this packet are NOT_RUN.

Root actual pure-unit entry, after non-author review, is the fixed Python executable
with -I -S -B -X utf8, the boundary Source path, --broker-source followed by the
absolute candidate broker Source path, --broker-sha256 followed by its bare SHA256,
and --verbosity 2. The boundary entry checks that exact Source pin before import.
Root preserves stdout/stderr/actual exit and full resource guard for that execution.
The Source author only parsed/compiled AST; no broker/unit import or helper call ran.

For the later native case Root creates a fresh fixed public HarnessConfig whose
BrokerSource RawPin binds this candidate's actual runtime path, sha256 prefix and
byte length. That exact pin belongs in the complete FrozenInputs/retained Source
guard. The public controller/harness request still forwards only four env keys;
controller proofRoot is consumed by the Go guard and is never sent to this broker.
Root must reconcile all actual compiler/product inventory and runtime public pins
without rewriting old T8 compilation receipts or assuming an unseen cache/closure.
Existing Root private stdin, grant, manual per-payload signing, specific release,
Job closure, database boundaries, and formal acceptance requirements remain in force.

Failure868 and earlier failures/counters are preserved without reset.
This packet has no new mechanical failure and no native/formal PASS.
HDF/MF include all nested input manifests. Exact top-level exclusions are MF.json
and postseal-tool-io.json only. Stop after seal; independent review/Root actual pending.
