import ast,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321-v2'
OLD=R/'execution/v2.4/receipts/W05/W05-99/exact38_integration_controller_v2_independent_review_codex/98a6d4c78b3b4aa48abce9426fd44ca8'
reads=[]
def ref(p,expected=None):
 raw=p.read_bytes();x={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 if expected is not None and x['sha256']!=expected:raise RuntimeError('Pinned input mismatch: '+str(p))
 reads.append(x);return x
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
launcher=ref(S/'launcher.py','48abd3b7c0a1230b65fdf61c6075691d667e661356e5edaccdbf99f7390af0de')
scope=ref(S/'scope_registration.json','254642660280442df4352e355d0e01f6c0fc8bab8bc7337554d6bbc26a223f90')
producer=ref(S/'grant-producer.py','dfbed4a9feb172a46aafa426775605428a1dc1f47d69b3d1c6cf91c50b0d6577')
sd=json.loads((S/'scope_registration.json').read_bytes());controller=ref(Path(sd['controller_ref']['path']),'e2f98bded200afc15cf1afecbc73d0423dcc1ab0a16e5497ca4a1dd7e244d6ff')
helper=ref(Path(sd['owned_process_helper_ref']['path']),'6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad')
old=ref(OLD/'review.json','ca641a19e3f10d0cda78a49719487987cd02eb396a4197ac33c6d7edd9aca66b')
oldmf=ref(OLD/'manifest.json','b15e2c3629bf033fbd6cc15f6941cc874a358a0d7e28b7855cd1de395e0981ff')
oldreview=json.loads((OLD/'review.json').read_bytes())
for name in ['checks','reads']:
 x=oldreview['basis'][name];ref(Path(x['path']),x['sha256'])
raw=(S/'launcher.py').read_bytes();tree=ast.parse(raw);lines=raw.decode().splitlines()
lin=lambda text:[i for i,s in enumerate(lines,1) if text in s]
finding={'id':'I38-LAUNCH-OWNERSHIP-01','priority':'BLOCKER','path':launcher['path'],
 'lines':{'out_assigned':lin('out = safe(LOG_PARENT /'),'mkdir':lin('out.mkdir(exist_ok=False)'),'unguarded_receipt_branches':lin('if out is not None:')},
 'actual_static_fact':'out becomes non-None before exclusive mkdir succeeds. If mkdir raises because the UUID leaf already exists, except and finally still attempt failure.origin.json and manifest.json within that existing leaf.',
 'scope_impact':'This violates own-output creation guard and preservation of prior immutable receipt namespaces. It is a static unexecuted branch finding, not an observed collision or native failure.',
 'minimal_revision':'Keep candidate_log_leaf separate and assign out only after candidate_log_leaf.mkdir(exist_ok=False) succeeds, or guard all output writes with an own_leaf_created flag set only after success. Before ownership, preserve original exception through stderr fallback, never append to the candidate leaf. Preserve current launcher as unexecuted history.'}
review={'schema':'researchos.exact38-integration-controller-review.v1','reviewer':'codex:/root/w05_merge_review',
 'decision':'REQUEST_CHANGES','requested_changes':[finding],'actual_integration_executed':False,
 'controller_sha256':controller['sha256'],'scope_sha256':scope['sha256'],'launcher_sha256':launcher['sha256'],
 'refs':{'launcher':launcher,'scope':scope,'producer':producer,'controller':controller,'helper':helper,'prior_full_review':old,'prior_manifest':oldmf},
 'resolved':'Original I38-V2-PRELAUNCH-01 coverage is implemented: launcher try encloses flags/fixed input validation and producer invocation, and wraps controller pretry in an owned child with raw streams and nullable results. Ownership branch above still prevents final READY.',
 'static_checked':[
 'AST parses without import or execution of launcher/helper/producer/controller.',
 'Actual helper supplies unnamed_exclusive_job and all required cleanup flags; both native results require0/errorNone/timeoutFalse/resumedTrue/fullcleanup.',
 'Producer600s/controller4500s run once sequentially with5s owned cleanup; first failure prevents subsequent controller invocation.',
 'Pinned lock/Python/helper/controller/scope/producer and point-time source/pyc/DLL runtime checks, -I -S -X utf8 and no pyc retained.',
 'Grant namespace/operation UUID/hash/bytes pinned and inputs rechecked before controller.',
 'Raw stdout/stderr and actual nullable native exit saved per owned child; wrapper error remains separate.',
 'Manifest-sealing exception affects returned nonzero exit and stderr fallback; no silent successful launcher result.',
 'Original full78,815-check audit576cd2 is inherited; large vectors/native were not rerun. Source/controller/scope/producer pins reconfirmed.'
 ],
 'limits':['Python runtime evidence remains POINT_IN_TIME_NOT_LIFECYCLE.','Current320/148/417 has not authorised FF; actual321/149/422 seal and distinct registration review still required.','This review does not accept source/Main/products/22parents/42formal cases.','No actual collision, target process, grant or FF was executed.'],
 'new_failure_origins':[],'formal_increment':0}
save('reads.json',reads.copy());rr=save('review.json',review)
mf=save('manifest.json',{'entries':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'excluded':['manifest.json','handoff.json']})
h=save('handoff.json',{'decision':review['decision'],'review_ref':rr,'manifest_ref':mf,'new_failure_origins':[],'actual_integration_executed':False,'next':'One immutable launcher ownership-guard revision, narrow review only; no current execution grant.'})
print(json.dumps({'review':rr,'manifest':mf,'handoff':h},ensure_ascii=True))
