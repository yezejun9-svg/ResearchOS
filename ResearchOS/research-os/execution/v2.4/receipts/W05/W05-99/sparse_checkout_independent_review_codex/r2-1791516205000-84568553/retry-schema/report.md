# T11 sparse checkout revised Source independent review

Verdict: SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL. This accepts the exact revision-exact-paths Source package only. No Git/Go/native/SQL/model action or formal product acceptance occurred.

70/70 independent checks pass. 24 changed-caller, accepted-base, previous-review and installed Git documentation inputs were held by SourceReadGuard and closed unchanged with zero retained handles.

The old sparse package is preserved as REQUEST_CHANGES in sibling review r1-1791516205000-32f0d0b8. Its prepare O and validate O/ISO still named old T11 outputs because the generator silently skipped unmatched replacements. The revised generator uses exact old literals and expected counts, and its actual generated paths now match the advertised new worktree, isolation and targeted output. All three were absent at review. The previous, never-used validate scratch remains absent and uses exclusive fresh mkdir; this does not reuse prior results.

Git semantics were checked against the installed official git-read-tree, git-sparse-checkout and gitignore documentation, independently from inverse text reconstruction. The 20-line non-cone pattern contains real LF separators, includes root regular files, recursively includes the 15 declared product directories, and includes execution root regular files plus execution/toolchains recursively. Other execution child directories are excluded, including v2.4 receipts and verifier. All original declared compiler-product inventory roots are included.

The sequence is six owned Git invocations: head-before, tracked-status, staged-status, create-worktree --no-checkout --detach, checkout-product-source via read-tree -mu HEAD, head-after. Patterns are created exclusively in the newly created worktree's info/sparse-checkout after resolving its .git pointer and verifying both containment under repository .git/worktrees and the metadata backpointer. Sparse flags and empty hooks are command-scoped; no git config writer was introduced. Actual checkout behavior and disk use still require Root execution receipts.

Both generated entrypoints reverse exactly to the previously accepted T11 bytes; choice bytes are identical. All existing helper functions and finally bodies are AST-identical, including owned invocation safety and five guard closures. The complete compiler-list/build/test/embed/product/compiler-tools block is byte-identical. The 58 Source members, 54 preserved parents, 2 selected parents and 52 unexecuted parents remain unchanged. Ordinary history20/full release/program rehearsal authority stays BLOCKED.

Root must supply fresh exact checkpoint SHA/bytes/revision, choice SHA/bytes and isolation-ready SHA/bytes. The runtime input guards remain necessary. This scoped revision review did not freshly reopen all 833 transitive prior inputs. The previous review's guard.final.json is a before/after pin-equality artifact; it was verified as that schema, not misrepresented as a SourceReadGuard observation.

One reviewer mechanical failure occurred before the successful retry: provisional/requested ordinal 896, KeyError closed at review.py line 35, actual outer/Python exit 1, chunk f7489e, ROOT_PYTHON_EXIT=1. Its original input/output and source are preserved, and its actual SourceReadGuard closed PASSED with zero handles. The corrected immutable retry completed exit 0, chunk f7b761, ROOT_PYTHON_EXIT=0. This is a single reviewer failure, not a new candidate failure or multiple failures for separate findings. No counter was reset.

Authority is SOURCE_REVIEW_ONLY. Native positive, Owner, nine cases, original trial, business readiness and formal acceptance remain unapproved. Review stopped after sealing.

