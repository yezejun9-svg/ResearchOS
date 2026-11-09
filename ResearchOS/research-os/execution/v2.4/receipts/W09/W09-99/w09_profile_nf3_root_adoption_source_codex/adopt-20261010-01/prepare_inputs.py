"""Read existing accepted inputs and preserve a non-authoritative Source baseline."""
import hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path(r'D:/作品集/ResearchOS/research-os');V=R/'execution/v2.4';W=V/'receipts/W09/W09-99';B=V/'receipts/W05/W05-99'
Q=W/'w09_profile_registry_compat_source_codex/adfab031c6ab45ea947f1994b65b43f5'
QR=W/'w09_profile_registry_compat_independent_source_review_codex/review-20261009-01'
NF=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03'
NR=W/'full_w09_main_native_producer_independent_source_review_codex/review-fullw09-20261010-03'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,obj):
 p=N/name
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
 return pin(p)
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=pin(gp);assert (gr['sha256'],gr['bytes'])==('e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
gm=types.ModuleType('task75_input_guard');exec(compile(gp.read_bytes(),str(gp),'exec'),gm.__dict__)
paths={'Q_hdf':Q/'HDF.json','Q_mf':Q/'MF.json','QR_hdf':QR/'HDF.json','QR_mf':QR/'MF.json','QR_decision':QR/'source-decision.json',
 'Q_profile':Q/'candidate-root/execution/v2.4/formal_profile_w09.py','Q_commands':Q/'candidate-root/execution/v2.4/commands.json',
 'Q_profile_before':Q/'inputs/formal_profile_w09.before.py','Q_contract':Q/'ROOT_CALLING_CONTRACT.source.md',
 'Q_index_before':Q/'formal_case_index.before.py','NF_hdf':NF/'HDF.json','NF_mf':NF/'MF.json','NR_hdf':NR/'HDF.json','NR_mf':NR/'MF.json',
 'NR_decision':NR/'source-review-decision.json','NF_contract':NF/'root-calling-contract.json','NF_choice':NF/'source.choice.json',
 'NF_runtime':NF/'full_w09_runtime.source.py','NF_prepare':NF/'prepare_full_w09.source.py','NF_run':NF/'run_full_w09.source.py',
 'NF_launcher':NF/'full_w09_launcher.source.py','NF_blueprint':NF/'compiler-source-blueprint.json',
 'peer_audits':S/'w09.reviewed-source-actual-audits.root.json','main23_qualification':S/'main23.programme.qualification.bound.actual.root.json',
 'CM39_archive':W/'checkpoint_r369_native_source_root/cp369-c19-20261009/historical.cp369.commands.json',
 'TP':B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py',
 'guard':gp,'locked':R/'execution/toolchains/locked.json'}
refs={k:pin(p) for k,p in paths.items()}
assert (refs['peer_audits']['sha256'],refs['peer_audits']['bytes'])==('18b5d44ccc3bafd1acd10a0171162254500b05c0e6a4d09328ac93698faabac9',1663)
assert (refs['main23_qualification']['sha256'],refs['main23_qualification']['bytes'])==('f4075c4e6250226e9c21a2e3cb3cb3d9ee3412c567a5caab391832ad7715ab6c',6117)
peers=json.loads(paths['peer_audits'].read_bytes())['audit_refs']
extra=[]
for ref in peers.values():
 d=json.loads(Path(ref['path']).read_bytes());extra.extend([ref,d['original_capture_ref']])
g=gm.SourceReadGuard(total_cap=128*1024*1024)
try:
 g.acquire(list(refs.values())+extra)
 qh=json.loads(g.get_buffer(str(paths['Q_hdf'])));qr=json.loads(g.get_buffer(str(paths['QR_decision'])))
 nr=json.loads(g.get_buffer(str(paths['NR_decision'])));nf=json.loads(g.get_buffer(str(paths['NF_hdf'])))
 assert qh['manifest_ref']==refs['Q_mf'] and qr['source_hdf_ref']==refs['Q_hdf'] and qr['source_mf_ref']==refs['Q_mf']
 assert qr['profile_ref']==refs['Q_profile'] and qr['commands_proposal_ref']==refs['Q_commands'] and qr['decision']=='ACCEPTED_SOURCE_ONLY'
 assert nf['manifest_ref']==refs['NF_mf'] and nr['source_handoff_ref']==refs['NF_hdf'] and nr['source_manifest_ref']==refs['NF_mf']
 assert nr['decision']=='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE'
 (N/'inputs').mkdir()
 baseline={}
 for name in ('checkpoint','path_ownership','step_state','commands'):
  path=V/(name+'.json');raw=path.read_bytes();target=N/'inputs'/('baseline.'+name+'.json')
  with target.open('xb') as f:f.write(raw)
  baseline[name]={'current_ref':pin(path),'snapshot_ref':pin(target)}
 assert baseline['commands']['current_ref']['sha256']==refs['CM39_archive']['sha256']
 assert pin(V/'formal_profile_w09.py')['sha256']==refs['Q_profile_before']['sha256']
 assert pin(V/'formal_case_index.py')['sha256']==refs['Q_index_before']['sha256']
 base_pending=S/'pending-diagnostics.cp373.live1089.root.json';pending=json.loads(base_pending.read_bytes())
 assert (pin(base_pending)['sha256'],pin(base_pending)['bytes'])==('6bab318465c9ee9fa6df207ac7a108daa83e564b95ae85f65abfd6327402874f',28525)
 with (N/'inputs/baseline.pending.json').open('xb') as f:f.write(base_pending.read_bytes())
 refs['baseline_pending']=pin(N/'inputs/baseline.pending.json')
 refs['baseline_pending_original']=pin(base_pending)
 out=save('input-pins.json',{'schema':'researchos.w09-adoption-input-pins.v1','refs':refs,'peer_audit_refs':peers,
  'baseline':baseline,'source_only':True,'current_pair_held':False,'future_current4_must_be_supplied_dynamically':True})
finally:
 closed=g.close();guard_ref=save('inputs.source-guard.closed.json',closed)
 assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
print(json.dumps({'input_pins_ref':out,'guard_ref':guard_ref,'existing_packages_retested':False,'actual_branch_called':False},ensure_ascii=False))
