"""Append the current read-only resume; preserve all Canon and history bytes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os
S=Path(__file__).resolve().parent
V=S.parents[4]
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(p,b):
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return pin(p)
old=S/'RESUME.cp391-w05-gen02-three-native0-closed-br8-source-pending.live1226.root.json'
d=json.loads(old.read_bytes());assert d['current4']==[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
d['created_at']=datetime.now(timezone.utc).isoformat();d['previous_resume_ref']=pin(old);d['live_next_original']=1231
for ordinal,actor,chunk,outer,py,description in (
    (1226,'codex:/root','400353',2,2,'Root selector global --plan placed after show; corrected read-only selection passed.'),
    (1227,'/root/attach_restore_independent_review','a27c9f',1,None,'Read-only rg queried nonexistent cmd directory; successful Git prefix preserved.'),
    (1228,'/root/attach_restore_independent_review','81ce7e',1,None,'Read-only rg in apps returned no match; public entry found in ops/backup.'),
    (1229,'/root/full_w09_source_review','f5ac7c',1,None,'Read-only extra Guard query used wrong W09 parent; successful Main and diagnosis reads preserved.'),
    (1230,'codex:/root','ee077d',0,None,'Read-only Get-Content used config.root.json instead of published configuration.root.json; last rg returned outer0.')):
    d['pending_originals'].append(dict(original_ordinal=ordinal,actor=actor,actual_host_chunk=chunk,actual_outer_exit=outer,actual_python_exit=py,state='FAILED_RETAINED_METADATA_ONLY',description=description))
d['W09']['BR7_activation_failure_correction']=dict(first_rejected_pointer='/dependency_snapshot/audit_ranges/0',typed_range_promoted_to_whole_file_ref=True,resource_marker_was_not_first_rejected=True,diagnosis_ref=pin(S.parents[1]/'w09_br7_activation_resource_boundary_diagnosis_codex/diagnose-20261010-01/decision.json'),actual_delivery_audit_ref=pin(S/'w09.br7-activation-boundary-diagnosis.actual-audit.root.json'))
d['W09']['BR8_state']='SOURCE_DELTA_IN_PROGRESS_PENDING_NON_AUTHOR_REVIEW'
d['Root_running_processes']=[];d['counter_reset']=False;d['Canon_written']=False
new=save(S/'RESUME.cp391-w05-three-native0-br8-source-pending.live1231.root.json',(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
h=V/'HANDOFF_RESUME_PACK.md';before=h.read_bytes();arch=save(S/'HANDOFF.before-cp391-live1231.raw.md',before)
prefix=('<!-- Root current resume CP391 / OW195 / live1231; prior history preserved. -->\n\n'
        'W05 GEN02 三次公开 Native 均0，所有Job/Guard closed0；等待独立实际组件复核，完整20→24 OPEN。Root无在途进程。W09 BR7 activate原1224为typed audit range误当整文件引用，已真实诊断；新BR8 Source及非作者独审进行中。正式接受仍0/42。\n\n'
        f'CP391/OW195/CM40保持；已登记至1224，pending1225..1230，live next1231。机器续跑：{new["path"]}，sha256={new["sha256"]}，bytes={new["bytes"]}。旧handoff原始字节：{arch["path"]}。\n\n').encode()
t=h.with_name('HANDOFF_RESUME_PACK.cp391-live1231.tmp');save(t,prefix+before);os.replace(t,h)
assert d['current4']==[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
print(json.dumps(dict(resume_ref=new,handoff_ref=pin(h),historical_handoff_ref=arch,Canon_written=False,formal_acceptance=False),ensure_ascii=False))
