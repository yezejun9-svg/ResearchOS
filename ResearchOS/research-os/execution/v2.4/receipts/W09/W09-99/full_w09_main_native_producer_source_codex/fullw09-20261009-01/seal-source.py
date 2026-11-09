"""Archive actual Source tool pairs and seal a reviewable, non-authoritative package."""
import ast, hashlib, json, os, re, sys, types
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os')
SELF_LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-49-27-01a11e22-ecb2-7720-80d2-af63727d414d.jsonl')
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(N/name)
def check(ok,message):
    if not ok:raise ValueError(message)
def undo(text,patch):
    original=text.splitlines(keepends=True);lines=patch.splitlines(keepends=True);out=[];pos=0;i=2
    while i<len(lines):
        match=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\r?\n',lines[i]);check(match is not None,'PATCH_HUNK_HEADER')
        start=int(match[1])-1;out.extend(original[pos:start]);pos=start;i+=1
        while i<len(lines) and not lines[i].startswith('@@ '):
            line=lines[i];tag=line[0];payload=line[1:]
            if tag in (' ','-'):check(pos<len(original) and original[pos]==payload,'INVERSE_CONTEXT');pos+=1
            if tag in (' ','+'):out.append(payload)
            check(tag in (' ','-','+'),'PATCH_TAG');i+=1
    out.extend(original[pos:]);return ''.join(out)
