# W13-01 registration: what the real apply exposed

W13-01 was registered ACCEPTED (ACCEPT_WITH_RESERVATIONS, 0 blocking issues) at checkpoint
revision 96 -> 97 by `.local/register_w1301_accepted.py --apply`. The verdict is
`receipts/W13/W13-01/independent_review_round3.json`, settled sha256 3db78045c7c10569...,
reviewed at ef94c153, reviewer `qoder-desktop:/root/w1301_verifier_r3` (fresh identity, had
ruled on no card). The written row carries 26 evidence entries with digests recomputed from
the files on disk, both the verdict digest and the receipt digest among them, and the verdict's
7 reservations / 10 limitations / empty blocking array. The other 17 rows were verified
byte-identical before and after; failure counters 17 -> 17 and integrity events 60 -> 60, neither
reset. This card-level acceptance accepts nothing for parent W13 and signs no formal case.

Two defects in the registrar were found only by running it against the real files, not by its
own guard suites:

1. dry-run and apply computed the evidence set differently. Dry-run filtered on `isfile`, apply
   hashed `sorted(os.listdir(RD))` raw and crashed on the `invocations` directory
   (PermissionError). Apply now uses the same isfile-filtered set. Nothing was written by the
   crashed run - checkpoint stayed at 96 and step_state had no W13-01 row - because the crash
   happened while building the record, before any temp-file write.
2. the registrar assumed `step_state.json` holds a dict keyed by step id. It is
   `{package_version, plan_sha256, schema_version, steps: [...]}` with `steps` a LIST of rows keyed
   by `id`, in registration order, whose `evidence` is a list of `{path, sha256}` with paths
   relative to `execution/v2.4`. The row was rewritten to match the live schema; `id`, `verdict`,
   `verdict_file`, `note`, `executor_id`, `accepted_at` all follow the W05-01 precedent. Only the
   three condition arrays are additions, so the acceptance does not lose the reviewer's conditions
   the way the 17 earlier rows did.

Consequence, since repaired the same session: 7 cases in `.local/test_register_guards_w1301.py` (3)
and `.local/test_register_rounds_w1301.py` (4) went red because their fixtures mirrored the
registrar's old wrong assumption instead of the file on disk - a fixture that agrees with the tool it
tests proves nothing. The fixtures are now **seeded from the live `execution/v2.4/step_state.json`**
(the throwaway copy inherits its top-level key set with `steps` emptied), `row(st)` asserts the list
shape before reading it, and one positive control was added that inspects the row apply actually wrote
(`id`/`verdict`/`verdict_file`/`accepted_at`/`verifier_id`/`executor_id` present, `evidence` a non-empty
list of `{path, sha256}` with 64-hex digests). Both suites pass: 15 and 9 cases, FAILED: none, with the
refusal cases still refusing - "no verdict on disk yet ... that is not a rejection, it is a missing
artifact". The refusal guards themselves (accept vocabulary, empty blocking_issues, ruled-identity
collection over both verifier_id and reviewer_id, instant comparison, receipt-hash match, CAS bump,
double-registration refusal) were exercised by the real registration and behaved.

What is still owed on W13-01, unchanged by this: the M26 provider catch-all mutant survives, the C23
frozen ids are still not emitted, `desktop.shell_launch` is still UNBOUND, step 4 is still blocked by
resource `Windows_desktop_session`, and 13 assertion rows have neither a mutant nor a stated reason.
