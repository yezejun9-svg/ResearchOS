-- Open original researchos.sqlite with URI mode=ro, never immutable=1 on live WAL.
-- Read-only evidence templates only; bind original ids from normal UI/receipts.
-- Never select credentials, cookies, idempotency headers, or private verifier Job.
PRAGMA query_only=ON;
BEGIN;
SELECT id,project_id,revision,writer_epoch,writer_client_id,lease_expires_at,
       workspace_ref,model_config_ref,core_build_id,sealed_at,archived_at
FROM client_sessions WHERE id=:session_id AND project_id=:project_id;
SELECT principal,project,operation,key,request_hash,body,created_at
FROM idempotency WHERE project=:project_id AND key=:request_id
AND operation IN ('host:qualification-confirmation','host:managed-runtime-qualification');
SELECT project,task,runtime,plan,plan_hash,author,author_root
FROM runtime_qualification_plans WHERE project=:project_id AND runtime=:runtime_id;
SELECT project,task,run,runtime,epoch,plan_hash,profile_hash,contract_hash,input_hash,context_bundle,owner_root
FROM runtime_qualification_runs WHERE project=:project_id AND run=:run_id;
SELECT project,run,epoch,dispatch_key,manifest_hash,manifest,state,worker,journal_locator,identity,observation_sequence,observation_hash
FROM runtime_dispatches WHERE project=:project_id AND run=:run_id;
SELECT rowid,project,run,effect_key,sequence,body FROM resource_effects
WHERE project=:project_id AND run=:run_id ORDER BY effect_key,sequence;
SELECT id,revision,body FROM domain_objects WHERE kind='BudgetPolicy' ORDER BY id;
SELECT id,revision,body FROM domain_objects WHERE project=:project_id
AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=:run_id ORDER BY id;
SELECT id,revision,json_remove(body,'$.lease_token_hash') AS safe_body FROM domain_objects
WHERE project=:project_id AND kind='Run' AND id=:run_id;
SELECT id,revision,body FROM domain_objects WHERE project=:project_id
AND kind='Task' AND id=:task_id;
SELECT id,revision,body FROM domain_objects WHERE project=:project_id
AND kind='AcceptanceReceipt' AND json_extract(body,'$.run_id')=:run_id;
-- Resolve only exact associated LOG/REPORT/profile/administration artifact ids,
-- then read their sealed bytes by storage_key and independently verify hash/size.
-- Preserve original bytes. Do not dump unrelated uploaded_content or secrets.
ROLLBACK;
