from pathlib import Path
import hashlib,json,collections,subprocess
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;V=N.parent.parent/'qualification_maintenance_c57_independent_review_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
refs={}
def verify(p,sha,n=None):
 a=ref(p);assert a['sha256']==sha,str(p)
 if n is not None:assert a['bytes']==n,str(p)
 refs[a['path']]=a;return a
seal=V/'PHASE2-final-seal.json';verify(seal,'5ca380f27f30d657569c154d4c392bfbe23e9c2af265da4e0c1f81698d2e03f3');s=read(seal)
for name,key in [('PHASE2-final-manifest.json','manifest_sha256'),('PHASE2-independent-final-review.md','report_sha256'),('PHASE2-final-coverage73.json','coverage73_sha256'),('PHASE2-test-summary.json','test_summary_sha256'),('PHASE2-diagnostics.json','diagnostics_sha256')]:verify(V/name,s[key])
m=read(V/'PHASE2-final-manifest.json');assert len(m['files'])==360
for x in m['files']:verify(V/x['path'],x['sha256'],x.get('bytes'))
post=V/'PHASE2-postseal-audit.json';verify(post,'e74f607e32cc7e720119936d819395eb114a345ef1bb52f7f80b1e38dec0d7f1');ps=read(post)
for x in ps['postseal_capture_refs']:verify(V/x['path'],x['sha256'])
assert ps['new_native_nonzero']==0 and ps['cumulative_native_nonzero']==9
snap=read(V/'PHASE2-v12-snapshot-verification.json');assert snap['commit']==s['candidate_commit']=='03aa4d687dfaa541d9b18d4c766805307a537d1d' and snap['tree']==s['candidate_tree']=='81059bc4cdba04716fcd2607496485bbbf22bc80'
S=Path(snap['snapshot']);assert len(snap['candidate_source_files'])==57 and len(snap['inherited40'])==40 and len(snap['supplementary_files'])==5
for x in snap['candidate_source_files']+snap['inherited40']+snap['supplementary_files']:verify(S/x['path'],x['sha256'],x.get('bytes'))
for x in snap['old2']:verify(Path(x['preserved']),x['sha256'])
for x in snap['fixed_inputs']:verify(Path(x['copy']),x['sha256'])
coverage=read(V/'PHASE2-final-coverage73.json');rows=coverage['rows'];assert len(rows)==73 and len({r['id']for r in rows})==73
summary=read(V/'PHASE2-test-summary.json');selected=summary['selected_groups'];assert len(selected)==10;counts=collections.Counter();groups=[]
for tag in selected:
 q=V/tag;result=read(q/'result.json');assert result['native_exit']==0 and not result.get('candidate_source_drift',[])
 verify(q/'stdout.raw',result['stdout_sha256']);verify(q/'stderr.raw',result['stderr_sha256']);c=collections.Counter()
 for line in(q/'stdout.raw').read_text(encoding='utf-8-sig').splitlines():
  if not line.startswith('{'):continue
  e=json.loads(line)
  if e.get('Test')and e.get('Action')in ['pass','skip','fail']:c[e['Action']]+=1
 counts.update(c);groups.append({'id':tag,'native_exit':0,'counts':dict(c),'result_ref':ref(q/'result.json')})
assert counts['pass']==172 and counts['skip']==3 and counts['fail']==0
diag=read(V/'PHASE2-diagnostics.json');assert len(diag['phase2_native_nonzero_additions'])==6 and diag['cumulative_reviewer_native_nonzero']==9 and diag['candidate_assertion_failures']==0
selector=read(N/'069-selector-cp549.recipe.stdout.raw');assert read(N/'069-selector-cp549.recipe.result.json')['native_exit']==0 and selector['state_source']=='VALIDATED_FILE'and selector['product_acceptance']=='NOT_ASSERTED'and selector['step']['id']=='W05-99'
out={'schema':'researchos.c57-independent-final-root-verification.v1','candidate_commit':s['candidate_commit'],'candidate_tree':s['candidate_tree'],'seal':ref(seal),'postseal_audit':ref(post),'manifest_count':360,'verified_unique_refs':len(refs),'verified_refs':list(refs.values()),'source57_snapshot_exact':True,'inherited40_snapshot_exact':True,'supplements5_exact':True,'coverage_count':73,'coverage_status_counts':dict(collections.Counter(r['status']for r in rows)),'selected_groups_recomputed':groups,'recomputed_test_events':dict(counts),'diagnostics':diag,'independent_verdict':s['status'],'Root_adoption_pending_registration':True,'formal_increment':0,'selector_state_source':'VALIDATED_FILE','limitations':['No claim that all73 are native or actual PASS.','Full public Host chain, distinct SID/elevated recovery, actual readable SACL, actual backup/deployment/FullRestart/original business run remain unavailable.','Historical native failures and capture gaps remain unchanged; candidate test failure0 is not totaldiagnostic0.']}
with(N/'C57-independent-final-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items()if k not in ['verified_refs','diagnostics','selected_groups_recomputed','coverage_status_counts']},ensure_ascii=False))
