from pathlib import Path
import hashlib,json,os
from datetime import datetime,timezone
r=Path(r'D:\作品集\ResearchOS\research-os')
n=Path(__file__).resolve().parent
target=r/'execution/v2.4/HANDOFF_RESUME_PACK.md';raw=target.read_bytes()
archive=n/'historical.HANDOFF.before-live1064.root.md'
with archive.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
state=dict(schema='researchos.root-live-resume-pointer.v1',issued_by='codex:/root',
    created_utc=datetime.now(timezone.utc).isoformat(),canonical_revisions=dict(checkpoint=371,path_ownership=175,commands=39),
    registered_next_original=1024,live_next_original=1064,formal_accepted=0,formal_required=42,parent_required=22,
    sealed_resume_path=str(n/'RESUME.cp371-time-contract-live1059.root.json'),
    sealed_pending_path=str(n/'pending-diagnostics.cp371.live1059.root.json'),sealed_pending_through=1058,
    additional_originals=dict(
        original1059='Attach Task59 source-key count assertion; 9c0bf7/session15349/68bba7 outer/Python1/1',
        original1060='Attach Task59 historical formula assertion; bc71b6/session95656/a3fee4 outer/Python1/1',
        original1061='Attach Task59 historical script rg path422c54 outer1/PythonNULL',
        original1062='Root functions.exec JavaScript parse failure before shell; all process exits NULL',
        original1063='Attach Task59 report closed field wrapper lookup; 051bda/session89233/8fa2d9 outer/Python1/1'),
    Main23='M3 blocked by true time and FINAL envelope findings; author Task61 creates M4; actual build not started.',
    W09='V3 true published package and author audit passed; independent report packaging pending; native groups not started.',
    public22='Readonly caller Source accepted; current full4 observed; new registration waits fresh leaf-review plaintext. Original1025 FAILED; prior four children not rerun.',
    failures_reset=False,goal_status='ACTIVE',execution_grant=False,formal_acceptance=False)
statepath=n/'RESUME_POINTER.live1064.root.json'
with statepath.open('xb') as f:f.write((json.dumps(state,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));f.flush();os.fsync(f.fileno())
prefix=('# 当前续跑入口：Root live1064 / Canon CP371-OW175-CM39\n\n'
    '读取 '+str(statepath)+' 与 '+str(n/'RESUME.cp371-time-contract-live1059.root.json')+'。'
    '35个待登记原件已封至1058，1059至1063待完整IO关联。正式接受0/42，目标ACTIVE；旧失败和完整交接正文保留。\n\n').encode('utf-8')
temp=n/'handoff.live1064.atomic.tmp'
with temp.open('xb') as f:f.write(prefix+raw);f.flush();os.fsync(f.fileno())
os.replace(temp,target);assert target.read_bytes().endswith(raw)
print(json.dumps(dict(pointer=str(statepath),sha256=hashlib.sha256(statepath.read_bytes()).hexdigest(),
    handoff_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),old_handoff_bytes_preserved=len(raw),goal_status='ACTIVE'),ensure_ascii=False))

