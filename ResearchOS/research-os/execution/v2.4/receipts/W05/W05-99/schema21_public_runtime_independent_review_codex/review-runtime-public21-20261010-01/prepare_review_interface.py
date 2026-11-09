"""Read the sealed interface only. No qualification or Root authority is emitted."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,types

R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
N=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-02'
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
source=(N/'public21_root.source.py').read_bytes();m=types.ModuleType('public21_runtime_interface_only');m.__file__=str(N/'public21_root.source.py')
exec(compile(source,m.__file__,'exec'),m.__dict__)
oc3=Path(m.OC3_REF['path']).read_bytes();tree=ast.parse(oc3)
node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='runtime_review_chain')
class Literals(ast.NodeTransformer):
 def visit_Constant(self,n):
  if type(n.value) is str and n.value in m.LITERAL_MAP:n.value=m.LITERAL_MAP[n.value]
  return n
effective=ast.unparse(ast.fix_missing_locations(Literals().visit(node)))
contract=json.loads((N/'root-calling-contract.source.json').read_bytes())
common_fields=['review_author','source_author','runner_source_author','root_thread_id','source_hdf_ref','source_mf_ref','caller_ref','runner_contract_ref','qualification_scope_ref','python_ref','control_ref','runtime_manifest_ref']
value={
 'schema':'researchos.public21-runtime-independent-review-interface-readiness.v1',
 'status':'OPEN_WAITING_ACTUAL_ROOT_SCOPE_MANIFEST_GUARD_HOSTPAIR',
 'created_utc':datetime.now(timezone.utc).isoformat(),
 'review_author':'codex:/root/full_w09_source_review','Root_thread_id':m.ROOT_THREAD,
 'Source_bindings':{'source_hdf_ref':pin(N/'HDF.json'),'source_mf_ref':pin(N/'MF.json'),'caller_ref':pin(N/'public21_root.source.py'),'calling_contract_ref':pin(N/'root-calling-contract.source.json'),'OC3_ref':m.OC3_REF},
 'Root_scope_schema':contract['runtime']['scope_schema'],'Root_scope_slice':contract['runtime']['scope_slice'],
 'review_HDF':{'schema':contract['runtime']['review_HDF_schema'],'fields':common_fields+['manifest_ref','decision_ref','reviewed_utc'],'formal_acceptance':False,'execution_grant':False},
 'review_MF':{'schema':'researchos.independent-source-review-manifest.v1','members':'exact three-key immutable refs, including the runtime decision','Root_scope_or_runtime_grant':False},
 'review_decision':{'schema':contract['runtime']['review_decision_schema'],'fields':common_fields+['resource_refs','independent_non_author','verdict','formal_acceptance','execution_grant'],'required_verdict':'RUNTIME_CLOSURE_ACCEPTED','formal_acceptance':False,'execution_grant':False},
 'ordinary_Final':{'schema':'researchos.public21-peer-review-delivery.v1','operation':'RUNTIME_QUALIFICATION_ISSUANCE','verdict':'RUNTIME_CLOSURE_ACCEPTED','review_author':'codex:/root/full_w09_source_review','root_thread_id':m.ROOT_THREAD,'review_refs':'[HDF, MF, decision] exact complete refs','formal_acceptance':False,'execution_grant':False},
 'resource_array_binding':'decision.resource_refs equals the Root runtime-manifest.resource_refs array as objects and in order; preserve Windows str(Path) spelling and all original SHA/bytes.',
 'causal_time_order':contract['runtime']['time_order'],
 'wrapper_projection_excludes':['schema','payload_ref','root_issuance_binding_ref','created_utc'],
 'required_future_actual_inputs':['Root-issued finite resource-only Scope','runtime-manifest.root.json from actual Caller02 prepare','prepare.guard.closed.json','completed Root prepare call/result raw plus original source offsets/binding','prerequisite Source and runner witnesses already observed by Root'],
 'resource_review_rules':[
  'One full independent SourceReadGuard acquisition of the actual new manifest, then finally close every retained handle; do not hold live CP/OW.',
  'Verify mandatory declared caller/leaf/OC3/Guard/TP/OwnedJob, accepted review/original chains, qualified old21 programme refs, locked Python, SQLite extension/DLL, stdlib/caches and actual loaded Windows resources against exact current manifest pins.',
  'Import and bounded read-only predicates are permitted; no SQL connection, Root stage, programme child, Native, Go, model or Canon mutation.',
  'No fixed historic resource count; earlier 353-resource evidence is reused only for unchanged conclusions, not as new Scope authorization.',
  'Root runtime closure includes sys.modules __file__/__cached__, including its __main__ helper. Later entry must use the same already inventoried immutable helper or obtain a new current resource qualification.',
  'Reject expired or borrowed Scope, wrong Source/thread/actor, self-review, mismatched resource arrays, loose ref spelling, noninteger size/bool, path alias, missing mandatory resource or incomplete guard closure.',
  'The independent reviewer emits no Root payload, wrapper, peer capture, issuer grant or future tool result.'
 ],
 'effective_runtime_review_chain_AST':effective,
 'old_Source_controls_or_resources_replayed':False,
 'qualification_decision_issued':False,'RootScope_issued':False,'actual_products_or_Root_stages':0,
 'execution_grant':False,'formal_acceptance':False}
out=D/'review-interface.readiness.json'
with out.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
print(json.dumps({'readiness_ref':pin(out),'status':value['status'],'qualification_decision_issued':False,'Root_stages_or_products':0},ensure_ascii=False))
