import sys
sys.dont_write_bytecode=True
import ast,difflib,hashlib,json,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99';N=Path(__file__).resolve().parent
V=W/'w09_evidence_v6_source_preparation_codex/7e91acb06d354c0aa87b5f30ab9951d0/w09_evidence_closure.v6.proposed.py'
Q=W/'w09c19_actual_independent_review_codex/review-9125f15c751245e287e1eb3b17ba84eb'
GP=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 q=pin(v['path']);assert (q['sha256'],q['bytes'])==(v['sha256'].removeprefix('sha256:'),v['bytes']);return q
def save(n,v):
 with (N/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/n)
assert pin(V)['sha256']=='2989eb2c89a0647cf9bf9fb99841dcb8e943d64c6dd84d0a0fe7bca4b9568eec' and pin(V)['bytes']==42128
assert pin(Q/'HDF.json')['sha256']=='f090e9d33cb52f5ede999d5db33312e3a3b29e0a740a4df00c78b1a15f263e10'
assert pin(Q/'MF.json')['sha256']=='ab8d44dba6a7c9e0e4bb1d509972dd3d24edfcb9fcd901a88d36110ab367bd3b'
assert pin(GP)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
h=json.loads((Q/'HDF.json').read_bytes());mf=json.loads((Q/'MF.json').read_bytes());members={Path(v['path']).name:v for v in mf['members']}
finding=verify(h['source_P1_ref']);proof=verify(h['lossless_reconstruction_ref']);report_ref=verify(next(v for v in mf['input_anchor_refs'] if Path(v['path']).name=='report.json'));report=json.loads(Path(report_ref['path']).read_bytes())
index_ref=verify(members['native-packet.public-index.json.input.json']);index=json.loads(Path(index_ref['path']).read_bytes());T=Path(index['consumer_source_root'])
assert index['original_report_ref']==report_ref
stdout_path=T/report['raw_evidence_references'][0];pair=next(v for v in index['raw_copy_mapping'] if Path(v['original_ref']['path'])==stdout_path)
stdout_ref=verify(pair['original_ref']);stdout_archive_ref=verify(pair['archive_ref']);assert stdout_ref['sha256']=='dedec7ea37a965791be5f11b9984e21cf779f8486b784fbae4c07ca062bf4930' and stdout_ref['bytes']==10560
assert (stdout_ref['sha256'],stdout_ref['bytes'])==(stdout_archive_ref['sha256'],stdout_archive_ref['bytes'])
canonical=[pin(R/'execution/v2.4'/(n+'.json')) for n in ('checkpoint','path_ownership','step_state','commands')]
assert json.loads(Path(canonical[0]['path']).read_bytes())['revision']==365 and json.loads(Path(canonical[1]['path']).read_bytes())['revision']==169
refs=[pin(V),pin(Q/'HDF.json'),pin(Q/'MF.json'),finding,proof,report_ref,index_ref,stdout_ref,stdout_archive_ref,verify(members['failure-origin.927.original-tool-io.json']),pin(GP),pin(__file__),pin(sys.executable)]+canonical
module=types.ModuleType('fragment_source_read_guard');module.__file__=str(GP);sys.modules[module.__name__]=module;exec(compile(GP.read_bytes(),str(GP),'exec'),module.__dict__)
for mod in list(sys.modules.values()):
 for field in ('__file__','__cached__'):
  p=getattr(mod,field,None)
  if p and Path(p).is_file():refs.append(pin(p))
refs=list({v['path']:verify(v) for v in refs}.values())
guard=module.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(refs)
 original=guard.get_buffer(str(V));source=original.decode('utf-8')
 old='''    assertions = []
    for event in events:
        output = event.get("Output", "")
        require(isinstance(output, str), "GO_OUTPUT_NOT_TEXT")
        for line in output.splitlines():
            if line.startswith("W09_ASSERTION "):
                item = json.loads(line[len("W09_ASSERTION "):])
                require(isinstance(item, dict) and event.get("Test") == item.get("test_name")
                        and item.get("test_name") in selected, "ASSERTION_STDOUT_OWNER_MISMATCH")
                item["raw_evidence_reference"] = refs[0]
                assertions.append(item)
'''
 helper='''def _go_assertions(events, selected, stdout_ref):
    """Assemble complete Output lines without joining different Package/Test owners."""
    assertions = []
    pending = {}
    for event in events:
        output = event.get("Output", "")
        require(isinstance(output, str), "GO_OUTPUT_NOT_TEXT")
        owner = (event.get("Package"), event.get("Test"))
        require(all(value is None or isinstance(value, str) for value in owner),
                "GO_OUTPUT_OWNER_NOT_TEXT")
        text = pending.get(owner, "") + output
        lines = text.split("\\n")
        pending[owner] = lines.pop()
        for line in lines:
            if line.startswith("W09_ASSERTION "):
                item = json.loads(line[len("W09_ASSERTION "):])
                require(isinstance(item, dict) and owner[1] == item.get("test_name")
                        and item.get("test_name") in selected, "ASSERTION_STDOUT_OWNER_MISMATCH")
                item["raw_evidence_reference"] = stdout_ref
                assertions.append(item)
    require(not any(pending.values()), "GO_OUTPUT_DANGLING_FRAGMENT")
    return assertions


'''
 assert source.count(old)==1
 anchor='def verify_native(root, source, report, expected, selected):'
 assert source.count(anchor)==1
 updated=source.replace(old,'    assertions = _go_assertions(events, selected, refs[0])\n').replace(anchor,helper+anchor)
 ast.parse(updated)
 inverse=updated.replace(helper,'',1).replace('    assertions = _go_assertions(events, selected, refs[0])\n',old,1)
 assert inverse.encode()==original
 target=N/'w09_evidence_closure.v7.proposed.py'
 with target.open('xb') as f:f.write(updated.encode())
 a=source.splitlines(keepends=True);b=updated.splitlines(keepends=True);ops=[]
 for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():ops.append(dict(op=op,old_start=i,old_end=j,new_start=k,new_end=l,old_lines=a[i:j],new_lines=b[k:l]))
 assert ''.join(x for v in ops for x in v['old_lines']).encode()==original and ''.join(x for v in ops for x in v['new_lines']).encode()==target.read_bytes()
 save('source-provenance.json',dict(original_source_ref=pin(V),candidate_source_ref=pin(target),old_parser_block=old,new_parser_call='    assertions = _go_assertions(events, selected, refs[0])\n',added_helper=helper,opcodes=ops,whole_original_byte_inverse=True,whole_candidate_byte_forward=True,changed_existing_function='verify_native',added_function='_go_assertions',all_other_source_bytes_preserved=True))
 save('source-inputs.json',dict(refs=refs,canonical_refs=canonical,original_source_ref=pin(V),actual_stdout_ref=stdout_ref,actual_stdout_archive_ref=stdout_archive_ref,actual_report_ref=report_ref,actual_review_handoff_ref=pin(Q/'HDF.json'),actual_review_manifest_ref=pin(Q/'MF.json'),finding_ref=finding,original_review_failure927_ref=verify(members['failure-origin.927.original-tool-io.json']),guard_ref=pin(GP)))
 for v in refs:assert pin(v['path'])==v
 print(json.dumps(dict(status='V7_SOURCE_PREPARED_PARSER_ONLY',candidate_ref=pin(target),input_count=len(refs),actual_producer_consumer=False)),flush=True)
finally:
 cleanup=guard.close();save('preparation-source-guard.cleanup.json',cleanup)
 assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
