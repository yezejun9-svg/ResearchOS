# CP432 normal Desktop first-use distribution, retry 03

The new package is `C:/Users/yqyyds/.codex/researchos-resource-cache/normal-first-use-causal-retry03-20261012`. It contains 58 approved shipped files. It has not been launched, and this assembly made no model, tool, qualification, Owner, GUI, or control call. Previous distributions and the original D data root were left untouched.

Component vector: Desktop UI/source-bound validator `90b72d19c760974af46dc4243c56107e886d7cf6`; reviewed Core control/verifier `b45008a754414cd795a4be396475aab8e74b2a8c`; fixed Mu SDK `8dfebe36508ac0c2508735bb866756dab9283e74`. Main was read at `84d6fc0f2018404170ec3fa4295c56cf4453a15a`. This is a component composition, not a new whole-Core build.

The 6441-input Desktop bound digest remains `e99cfe80d39fef7d797c505e4a6a3cf4906877f3b7cfcce3e05888164f35191b`, with validator SHA-256 `cfdcbd5dd3c46cb5b44ad6c7e57b00b21a51126191ce2f3294de566d9399680e` and zero drift. Fourteen main/preload modules match the descriptor and Main Git blobs; three React assets match the descriptor; all 32 public schema/migration files match the approved public root and Main Git blobs. The Core binaries match their independently reviewed hashes. `retry02-retry03-delta.json` verifies that only the two Core executables and the new installation manifest differ from retry02; the other 55 files are byte-identical.

`composition.json` records each shipped file's source, size, and hash. The verifier installation manifest uses the new C absolute path and the reviewed `b450` verifier hash. `manifest-acl.json` records its protected single-ACE current-SID ACL. `verification.json` records a read-only check of all 58 package files. Assembly, ACL, and verification command output is preserved here.

Status: components assembled and hash-verified; activation not started. Root owns the ordinary GUI first-use attempt. Product qualification, installer release, parent, and formal acceptance remain unclaimed; formal increment is 0.
