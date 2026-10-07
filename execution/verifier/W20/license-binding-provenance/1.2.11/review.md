# Native binding license provenance: 1.2.11

Verdict: **UNRESOLVED**. The first-party MIT license text now has a precise official source-to-binding provenance chain. Complete third-party notice coverage for the published native binary has not been established. This evidence does not clear the existing gap or change redistribution status.

## Exact identity and provenance

- Package: `@rolldown/binding-win32-x64-msvc@1.2.11`.
- Official metadata: https://registry.npmjs.org/@rolldown%2Fbinding-win32-x64-msvc/1.2.11 . The previously archived response declares MIT but contains no license text.
- Official attestation: https://registry.npmjs.org/-/npm/v1/attestations/@rolldown%2fbinding-win32-x64-msvc@1.2.11 . Saved raw response SHA-256: `46e9d4162f1d28f51efece062ea10357f8ba1210931f50b4f81fe3c4acb0c135`.
- Decoded SLSA statement subject is the exact package/version. Its SHA-512 digest equals the current lock entry and the existing tarball audit: `fcfccaab3009d378b5f68cb622d3efcaf6958ce8c108d9df689b3ccaf51d1812a68844a09eb2524366b077cd50cc56db9c09aeed83bd66726b0c26fd55224f44`.
- SLSA resolved dependency commit: `8df421985114ecfaf52cce038d4a5a6ea8c05408`. Official tag API https://api.github.com/repos/rolldown/rolldown/git/ref/tags/v1.2.11 identifies the same commit.
- SLSA workflow: `.github/workflows/publish-to-npm.yml`; reported run: https://github.com/rolldown/rolldown/actions/runs/36006813531/attempts/1 . The run page itself was not inspected.
- This establishes consistency among registry-supplied attestations, pinned source, tag, lock integrity, and an existing tarball audit. DSSE/Sigstore signatures and transparency proofs were not independently verified. No binary was fetched, rebuilt, or executed in this task.

## Binding-specific source connection

All source paths below are pinned to the exact commit, not `main`:

1. [Release build workflow](https://github.com/rolldown/rolldown/blob/8df421985114ecfaf52cce038d4a5a6ea8c05408/.github/workflows/reusable-release-build.yml) selects `x86_64-pc-windows-msvc`, invokes `ci:build-release-binding`, and uploads `packages/rolldown/src/rolldown-binding.*.node` under `bindings-${matrix.target}`.
2. [Root package manifest](https://github.com/rolldown/rolldown/blob/8df421985114ecfaf52cce038d4a5a6ea8c05408/package.json) resolves that script to `rolldown`'s `build-binding:release`. The [package manifest](https://github.com/rolldown/rolldown/blob/8df421985114ecfaf52cce038d4a5a6ea8c05408/packages/rolldown/package.json) specifies version `1.2.11`, binding package name `@rolldown/binding`, binary name `rolldown-binding`, and the Windows x64 target.
3. [build-binding.ts](https://github.com/rolldown/rolldown/blob/8df421985114ecfaf52cce038d4a5a6ea8c05408/packages/rolldown/build-binding.ts) explicitly selects `../../crates/rolldown_binding/Cargo.toml` and package `rolldown_binding`.
4. [Binding Cargo manifest](https://github.com/rolldown/rolldown/blob/8df421985114ecfaf52cce038d4a5a6ea8c05408/crates/rolldown_binding/Cargo.toml) explicitly sets `license.workspace = true`. [Workspace Cargo manifest](https://github.com/rolldown/rolldown/blob/8df421985114ecfaf52cce038d4a5a6ea8c05408/Cargo.toml) sets `[workspace.package] license = "MIT"`.
5. [Publish workflow](https://github.com/rolldown/rolldown/blob/8df421985114ecfaf52cce038d4a5a6ea8c05408/.github/workflows/publish-to-npm.yml) downloads those binding artifacts, creates the npm platform directories, moves the artifacts there, and publishes the binding packages through the NAPI prepublish hook.

This is explicit binding crate license inheritance in upstream's own manifest, with a concrete build and publish chain. It is stronger than assuming that a sibling/parent npm package license automatically applies. It does not prove the entire linked binary has only one license.

## Candidate texts and exact hashes

| Text | Official pinned source | SHA-256 |
|---|---|---|
| First-party MIT text | https://raw.githubusercontent.com/rolldown/rolldown/8df421985114ecfaf52cce038d4a5a6ea8c05408/LICENSE | `23ecfff35a5a2e80d92142f75228912c3b1abc4b5a8337a821ff4397e2f9f734` |
| Upstream derived-code notices | https://raw.githubusercontent.com/rolldown/rolldown/8df421985114ecfaf52cce038d4a5a6ea8c05408/THIRD-PARTY-LICENSE | `a877291d800ed43692f3f9ae09d8e01cc6f7293ad39d43896059c188ffbb8b7c` |

The first-party text names VoidZero Inc. & Contributors and points to the repository's third-party license file for externally maintained code from which parts are derived. Its link uses `main`; this investigation instead fetched the same file at the exact release commit. The pinned third-party file contains two MIT notices: Rollup contributors (2017) and Evan Wallace (2020). It contains no binding-target dependency inventory or assertion that these are all third-party components linked into the Windows binary.

The binding Cargo manifest lists additional external dependencies, including NAPI, OXC and a Windows-applicable mimalloc dependency. Their presence in the manifest is evidence that the two-notice document alone cannot establish a complete native dependency notice inventory; it is not a finding about any particular dependency's redistribution requirements or proof of every dependency's final binary inclusion. No dependency license is inferred solely from its name.

## Why the gap remains

- Existing archived tarball audit found only `README.md`, `package.json`, and `rolldown-binding.win32-x64-msvc.node`; no license document. That earlier audit is reused, not repeated.
- Upstream's `Copy Licenses` step copies root texts to directories at `packages/` depth one. It does not copy them into `packages/rolldown/npm/<platform>`. This explains a packaging boundary, but does not supply a complete native notice document.
- The untruncated GitHub tree metadata for the pinned commit had 18,502 entries. A path-name search for license, notice, copyright, cargo-about/cargo-deny and their usual config names found root `LICENSE`, root `THIRD-PARTY-LICENSE`, and two test-fixture licenses. The reduced search result and full-response hash are saved. This is a bounded filename search; it does not prove that no relevant statement exists elsewhere.
- No official binding-specific complete third-party notice inventory, generated license bundle, or maintained statement asserting complete native artifact notice coverage was established from the inspected release sources.

To resolve the remaining evidence question, a later authorized step would need a complete, version/target-specific upstream notice source or separately evidenced linked-dependency license inventory. This task does not synthesize that inventory or make a legal determination.

## Files and boundaries

`provenance-evidence.json` records all retrieved file URLs and SHA-256 hashes, input file hashes, exact source commit, positive checks, and limitations. `upstream/` holds the exact fetched text sources. `npm-attestations.json` retains the official response; the two payload JSON files are decoded statements. Three attempted generated-package source paths returned HTTP 404 and are recorded as unavailable, consistent with the workflow generating/copying them during publication.

Only this verifier directory was written. No source/build/SBOM/license ledger edits, ResearchOS main-license selection, gap clearance, archive repack, native download, native execution, paid API usage, or external account creation occurred. The final bundle was not reverified. The fetched files are retained as audit evidence; no disposable helper scripts were created.
