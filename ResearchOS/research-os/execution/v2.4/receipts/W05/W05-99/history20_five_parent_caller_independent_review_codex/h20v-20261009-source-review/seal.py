import pathlib,json,hashlib
P=pathlib.Path;N=P(__file__).resolve().parent;B=N.parent.parent
C=B/'integration_codex/history20-five-parent-sparse-root-source-h20v-1a11ebe661670a1a49d0ea22092604a'
def pin(p):
 p=P(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(P(p).read_bytes())
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(N/n)
checks=read(N/'checks.json');g=read(N/'sourceguard.final.json')
assert checks['passed']==4981 and checks['failed']==0 and checks['input_count']==978 and g['closed'] and not g['errors'] and g['retained_handles_count']==0
mf=save('MF.json',dict(schema='researchos.independent-source-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
hf=save('HDF.json',dict(schema='researchos.h20-five-parent-caller-independent-source-review.v1',status='SOURCE_APPROVED_FOR_ROOT_FRESH_SPARSE_AND_NARROW_VALIDATION',candidate_handoff_ref=pin(C/'HDF.json'),candidate_manifest_ref=pin(C/'MF.json'),prepare_ref=pin(C/'prepare_history20_five_parent.actual_owned.py'),validate_ref=pin(C/'validate_history20_five_parent.actual_owned.py'),choice_ref=pin(C/'source.integration.choice.json'),manifest_ref=mf,report_ref=pin(N/'report.md'),checks_ref=pin(N/'checks.json'),guard_ref=pin(N/'sourceguard.final.json'),checks_passed=4981,input_count=978,source_count=61,selected_parents=5,exact_terminal_names=9,ops_backup_CLI_built_or_executed=False,actual_Git_Go_SQL_native_model=False,formal_acceptance=False,overall20_to24='OPEN',new_failure_ordinals=[],guard_released=True,STOP=True,FINAL=True))
print(json.dumps(dict(HDF=hf,MF=mf)))

