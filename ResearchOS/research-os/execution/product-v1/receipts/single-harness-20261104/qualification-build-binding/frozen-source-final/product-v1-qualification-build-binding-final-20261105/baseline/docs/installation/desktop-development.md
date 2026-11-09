# Windows Desktop development tree

This workflow builds an isolated, repository-shaped development tree. It is not an installer, an upgrade path, or evidence of a native run. Keep the source worktree, build output, and runtime state separate. Never point the launcher at an existing ResearchOS data directory.

## Build

Use a clean, isolated source worktree and pinned tools. Create a unique output path under that worktree's ignored `.local` directory and a unique receipt path. The example uses existing local public caches and does not download packages:

```powershell
& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -B -X utf8 apps/desktop/build-development.py `
  --go 'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe' `
  --node 'C:/nvm4w/nodejs/node.exe' `
  --electron-dist 'D:/作品集/ResearchOS/research-os/apps/desktop/node_modules/electron/dist' `
  --module-cache 'D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod' `
  --web-modules 'D:/作品集/ResearchOS/research-os/apps/web/node_modules' `
  --mu-common 'D:/作品集/ResearchOS/research-os' `
  --output '<isolated-worktree>/.local/desktop-complete-unique' `
  --receipts '<approved-canonical-receipts>/build-unique'
```

The builder first snapshots tracked files and the seven scoped source files. It runs the existing client-wire builder and the current `adapters/runtime/mu/build.mjs` producer; the latter rechecks all 5083 public vendored Mu files from the common Main repository and pinned esbuild. It then compiles Core and the real verifier with the locked Go compiler, copies the complete pinned Electron runtime, the current Mu output, all numbered SQLite migrations and session migration, four Core cwd contracts, and the compiled React assets. It verifies source and public Mu input hashes again and writes `development-manifest.json` with every output file's SHA-256 and size. A failed subcommand leaves raw stdout, stderr, exit and first failure in the new receipt directory; do not overwrite or retry with the same inputs.

The verifier registration contains the absolute path in this output tree, and the manifest records the output root. Moving or copying the tree invalidates the bound paths. A fresh build is required for a new location. The Mu vendor and package cache are external public build inputs; the resulting bundle and metadata are copied into the output tree.

## Validate without starting processes

Run the launcher in dry-run mode with a **nonexistent** state path outside the bundle. It verifies every inventory file, the verifier and Mu bindings, the Electron files, the React assets and migrations, then reports the exact spawn arguments and environment variable names. It does not create the state path or start Electron or Core.

```powershell
& 'C:/nvm4w/nodejs/node.exe' '<isolated-worktree>/.local/desktop-complete-unique/launch-development.mjs' `
  --bundle '<isolated-worktree>/.local/desktop-complete-unique' `
  --state '<isolated-worktree>/.local/new-state-unique' --dry-run
```

The launcher refuses missing or modified files, symlinks and junctions, existing state directories, case-insensitive environment-key collisions, and stale manifest bindings. Its child environment is constructed from essential Windows paths plus new state-specific data, discovery, Electron user data, profile and temporary paths. It does not pass ambient `RESEARCHOS_*`, `ROS_DESKTOP_*`, `NODE_OPTIONS`, `NODE_PATH` or `ELECTRON_*` values to the child.

## Later native observation

Only under a separate approved native-run scope, use `--launch --smoke` with a new state path. The launcher then creates that state and runs the pinned Electron executable from the bundle. A smoke result is accepted only when the real Desktop reports a React renderer, management `READY`, a successful native `host.status` probe for the owned Core, and a `shutdown_confirmed` event with the same PID, creation time, image hash and Host ID after `process_exit_confirmed`. A failed or uncertain shutdown is a failure and leaves its state for diagnosis. The code and mock tests in this branch do not provide that native observation.
