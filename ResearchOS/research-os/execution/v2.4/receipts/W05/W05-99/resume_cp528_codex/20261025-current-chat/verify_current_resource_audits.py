import hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;E=N.parent.parent
P=E/'c57_privileged_resource_readiness_codex/20261025-current-chat';D=E/'c57_next_ready_audit_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
refs=[]
for p,sha in [(P/'FINAL-SEAL.json','0286e8785b2782e772f0a9c62c789fc2630e2e9ae43a09ab56ccb4078388676b'),(D/'READINESS-AUDIT.md','6d51c088c4cd7251dddf7f4b7113e1d184fa9f2b0db331f69f699fdea6380bf7'),(D/'dag-overlay.json','6db860856201cbf951bd380bdb6c78420b384b73a81ebf9e7607980eb67a65d9')]:
 a=ref(p);assert a['sha256']==sha;refs.append(a)
seal=read(P/'FINAL-SEAL.json')
for x in seal['files']:
 p=P/x['name'];a=ref(p);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
for name,sha in read(D/'dag-overlay.json')['authority_sha256'].items():
 a=ref(R/name);assert a['sha256']==sha;refs.append(a)
for name in ['task-packet-next.recipe.txt','task-packet-next.stdout.raw','task-packet-next.stderr.raw','task-packet-next.exit.txt','derive_dag.py']:
 refs.append(ref(D/name))
assert (D/'task-packet-next.exit.txt').read_text(encoding='utf-8-sig').strip()=='0'
packet=read(D/'task-packet-next.stdout.raw');assert packet['state_source']=='VALIDATED_FILE'
priv=read(P/'RESOURCE-READINESS.json');assert priv['distinct_sid_process_count']==0 and priv['query_success_count']==23 and priv['elevated_count']==15
for name in ['073-selector-cp550.recipe.result.json','074-cp550-live-resume.recipe.result.json','075-current-anchor-metadata.recipe.result.json']:
 p=N/name;v=read(p);assert v['native_exit']==0;refs.append(ref(p))
 for k in ['recipe','stdout','stderr']:
  x=v[k];a=ref(Path(x['path']));assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
refs.append(ref(N/'CP550-live-resume-progress-label-addendum.json'))
anchors=read(N/'075-current-anchor-metadata.recipe.stdout.raw')
v={'schema':'researchos.current-readiness-root-verification.v1','verified_refs':refs,'privileged_verdict':seal['verdict'],'sample_scope':'23 named interactive processes and current token; not universal absence proof','original_anchor_metadata':anchors,'next_branch':'ISOLATED_MAIN7D_DESKTOP_BUILD_DEVELOPMENT_ONLY','formal_increment':0,'diagnostics_to_preserve':[{'key':'dag-first-derive-path','description':'Auditor first derive failed FileNotFoundError; corrected receipt parent index. Raw original capture not asserted; audit report retained.'},{'key':'cp550-progress-label','description':'074 metadata incorrectly named prior starting checkpoint CP541; append-only addendum records CP545->CP550.'},{'key':'root-read-missing-parent-agents','description':'Read-only Get-Content D:/作品集/ResearchOS/AGENTS.md missing; repository AGENTS.md read successfully. PowerShell nonterminating error, outer exit0. Current-chat transcript only.'}]}
with (N/'current-resource-audits-root-verification.json').open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'verified_refs':len(refs),'distinct_elevated':0,'same_sid_elevated':15,'formal_increment':0,'next_branch':v['next_branch']},ensure_ascii=False))
