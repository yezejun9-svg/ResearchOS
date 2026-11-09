# B3 rev4 independent security review

Decision: **APPROVED_SOURCE_FIXTURE_ONLY**. Pending source blockers: none. All eight full repository paths match the lease and frozen manifest `522a562016d0b94ea4576d956106b08068bbf47449b6f9de01683d12b709b2b2`; both patch hashes match.

- B3-F1: strconv is now used by full canonical epoch validation. Static unused-import defect resolved; compilation remains Root-owned validation.
- B3-F2: Final Sync/Close errors are joined into stream.err; complete stream hash requires err=nil. Collector joins both stream errors into capture.Err and CleanupComplete, and evaluator independently rejects stream errors. Error fixture now supplies otherwise-valid Job-limit evidence.
- B3-F3: Distinct stdout/stderr prefix/hash tags; terminal context includes Task/Run/epoch/source/native/helper/build/template/env/home/boot, encoded plan/hash/nonce/IPv4 port, argv/hash, ordered results, findings, control status, and verified queried Job limits. These receipts remain diagnostic and cannot mint the private observation.
- B3-F4: Read slice is clamped to remaining1MiB before read; zero remaining fails closed without ingesting another byte, including exact-cap streams. Listener consumes at most129 bytes and requires <=128. Drain timeout closes owned readers, attempts bounded join and retains UNKNOWN/error if a reader cannot join; no successful drain inferred.
- B3-F5: Exact create targets receive Host CREATE_NEW/remove pre/post controls. Existing child-created evidence is preserved because O_EXCL control cannot replace it. Fixed case order and preferred-reason ranking retain POLICY_VIOLATION while FindingCodes preserves other observations.
- B3-F6: exactReal inspects Windows reparse attribute for every ancestor and leaf before canonical path comparison. Fixed fixture leaves and S/QW/D/helper are checked pre/post; this is not a claim against malicious concurrent same-user mutation.
- B3-F7: Pure full B1 launch gate runs before qualification consumption: canonical positive epoch, bounded nonblank prompt, absolute paths, timeout, required callbacks and execution-input validity. Invalid-launch fixtures inspect no state consumption.
- B3-TIMING: ensureLaunch records final context failure; wrapper captures prepCtx.Err before cancel and rejects apparent success on expired/cancelled preparation. Overall Task remaining budget remains independently checked and passed to B1.

The fixed helper retains seven operations: one synthetic source read, denied sibling read, source/QW write-open and create denial, and one owned IPv4 TCP connect denial with Host pre/post controls. Its argv is the existing B1 policy projection followed by the reviewed sandbox command. No added grants, generic commands or fallback were introduced.

Private wrapper hooks are unexported; production construction binds concrete methods. Failure facts are copied only from a terminal original private handle and now include Native/helper/source provenance. Expected build pins are not represented as evidence that preflight executed the binaries. Archived JSON cannot reconstruct authority.

The collector applies/queries active-process16 and Job-commit2048MiB limits. It clamps ingestion, preserves bounded durable prefixes, retains stream errors and reports uncertain drain/join as failure. These are active-process/commit bounds, not cumulative-process/RSS claims. QW qualification does not directly probe the later B1 RPC cwd.

No tests, Native, model or probes were run by this reviewer. Root must audit a fresh registered compile/fake run against these pins. The short deadline fixture combines preparation/overall expiry; the separate preparation deadline backstop was inspected in source. Host/helper integration and a separately authorized synthetic Native qualification remain prerequisites. Finite probes do not prove the full permission graph; B1/B2 fences remain mandatory. Formal/product increment 0; prior blocked evidence is preserved.

