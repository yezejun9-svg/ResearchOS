"""Seal current genuine BR8 closures; formal acceptance stays zero."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
S=Path(__file__).resolve().parent;V=S.parents[4];W=S.parents[1];RUN=W/'w09_br8_actual_root/actual-20261010-01'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(p,b):
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return pin(p)
old=S/'RESUME.cp392-gen02-qualified-br8-finite-lease-pending.live1237.root.json';d=json.loads(old.read_bytes())
current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[0]['sha256']=='60c2b89163ebf1522454331a6b774bf80c801d262208872db981b7b1e85a09d2' and current[1]['sha256']=='b949831cc4827ae2cadae77235188dfff0776a0c8074a57714c1445e16c32a86'
d.update(created_at=datetime.now(timezone.utc).isoformat(),previous_resume_ref=pin(old),current4=current,live_next_original=1246,registered_through=1245,pending_originals=[],Root_running_processes=[],counter_reset=False,Canon_written=False,formal_acceptance=False)
d['W09']['BR8_state']='ASSEMBLED_ACTUAL0_SIX_CONSUMERS0_ROLES_REGISTERED_WAITING_FORMAL_REVIEW'
d['W09']['BR8_current']=dict(proposal_ref=pin(RUN/'propose-e1111124d5e54bfc810d9ebe1d167664/result.json'),activation_ref=pin(RUN/'activate-d012301df2404531b8a15ec84d1aeddd/result.json'),consumer_ref=pin(RUN/'consume-fb16497eef2f43c2858a3e00df3ba31f/result.json'),role_builder_ref=pin(W/'w09_br8_role_inputs_root/d2abba5f35784840acaed5cf70b98aed/result.json'),roles_publication_ref=pin(RUN/'roles-764da9a75846495cb9557bb8114f6151/result.json'),roles_registration_ref=pin(RUN/'publish-registration-c2bc5b2db91547438e6d53a12240012e/result.json'),registered_role_seed_ref=pin(RUN/'seed-e8289431c01f463f9abd2173d5789c5e/result.json'),assembled_result_ref=pin(RUN/'assemble-259182b5a7584e23bc58a273088e06cd/result.json'),FREV_v4_independent_review_ref=pin(W/'w09_br8_formal_actual_review_independent_source_review_codex/review-20261010-01-full/review-decision.json'),FREV_v4_true_final_capture_ref=pin(S/'w09.br8-and-main24-source-review-redelivery02.actual-audit.root.json'),Native_producers_replayed=False,actual_consumer_exit_codes=[0]*6,formal_acceptance=False,next_action='Root complete dynamic CP395 resource bundle; Backup actual independent review, then Root capture/index/issuance/owner/derive. Lease remains finite; preserve all failed receipts.')
d['Main24_handoff_Source_current']=dict(independent_review_ref=pin(V/'receipts/W05/W05-99/public23_to24_handoff_independent_review_codex/review-20261010-01-full/review-decision.json'),actual_true_final_capture_ref=pin(S/'w09.br8-and-main24-source-review-redelivery02.actual-audit.root.json'),integration_recipe_hdf_ref=pin(V/'receipts/W05/W05-99/public23_to24_root_integration_preparation_codex/prepare-20261010-01/HDF.json'),Source_only=True,Main_adopted=False,build_and_Native_executed=False)
new=save(S/'RESUME.cp395-br8-assembled0-formal-review-pending.live1246.root.json',(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
h=V/'HANDOFF_RESUME_PACK.md';before=h.read_bytes();arch=save(S/'HANDOFF.before-cp395-live1246.raw.md',before)
prefix=('<!-- Root current resume CP395 / OW197 / live1246; prior history preserved. -->\n\nW09 BR8 propose/activate/consume/roles/publish-registration/role-seed/assemble全部实际0；六consumer均0、Job闭合，五角色已登记，八GLOBAL已生成。FREV v4非作者11项Source审查已有效接收，Root等待完整资源bundle后交Backup正式独立审查。W05 GEN02组件闭合；Main24 handoff Source独审23项通过，尚未Main整合/build/真实23→24。正式接受仍0/42；Root无在途进程。\n\n'+f'诊断逐条登记至1245，live next1246。机器续跑：{new["path"]}，sha256={new["sha256"]}，bytes={new["bytes"]}。旧handoff原始字节：{arch["path"]}。\n\n').encode()
t=h.with_name('HANDOFF_RESUME_PACK.cp395-live1246.tmp');save(t,prefix+before);os.replace(t,h)
assert current==[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
print(json.dumps(dict(resume_ref=new,handoff_ref=pin(h),historical_handoff_ref=arch,formal_acceptance=False),ensure_ascii=False))
