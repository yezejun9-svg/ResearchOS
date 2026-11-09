"""Source-only schema projection correction and new pure delta controls."""
from pathlib import Path
import ast, copy, hashlib, json, types
O=Path(__file__).resolve().parent;P=O.parent/'continue-20261010-02';W=O.parents[1]
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v,raw=False):
    with (O/n).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(O/n)
def read(p):return json.loads(Path(p).read_bytes())
protected=[pin(p) for p in sorted(P.iterdir()) if p.is_file()]
before=(P/'public22_to23_root.source.py').read_bytes()
assert hashlib.sha256(before).hexdigest()=='01598d424d9f94d1b47288393d4fa3e208962b0f661cb6cf8837df2db0656025'
helper='''def validate_working22(leaf,sealed,retained,manifest):
    # Original1025 used a pre-v3 schema projection excluding SQLite internal rows.
    # Preserve that historical hash and also require the full Native manifest hash.
    need(sealed['tables']==retained['tables'],'COPIED22_TABLE_STATE')
    need(all(sealed['database_ref'][key]==retained['database_ref'][key] for key in ('sha256','bytes')),'COPIED22_BYTE_IDENTITY')
    need(sealed['versions']==retained['versions']==manifest['migrations']==list(range(1,23)),'COPIED22_LEDGER_BINDING')
    rows=sealed['schema_rows']
    full=leaf.schema_digest(rows)
    need(sealed['schema_sha256']==full and manifest['schema_hash']=='sha256:'+full,'COPIED22_FULL_NATIVE_SCHEMA')
    # SQLite LIKE 'sqlite_%': six ASCII letters, one arbitrary character, then any suffix.
    legacy=[row for row in rows if not (len(row[1])>=7 and row[1][:6].lower()=='sqlite')]
    # v3 coalesces NULL SQL. Every retained non-internal row here must be actual SQL.
    need(all(row[3] for row in legacy),'COPIED22_LEGACY_SQL_UNREPRESENTABLE')
    legacy_hash=hashlib.sha256(json.dumps(legacy,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    need(legacy_hash==retained['schema_sha256'],'COPIED22_RETAINED_LEGACY_SCHEMA')
    return dict(schema='researchos.public22-working-copy-schema-compatibility.v1',tables_equal=True,
        byte_identity_equal=True,legacy_schema_sha256=legacy_hash,full_schema_sha256=full,
        manifest_schema_hash=manifest['schema_hash'],legacy_schema_rows=len(legacy),full_schema_rows=len(rows),
        historical_observation_rewritten=False,formal_acceptance=False)

'''
anchor=b'def validate_upgrade23(leaf,sealed,target,report,snapshot,contract,program):\n'
old=b"        need(sealed['tables']==retained['tables'] and sealed['schema_sha256']==retained['schema_sha256'],'COPIED22_LOGICAL_STATE')\n        state['observations']['working22_input']=sealed\n"
new=b"        state['observations']['working22_input']=sealed\n        state['observations']['working22_schema_compatibility']=validate_working22(leaf,sealed,retained,doc(i['evidence']['backup_manifest_ref']))\n"
assert before.count(anchor)==before.count(old)==1
after=before.replace(anchor,helper.encode()+anchor,1).replace(old,new,1)
assert after.replace(new,old,1).replace(helper.encode()+anchor,anchor,1)==before
caller=save('public22_to23_root.source.py',after,True)
source_inputs=save('source-inputs.json',(P/'source-inputs.json').read_bytes(),True)
oldast=ast.parse(before);newast=ast.parse(after)
oldnodes={n.name:ast.dump(n,include_attributes=False) for n in oldast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
newnodes={n.name:ast.dump(n,include_attributes=False) for n in newast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert set(newnodes)-set(oldnodes)=={'validate_working22'}
assert [n for n in oldnodes if oldnodes[n]!=newnodes[n]]==['execute']
inverse=save('revision-inverse.json',dict(schema='researchos.public22-continuation-source-inverse.v1',
    base_caller_ref=pin(P/'public22_to23_root.source.py'),candidate_caller_ref=caller,
    exact_inverse=True,changes=[dict(before=old.decode(),after=new.decode()),dict(before=anchor.decode(),after=helper+anchor.decode())],
    changed_existing_functions=['execute'],added_functions=['validate_working22'],all_other_function_AST_equal=True,
    source_inputs_byte_identical=True,prior_namespace_protected_refs=protected))

# Execute only extracted pure validators against in-memory synthetic observations.
i=read(P/'source-inputs.json');leaf_text=Path(i['leaf_runner_ref']['path']).read_text('utf-8')
assert pin(i['leaf_runner_ref']['path'])==i['leaf_runner_ref']
leaf_fn=next(n for n in ast.parse(leaf_text).body if isinstance(n,ast.FunctionDef) and n.name=='schema_digest')
need_fn=next(n for n in newast.body if isinstance(n,ast.FunctionDef) and n.name=='need')
fn=next(n for n in newast.body if isinstance(n,ast.FunctionDef) and n.name=='validate_working22')
env=dict(hashlib=hashlib,json=json)
exec(compile(ast.Module(body=[need_fn],type_ignores=[]),'<pure-need>','exec'),env)
env['require']=env['need']
exec(compile(ast.Module(body=[leaf_fn],type_ignores=[]),'<pure-leaf-schema>','exec'),env)
exec(compile(ast.Module(body=[fn],type_ignores=[]),'<pure-copy-validator>','exec'),env)
leaf=types.SimpleNamespace(schema_digest=env['schema_digest'])
rows=[['index','sqlite_autoindex_fixture_1','fixture',''],['table','fixture','fixture','CREATE TABLE fixture(id TEXT PRIMARY KEY)']]
full=env['schema_digest'](rows);legacy=env['schema_digest'](rows[1:])
sealed=dict(tables={'fixture':dict(count=0,rows_sha256=hashlib.sha256(b'').hexdigest())},
    database_ref=dict(path='synthetic-working.sqlite',sha256='a'*64,bytes=4096),versions=list(range(1,23)),schema_rows=rows,schema_sha256=full)
retained=dict(tables=copy.deepcopy(sealed['tables']),database_ref=dict(sealed['database_ref'],path='synthetic-original.sqlite'),
    versions=list(range(1,23)),schema_sha256=legacy)
manifest=dict(migrations=list(range(1,23)),schema_hash='sha256:'+full)
checks=[]
value=env['validate_working22'](leaf,sealed,retained,manifest)
assert value['legacy_schema_sha256']==legacy and value['full_schema_sha256']==full and legacy!=full
checks.append(dict(name='accept_exact_two_schema_projections_with_all_table_and_byte_bindings',passed=True))
def reject(name,mutate,expected):
    a,b,c=copy.deepcopy(sealed),copy.deepcopy(retained),copy.deepcopy(manifest);mutate(a,b,c)
    try:env['validate_working22'](leaf,a,b,c)
    except ValueError as exc:assert str(exc)==expected,(name,str(exc),expected)
    else:raise AssertionError(name+' accepted')
    checks.append(dict(name=name,passed=True,expected_error=expected))
reject('reject_table_digest_change',lambda a,b,c:a['tables']['fixture'].update(rows_sha256='b'*64),'COPIED22_TABLE_STATE')
reject('reject_table_set_change',lambda a,b,c:a['tables'].update(extra=dict(count=0,rows_sha256='b'*64)),'COPIED22_TABLE_STATE')
reject('reject_working_byte_digest_change',lambda a,b,c:a['database_ref'].update(sha256='b'*64),'COPIED22_BYTE_IDENTITY')
reject('reject_working_byte_size_change',lambda a,b,c:a['database_ref'].update(bytes=4097),'COPIED22_BYTE_IDENTITY')
reject('reject_ledger_change',lambda a,b,c:c.update(migrations=list(range(1,22))),'COPIED22_LEDGER_BINDING')
reject('reject_claimed_full_schema_change',lambda a,b,c:a.update(schema_sha256='b'*64),'COPIED22_FULL_NATIVE_SCHEMA')
reject('reject_native_manifest_schema_change',lambda a,b,c:c.update(schema_hash='sha256:'+'b'*64),'COPIED22_FULL_NATIVE_SCHEMA')
reject('reject_retained_legacy_schema_change',lambda a,b,c:b.update(schema_sha256='b'*64),'COPIED22_RETAINED_LEGACY_SCHEMA')
def change_internal(a,b,c):
    a['schema_rows'][0][1]='sqlite_autoindex_fixture_2';a['schema_sha256']=env['schema_digest'](a['schema_rows'])
reject('reject_internal_row_change_even_when_legacy_unchanged',change_internal,'COPIED22_FULL_NATIVE_SCHEMA')
def null_legacy(a,b,c):
    a['schema_rows'][1][3]='';a['schema_sha256']=env['schema_digest'](a['schema_rows']);c['schema_hash']='sha256:'+a['schema_sha256']
reject('reject_unrepresentable_legacy_null_SQL',null_legacy,'COPIED22_LEGACY_SQL_UNREPRESENTABLE')
assert after.index(b"state['observations']['working22_input']=sealed")<after.index(b"state['observations']['working22_schema_compatibility']=validate_working22")
checks.append(dict(name='actual_execute_retains_observation_before_fallible_validator',passed=True))
controls=save('delta-source-controls.json',dict(schema='researchos.public22-source03-pure-delta-controls.v1',checks=checks,
    count=len(checks),passed=len(checks),synthetic=True,product_success=False,SQL_queries=0,Native_calls=0,Root_stages_run=0,
    MainCanonScope_writes=0,old_controls_rerun=False))
probe=read(O/'working22-difference-probe.json')
assert not probe['table_differences'] and probe['table_count']==83 and probe['manifest_current_equal']
assert probe['legacy_exclude_sqlite_compact_sha256']==probe['retained_schema_sha256'] and probe['working_bytes_unchanged']
review=W/'public22_to_main23_continuation_independent_review_codex/review-20261010-02-full'
prior_review_refs=[pin(review/n) for n in ['HDF.json','MF.json','decision.json']]
prefix=save('historical-review-prefix.json',dict(schema='researchos.public22-source03-historical-prefix.v1',
    source02_HDF_ref=pin(P/'HDF.json'),source02_MF_ref=pin(P/'MF.json'),source02_review_refs=prior_review_refs,
    source02_delta_controls_ref=pin(P/'delta-source-controls.json'),source02_historical_prefix_ref=pin(P/'historical-review-prefix.json'),
    source02_controls_and_144_149_reviews_rerun=False,old_SQL_validation_replayed=False,old_four_Native_children_replayed=False,
    original1025_result='FAILED_RETAINED',original1201_result='FAILED_PREPARE_COPIED22_LOGICAL_STATE_RETAINED'))
contract=read(P/'root-calling-contract.source.json')
contract.update(caller_ref=caller,source_inputs_ref=source_inputs,source_only_controls=controls,source_revision='continue-20261010-03',
    copy_schema_compatibility=dict(table_state='Exact all 83 table names/counts/row digests retained, no credential row values emitted.',
        byte_identity='Working copy SHA256 and bytes equal original retained source ref.',
        legacy_schema='Project complete v3 schema using exact historical SQLite LIKE sqlite_% exclusion; require original1025 retained compact JSON digest unchanged.',
        full_schema='Recompute complete ordered schema with leaf v3 schema_digest and bind original Native backup22 manifest schema_hash.',
        ledger='Exact versions 1..22 in current, retained and original Native manifest.',
        observation_retention='Save current working observation in state before the compatibility gate can fail.',
        original1201='Retained failure; consumed old Scope cannot execute again.',
        future_execution='Requires new non-author Full Source review, new Root registration, fresh current4 and finite lease.'))
contract_ref=save('root-calling-contract.source.json',contract)
decision=read(P/'source-decision.json')
decision.update(caller_ref=caller,source_inputs_ref=source_inputs,calling_contract_ref=contract_ref,
    source_controls_ref=controls,revision='continue-20261010-03',decision='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW',
    original1201=probe['case_closed_ref'],working22_difference_probe_ref=pin(O/'working22-difference-probe.json'),
    exact_inverse_ref=inverse,formal_acceptance=False,execution_grant=False,self_acceptance=False)
decision_ref=save('source-decision.json',decision)
assert all(pin(x['path'])==x for x in protected)
print(json.dumps(dict(caller_ref=caller,controls_ref=controls,calling_contract_ref=contract_ref,source_decision_ref=decision_ref,
    controls_passed=len(checks),old_files_unchanged=len(protected),Native_calls=0,SQL_queries=0,Root_stages_run=0,formal_acceptance=False),ensure_ascii=False))
