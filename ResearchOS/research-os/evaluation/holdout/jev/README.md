# Independent protected evaluator source

This directory contains public code, not a generated holdout. No formal seed,
corpus, input, label or per-case output is committed or produced by the build.
`GenerateProtected` checks SCM execution and the exact virtual-account token
user `NT SERVICE\ResearchOSVerifierCanary` before reading fresh entropy. Only
the installed trusted service may call it and retain the returned `Batch`.
The package creates no files, processes, network connections or logs.

`GeneratePublicFixture` uses one expressly public fixed seed. Its return value
has `split=PUBLIC_FIXTURE`, `access_class=PROJECT` and contributes **zero** formal
holdout examples. Tests use only that fixture and test that the current ordinary
identity cannot generate a protected batch. The code-level tests are not proof
of installed service isolation or independent execution of a formal evaluation.

The shared rubric is `objective-source-records-v1`, model `jev-1.13.0`, threshold
`0.8`, task type `evidence-validity`. `Questions`, `NewRequest`, `ScopeFor`,
`Rubric` and `RubricHash` are the public development integration interface. Older
`objective-evidence-v1` development counts cannot be transferred to these keys.

The private batch contains 30 generated cases, 15 `zh` and 15 `zh-en`. Each
candidate receives **only its `Case.Request`**. Labels, critical flags, source
families, semantic/paraphrase groups, truth hashes, case identities and seed are
private evaluator metadata. A language pair belongs to the same source group;
30 examples are not 30 independent empirical sources. The batch explicitly
records zero independent empirical sources. It does not establish open-ended
research, scientific validity or general adversarial robustness.

The independent labeler excludes the entire previous
`synthetic-six-checks-template-v1` family, the announced
`dev-v2-ledger-documents` umbrella, all six development v2 families named in
`ExcludedFamilies`, and their translations, numeric variants and synonymous
derivatives. The new code was independently authored against the public rubric
without using candidate model answers. Distinct family identifiers are only
provenance metadata; names alone do not prove source independence. Review must
also compare authorship and generation logic with the frozen public development
generator, without reading the installed formal batch or tuning its content.

`Recompute` calculates labels directly from original fields. It ignores stored
labels and prior model judgments. `Validate` regenerates a private batch from its
private seed, recomputes labels, and checks exact content, scope, rubric, source
groups and all bindings after JSON persistence. The caller must reject any
validation failure, keep private errors/raw data inside the service and publish
only the separately reviewed aggregate. A passing generator test does not grant
qualification. In particular, 15 holdout cases per key do not meet a 30-case
qualification minimum; the first run remains FAILED/ADVISORY with no automatic
authority even if every observed choice is correct.

Build and fixture verification:

```powershell
& $env:RESEARCHOS_GO test ./evaluation/holdout/jev -count=1 -v
```

The service integration must freeze this source hash and public rubric hash
before generating formal data; record original official responses and actual
service identity/permission evidence; retain raw bytes, labels and per-case
feedback exclusively in its private store; and disallow repeat adaptive queries.
