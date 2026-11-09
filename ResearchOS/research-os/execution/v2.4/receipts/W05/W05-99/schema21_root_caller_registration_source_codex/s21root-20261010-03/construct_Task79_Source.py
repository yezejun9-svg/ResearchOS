from __future__ import annotations
import ast,difflib,hashlib,json,types
from pathlib import Path
Q=Path(__file__).resolve().parent
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/schema21_root_caller_registration_source_codex/s21root-20261010-02")
LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def pin(p):
    r=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    h_ref=dict(path=str(BASE/'HDF.json'),sha256='05edd46f975d5d85cfa6c157cad648d90ab8c0ac9ad60e8514e280863a4f7492',bytes=12700)
    m_ref=dict(path=str(BASE/'MF.json'),sha256='73add6a949ad89cebcfe880b49035e6e88eeebdad8fe4309f0baefa9bf85ffdf',bytes=13633)
    h=json.loads(Path(h_ref['path']).read_bytes());mf=json.loads(Path(m_ref['path']).read_bytes())
    prior_h=json.loads(Path(h['base_Source_hdf_ref']['path']).read_bytes());prior_mf=json.loads(Path(h['base_Source_mf_ref']['path']).read_bytes());gr=next(r for r in prior_mf['members'] if Path(r['path']).name=='read_Task69_basis_revision.py')
    helper=Path(gr['path']).read_bytes();assert len(helper)==gr['bytes'] and hashlib.sha256(helper).hexdigest()==gr['sha256']
    gm=types.ModuleType('Task79_guard');gm.__file__=gr['path'];exec(compile(helper,gm.__file__,'exec'),gm.__dict__);guard=gm.Guard();closed=False
    try:
        refs=[h_ref,m_ref,gr]+[h[k] for k in ('caller_ref','contract_ref','source_inputs_ref','inverse_ref','controls_ref','controls_guard_ref','Source_final_guard_ref')]+h['original_failure_refs']
        for r in refs:guard.read(r['path'],r)
        # Three bounded original Root records. Source observation is not Root-issued witness/authority.
        offsets=[0,273574422,273574556];prefix=LOG.stat().st_size;selected=[]
        with LOG.open('rb') as f:
            for offset in offsets:f.seek(offset);line=f.readline();assert line.endswith(b'\n') and offset+len(line)<=prefix;selected.append(line)
        rows=[json.loads(x) for x in selected];first,last=rows[1:]
        assert rows[0]['type']=='session_meta' and rows[0]['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
        assert first['ordinal']==62777 and last['ordinal']==62778 and first['timestamp']=='2026-10-09T18:48:49.566Z' and last['timestamp']=='2026-10-09T18:48:49.567Z'
        assert first['type']=='inter_agent_communication_metadata' and last['payload']['type']=='agent_message' and last['payload']['author']=='/root/full_w09_source_review' and last['payload']['recipient']=='/root' and last['metadata']['client_authored'] is False and last['payload']['id']=='amsg_01a121ff-1c9e-7fc0-b9fe-93ee27453217'
        rootraw=Q/'actual-Task76-platform-delivery.raw.jsonl'
        with rootraw.open('xb') as f:f.write(b''.join(selected))
        obs=save('actual-Task76-platform-delivery.observation.json',dict(schema='researchos.independent-actual-peer-observation.v1',observed_by='codex:/root/backup_regression_resources',root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',source_audit_path=str(LOG),source_prefix_size_observed=prefix,source_line_offsets=offsets,source_line_bytes=[len(x) for x in selected],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in selected],original_capture_ref=pin(rootraw),peer_actor='codex:/root/full_w09_source_review',message_id=last['payload']['id'],received_at=last['timestamp'],metadata_at=first['timestamp'],metadata_ordinal=first['ordinal'],delivery_ordinal=last['ordinal'],observed_interval_milliseconds=1,issued_by_Root=False,Root_witness=False,Root_authorization=False,formal_acceptance=False,execution_grant=False))
        original=Path(h['caller_ref']['path']).read_bytes();old=b'and first.get("timestamp") == last.get("timestamp") and payload.get("type") == "agent_message"'
        new=b'and when(first.get("timestamp")) <= when(last.get("timestamp")) and (when(last.get("timestamp")) - when(first.get("timestamp"))).total_seconds() <= 1 and payload.get("type") == "agent_message"'
        assert original.count(old)==1;candidate=original.replace(old,new);compile(candidate,str(Q/'old21_root.source.py'),'exec');assert candidate.replace(new,old)==original
        p=Q/'old21_root.source.py'
        with p.open('xb') as f:f.write(candidate)
        inv=save('Task79-exact-inverse.json',dict(schema='researchos.old21-caller-Task79-inverse.v1',base_ref=h['caller_ref'],candidate_ref=pin(p),old_hex=old.hex(),new_hex=new.hex(),candidate_byte_offset=original.index(old),full_original_Source_restored=True,restored_Source_SHA=hashlib.sha256(candidate.replace(new,old)).hexdigest(),prior_complete_inverse_ref=h['inverse_ref'],only_changed_function='validate_peer_delivery',only_source_logic_change='metadata timestamp <= adjacent Final timestamp with interval <=1second'))
        d=Q/'candidate.diff'
        with d.open('xb') as f:f.write(''.join(difflib.unified_diff(original.decode().splitlines(keepends=True),candidate.decode().splitlines(keepends=True),fromfile='sealed-s21root-02/old21_root.source.py',tofile='s21root-03/old21_root.source.py')).encode())
        basis=save('source-inputs.basis.json',dict(schema='researchos.old21-caller-Task79-basis.v1',source_author='codex:/root/backup_regression_resources',base_hdf_ref=h_ref,base_mf_ref=m_ref,base_caller_ref=h['caller_ref'],base_contract_ref=h['contract_ref'],base_source_inputs_ref=h['source_inputs_ref'],base_inverse_ref=h['inverse_ref'],base_successful_guard_ref=h['Source_final_guard_ref'],base_controls39_ref=h['controls_ref'],base_controls_guard_ref=h['controls_guard_ref'],guard_helper_ref=gr,original_failure_refs=h['original_failure_refs'],references=refs,actual_Task76_observation_ref=obs,actual_Task76_raw_ref=pin(rootraw),known_builder_Source_review_refs=h['known_builder_Source_review_refs'],current_before_archive_refs=h['current_before_archive_refs'],legacy_Task68_raw_ref=h['actual_Task68_raw_ref'],legacy_Task68_observation_ref=h['actual_Task68_observation_ref'],Root_original1091='Root-owned original receipt preserved externally; never reset or reinterpret as product error',old_failed_guard_status=h['old_failed_guard_status'],actual_RootScope_ref=None,actual_runtime_qualification_ref=None,actual_programme_qualification_ref=None,execution_grant=False,formal_acceptance=False))
        closure=save('construction-Source-guard.closed.json',guard.close());closed=True
        print(json.dumps(dict(caller_ref=pin(p),basis_ref=basis,inverse_ref=inv,actual_observation_ref=obs,actual_raw_ref=pin(rootraw),guard_ref=closure),ensure_ascii=False))
    finally:
        if not closed and any(not s.closed for s,_,_ in guard.held):save('construction-attempt-failure.guard.closed.json',guard.close())
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
