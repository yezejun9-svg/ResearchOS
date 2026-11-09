"""Preserve prior handoff bytes and publish the verified CP392 resume."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os
S=Path(__file__).resolve().parent; V=S.parents[4]; W=S.parents[1]
def pin(p):
    b=p.read_bytes(); return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(p,b):
    with p.open('xb') as f: f.write(b); f.flush(); os.fsync(f.fileno())
    return pin(p)
old=S/'RESUME.cp391-w05-three-native0-br8-source-pending.live1231.root.json'
d=json.loads(old.read_bytes())
current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert [r['sha256'] for r in current]==['94be902e6b5efe6b19981c90727dfe765bdd82d53f83100dae2033dd0f1dfa06','7dc0f5760dbd2b7e6589f22aba4cf071b43fdc70c615b4b5d7e11373a98367c6','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149','12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97']
d.update(created_at=datetime.now(timezone.utc).isoformat(),previous_resume_ref=pin(old),current4=current,live_next_original=1237,registered_through=1236,pending_originals=[],Root_running_processes=[],counter_reset=False,Canon_written=False,formal_acceptance=False)
d['W05_GEN02_current']=dict(state='QUALIFIED_COMPONENT_ONLY_SCOPE_CONSUMED',actual_native_exit_codes=[0,0,0],independent_actual_checks=30,read_only_database_oracles=3,case_ref=pin(V/'receipts/W05/W05-99/integration_codex/public22-continuation-862bd0e97cad44eab8e28b37f8063f20/case.closed.json'),corrected_review_ref=pin(V/'receipts/W05/W05-99/public22_to_main23_continuation_actual_independent_review_codex/actual-20261010-04/review-decision.json'),closure_ref=pin(S/'cp392-w05-gen02-consumed-diagnostics1236-live1237/closure.committed.root.json'),full_20_to_24='OPEN',formal_acceptance=False)
d['W09']['BR8_state']='SOURCE_INDEPENDENTLY_ACCEPTED_SEED0_PROPOSE1236_FAILED_MISSING_FINITE_LEASE'
d['W09']['BR8_current']=dict(source_review_ref=pin(W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-08-backup/review-decision.json'),seed_result_ref=pin(W/'w09_br8_actual_root/actual-20261010-01/seed-c0b41d982ba14201965fe05216e9c82b/result.json'),failed_propose_directory=str(W/'w09_br8_actual_root/actual-20261010-01/propose-7a81926e02c048e3a53c19bba371c0ad'),original_1236_retained=True,Scope_registered=False,TP_called=False,Native_called=False,next_action='Fresh propose from current4 with lease_expires_at, new output and genuine Root grant; retain seed and failed proposal.',formal_review_source='V4_PENDING_NONAUTHOR_REVIEW',Main24_handoff_source='PENDING_TRUE_INDEPENDENT_FINAL')
new=save(S/'RESUME.cp392-gen02-qualified-br8-finite-lease-pending.live1237.root.json',(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
h=V/'HANDOFF_RESUME_PACK.md'; before=h.read_bytes(); arch=save(S/'HANDOFF.before-cp392-live1237.raw.md',before)
prefix=('<!-- Root current resume CP392 / OW196 / live1237; prior history preserved. -->\n\nW05 GEN02 三次公开 Native 均0，独立30项检查与3个只读数据库核验通过；组件接受、Scope已消费，完整20→24仍OPEN。W09 BR8 Source已独立接受、seed实际0，propose原1236缺有限租约字段，未产生Scope/TP/Native；下一步使用新请求、新授权及有限租约续跑。正式接受0/42；Root无在途进程。\n\n'+f'已登记至1236，live next1237。机器续跑：{new["path"]}，sha256={new["sha256"]}，bytes={new["bytes"]}。旧handoff原始字节：{arch["path"]}。\n\n').encode()
t=h.with_name('HANDOFF_RESUME_PACK.cp392-live1237.tmp');save(t,prefix+before);os.replace(t,h)
assert current==[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
print(json.dumps(dict(resume_ref=new,handoff_ref=pin(h),historical_handoff_ref=arch,Canon_written=False,formal_acceptance=False),ensure_ascii=False))
