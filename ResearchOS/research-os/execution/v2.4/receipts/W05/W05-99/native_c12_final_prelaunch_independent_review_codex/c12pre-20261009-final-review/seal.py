import pathlib,json,hashlib
N=pathlib.Path(__file__).resolve().parent
B=N.parent.parent
C=B/'root_native_c12_manual_caller_source_codex/c12-1a11ebe661670a1a49d0ea22092604a'
S=B/'integration_codex/native-cleanup-root-one-spec-source-1791517434000'
D=B/'integration_codex/native-cleanup-controller-source-root-1791517434000'
def pin(p):
 p=pathlib.Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(name,v):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(N/name)
checks=json.loads((N/'checks.json').read_bytes());guard=json.loads((N/'sourceguard.final.json').read_bytes())
assert checks['failed']==0 and checks['passed']==17656 and guard['closed'] and not guard['errors'] and guard['retained_handles_count']==0
mf=write('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
hf=write('HDF.json',dict(schema='researchos.c12-final-prelaunch-independent-review.v1',status='FINAL_PRELAUNCH_SOURCE_ACCEPTED_FOR_ONE_ROOT_SYNTHETIC_CASE',case_id='t12cl149d6f49321',candidate_handoff_ref=pin(C/'HDF.json'),candidate_manifest_ref=pin(C/'MF.json'),one_spec_handoff_ref=pin(S/'HDF.json'),one_spec_manifest_ref=pin(S/'MF.json'),config_ref=pin(D/'controller.public.config.json'),prepared_ref=pin(D/'controller-config.prepared.json'),manifest_ref=mf,report_ref=pin(N/'report.md'),checks_ref=pin(N/'checks.json'),guard_ref=pin(N/'sourceguard.final.json'),original_review_io_ref=pin(N/'review.original-tool-io.json'),frozen_input_count=4185,review_input_count=4245,checks_passed=17656,guard_released=True,conditional_one_root_case_only=True,automatic_phase_approval=False,native_cases_executed=0,formal_acceptance=False,overall20_to24='OPEN',new_failure_ordinals=[908,909,911],STOP=True,FINAL=True))
print(json.dumps(dict(HDF=hf,MF=mf)))

