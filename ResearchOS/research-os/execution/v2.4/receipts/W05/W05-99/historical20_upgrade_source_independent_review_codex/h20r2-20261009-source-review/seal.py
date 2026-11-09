import pathlib,json,hashlib
P=pathlib.Path;N=P(__file__).resolve().parent;B=N.parent.parent;C=B/'historical20_upgrade_test_revision_codex/h20r2-1a11ee4f162766098eda3028b0679f2'
def pin(p):
 p=P(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):return json.loads(P(p).read_bytes())
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(N/n)
c=read(N/'checks.json');g=read(N/'guard.final.json')
assert c['passed']==587 and c['failed']==0 and c['input_count']==119 and g['state']=='RELEASED'
mf=save('MF.json',dict(schema='researchos.independent-source-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
hf=save('HDF.json',dict(schema='researchos.h20r2-independent-source-review.v1',status='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_CALLER_AND_RUNTIME',candidate_handoff_ref=pin(C/'HDF.json'),candidate_manifest_ref=pin(C/'MF.json'),test_ref=pin(C/'candidate-root/internal/domain/backup_history20_upgrade_test.go'),manifest_ref=mf,report_ref=pin(N/'report.md'),checks_ref=pin(N/'checks.json'),guard_ref=pin(N/'guard.final.json'),checks_passed=587,input_count=119,exact_inverse_replacements=9,four_production_unchanged=True,baseline66_unchanged=True,entire_R1_positive_test_unchanged=True,expected_parents=5,expected_leaves=4,expected_terminals=9,actual_Git_Go_SQL_native_API_private_model=False,new_failure_ordinals=[],formal_acceptance=False,overall20_to24='OPEN',guard_scope='before_after_hash_observation_only_no_OS_handles',guard_released=True,STOP=True,FINAL=True))
print(json.dumps(dict(HDF=hf,MF=mf)))

