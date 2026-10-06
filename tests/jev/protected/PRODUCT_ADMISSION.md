# Completed frozen evaluation admission

The Windows service owns the holdout, labels, response bodies and credential. The
control application only queries the authenticated fixed aggregate. `--import-jev`
does not start the evaluator and cannot import a supplied aggregate.

Use the trusted local control CLI to provision two distinct, explicitly scoped
principals (one OWNER registrar, one VERIFIER). A principal definition uses the
existing `domain.Principal` shape, for example:

```json
{"ID":"evaluation-registrar","Roles":["OWNER"],"CanCreateProject":false,"Grants":[{"ProjectID":"<product-project-id>","TaskID":"","RunID":"","Restricted":true}]}
```

```powershell
control.exe --provision-principal registrar.json --credential-file .local/secrets/registrar.json
control.exe --issue-credential evaluation-registrar --credential-file .local/secrets/registrar-renewed.json
control.exe --import-jev <product-project-id> --credential-file .local/secrets/registrar.json
```

Credential files must be new paths, are private before any secret is written and
expire after 15 minutes. No administration command is exposed over HTTP. Existing
principal definitions and grants cannot be silently replaced. Local principal
roles do not establish OS isolation; that boundary comes from the independently
installed service.

Import registers only an opaque VERIFIER_ONLY artifact descriptor and the exact
public `evaluation/development/jev-v2/dataset.json`. It creates/reuses two DRAFT
Qualification records, one per fixed language key, and returns their version refs,
contract hashes, check IDs and current policy revision for independent review.

The independent VERIFIER uses the existing `POST /v1/projects/{project_id}/acceptances`
and `POST /v1/projects/{project_id}/qualifications/{object_id}/result` contracts,
including their Idempotency-Key and If-Match requirements. The acceptance subject
is the exact Qualification ref, run_id is null, and measurement_mode is LIVE.
The server recomputes checks and seals the fixed service summary; client checks
or statistics never grant authority. The registrar cannot accept its own inputs.

The result uses the returned acceptance ID and artifact_refs as test_receipt_refs.
Rates must match the authenticated key: false_accept/planned,
false_reject/positive_label_count and abstain/planned. Regardless of requested mode,
these sample sizes remain FAILED/ADVISORY and automatic authority NONE. No other
rubric's history or language sample counts are inherited.

Public simulated SQLite admission tests validate authorization, exact bindings,
idempotent registration and tampering rejection. They do not prove installed
isolation, real provider execution or an independent product acceptance.