def main():
    choice=json.loads((N/'source.choice.json').read_bytes());common=choice['common']
    base_ref=json.loads((N/'source-build-observation.json').read_bytes())['base_runtime_ref']
    # Read bytes directly, preserving mixed original/new line endings.
    runtime=(N/'full_w09_runtime.source.py').read_bytes().decode();base=Path(base_ref['path']).read_bytes().decode()
    restored=undo(runtime,(N/'runtime.inverse.diff').read_bytes().decode())
    check(restored.encode()==base.encode(),'EXACT_RUNTIME_INVERSE_BYTES')
    check(undo(base,(N/'runtime.forward.diff').read_bytes().decode()).encode()==runtime.encode(),'EXACT_RUNTIME_FORWARD_BYTES')
    inverse=save('inverse-byte-check.json',dict(status='PASS_SOURCE_ONLY',base_runtime_ref=base_ref,runtime_ref=pin(N/'full_w09_runtime.source.py'),
        inverse_ref=pin(N/'runtime.inverse.diff'),forward_ref=pin(N/'runtime.forward.diff'),exact_original_bytes_restored=True,Main_written=False))
    # Capture actual session header and complete matching tool call/result records.
    size=SELF_LOG.stat().st_size
    with SELF_LOG.open('rb') as f:
        header=f.readline();f.seek(max(len(header),size-64*1024*1024))
        if f.tell()!=len(header):f.readline()
        start=f.tell();tail=f.read(size-start)
    check(json.loads(header)['payload']['id']==os.environ['CODEX_THREAD_ID']=='01a11e22-ecb2-7720-80d2-af63727d414d','ACTUAL_SOURCE_ACTOR_SESSION')
    calls={};pairs={};offset=start
    chunks={'dd1744','168169','a09cda','fceb00','d826dd','c56c4a'}
    for line in tail.splitlines(keepends=True):
        try:item=json.loads(line)
        except (ValueError,UnicodeDecodeError):offset+=len(line);continue
        payload=item.get('payload',{});kind=payload.get('type');cid=payload.get('call_id')
        if kind in ('function_call','custom_tool_call') and cid:calls[cid]=(offset,line,item)
        elif kind in ('function_call_output','custom_tool_call_output') and cid in calls:
            output=payload.get('output','')
            for chunk in chunks:
                if chunk in str(output) and chunk not in pairs:pairs[chunk]=(calls[cid],(offset,line,item))
        offset+=len(line)
    check(set(pairs)==chunks,'ALL_REQUIRED_ACTUAL_TOOL_PAIRS')
    archive=[]
    for chunk,(call,result) in sorted(pairs.items()):
        raw=header+call[1]+result[1];p=N/('actual-Source-tool-'+chunk+'.raw.jsonl')
        with p.open('xb') as f:f.write(raw)
        binding=save('actual-Source-tool-'+chunk+'.binding.json',dict(source_actor='codex:/root/native_temp_independent_review',
            source_thread_id=os.environ['CODEX_THREAD_ID'],source_audit_path=str(SELF_LOG),source_prefix_size_observed=size,
            source_line_offsets=[0,call[0],result[0]],source_line_bytes=[len(header),len(call[1]),len(result[1])],
            original_line_sha256=[hashlib.sha256(v).hexdigest() for v in (header,call[1],result[1])],original_capture_ref=pin(p),
            original_call_id=call[2]['payload']['call_id'],chunk_id=chunk))
        archive.append(dict(chunk_id=chunk,binding_ref=binding,raw_ref=pin(p)))
    save('original-diagnostics.json',dict(originals=[dict(ordinal=1026,chunk_id='dd1744',actual_outer_exit=1,Python_exit=None,rg_exit=None,Go_exit=None,Native_exit=None,
        SQL_exit=None,dispatcher_exit=None,model_exit=None,description='Read query guessed a nonexistent test file; no actual runtime.')
        ,dict(ordinal=1029,chunk_id='168169',actual_outer_exit=0,Python_exit=None,rg_exit=None,Go_exit=None,Native_exit=None,
        SQL_exit=None,dispatcher_exit=None,model_exit=None,description='rg emitted missing candidate-directory diagnostic; following read succeeded; individual rg exit unobserved.')],
        actual_original_captures=archive,automatic_retry=False))
    controls=json.loads((N/'source-controls.json').read_bytes());extra=json.loads((N/'audit-and-closure-controls.json').read_bytes())
    check(controls['status']==extra['status']=='PASS_SOURCE_ONLY','SOURCE_CONTROLS_PASSED')
    for ref in common['source21']:check(pin(ref['path'])==ref,'MAIN21_POST_CHECK')
    mr=R/'execution/v2.4/receipts/W09/W09-99/main_c19_native_actual_independent_review_codex/review-1a12035-v2'
    evidence=json.loads((mr/'native-evidence-review.json').read_bytes());closure=json.loads(Path(evidence['compiler_closure_ref']['path']).read_bytes())
    inventory=json.loads(Path(closure['original_inventory_ref']['path']).read_bytes())
    check(pin(closure['original_inventory_ref']['path'])==closure['original_inventory_ref'],'MR2_INVENTORY_PIN')
    save('MR2-program-reuse-evaluation.json',dict(status='DO_NOT_REUSE_AS_TWO_PACKAGE_TEST_PROGRAM',MR2_handoff_ref=pin(mr/'HDF.json'),
        MR2_manifest_ref=pin(mr/'MF.json'),MR2_decision_ref=pin(mr/'actual-decision.json'),MR2_native_review_ref=pin(mr/'native-evidence-review.json'),
        compiler_closure_ref=evidence['compiler_closure_ref'],actual_inventory_ref=closure['original_inventory_ref'],
        retrieval_packages=[v for v in inventory['packages'] if '/adapters/retrieval' in v],
        domain_packages=[v for v in inventory['packages'] if '/internal/domain' in v],
        retained_executable_program_refs=[v for v in inventory['private_generated_input_refs']+inventory['private_export_refs'] if v['path'].endswith('.exe')],
        reason='Only domain test variants are in actual closure; MR2 qualifies C19 modes only and has no reusable two-package test-executable authority.',
        old_C19_results_preserved=True,prior_results_used_as_new_selector_results=False,actual_native_rerun=False))
    # Final Source guard excludes current canonical files; validate all source input bytes.
    gm=types.ModuleType('final_source_guard');gm.__file__=common['guard_ref']['path']
    check(pin(gm.__file__)==common['guard_ref'],'GUARD_PIN')
    exec(compile(Path(gm.__file__).read_bytes(),gm.__file__,'exec'),gm.__dict__)
    local=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
    guards=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    guards.acquire(local+common['source21'])
    try:
        for ref in local+common['source21']:check(pin(ref['path'])==ref,'SEALED_INPUT_DRIFT')
    finally:
        closed=guards.close();save('source-final-guard.closed.json',closed)
        check(closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0,'FINAL_GUARD_CLOSED')
    mf=save('MF.json',dict(schema='researchos.w09-three-selector-producer-source-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
    hdf=save('HDF.json',dict(schema='researchos.w09-three-selector-producer-source-handoff.v1',actor_id='codex:/root/native_temp_independent_review',
        source_thread_id=os.environ['CODEX_THREAD_ID'],status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW',manifest_ref=mf,
        calling_contract_ref=pin(N/'root-calling-contract.json'),source_choice_ref=pin(N/'source.choice.json'),
        runtime_ref=pin(N/'full_w09_runtime.source.py'),launcher_ref=pin(N/'full_w09_launcher.source.py'),
        prepare_caller_ref=pin(N/'prepare_full_w09.source.py'),producer_caller_ref=pin(N/'run_full_w09.source.py'),
        controls_ref=pin(N/'source-controls.json'),audit_closure_controls_ref=pin(N/'audit-and-closure-controls.json'),inverse_check_ref=inverse,
        final_guard_ref=pin(N/'source-final-guard.closed.json'),MR2_reuse_evaluation_ref=pin(N/'MR2-program-reuse-evaluation.json'),
        original_diagnostics_ref=pin(N/'original-diagnostics.json'),Source21=common['source21'],
        selectors={k:{field:c[field] for field in ('selector','run_id','mode','native_scope','selected_tests','expected_native_ids','packages','receipt_root','scratch_root','output_root')} for k,c in choice['selectors'].items()},
        finite_Source_checks=len(controls['controls'])+len(extra['controls'])+1,actual_executed=False,actual_Go_runs=0,actual_Native_runs=0,
        actual_dispatcher_runs=0,actual_SQL_runs=0,actual_model_provider_calls=0,Main_written=False,Canon_written=False,current_CanonicalPair_held=False,
        formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,execution_grant=False,
        future_Root_scope=None,future_Root_request=None,future_registration=None,future_ModeProof=None,future_route_leases=None,future_capture_index=None,
        next_gate='Independent non-author Source review; Root must later capture real author/reviewer delivery and issue fresh scope/lease/current Canon vector before prepare/run.'))
    check(pin(N/'MF.json')==mf and pin(N/'HDF.json')==hdf,'SEALED_PAIR_FINAL')
    print(json.dumps(dict(status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW',HDF=hdf,MF=mf,contract=pin(N/'root-calling-contract.json'),checks=69),ensure_ascii=False))
if __name__=='__main__':main()
