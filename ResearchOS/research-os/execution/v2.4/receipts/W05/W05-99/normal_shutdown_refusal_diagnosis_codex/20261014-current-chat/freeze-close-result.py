import pathlib,json,hashlib,datetime
E=pathlib.Path(__file__).parent;ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
refs=[]
for rel in ['execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry09_codex/20261014-current-chat/02-bounded-close-retry-decision.json','execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry09_codex/20261014-current-chat/03-bounded-close-request.json','execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry08_codex/20261014-current-chat/electron-process-wait.observed.json']:
 p=ROOT/rel;body=json.loads(p.read_text(encoding='utf-8-sig'));refs.append({'path':rel,'sha256':sha(p),'bytes':p.stat().st_size,'observed':body})
for ref in refs[0]['observed']['observer_refs']:
 p=ROOT/ref['path'];assert sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes']
assert refs[0]['observed']['limit']==1 and refs[2]['observed']['actual_numeric_wait_status']==0
absence=json.loads((E/'post-retry-original-process-absence.json').read_text(encoding='utf-8-sig'));assert absence['matching_processes']==[]
r=json.loads((E/'FINAL-report.json').read_text(encoding='utf8'))
r.update(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),verdict='READ_ONLY_DURABLE_GUARD_PASSES_ROOT_SINGLE_NORMAL_RETRY_EXITED_SUCCESSFULLY_CAUSE_UNOBSERVED',pre_retry_final={'path':'FINAL-report.json','sha256':sha(E/'FINAL-report.json'),'manifest_sha256':sha(E/'FINAL-manifest.json')})
r['root_recovery_result']={'bounded_action':'one normal WM_CLOSE sent by Root, without kill','root_receipts':refs,'reviewer_process_absence':absence,'electron_numeric_wait':0,'core_numeric_wait':'NOT_OBSERVED','first_refusal_cause':'NOT_OBSERVED','new_package_activation':'Root reports fresh normal launch; excluded from this diagnosis acceptance'}
r['recovery']['root_retry_execution']='ROOT_EXECUTED_ONCE; receipt hashes re-read and verified; reviewer did not operate GUI or private pipe'
r['recovery']['success_interpretation']='Successful ordinary close after one bounded retry. No precise first-error cause found or inferred.'
(E/'FINAL-with-close-result-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
manifest={'schema':'researchos.evidence-manifest/1','files':[{'path':p.relative_to(E).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-with-close-result-manifest.json']}
(E/'FINAL-with-close-result-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for name in ['FINAL-with-close-result-report.json','FINAL-with-close-result-manifest.json']:print(name,sha(E/name))
print('members',len(manifest['files']))
