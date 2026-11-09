# Revision 04 provenance

This new C-only candidate copies frozen single-task revision 03. The exact
revision-03 freeze is preserved as `03-FROZEN.json`; revisions 01–03 remain
unchanged. Revision 03's independent source review was
`APPROVED_SOURCE_FIXTURE_ONLY`, not runtime approval (review SHA-256
`81f17d92cb4efa28b4f55e5102ee267654dc6bfbf4d7ff5ed390cc7d398dc962`).

The sole new Native change comes from frozen Native controller 05. Its actual
zero-model flow 03 observed a single owned warning Button with control ID 2;
the MessageBox return IDOK value 1 is not its child control ID. The helper now
requires that exact ID 2 Button, unique among all observed Buttons, and
rechecks it before one queued click. The chooser's separate direct ID 1 Button
policy remains intact. The helper differs from Native05 only in its explicit
zero-task/zero-model Native-stage guard under this one-Harness-Task scope.

The runner adds Native05's exact selector evidence/path/hash gate. The scope
template adds the same selector, pinned to actual flow03's public helper receipt
SHA-256 `392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423`,
event `WARNING_IDOK_CHILD_METADATA` sequence 36, control ID 2, Button count 1.
Both helper and runner read and hash that receipt before acting. The frozen
revision-03 Task identity/pending/Run logic is unchanged.

The Native prerequisite has still not succeeded. The template remains inert
with no prior successful flow/Job hashes, Root launch approval, or harness
file hashes. No app, Native helper, Codex CLI, task, or model was run by this
preparation. Any further change requires a new revision directory.
