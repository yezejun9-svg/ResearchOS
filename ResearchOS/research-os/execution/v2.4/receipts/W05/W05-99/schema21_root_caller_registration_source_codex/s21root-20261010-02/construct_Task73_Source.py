from __future__ import annotations
import ast,difflib,hashlib,json,types
from pathlib import Path
Q=Path(__file__).resolve().parent
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/schema21_root_caller_registration_source_codex/s21root-20261010-01")
REVIEW=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/schema21_root_caller_registration_independent_source_review_codex/review-s21root-20261010-01")
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    href=dict(path=str(BASE/'HDF.json'),sha256='82b5f5af96d0fe62d4fa968181e061423595a670f9bcec63230effbcfe9c0b58',bytes=9999)
    mref=dict(path=str(BASE/'MF.json'),sha256='c5cf3440f97f0b9daa909c6287cec73c6fc2f7d85e33f38d568e8a49d9251a63',bytes=45184)
    h=json.loads(Path(href['path']).read_bytes());mf=json.loads(Path(mref['path']).read_bytes())
    guardref=next(r for r in mf['members'] if Path(r['path']).name=='read_Task69_basis_revision.py')
    raw=Path(guardref['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==guardref['sha256'] and len(raw)==guardref['bytes']
    gm=types.ModuleType('Task73_finite_guard');gm.__file__=guardref['path'];exec(compile(raw,gm.__file__,'exec'),gm.__dict__);guard=gm.Guard();closed=False
    try:
        refs=[href,mref,guardref]+[h[k] for k in ('caller_ref','contract_ref','source_inputs_ref','inverse_ref','controls_ref','actual_Task68_binding_ref','Source_final_guard_ref')]+h['original_failure_refs']
        refs+=[dict(path=str(REVIEW/'finite-Source-review.json'),sha256='782b9bda116048d8dfd7853689240452c7f6e6758b6ff38b38fd7e3e8bd91057',bytes=11522),dict(path=str(REVIEW/'independent-Source-guard.closed.json'),sha256='7e77b99d2d1c29dd5edc688649ad0e0e2080d057bd3ad9917052196be1ba95c7',bytes=65423)]
        task70=dict(hdf=dict(path=str(REVIEW/'HDF.json'),sha256='2ce6bf8678945854660d5f013e45907f5a064ae661fc7c032d703516c818385d',bytes=5336),mf=dict(path=str(REVIEW/'MF.json'),sha256='13578763ac817551d2a12a0a7e40f153b939dcf841088c4087f89a953b6739df',bytes=4389),decision=dict(path=str(REVIEW/'decision.json'),sha256='99c0fffae8ab7ac3e1c95a4a85d5624643e7737ff2385c62c7542b8996721842',bytes=10403))
        finite_ref,review_guard_ref=refs[-2:]
        refs+=list(task70.values())
        obsref=pin(REVIEW/'actual-Task68-Root-received-Final.observation.json');obs=json.loads(Path(obsref['path']).read_bytes());refs+=[obsref,obs['original_capture_ref']]
        for r in refs:guard.read(r['path'],r)
        original=Path(h['caller_ref']['path']).read_bytes();source=original.decode('utf-8')
        old='    need(type(start) is int and [x.get("ordinal") for x in value["pending"]] == list(range(start, value["next_original_failure_ordinal"])), "PENDING_CONTIGUOUS_CURRENT_COUNTER")'
        new='    next_ordinal = value["next_original_failure_ordinal"]\n    need(type(start) is int and type(next_ordinal) is int and next_ordinal >= start, "PENDING_CONTIGUOUS_CURRENT_COUNTER")\n    need(all(type(x) is dict and type(x.get("ordinal")) is int for x in value["pending"]) and [x["ordinal"] for x in value["pending"]] == list(range(start, next_ordinal)), "PENDING_CONTIGUOUS_CURRENT_COUNTER")'
        assert source.count(old)==1;source=source.replace(old,new)
        rawpeer=Path(obs['original_capture_ref']['path']).read_bytes();rows=[json.loads(x) for x in rawpeer.splitlines()];payload=rows[2]['payload']
        peer=obs['peer_actor'];envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+peer.removeprefix('codex:')+'\nPayload:\n'
        deliveredtext=payload['content'][0]['text'];delivered=json.loads(deliveredtext[len(envelope):] if deliveredtext.startswith(envelope) else deliveredtext)
        assert delivered['schema']=='researchos.main23-peer-review-delivery.v2' and delivered['component']=='OLD21_PROGRAMME_BUILDER_SOURCE' and delivered['operation']=='SOURCE_REVIEW_WITNESS'
        old2='    need(type(delivered) is dict and delivered.get("schema") == "researchos.old21-peer-review-delivery.v2",\n         "PEER_TYPED_DELIVERY_REQUIRED")\n'
        new2='''    legacy_builder = type(delivered) is dict and operation == "BUILDER_SOURCE_REVIEW_WITNESS" and delivered.get("schema") == "researchos.main23-peer-review-delivery.v2"
    delivery_operation = operation
    if legacy_builder:
        need(peer_actor == "codex:/root/full_w09_source_review" and delivered.get("component") == "OLD21_PROGRAMME_BUILDER_SOURCE"
             and payload.get("id") == %r and last.get("timestamp") == %r
             and len(checked(binding["original_capture_ref"])) == %d
             and hashlib.sha256(checked(binding["original_capture_ref"])).hexdigest() == %r
             and exact_ref_set(expected_refs) == exact_ref_set(list(BUILDER_ACCEPTED_REVIEW_REFS.values())),
             "EXACT_LEGACY_OLD21_BUILDER_DELIVERY")
        delivery_operation = "SOURCE_REVIEW_WITNESS"
    else:
        need(type(delivered) is dict and delivered.get("schema") == "researchos.old21-peer-review-delivery.v2",
             "PEER_TYPED_DELIVERY_REQUIRED")
'''%(obs['message_id'],obs['received_at'],obs['original_capture_ref']['bytes'],obs['original_capture_ref']['sha256'])
        assert source.count(old2)==1;source=source.replace(old2,new2)
        old3='and delivered.get("operation") == operation and delivered.get("verdict") == "ACCEPTED_SOURCE_ONLY"'
        new3='and delivered.get("operation") == delivery_operation and delivered.get("verdict") == "ACCEPTED_SOURCE_ONLY"'
        assert source.count(old3)==1;source=source.replace(old3,new3)
        old4='    cp = copy.deepcopy(old_cp); ow = copy.deepcopy(old_ow)'
        new4='    start = old_cp["work_in_progress"]["root_next_failure_ordinal_live"]; next_ordinal = pending["next_original_failure_ordinal"]\n    need(type(start) is int and type(next_ordinal) is int and next_ordinal >= start, "PENDING_CONTIGUOUS_CURRENT_COUNTER")\n    need(type(pending.get("pending")) is list and all(type(x) is dict and type(x.get("ordinal")) is int for x in pending["pending"]) and [x["ordinal"] for x in pending["pending"]] == list(range(start, next_ordinal)), "PENDING_CONTIGUOUS_CURRENT_COUNTER")\n    cp = copy.deepcopy(old_cp); ow = copy.deepcopy(old_ow)'
        assert source.count(old4)==1;source=source.replace(old4,new4)
        candidate=source.encode('utf-8');compile(candidate,str(Q/'old21_root.source.py'),'exec')
        # Sequence of three exact inverses, not broad substring replacement or untouched function recompilation.
        restored=candidate.decode().replace(new4,old4).replace(new3,old3).replace(new2,old2).replace(new,old).encode('utf-8');assert restored==original
        p=Q/'old21_root.source.py'
        with p.open('xb') as f:f.write(candidate)
        inv=save('Task73-exact-inverse.json',dict(schema='researchos.old21-caller-Task73-inverse.v1',base_ref=h['caller_ref'],candidate_ref=pin(p),layers=[dict(old_hex=a.encode().hex(),new_hex=b.encode().hex()) for a,b in [(old,new),(old2,new2),(old3,new3),(old4,new4)]],full_original_Source_restored=True,restored_Source_SHA=hashlib.sha256(restored).hexdigest(),prior_complete_inverse_chain_ref=h['inverse_ref'],only_changed_functions=['failure_rows','projection','validate_peer_delivery']))
        d=Q/'candidate.diff'
        with d.open('xb') as f:f.write(''.join(difflib.unified_diff(original.decode().splitlines(keepends=True),source.splitlines(keepends=True),fromfile='sealed-s21root-01/old21_root.source.py',tofile='s21root-02/old21_root.source.py')).encode())
        basis=save('source-inputs.basis.json',dict(schema='researchos.old21-caller-Task73-basis.v1',source_author='codex:/root/backup_regression_resources',base_hdf_ref=href,base_mf_ref=mref,base_caller_ref=h['caller_ref'],base_contract_ref=h['contract_ref'],base_source_inputs_ref=h['source_inputs_ref'],base_inverse_ref=h['inverse_ref'],base_successful_guard_ref=h['Source_final_guard_ref'],base_controls_ref=h['controls_ref'],base_Task68_binding_ref=h['actual_Task68_binding_ref'],original_failure_refs=h['original_failure_refs'],Task70_finite_review_ref=finite_ref,Task70_guard_ref=review_guard_ref,Task70_review_refs=task70,actual_Task68_observation_ref=obsref,actual_Task68_raw_ref=obs['original_capture_ref'],known_builder_Source_review_refs=h['known_builder_Source_review_refs'],current_before_archive_refs=h['current_before_archive_refs'],references=refs,old_failed_guard_status=h['Source_old_failed_guard_status'],actual_RootScope_ref=None,actual_runtime_qualification_ref=None,actual_programme_qualification_ref=None,execution_grant=False,formal_acceptance=False))
        closure=save('construction-Source-guard.closed.json',guard.close());closed=True
        print(json.dumps(dict(caller_ref=pin(p),basis_ref=basis,inverse_ref=inv,diff_ref=pin(d),guard_ref=closure),ensure_ascii=False))
    finally:
        if not closed and any(not stream.closed for stream,_,_ in guard.held):save('construction-attempt-failure.guard.closed.json',guard.close())
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
