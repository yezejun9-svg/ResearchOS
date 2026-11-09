# CTL3 Root controller public temporary environment bridge

Status: SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_FRESH_ACTUAL.
Authority: NONE. Formal acceptance: false.

This packet changes one Python Source file only. Main, T5/T6/T7, canonical files,
CTL2, and the native broker TEMP Source packet remain untouched.
This author did not import the controller/observer, call context or its new helper,
launch a Job/native process, execute SQL, sign/release a payload, or use a model.
Python AST parsing and compile-to-code checks are static checks only.

## Fixed public environment

The existing ENV_KEYS remain intact. The only additional allowed key is
RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT.
Unknown keys, non-string values, NUL values, and missing SystemRoot/WINDIR/TEMP/TMP
retain their existing rejection gates.

If the new key is present, proofRoot, TEMP, and TMP must be the exact same string.
ProofRoot must be nonempty, absolute, canonical, and an existing directory strictly
below D:/作品集/ResearchOS/research-os/.local.
It must not be the original trial directory
D:/作品集/ResearchOS/research-os/.local/mu-sdk-isolated-project-ed84838046934329a76733a005c9b162,
a descendant, or a containing ancestor of that directory.
The lexical trial check precedes resolving or statting the proof path.
The existing canonical_path gate rejects aliases/junction/symlink escape or any
noncanonical spelling whose resolved path differs after Windows case folding.
The physical root remains below the canonical local directory and cannot overlap
canonical existing SystemRoot/WINDIR directories in either ancestor direction.
The helper reads directory metadata only, never directory listings or file contents.
Original trial database/private resource contents are not read or snapshotted.

Without the proof key, this new optional guard is not called. Prior CTL2 context
behavior is preserved; this does not assert that an old config can launch under
the newer broker Source's required proof-key contract.
Schema researchos.root-native-migration-controller.v1 is unchanged.

## Bridge and unchanged gates

Root supplies the fixed cfg.Environment explicitly; the existing worker copies
that dictionary and adds the existing harness config reference.
It never inherits os.environ. The proof key reaches only the fixed harness.
The separate native broker Source consumes the proof and forwards only the four
reviewed public keys SystemRoot, WINDIR, TEMP, TMP to request and command.Env.
That proof key is not forwarded to the backup child.

All existing full frozen-input, actual compilation, Source identity, private stdin,
Owner/Root grant, manual per-payload signing, specific-release, native Job closure,
atomic publication, Case9, four-minute grant, and read-only SQL boundaries are
preserved. The other 30 top-level functions/classes retain exact raw Source and AST.
Removing the one new optional context guard recovers the original context AST.
The exact inverse recovers the complete CTL2 controller bytes.

## Root actual prerequisites

root-public-context-prerequisites.json maps all 12 fixed config fields, eight
public references, seven harness RawPins, compiler/test/embed/product inventory,
and every OriginalOwnedHelper.runtime_resource_paths reference required in
FrozenInputs. Root must create fresh fixed public paths and a full retained Source
guard closure; this packet does not invent unobserved resource pins or cache hits.
ControllerSource must pin the actual executing __file__, including a byte-identical
Root fresh copy if used. The native broker TEMP Source must be independently
reviewed and compiled in a fresh Root composition before the actual harness.

boundary-matrix.json contains 16 expected public environment boundaries.
All are NOT_RUN. Pure context/helper results require Root's actual input, output,
exit, and resource closure. A pure context result cannot authorize native launch,
signing, release, or acceptance of a formal product case.

## Failure and exact time preservation

Original failures 835/841 and every earlier failure remain preserved; no count resets.
Root's original 835 diagnostic included rounded uint64 FILETIME values. Root843
qualifies the original diagnostic without rewriting it.
The held native Go invocation was read as public raw bytes and parsed with Python
int; its exact decimal FILETIME is 134359787460741284.
Root's task reports rehearsal FILETIME 134359787476336016; this packet labels that
decimal string as Root-reported actual, without opening the rehearsal child file.
No JavaScript Number is used to reconstruct those uint64 values.

HDF/MF close this Source packet and its snapshots/IO. Only the top-level MF.json
and postseal-tool-io.json are excluded from MF members; nested input MF.json files
are members. Postseal IO independently records the seal call and its actual exits.
This Source author stops after sealing. Independent review and fresh Root actual
remain pending; no self-approval or formal PASS is issued here.
