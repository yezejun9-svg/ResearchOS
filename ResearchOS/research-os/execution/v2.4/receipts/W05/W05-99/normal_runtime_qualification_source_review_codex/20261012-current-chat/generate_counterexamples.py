from pathlib import Path
import json, hashlib
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-runtime-qualification-source-20261012'
source=WT/'internal/host/runtime_qualification_integration_windows_test.go'
raw=source.read_text(encoding='utf-8')
imports=raw[:raw.index('var localVerifierExecutable')].replace('\n\t"flag"','')
function=raw[raw.index('func TestManagedLocalRuntimeQualificationSyntheticTransport'):]
prefix=function[:function.index('\tresult, e := h.QualifyLocalRuntime')]
mutation_point='\t\t\trecorder := httptest.NewRecorder()'
finish=r'''
	result, e := h.QualifyLocalRuntime(ctx, svc, c, server.URL, request, installed)
	if e == nil || !mutated.Load() || calls.Load() != 1 {
		t.Fatalf("expected current-authority rejection after one synthetic model call: mutated=%v calls=%d result=%s error=%v", mutated.Load(), calls.Load(), domain.Bytes(result), e)
	}
	var pass, available, liveVerifierCredentials, unknown int
	queries := []struct{sql string; into *int; want int}{
		{`SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt' AND json_extract(body,'$.verdict')='PASS'`, &pass, 0},
		{`SELECT count(*) FROM domain_objects WHERE kind='RuntimeRegistration' AND json_extract(body,'$.status')='AVAILABLE'`, &available, 0},
		{`SELECT count(*) FROM auth_credentials c JOIN auth_principals p ON c.principal=p.id WHERE p.roles='["VERIFIER"]' AND c.revoked=0`, &liveVerifierCredentials, 0},
		{`SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.operation')='UNKNOWN' AND json_type(body,'$.money')='null' AND json_type(body,'$.reservation_id')='null'`, &unknown, 1},
	}
	for _, q := range queries { if err:=db.QueryRow(q.sql).Scan(q.into); err!=nil || *q.into!=q.want { t.Fatalf("post-refusal invariant got=%d want=%d err=%v",*q.into,q.want,err) } }
	if _, err:=h.QualifyLocalRuntime(ctx,svc,c,server.URL,request,installed); err==nil || calls.Load()!=1 {t.Fatal("failed qualification was replayed")}
	t.Logf("REVIEWER_NEGATIVE mutation_applied=true refusal=%v synthetic_model_calls=1 PASS=0 AVAILABLE=0 verifier_live_tokens=0 original_UNKNOWN_null=1 retry_calls=0",e)
}
'''.replace('\\t','\t')
mutations={
 'VerifierRevokedBeforeAcceptance': '''if _, err := db.Exec(`UPDATE auth_principals SET revoked=1 WHERE roles='["VERIFIER"]' AND id IN (SELECT principal FROM auth_grants WHERE project=?)`, projectID); err != nil {t.Error(err)}''',
 'UnknownPolicyDriftBeforeAcceptance': '''if _, err := db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.updated_at',?) WHERE kind='BudgetPolicy'`, time.Now().UTC().Add(time.Hour).Format(time.RFC3339Nano)); err != nil {t.Error(err)}''',
}
generated=imports
for name,mutation in mutations.items():
    body=prefix.replace('TestManagedLocalRuntimeQualificationSyntheticTransport','TestReviewer'+name)
    body=body.replace('var calls atomic.Int32','var calls atomic.Int32\n\tvar mutated atomic.Bool')
    body=body.replace(mutation_point,'\t\t\tif strings.HasSuffix(r.URL.Path, "/acceptances") && mutated.CompareAndSwap(false,true) {\n\t\t\t\t'+mutation+'\n\t\t\t}\n'+mutation_point)
    generated+=body+finish+'\n'
target=OUT/'reviewer_counterexamples_windows_test.go'
target.write_text(generated,encoding='utf-8')
(OUT/'counterexamples-overlay.json').write_text(json.dumps({'Replace':{str(WT/'internal/host/reviewer_counterexamples_windows_test.go'):str(target)}},indent=2)+'\n',encoding='utf-8')
(OUT/'counterexamples-lineage.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generated_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'method':'Reuse current immutable integration setup; inject verifier revocation or budget policy timestamp drift immediately before server POST /acceptances. No production code overlay. No real model calls.'},indent=2)+'\n',encoding='utf-8')
print('generated reviewer-only counterexamples')
