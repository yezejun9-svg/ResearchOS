# W14 LIVE preparation repair (2026-10-05)

The existing Native chooser selection, workspace binding, project, Goal, Task, and sealed profile were retained. No business table was written directly and no provider request was sent during this repair.

The first preparation attempt stopped because the frozen `sealArtifact` operation requires an `EXECUTOR`, `VERIFIER`, `SOURCE_ADAPTER`, or `SCHEDULER`; an `OWNER` alone receives 403. The profile upload and artifact creation now use a project-granted `EXECUTOR` credential. A later attempt stopped at `createContextBundle` because its frozen roles are `SCHEDULER` or `PLANNER`; that call now uses a project-granted `SCHEDULER` credential. Other preparation mutations remain on the published `OWNER` route. Qualification acceptance and runtime qualification use the independent `VERIFIER` credential.

If local state lacks `task_id` after a successful production `createTask`, preparation queries the existing Goal's `runtime_qualification` tasks read-only. It recovers only a unique Task whose input and requirement refs exactly equal the sealed profile and accepted requirement; a conflicting or ambiguous Task blocks preparation. It saves the recovered ID before the next API call.

The prior `BLOCKED` receipts remain at `execution/v2.4/receipts/W14/W14-01/live_setup_codex_20261005T153413.812869400Z_1f347b60489ec618ba376cb025368d7e.json` and `live_setup_codex_20261005T153555.919738100Z_5c1ba29495305962cce58496d61f5100.json`. The subsequent production `--prepare-only` call produced `live_setup_codex_20261005T153817.829818800Z_81f4d404cef088befc33c22fda974f7c.json` with `READY_TO_QUALIFY` and `qualification_executed=false`.

Read-only post-run inspection: project `e1a53506f75992a415ed6b81f1c4055e`, Task `43ad2190055206a109eadc821c8346fa` is `DRAFT` with a ContextBundle, profile Artifact `961ae61e30fa6b60df2bca5bd61e7254` is sealed and `CURRENT`, there is exactly one private qualification plan, and there are zero qualification Runs. The RuntimeRegistration is `REGISTERED` with no qualification receipt, as expected before `--qualify`.
