# ResearchOS product host candidate

This package is a location-bound Windows product layout for reviewing the owned Desktop host. It is not an installer, upgrade, rollback, or uninstall package. `installed-product.json` binds the complete file inventory and five executable hashes to the absolute package directory. Moving or editing the package invalidates it.

The intended install paths are `%LOCALAPPDATA%\Programs\ResearchOS` for the package and `%LOCALAPPDATA%\ResearchOS` for the user's data and Chromium profile. The current builder emits an isolated candidate under the worktree `.local` for static review. It does not copy that candidate to either install path.

On first run, Electron takes the single-instance lock, claims an empty data root for this exact installation ID, and starts Core through its private management channel. A second launch requests either `show-ui` or `ensure-host` from the primary instance. The CLI checks the package manifest, both live process identities, discovery, the Electron-written supervisor witness, Native3 credential bootstrap, and `host.status` before sending host-bound commands. `doctor` reads only and does not start the host.

The tray exposes Open, Diagnostics, and Safe Exit. Closing the window requests the same safe shutdown as Safe Exit. If shutdown is busy or uncertain, the window remains usable and exit is refused. Once exit is confirmed, a later open uses the same data, project, and session with a new Core process identity. An orphan Core is a refusal requiring diagnosis; this package does not adopt or kill it.

The build product and automated tests provide only source, package, and simulated identity evidence. They do not establish a real GUI session, nonempty-data reopen, installed Start Menu entry, upgrade, rollback, uninstall, or formal W20 acceptance.
