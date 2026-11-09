"""Prepare a bounded actual-review input contract; no actual build qualification."""
from pathlib import Path
import ast,hashlib,json,types
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
FB=B/'fresh_main23_programme_builder_source_codex/main23b-20261009-01'
FBR=B/'fresh_main23_programme_builder_independent_source_review_codex/src-review-20261009-01'
M=B/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04'
D=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def pin(path):
 p=Path(path);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(path):return json.loads(Path(path['path'] if isinstance(path,dict) else path).read_bytes())
def save(name,value):
 p=N/name
 with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
contract=read(FB/'contract.json');source=read(FB/'HDF.json');review=read(FBR/'HDF.json');decision=read(FBR/'source-decision.json')
qr=pin(D/'main23.v4.runtime-qualification-v2.issued.actual.root.json');q=read(qr)
assert qr['sha256']=='be5e4799f995222cf7867ec7d9319357dfac873a2bcf83b512ab219606b37c55' and qr['bytes']==36864
assert decision['verdict']==review['status']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' and decision['source_author']==source['source_author']=='codex:/root/native_temp_independent_review'
assert decision['independent_non_author'] is True and decision['formal_programme_qualification'] is False
assert decision['author_contract_ref']['sha256']==pin(FB/'contract.json')['sha256'] and decision['author_builder_ref']==source['builder_ref']
assert q['status']=='QUALIFIED_FOR_MAIN23_BUILD' and q['formal_programme_qualification'] is False and q['source_hdf_ref']['sha256']=='348034a2f2f23342f6a309ed14ffe64183a3bbb031ed79d6c8ed5facf34c0fd3'
refs=[pin(FB/n) for n in ('HDF.json','MF.json','contract.json','main23_builder.py','input-manifest.json','source-facts.json')]+[pin(FBR/n) for n in ('HDF.json','MF.json','source-decision.json')]+[qr,q['qualification_scope_ref'],q['payload_ref'],q['root_issuance_binding_ref'],q['review_hostpair_binding_ref'],q['caller_ref'],q['source_hdf_ref'],q['source_mf_ref'],contract['source_guard_ref'],pin(__file__),pin(N/'review_checks.py')]
gm=types.ModuleType('actual_review_prepare_guard');exec(compile(Path(contract['source_guard_ref']['path']).read_bytes(),contract['source_guard_ref']['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=64*1024*1024)
try:
 guard.acquire(refs)
 assert all(pin(r['path'])['sha256']==r['sha256'] and pin(r['path'])['bytes']==r['bytes'] for r in refs)
 inventory=read(contract['input_manifest_ref'])
 counts={kind:sum(item['kind']==kind for item in inventory['items']) for kind in sorted({item['kind'] for item in inventory['items']})}
 ast.parse((N/'review_checks.py').read_bytes())
finally:closed=guard.close()
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('preparation-Source-guard.closed.json',closed)
out=save('actual-review-input-contract.json',dict(schema='researchos.main23-actual-programme-review-input-contract.v1',status='PREPARED_WAITING_ROOT_ACTUAL_BUILD_INPUTS',review_author='codex:/root/attach_fixture_source_review',excluded_authors=['codex:/root/backup_regression_resources','codex:/root/native_temp_independent_review'],source_contract_ref=pin(FB/'contract.json'),builder_source_pair=[pin(FB/'HDF.json'),pin(FB/'MF.json')],builder_independent_source_review_refs=[pin(FBR/n) for n in ('HDF.json','MF.json','source-decision.json')],Root_runtime_qualification_ref=qr,preparation_held_refs=refs,preparation_Source_guard_ref=gr,declared_inventory_counts=counts,declared_inventory_total=len(inventory['items']),inventory_target_files_rehashed_in_preparation=False,historical_Source_controls_rerun=False,required_Root_delivery=['actual_request_ref','case_request_ref','scope_ref','facts_ref','registration_result_ref','registration_request_ref','owner_ref','worker_ref','full_original_current_and_before_four_refs','transaction_committed_ref','host_call_intent_ref','complete_original_Root_host_capture_and_binding_refs','caller_return_ref','persisted_builder_state_ref','build_closed_ref','candidate_program_and_provenance_refs'],required_actual_build_evidence=['prepare plus five exact Go phases in contract order','five original before/result/stdout/stderr refs with exact argv/cwd/env/timeouts and native exit 0','typed uint32 PID and uint64 FILETIME with suspended-before-assignment, Job idle and handles closed','original/frozen vectors before and after; all 572 Main refs plus all frozen module and official toolchain inputs','complete raw go list declared/export streams; recomputed file fields, embeds, imports and exact module versions/go.mod/sums without replacements','every export archive pinned and held, unique initially empty GOCACHE, exact cache before/after no drift','go build raw -x/-work output and retained work metadata with compiler/linker coverage','binary go version -m raw metadata bound to candidate and current Main five refs; current Main and frozen full inventory NO_DRIFT','Root caller guard plus original/frozen/export/program guards PASSED closed0','actual Root registration and lease at execution; original audit bytes and timestamps rather than future-time substitutes'],future_review_method='Use review_checks.py only on actual Root-delivered refs, then independently verify original audit provenance, complete guard coverage, module graph and full current/frozen/toolchain pin sets under a real finite guard. No product rerun.',review_program_ref=pin(N/'review_checks.py'),programme_qualification=None,candidate_program_ref=None,formal_acceptance=False,execution_grant=False,actual_Go_runs=0,actual_Native_runs=0,actual_SQL_runs=0,actual_dispatcher_runs=0,actual_model_requests=0,Canon_written=False))
print(json.dumps(dict(input_contract_ref=out,guard_ref=gr,declared_inventory_counts=counts,preparation_only=True,programme_qualification=None,formal_acceptance=False),ensure_ascii=False),flush=True)
