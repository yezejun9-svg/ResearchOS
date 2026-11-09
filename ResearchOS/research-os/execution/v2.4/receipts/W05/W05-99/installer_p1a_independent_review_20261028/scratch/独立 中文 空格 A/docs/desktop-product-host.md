# ResearchOS product host candidate

This package is a location-bound Windows product layout for reviewing the owned Desktop host. It is not an installer, upgrade, rollback, or uninstall package. `installed-product.json` binds the complete file inventory and five executable hashes to the absolute package directory. Moving or editing the package invalidates it.

The intended install paths are `%LOCALAPPDATA%\Programs\ResearchOS` for the package and `%LOCALAPPDATA%\ResearchOS` for the user's data and Chromium profile. The current builder emits an isolated candidate under the worktree `.local` for static review. It does not copy that candidate to either install path.

On first run, Electron takes the single-instance lock, claims an empty data root for this exact installation ID, and starts Core through its private management channel. A second launch requests either `show-ui` or `ensure-host` from the primary instance. The CLI checks the package manifest, both live process identities, discovery, the Electron-written supervisor witness, Native3 credential bootstrap, and `host.status` before sending host-bound commands. `doctor` reads only and does not start the host.

The tray exposes Open, Diagnostics, and Safe Exit. Closing the window requests the same safe shutdown as Safe Exit. If shutdown is busy or uncertain, the window remains usable and exit is refused. Once exit is confirmed, a later open uses the same data, project, and session with a new Core process identity. An orphan Core is a refusal requiring diagnosis; this package does not adopt or kill it.

The build product and automated tests provide only source, package, and simulated identity evidence. They do not establish a real GUI session, nonempty-data reopen, installed Start Menu entry, upgrade, rollback, uninstall, or formal W20 acceptance.

## Owned native qualification sequence

This sequence is for a separately authorized native review of one freshly built layout. Set `LOCALAPPDATA` to a new, empty review directory before either entry point runs. Keep that value unchanged for every command and Desktop launch in the sequence; the data root will be `<LOCALAPPDATA>\ResearchOS\data`. Do not move the built layout after its marker is generated.

1. Run `<layout>\bin\researchos.exe version` and inspect `installed-product.json` before any host-bound command. The product entry point is `<layout>\runtime\electron\electron.exe <layout>\apps\desktop`; the CLI starts the same Electron host for host-bound verbs.
2. Start a local listener that only counts connections on a chosen loopback port. Run `<layout>\bin\researchos.exe config set-model --model openai/lifecycle-no-call --base-url https://127.0.0.1:<port>/v1 --config-revision 0 --default`. This sends `host.configure` with `credential_ref: null`; saving the unverified model reference does not call `provider.probe` or the listener. Confirm the listener count stays zero.
3. Run `<layout>\bin\researchos.exe init <new-workspace-path>` and confirm the Native3 folder chooser. Record the resulting `project_id` and `workspace_ref`; keep the same config and data directory.
4. Open the Desktop entry point. Select that project, then create one session using the saved `openai/lifecycle-no-call` model reference. Record the `session_id`. Session creation is an offline persistence check; do not send a message or request provider qualification.
5. Run `<layout>\bin\researchos.exe status --project <project_id> --session <session_id>` while the Desktop host remains open. Use the tray Safe Exit or close the window. Confirm the private shutdown and process exit, then run the same status command again and open Desktop again. Compare the data, project and session IDs and observe a new Core process identity after the controlled restart.

The local listener, data directory and workspace must be newly owned review inputs. A source or mock pass does not establish that this sequence succeeded; its native receipts are separate.
