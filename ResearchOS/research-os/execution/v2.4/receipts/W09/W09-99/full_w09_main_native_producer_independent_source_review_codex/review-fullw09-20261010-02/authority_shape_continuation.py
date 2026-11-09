"""Finish exact Scope shape review after observed package/delivery blockers."""
import hashlib
import json
import os
from pathlib import Path
import sys
import textwrap
import types

sys.dont_write_bytecode=True
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-02'
OLD=W/'full_w09_main_native_producer_source_codex/fullw09-20261009-01'
PRIOR=W/'full_w09_main_native_producer_independent_source_review_codex/review-fullw09-20261009-01'
D=Path(__file__).resolve().parent
ACTOR='codex:/root/full_w09_source_review'
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
    with (D/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(D/name)
def inert(p,name):
    m=types.ModuleType(name);m.__file__=str(p)
    exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def main():
    checks=[]
    def check(name,ok,detail=None):
        if not ok:raise AssertionError(name)
        checks.append(dict(name=name,status='PASS_SOURCE_ONLY',detail=detail))
    def reject(name,fn,code):
        try:fn()
        except (ValueError,KeyError,TypeError,FileNotFoundError) as exc:
            check(name,code in str(exc),dict(exception_type=type(exc).__name__,error=str(exc)));return
        raise AssertionError(name+'_ACCEPTED')
    h=load(S/'HDF.json');c=load(S/'source.choice.json');contract=load(S/'root-calling-contract.json')
    m=inert(S/'full_w09_runtime.source.py','shape_continuation_runtime')
    href,mref=pin(S/'HDF.json'),pin(S/'MF.json')
    check('Root_HDF_pin',href['sha256']=='f5bbc877a80892fc25b944d35462ff49a230ae180a0c3fd1e87c9971fda34260' and href['bytes']==8106)
    check('Root_MF_pin',mref['sha256']=='348787ca166129839be1e71c4128597c20e840590c02a1d2d263b2668ffb2715' and mref['bytes']==9888)
    pair_h,pair_refs=m.pair(href,mref)
    bound={key:pin(S/name) for key,name in contract['source_file_bindings'].items()}
    refs=[*pair_refs,*c['common']['source21'],pin(PRIOR/'source-review-decision.json'),pin(D/'original-failure-168ba0.script.py'),
          pin(D/'original-failure-f2df44.script.py'),c['common']['guard_ref']]
    gm=inert(c['common']['guard_ref']['path'],'continuation_guard')
    guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    findings=[]
    try:
        guard.acquire(refs)
        reject('actual_sealed_package_refs_blocker',m.package_refs,'SOURCE_PACKAGE')
        findings.append(dict(id='V2-SOURCE-BLOCKER-01',priority='BLOCKER',source_ref=pin(S/'full_w09_runtime.source.py'),line=86,
            title='package_refs rejects the immutable v2 HDF status',handoff_ref=href,actual_status=h['status'],
            required_status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW',production_rejection='SOURCE_PACKAGE',
            impact='Every validate_authority invocation fails before actualprepare/run.',
            fix='Issue a new Source revision with exact compatible Source-only HDF schema/status, and test real package_refs against the final sealed pair. Keep all review, Root audit, Scope, lease and canonical registration gates.'))
        # Exact observed Root offsets from successful a13189 probe; no searching, fabricated rows or expanded authority.
        root=Path(m.ROOT_AUDIT);size=root.stat().st_size
        with root.open('rb') as f:
            header=f.readline();f.seek(264502261);result_line=f.readline()
            f.seek(264502261-65536);near=f.read(65536)
        result=json.loads(result_line)
        check('observed_new_author_message',result['ordinal']==60713 and result['payload']['author']=='/root/w09_formal_profile_source_impl')
        # Find the original adjacent metadata by ordinal within this bounded preceding window.
        offset=264502261-65536;call=None
        for line in near.splitlines(keepends=True):
            try:item=json.loads(line)
            except (ValueError,UnicodeDecodeError):offset+=len(line);continue
            if item.get('ordinal')==60712 and item.get('type')=='inter_agent_communication_metadata':call=(offset,line,item)
            offset+=len(line)
        check('observed_adjacent_metadata',call is not None and call[2]['timestamp']==result['timestamp'])
        peerpath=D/'actual-v2-author-short-digest-Root-peer.raw.jsonl'
        with peerpath.open('xb') as f:f.write(header+call[1]+result_line)
        author_audit=save('actual-v2-author-short-digest-Root-peer.binding.json',dict(schema='researchos.w09-native-producer.actual-audit.v1',
            actor_id=m.AUTHOR,Root_thread_id=m.ROOT_THREAD_ID,source_audit_path=m.ROOT_AUDIT,
            source_line_offsets=[0,call[0],264502261],original_line_sha256=[hashlib.sha256(line).hexdigest() for line in (header,call[1],result_line)],
            source_prefix_size_observed=size,original_capture_ref=pin(peerpath),binding_sha256=href['sha256']))
        with root.open('rb') as f:
            for offset,line in zip([0,call[0],264502261],(header,call[1],result_line)):
                f.seek(offset);check('real_peer_original_bytes_'+str(offset),f.read(len(line))==line)
        reject('actual_new_author_delivery_full_digest_missing',lambda:m.actual_audit(author_audit,m.AUTHOR,href['sha256']),'AUDIT_ARTIFACT_BINDING')
        findings.append(dict(id='V2-ROOT-DELIVERY-GAP-01',priority='PREPARE_PREREQUISITE',source_ref=pin(peerpath),
            actual_author='/root/w09_formal_profile_source_impl',actual_host_observed_ordinal=60713,
            visible_digest='f5bbc877…34260',required_digest=href['sha256'],production_rejection='AUDIT_ARTIFACT_BINDING',
            fix='The Source author must deliver the full sealed HDF path/SHA256/bytes in a real plaintext final peer message, which Root then captures without modifying original host records.'))
        # Reuse the explicit complete chain fixture from the corrected script, changing ONLY the now-known missing author proof to a declared mock.
        text=(D/'delta_authority_review.py').read_text()
        start=text.index('        # Construct the WHOLE exact authority chain in memory.')
        end=text.index("        check('all_delta_inputs_preserved'",start)
        chunk=textwrap.dedent(text[start:end])
        old="if ref == author_audit:\n        return originals[2](ref, actor, binding)"
        assert chunk.count(old)==1
        chunk=chunk.replace(old,"if ref == author_audit:\n        m.require(actor == m.AUTHOR and binding == href['sha256'], 'SYNTHETIC_AUTHOR_AUDIT_BINDING')\n        audit_calls.append(actor)\n        return [ref]")
        chunk=chunk.replace("audit_calls == [reviewer, m.ROOT_ACTOR]","audit_calls == [m.AUTHOR, reviewer, m.ROOT_ACTOR]")
        import copy
        from datetime import datetime,timedelta,timezone
        namespace=dict(m=m,c=c,contract=contract,href=href,mref=mref,pair_refs=pair_refs,bound=bound,author_audit=author_audit,
            old_peer_ref=pin(PRIOR/'actual-Source-author-real-Root-peer.binding.json'),old_c=load(OLD/'source.choice.json'),
            R=R,S=S,OLD=OLD,pin=pin,json=json,copy=copy,datetime=datetime,timedelta=timedelta,timezone=timezone,check=check,reject=reject)
        exec(compile(chunk,'<complete-authority-shape-IN_MEMORY_ONLY>','exec'),namespace)
        check('real_package_gate_still_closed_after_fixture',m.package_refs is namespace['originals'][1])
        reject('actual_package_still_rejects_after_fixture',m.package_refs,'SOURCE_PACKAGE')
        check('no_actual_Scope_or_native_directories_created',all(not Path(row[key]).exists() for row in c['selectors'].values()
              for key in ('receipt_root','scratch_root','output_root')))
        check('all_refs_still_exact',all(pin(ref['path'])==ref for ref in refs))
    finally:
        cleanup=guard.close();guard_ref=save('continuation-Source-guard.closed.json',cleanup)
    check('all_guards_closed_zero',cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0)
    ref=save('complete-authority-shape-and-real-blockers.json',dict(status='CHANGES_REQUIRED',actor_id=ACTOR,
        reviewer_thread_id=os.environ['CODEX_THREAD_ID'],findings=findings,checks=checks,guard_ref=guard_ref,source_author_real_peer_ref=author_audit,
        complete_Scope_fields_checked=len(contract['scope_required_fields']),complete_request_fields_checked=len(contract['request_exact_fields']),
        authority_positive='PACKAGE GATE BYPASS + THREE MOCK AUDITS IN MEMORY ONLY; NEVER CURRENT AUTHORITY',
        actual_package_refs_called=True,actual_new_author_full_digest_audit_qualified=False,actual_prepare_run=False,
        old_69_and_112_not_rerun=True,new_20_reproduction_ref=pin(D/'reproduced-peer-audit-controls.json'),
        actual_Go_runs=0,actual_Native_runs=0,actual_SQL_runs=0,actual_dispatcher_runs=0,actual_model_provider_calls=0,
        current_Canon_read=False,Main_written=False,Canon_written=False,current_CanonicalPair_held=False,
        all_Source_guards_closed=True,retained_handles_count=0,execution_grant=False,formal_case_accepted_delta=0,
        original_failures_preserved=[1042,1044,1045,1047,1051],new_failure_ordinals_assigned_only_by_Root=True))
    print(json.dumps(dict(status='CHANGES_REQUIRED',controls_ref=ref,check_count=len(checks),guard_ref=guard_ref,
        source_author_actual_peer_ref=author_audit,all_Source_guards_closed=True,retained_handles_count=0,
        actual_Go_runs=0,actual_Native_runs=0,formal_case_accepted_delta=0),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
