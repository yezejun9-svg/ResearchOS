from pathlib import Path
import hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';S=Path(__file__).resolve().parent;RUN=V/'receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01'
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def checked(p,d):
 r=pin(p);assert r['sha256']==d;return r
owner=checked(RUN/'prospective-owner.literal02.actual.root.json','4858c914f310e2fc83999a511fc070e054c57b12ce594ab14347e0f1612ee9d6')
approval=checked(V/'receipts/W09/W09-99/w09_br8_prospective_owner_independent_approval_codex/approve-20261010-02/approval.json','bd843d082c1f9dbdf92d51aba2c6848511a1ab0799a3ae88773e299f867016fd')
audit=checked(S/'w09.owner-literal02-approval01.actual-audit.root.json','4c48c60645479fab87b91f4ded712e1b062273e62e534d1b321289c53313bac2')
result=checked(RUN/'check-9482e0c14ee24c5fa7f24855f8dfc27a/result.json','f48c93f5df390b1156cefdb5bfbc52166cb57cadee945391025e63b24c66d4ef')
guard=json.loads((RUN/'check-9482e0c14ee24c5fa7f24855f8dfc27a/source-guard.closed.json').read_bytes());assert guard['closed'] and guard['retained_handles_count']==0 and not guard['errors']
req=dict(actor_id='codex:/root',current4=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],prospective_owner_ref=owner,approval_ref=approval,approval_actual_audit_ref=audit,precheck_result_ref=result)
assert req['current4'][0]['sha256']=='f7a2027f5fe21fe5b0524d1731eba7304327e067f0ea937489b234e07dc2983e' and req['current4'][2]['sha256']=='fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149'
p=RUN/'ss-append.literal02.request.actual.root.json';b=(json.dumps(req,ensure_ascii=False,indent=2)+'\n').encode()
with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
print(json.dumps(dict(request_ref=pin(p),formal_derivation_pending=True,SS_written=False),ensure_ascii=False))
