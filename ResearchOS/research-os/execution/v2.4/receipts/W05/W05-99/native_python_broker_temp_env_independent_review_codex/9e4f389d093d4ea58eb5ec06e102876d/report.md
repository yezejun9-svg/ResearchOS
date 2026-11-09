# Independent BR4 Python broker Source review

Decision: SOURCE_ACCEPTED_PENDING_ROOT_BOUNDARY_ACTUAL. Authority NONE; formal acceptance false. Independent static review d2edc3 returned outer0/markedPython0, 87/87 checks passed, 46 public inputs held through verification and then truly closed (retained0/errors[]). Separate gpt-6-astra high semantic review accepted this bounded Source change with the qualifications below. No candidate broker, boundary tests, main, controller/context, private helper, native process, Go, SQL, key, sign or application model runtime was executed. Only the reviewed SourceReadGuard infrastructure was imported for public file handles.

The fixed BR4 HDF ed0f388870aef974f9577e6d5146637d5a1a77ce6b22c57e989227654de05824 /6761 and MF deab5d3bb0fc512c37808a4dcd9b66d370dcd0c1ae14b84e1949fcfdb915ebdc /9803 match. All25 MF members match exact SHA256/bytes and the recursive inventory with only top-level MF.json/postseal-tool-io.json exclusions. The older base MF is a dict with14 members, all independently reverified. Eight source/snapshot pairs, including failure868, match byte-for-byte. The author's Source-guard closure is explicitly static; actual Root retained runtime guard is still NOT_RUN. This review does not silently turn it into a runtime closure claim.

Candidate root_only_native_broker.py is70b8eba1de168849d041488ac9268da60fd2ae8a059cc9518e9dc93d0cd4b87c /8562. Independently removing exactly one inserted helper and reversing exactly one guard replacement reproduces every6201 base byte, SHA5f3b4e957d85aeb091a2a801d72bcbf2afb2135c42e0a0a86fc740ff9f99750e. raw_pin, require_pin, write_new and read_private_pipe remain byte/AST identical; the rest of main remains AST identical. The recovered base is retained as evidence.

Lines67-74 require exactly SystemRoot/WINDIR/TEMP/TMP in a dict, nonempty non-whitespace NUL-free strings, and literal TEMP==TMP. Old two-key requests remain rejected. There is no new os.environ inheritance. Lines83-110 require a Path-resolved canonical existing absolute strict child of fixed R/.local. Component-aware case-folded commonpath rejects outside/root/trial namespace; lexical trial checks precede proof directory metadata, and both physical trial and system overlap checks are symmetric. The helper performs validation and directory metadata only.

main line131 invokes that guard before output.mkdir134, helper spec135/import137, private pipe138 and child140. Original RawPin public file reads126-127 remain before the ENV guard. Schema/CWD/pins/Arguments/private input read-size/wipe/owned helper/result closure/error suppression/return/publisher behavior retain the baseline.

The17 boundary test methods exactly match static evidence and boundary matrix. Every actual result remains NOT_RUN. Source pin verification precedes import, and tests call only require_public_environment with synthetic public directories. No native/pipe/helper/SQL path is invoked by the test Source.

Four explicit limits are retained:
1. Path(value) itself normalizes /./, repeated and terminal separators. The accepted canonical property is the physical directory represented by Path after normalization, not one unique raw ENV spelling. Raw equivalent strings may be forwarded unchanged; no ordinary physical isolation bypass was found.
2. The system overlap test covers equality and system-as-ancestor. The reverse system-descendant branch is present in Source but has no dedicated case in these17 methods; full boundary coverage is not claimed.
3. Alias/escape tests mock Path.resolve; they are not real Windows junction verification.
4. Existing error handling at candidate161-163/base115-117 may write broker-error.json under a pre-existing output after rejection. It is unchanged; guard-before-mkdir does not imply all rejection paths are write-free.

Root must next run the fixed public boundary tests under actual resource guards, preserve actual stdout/stderr/exits/closure, then bind the new BrokerSource RawPin into a freshly reconciled HarnessConfig/FrozenInputs. Existing compiler/product/test/embed evidence and failure868 remain immutable. Native positive, Owner, nine-case coverage, original business and formal acceptance are not granted by this Source review.

Canonical files were only briefly pinned, never held; before/after matched. Main, canonical, prior Source and T* worktrees were not written. No original trial contents/private resource was read. New mechanical errors0; global provider usage NULL; formal progress0/42. Full actual review tool input/output, Source read outputs and exact author I/O copies are preserved. FINAL STOP.

