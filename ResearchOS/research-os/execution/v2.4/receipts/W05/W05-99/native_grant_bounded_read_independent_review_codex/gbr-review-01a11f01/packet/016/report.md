# GPA-R01 bounded-read Source revision

SOURCE_FIXED_PENDING_INDEPENDENT_REVIEW. Only read_ref changes: open the exact pinned file in binary mode, request at most expected bytes + 1, reject a short or overlong result, then verify SHA256. The old error message and remaining semantics are preserved. Full-file inverse restores the original 23,856 bytes and all other top-level AST nodes are identical. Old helper/HDF/MF/calling contract remain unchanged.

Both runtime readers were tested through fake binary streams: each received exactly expected+1, including zero-length, short, one-extra, virtual trillion-byte source, cap-sized declaration, invalid typed lengths, digest mismatch and read failure with stream closure. There are 13 controls per reader, 26 boundary controls total; 45 controls including request selection and static wiring passed on the final standalone builder. No real archive main, builder main/compose, Win32 guard, native/API/SQL/Go/private/model operation ran. Source controls execute pure functions only.

The helper retains the old CLI/request schema and full 28+29 inventory/backup/rehearsal/cipher closure, alias, output boundary, finally guard and nonacceptance claims. Its remaining output verification read_bytes is after an exclusive own output write, not guard-before input reading; this revision intentionally changes only read_ref as assigned.

The separate request-builder statically embeds the pure metadata predicates and inventory; it does not import, execute or invoke the helper. It bounded-reads HelperSource only to verify its exact pin. Independent NativeReviewer must review this delta and the builder's AF review before Root proceeds. No new failure origin; last observed Parent next917 is read-only.

