"""Bind the completed prebuild host pair, then create the one-shot actual Root request."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os, sys, types
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_helper_functions_only','exec'),globals())
def match(call,result):return any(x.get('chunk_id')=='8d44b3' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,106035,match,root=True);assert pair
binding=json.loads(Path(pair[1]['path']).read_bytes())
binding.update(source_audit_path=AUDIT.as_posix(),operation='OLD21_BUILD_PREREQUISITES')
binding_ref=save('old21.v3.build-prerequisites.binding.actual.root.json',binding)
context=json.loads((N/'old21.v3.build-prerequisites.context.actual.root.json').read_bytes())
actual={k:context[k] for k in ('scope_ref','facts_ref','case_request_ref','registration_result_ref','runtime_qualification_ref','current_canonical_refs')}
for ref in actual['current_canonical_refs']:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
p=B/'schema21_root_caller_registration_source_codex/s21root-20261010-03/old21_root.source.py'
exact(p,'b538b9b543ac0d45140834d52b0a209dc47546ac7c007ec9aaeda9e8602a1b06',65191)
caller=types.ModuleType('root_old21_prebuild_request_verifier');caller.__file__=str(p);sys.modules[caller.__name__]=caller
exec(compile(p.read_bytes(),str(p),'exec'),caller.__dict__)
observed=[actual[k] for k in ('scope_ref','facts_ref','registration_result_ref','runtime_qualification_ref')]+list(context['builder_review_refs'].values())+actual['current_canonical_refs']
caller.validate_root_capture(binding,Path(pair[0]['path']).read_bytes(),observed,'OLD21_BUILD_PREREQUISITES')
scope,facts,q,current=caller.live_lease(actual,require_new=True)
intent_ref=save('old21.v3.build.host-call-intent.actual.root.json',dict(schema='researchos.root-old21-host-call-intent.v1',
    issued_by='codex:/root',root_thread_id=THREAD,created_utc=datetime.now(timezone.utc).isoformat(),kind='ACTUAL_HOST_CALL_INTENT',
    external_hostpair_required=True,scope_ref=actual['scope_ref'],case_request_ref=actual['case_request_ref'],
    formal_acceptance=False,parent_acceptance=False,automatic_retry=False))
actual.update(schema='researchos.root-old21-actual-request.v1',issued_by='codex:/root',formal_acceptance=False,
    host_call_intent_ref=intent_ref,prebuild_host_binding_ref=binding_ref,created_utc=datetime.now(timezone.utc).isoformat())
request_ref=save('old21.v3.build.actual-request.root.json',actual)
print(json.dumps(dict(actual_request_ref=request_ref,prebuild_host_binding_ref=binding_ref,host_call_intent_ref=intent_ref,
    complete_original_pair_refs=pair,actual_old21_build_started=False,actual_output_root=scope['output_root'],
    actual_caller_receipt_root=scope['caller_receipt_root'],current_canonical_refs=actual['current_canonical_refs'],
    formal_acceptance=False,parent_acceptance=False,Canon_unchanged=True),ensure_ascii=False,indent=2))
