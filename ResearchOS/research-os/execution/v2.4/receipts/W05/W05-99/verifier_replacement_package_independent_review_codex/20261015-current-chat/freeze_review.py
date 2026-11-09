import pathlib,hashlib,json,datetime
E=pathlib.Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(n):return json.loads((E/n).read_text(encoding='utf-8'))
def save(n,v):
 with (E/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
b=read('01-baseline.json');g=read('07-guards-after.json');r=read('05-input-and-result-check.json')
assert g['source_guards_unchanged']==len(b['source_guards'])
for rec in b['checked_author_refs']:
 p=pathlib.Path(rec['path']);assert pin(p)==rec
save('FINAL-report.json',{'verdict':'LIMITED_PACKAGE_ACCEPTED','reviewer':'codex:/root/verifier_revision_review','model':'gpt-6-astra','reasoning_effort':'high','source_commit':'4f4023c956f84d65743f39ce77d6c8899a21ada1','source_tree':'3db13a15cc52b2b0bd75cae3452c66509a9f55c9','scope':b['scope'],'author_final':b['author_final'],'author_supplement':b['author_supplement'],'package_members':58,'unchanged_baseline_members':55,'changed_members':b['changed'],'compiler_module_inputs_current_verified':2294,'new_native_probe_pass':7,'new_native_probe_fail':0,'new_native_probe_skip':0,'expected_negative_process_exit2':2,'reused_author_wire_pass':214,'product_execution':False,'formal_increment':0,'formal_accepted':0,'formal_total':42,'parents_open':22,'blocking_findings':[],'author_missing_initial_checker_failure_raw_output_preserved_as_disclosed_limitation':True})
save('FINAL-manifest.json',{'schema':'researchos.verifier-replacement-package-independent-review/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'LIMITED_PACKAGE_ACCEPTED','evidence':[pin(p) for p in sorted(E.iterdir()) if p.is_file()],'formal_increment':0})
m=read('FINAL-manifest.json')
for ref in m['evidence']:assert pin(pathlib.Path(ref['path']))==ref
print(json.dumps({'review':pin(E/'REVIEW.md'),'manifest':pin(E/'FINAL-manifest.json'),'report':pin(E/'FINAL-report.json'),'source_guard_count':len(b['source_guards']),'author_refs':len(b['checked_author_refs'])},ensure_ascii=False,indent=2))
