"""Pure static sealing; no controller/helper import or execution."""
import ast
import hashlib
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def pin(p):
    raw=Path(p).read_bytes();return {'path':str(Path(p).absolute()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
before=json.loads((OUT/'inputs.before.json').read_text(encoding='utf8'))
after=[pin(r['path']) for r in before]
if before!=after:raise ValueError('input drift')
fixed=json.loads((OUT/'fixed-inputs.json').read_text(encoding='utf8'))
mapping=[('test_source_ref','fork/driver18_innocuous_test.go'),('surface_ref','consumer/surface.go'),
 ('producer_ref','consumer/cmd/i16fixture/main.go'),('probe_ref','old-probe/main.go'),
 ('consumer_mod_ref','consumer/go.mod'),('sum_ref','consumer/go.sum'),('old_mod_ref','old-probe/go.mod'),('sum_ref','old-probe/go.sum')]
rows=[]
for key,dest in mapping:
    raw=Path(fixed[key]['path']).read_bytes()
    # Identity transform is the exact future source operation; no gofmt or text substitution.
    forward=bytes(raw);inverse=bytes(forward)
    if raw!=inverse:raise ValueError('inverse bytes')
    rows.append({'source_ref':fixed[key],'future_relative_path':dest,'forward':'identity raw byte copy with xb',
                 'inverse':'identity copied bytes; candidate source unchanged','byte_equal':True})
for name in ('driver18_controller.proposed.py','launch.proposed.py','freeze_preparation.py','seal_preparation.py'):
    ast.parse((OUT/name).read_text(encoding='utf8'),filename=name)
save('forward-inverse-map.json',{'source_operations':rows,'original1899_prefix':'Exact locked copies. Only one new test file is added; removing its membership recovers the original locked path/hash map. No original source replacement.',
 'Go_runtime_test_not_executed':True,'original_regression_ref':fixed['original_regression_ref']})
save('inputs.at-seal.json',after)
save('tool-observations.json',{'reads':[
 {'chunk':'fd3ec6','outer_exit':0,'actual_native_exit':None,'operation':'bounded actual filenames'},
 {'chunk':'558c22','outer_exit':0,'actual_native_exit':None,'operation':'read complete handoffs and consumer contract'},
 {'chunk':'120d7a','outer_exit':0,'actual_native_exit':None,'operation':'read candidate proposal/non-author review'},
 {'chunk':'e4d292','outer_exit':0,'actual_native_exit':None,'operation':'read candidate source/layout/lock shape'},
 {'chunk':'f9d339','outer_exit':0,'actual_native_exit':None,'operation':'read I16/I17/I18 sources and origin verification'},
 {'chunk':'6cb9bb','outer_exit':0,'actual_native_exit':None,'operation':'read module dependencies and known utility signatures'},
 {'chunk':'12168b','outer_exit':0,'actual_native_exit':None,'operation':'create own new preparation namespace'},
 {'chunk':'29cdb8','outer_exit':0,'actual_python_exit':0,'operation':'pure IO/hash/AST freeze',
  'invocation_ref':pin(OUT/'static.invocation.json'),'stdout_ref':pin(OUT/'static.stdout.raw'),'stderr_ref':pin(OUT/'static.stderr.raw')}],
 'new_failure_origins':[],'target_helper_DLL_Go_gofmt_SQL_Node_SDK_HTTP_model_calls':0,'canonical_counter_written':False})
save('handoff.json',{'schema':'researchos.driver18-root-execution-preparation-handoff.v1','actor':'codex:/root/command_queue_impl',
 'status':'PREPARATION_ONLY_STOPPED','controller_ref':pin(OUT/'driver18_controller.proposed.py'),
 'launcher_ref':pin(OUT/'launch.proposed.py'),'unbound_scope_ref':pin(OUT/'scope.UNBOUND.proposed.json'),
 'fixed_inputs_ref':pin(OUT/'fixed-inputs.json'),'resource_authority_contract_ref':pin(OUT/'resource-and-authority-contract.json'),
 'I16_provenance_contract_ref':pin(OUT/'I16-provenance-contract.json'),'finite_roster_ref':pin(OUT/'finite-operation-roster.json'),
 'static_checks_ref':pin(OUT/'static-checks.json'),'forward_inverse_ref':pin(OUT/'forward-inverse-map.json'),
 'tool_observations_ref':pin(OUT/'tool-observations.json'),'input_vector_ref':pin(OUT/'inputs.at-seal.json'),
 'source_non_author_ref':fixed['non_author_handoff_ref'],'full_fork_consumer_contract_ref':fixed['consumer_contract_ref'],
 'actual_candidate_execution':0,'all18':'NOT_RUN','partial17_native_call_plan':30,'native_cap':32,
 'I18_body_unchanged':True,'I18_proposed_seconds':750,'I17':'FATAL_OPEN; only separately authorized partial17 supported now',
 'required_before_use':['Non-author review of controller/launcher and exact partial17 scope.',
 'Root actual source/resource lease, explicit numeric tuple/origin cut, complete offline dependency/tool/Python OS catalog.',
 'Separately reviewed Root driver18 authority adapter validating actual registration/canonical copies/sealed review/manifest; no permissive authorized:true gate.',
 'One actual prepare grant produces immutable prepared.json; Root validates completion and binds exact prepared ref into a new execute grant.',
 'New source/cache/WORK/executable namespaces and finite owned runtime captures; no old exe/cache use.'],
 'limitations':['No Go AST/typecheck/build/run/gofmt/SQL proof here. Python AST is preparation syntax only.',
 'I16 before/after old-stage exact closed bytes proves unchanged content, not a separate SQL full-table/typeof scan; that stronger observed inventory remains OPEN if separately required.',
 'Full18 future support needs actual independently reviewed callback adapter/names/raw vectors and an explicit extension; no placeholders will pass.',
 'Directory/ZIP matching and local replacement locks are not upstream signed sumdb or GoSum authentication of modified fork.',
 'Python/OS inventory is point-in-time only; does not attest full controller lifecycle.'],
 'new_failure_origins':[],'counter_reset':False,'source_acceptance':False,'SQL24_permission':False,'formal_increment':0})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.immutable-preparation-manifest.v1','members':members,'member_count':len(members),'excluded_only_self':True})
print(json.dumps({'handoff':pin(OUT/'handoff.json'),'manifest':pin(OUT/'manifest.json'),'members':len(members)},ensure_ascii=False))
