import sys
sys.dont_write_bytecode = True
import ast, hashlib, json, re
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os')
T5=R/'.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
Q=Path(__file__).resolve().parent
C=Q/'candidate-root'

def pin(path):
 raw=path.read_bytes()
 return {'path':path.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def write_new(name, obj):
 with (Q/name).open('x',encoding='utf-8',newline='\n') as out:
  json.dump(obj,out,ensure_ascii=False,indent=2)
  out.write('\n')

definitions={'tokens','close_index','call_nodes','assertion_if_nodes','balanced'}
producer_ast=ast.parse((Q/'construct.py').read_text(encoding='utf-8'))
selected=[n for n in producer_ast.body if isinstance(n,ast.FunctionDef) and n.name in definitions]
if {x.name for x in selected} != definitions:
 raise ValueError('explicit lexical check function set differs')
context={}
exec(compile(ast.Module(body=selected,type_ignores=[]),'selected-lexical-check-functions','exec'),context)
tokens=context['tokens']; call_nodes=context['call_nodes']
assertion_if_nodes=context['assertion_if_nodes']; balanced=context['balanced']
base=json.loads((Q/'base-refs.json').read_text(encoding='utf-8'))
for ref in base['refs']:
 if pin(Path(ref['path']))!=ref:
  raise ValueError('guarded T5 base changed: '+ref['path'])
helper_rel='internal/domain/runtime_typed_client_fixture_windows_test.go'
if (T5/helper_rel).exists():
 raise ValueError('new helper unexpectedly exists in guarded T5')
checks=[]; final_refs=[]
test_pattern=re.compile(r'func (Test\w+)\(t \*testing.T\)')
for ref in base['refs']:
 relative=Path(ref['path']).relative_to(T5)
 before=Path(ref['path']).read_text(encoding='utf-8')
 after=(C/relative).read_text(encoding='utf-8')
 old_tokens,new_tokens=tokens(before),tokens(after)
 old_calls,new_calls=call_nodes(old_tokens),call_nodes(new_tokens)
 old_ifs,new_ifs=assertion_if_nodes(old_tokens),assertion_if_nodes(new_tokens)
 result={'file':relative.as_posix(),'original_assertion_and_skip_calls':len(old_calls),'original_assertion_if_nodes':len(old_ifs),'original_calls_preserved':all(new_calls.count(v)>=old_calls.count(v) for v in set(old_calls)),'original_assertion_if_nodes_preserved':all(new_ifs.count(v)>=old_ifs.count(v) for v in set(old_ifs)),'original_test_names_preserved':test_pattern.findall(before)==test_pattern.findall(after),'go_lexical_delimiters_balanced':balanced(new_tokens),'not_compiled':True}
 if any(v is False for v in result.values()):
  raise ValueError('final original assertion preservation failed: '+relative.as_posix())
 checks.append(result); final_refs.append(pin(C/relative))
helper=C/helper_rel
text=helper.read_text(encoding='utf-8')
ts=tokens(text)
helper_checks={
 'go_lexical_delimiters_balanced':balanced(ts),
 'no_skip_call':not any(len(x)>2 and x[2] in ('Skip','Skipf') for x in call_nodes(ts)),
 'no_insecure_tls':not any(x[0]=='InsecureSkipVerify' for x in ts),
 'normal_fallback_roots':'handlerTLSRootsOnce.Do(func() { x509.SetFallbackRoots(pool) })' in text,
 'public_config_before_profile':text.index('handlerCommand(t, f, service, env)')<text.index('handlerTLSCoordinatorFixture(t, f,'),
 'root_absolute_evidence_required':'!filepath.IsAbs(evidence)' in text,
 'fresh_exclusive_evidence':'os.Mkdir(dir, 0700)' in text and 'os.O_EXCL' in text,
 'eight_native_leaf_names':all(x in text for x in ('/ALLOW_ONCE','/DENY','PermissionExpiresWithoutPhysicalWrite','PermissionDecisionWaitsForAnotherRequiredResource','MuSessionToolAndIndependentAcceptance','MuToolRefusalAllowsNextTurn','/rollback=false','/rollback=true')),
 'bounded_host_credential_metadata':'provider != "openai" || *ref != typedRuntimeFixtureCredential' in text,
 'exact_model_credential_route':all(x in text for x in ('provider.ProjectID != f.project','provider.RuntimeID != route.RuntimeID','provider.Capability != "MODEL"','provider.CredentialRef != typedRuntimeFixtureCredential','provider.CredentialRevision != typedRuntimeFixtureCredential','Hash(provider.ModelConfig) != Hash(config)')),
 'parent_child_raw_result_files':all(x in text for x in ('child-invocation.json','child.stdout.raw','child.stderr.raw','child-result.json','parent-result.json')),
 'descendant_closure_pending':'REQUIRES_ROOT_GO_JOB_RECEIPT' in text,
 'same_owner_attach':'Object{"after_sequence": 0, "request_write_owner": true}' in text and '*reply.Revision != *created.Revision' in text,
 'source_authority_none':'"authority": "NONE"' in text and '"formal_acceptance": false' in text,
}
if not all(helper_checks.values()):
 raise ValueError('final helper static check failed')
checks.append({'file':helper_rel,'checks':helper_checks,'not_compiled':True})
final_refs.append(pin(helper))
actual_files=sorted(p.relative_to(C).as_posix() for p in C.rglob('*') if p.is_file())
expected_files=sorted([Path(x['path']).relative_to(T5).as_posix() for x in base['refs']]+[helper_rel])
if actual_files!=expected_files or any(not x.endswith('_test.go') for x in actual_files):
 raise ValueError('candidate source scope differs from five complete tests')
# Preserve provisional construction metadata before replacing its unsealed head.
for name in ('source-refs.json','static-checks.json'):
 with (Q/('construction-stage-'+name)).open('xb') as out:
  out.write((Q/name).read_bytes())
final_source={'candidate_root':C.as_posix(),'refs':final_refs,'production_members':0,'authority':'NONE','formal_acceptance':False,'stage':'FINAL_SEALED_SOURCE_INPUTS'}
final_static={'mode':'PYTHON_AST_SELECTION_AND_GO_LEXICAL_TEXT_NODE_CHECKS_NOT_GO_AST','checks':checks,'compiled':False,'Go_native_SQL_model_executed':0,'formal_acceptance':False,'original_assertion_and_skip_calls':sum(x.get('original_assertion_and_skip_calls',0) for x in checks),'original_assertion_if_nodes':sum(x.get('original_assertion_if_nodes',0) for x in checks)}
for name,obj in (('source-refs.json',final_source),('static-checks.json',final_static)):
 with (Q/name).open('w',encoding='utf-8',newline='\n') as out:
  json.dump(obj,out,ensure_ascii=False,indent=2); out.write('\n')
dep_names=[
 'internal/domain/runtime_configuration_binding_windows_test.go',
 'internal/domain/client_protocol_configuration_test.go',
 'internal/domain/runtime_model_test.go',
 'internal/domain/domain_test.go',
 'internal/domain/runtime_coordinator_windows_test.go',
 'internal/domain/runtime_sessions_windows.go',
 'internal/domain/client_protocol.go',
 'internal/domain/client_protocol_configuration.go',
 'internal/domain/runtime_qualification.go',
 'internal/api/contracts/client.protocol.schema.json',
]
dependencies=[pin(T5/x) for x in dep_names]
review=R/'execution/v2.4/receipts/W05/W05-99/legacy_first_turn_contract_review_codex/17301aa504cea371af1ac4c671c00a24/report.md'
closed=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/current-composition-full-domain-root-0d2a82e73b754a5f/validation.closed.json'
mapping=json.loads((Q/'scope-map.json').read_text(encoding='utf-8'))
hdf={
 'version':'SOURCE_HANDOFF_V1',
 'source_namespace':Q.as_posix(),
 'author':'backup_regression_resources',
 'status':'SOURCE_CONSTRUCTED_NOT_EXECUTED_PENDING_ROOT_AND_INDEPENDENT_REVIEW',
 'authority':'NONE',
 'formal_acceptance':False,
 'Main_adopted':False,
 'candidate_root':C.as_posix(),
 'base_root':T5.as_posix(),
 'parent_source_description':'Root-designated accepted 43Source T5 composition; Source author did not independently issue acceptance',
 'write_scope':expected_files,
 'production_members':0,
 'protected_roots_written':[],
 'base_refs':pin(Q/'base-refs.json'),
 'source_refs':pin(Q/'source-refs.json'),
 'static_checks':pin(Q/'static-checks.json'),
 'scope_map':pin(Q/'scope-map.json'),
 'contract_review':pin(review),
 'original_full_closed':pin(closed),
 'original_test_totals':mapping['original_test_totals'],
 'scoped_failure_leaf_count':10,
 'read_dependencies':dependencies,
 'synthetic_not_formal':['loopback TLS model','strict host metadata','synthetic credential','existing fixture workspace ports','Goal scoped unit runtime port'],
 'execution_performed':{'Go':0,'Go_AST_or_compiler':0,'gofmt':0,'native':0,'SQL':0,'model':0,'real_provider':0,'private_claim_or_DPAPI_reads':0,'production_database_writes':0},
 'required_resources':[
  {'env':'RESEARCHOS_NODE','requirement':'Root-reviewed pinned Node; requested/resolved bytes equal; not chosen through PATH'},
  {'env':'RESEARCHOS_MU_BUNDLE','requirement':'Root-reviewed immutable bundle; frozen exact hash'},
  {'env':'RESEARCHOS_TYPED_RUNTIME_EVIDENCE_DIR','requirement':'absolute Root-owned fresh directory for every actual run; do not reuse a failed run directory'},
  {'resource':'Root-owned Go Job','requirement':'covers compiled parent, all exact Go test children, all SDK/native descendants; independent closure and lease proof required'},
 ],
 'actual_child_evidence':['child-invocation.json','child.stdout.raw','child.stderr.raw','child-result.json','parent-result.json','leaf/tls-public-cert.der'],
 'child_result_limit':'parent passes only actual exit0 plus original eight RUN/PASS leaves and no SKIP/FAIL; descendant closure pending Root receipt; no formal self-acceptance',
 'remaining_work':['independent Source review','fresh isolated composition of T5 plus five test members','Root actual compile/test of ten leaves with fresh resources/evidence','Root descendant/Job/lease closure','independent actual review'],
 'not_in_scope':['fresh legacy production compatibility','production gate order','writer epoch fixture','ledger fixture','W16 schema20 resource','other FULL failures','four original explicit skips','product holdouts'],
 'new_source_author_failures':[],
 'failure_counter_reset':False,
}
write_new('HDF.json',hdf)
all_members=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file()]
mf={'version':'IMMUTABLE_SOURCE_MANIFEST_V1','status':'SEALED_SOURCE_ONLY_NOT_EXECUTED','authority':'NONE','formal_acceptance':False,'source_namespace':Q.as_posix(),'source_member_count':5,'production_member_count':0,'members':all_members,'self_hash_excluded':['MF.json'],'postseal_io_excluded':['seal-tool-io.json','seal-tool-io.ref.json']}
write_new('MF.json',mf)
member_drift=sum(pin(Path(x['path']))!=x for x in all_members)
base_drift=sum(pin(Path(x['path']))!=x for x in base['refs'])
print(json.dumps({'namespace':Q.as_posix(),'MF':pin(Q/'MF.json'),'HDF':pin(Q/'HDF.json'),'report':pin(Q/'report.md'),'source_refs':pin(Q/'source-refs.json'),'static_checks':pin(Q/'static-checks.json'),'scope_map':pin(Q/'scope-map.json'),'source_members':final_refs,'member_count':len(all_members),'member_drift':member_drift,'T5_base_drift':base_drift,'source_scope_count':len(actual_files),'preserved_assertion_calls':final_static['original_assertion_and_skip_calls'],'preserved_assertion_if_nodes':final_static['original_assertion_if_nodes'],'formal_acceptance':False},ensure_ascii=False))

