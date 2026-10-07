# What each unbindable registry key is waiting on

Companion to `registry_binding_readiness.json`. The dispatcher refuses every key whose state is not `BOUND`, so
these are not untested paths - they cannot produce evidence at all until the handler exists. The lines below were
read off the registry, the fork's own `package.json` scripts and the filesystem, not inferred from names.

## fork.install_deps and fork.build_worker - a build step, not a missing file

Both run inside `third_party/mu` with the pinned `npm_cli`: `ci --ignore-scripts --no-audit --no-fund`, then
`run build`. Their owner is recorded as `W02-99/W01-G03 rerun`, and both are wildcard-selector keys. Nothing is
missing here except the decision to execute them; they are prerequisites for the next line rather than evidence
gates of their own.

## fork.worker_launch_rpc - the handler does not exist yet, and its owner is accepted

The entry names `packages/coding-agent/dist/rpc-entry.js` under `third_party/mu`. That file **does not exist**;
`packages/coding-agent/package.json` produces it through `build:unbundled`
(`tsgo -p tsconfig.build.json && shx chmod +x dist/cli.js dist/rpc-entry.js`). So the order is fixed by the
fork's own build: install deps, build, then this key can bind. Owner card `W05-01` is **ACCEPTED**, which means
this is a post-acceptance obligation of a finished card - it has to be handled through that card's write scope
plus errata for the pins it moves, not by whoever needs the key first.

## fork.worker_stop - the entry is wrong, not unfinished

`argv: ["--stop"]` with `executable_tool: node` and `cwd: "."` would start node with a flag and no script. No
handler can be bound to that text, so this is a registry-correctness defect on an accepted card (`W05-01`), and
the honest fix is to design the stop path - a script or the CLI's own subcommand - and then bind what exists.
Recording it as "waiting for a handler" would hide that the entry as written can never run.

## The narrowing rule that applies to all four

Every one of these keys currently lists `*` for `task_id`, `check_id` and `case_id`. The dispatcher resolves by
exact key, so binding them cannot shadow another key - but a bound wildcard key answers every selector in the
tree for its own key, which is how a narrow handler ends up pretending to be general. Bindings should narrow
selectors to the owning task at the same time as flipping `state`, the way the staged `cli.entry_run` binding
does (`task_id=[W03]`, `check_id=[*]`, `case_id=[]`), and widen only by deliberate per-selector decision.

## Not claimed

Nothing in this file says any of these keys is bound, any card is accepted because of it, or any formal case is
closer to acceptance. `cli.entry_run` is the one that is bindable right now and it is still unapplied, because an
independent review of W13-01 is running against the same registry file.
