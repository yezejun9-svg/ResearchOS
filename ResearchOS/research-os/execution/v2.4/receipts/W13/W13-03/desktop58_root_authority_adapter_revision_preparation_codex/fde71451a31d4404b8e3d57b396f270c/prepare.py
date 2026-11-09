"""Source IO/AST preparation only. No candidate import, evaluation or execution."""
import ast,difflib,hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
P13=ROOT/'execution/v2.4/receipts/W13/W13-03'
OUT=Path(__file__).parent
OLD=P13/'desktop58_root_authority_adapter_preparation_codex/9edf4a8dab83408a8614d050df1c803e'
REVIEW=P13/'desktop58_root_authority_adapter_independent_source_review_codex/0e5b41d764c448d892b1224520b9de0c'
reads={}
def read(p):
    p=Path(p);b=p.read_bytes();reads[str(p)]=b;return b
def ref(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def put(n,b):
    with (OUT/n).open('xb') as f:f.write(b)
review_raw=read(REVIEW/'review.json');assert hashlib.sha256(review_raw).hexdigest()=='660e1bc5df0be77e0c7babbfabaf6bea4fca51975c14f212e401150cca9f2a34'
review=json.loads(review_raw);assert [x['id'] for x in review['requested_changes']]==['D58-AUTH-R01']
assert hashlib.sha256(read(REVIEW/'manifest.json')).hexdigest()=='89009af053ee07ba401ec612d3dd6d5bda48572d5fd6e898121fc941e7a30464'
base=read(OLD/'authorization_adapter.final.proposed.py')
assert hashlib.sha256(base).hexdigest()=='2e4ead4bf7f981014b30c400182ff1d0afeafc561f5b06e0d8a24052c6a80283' and len(base)==48029
scope=json.loads(read(OLD/'scope.final.proposed.json'))
contract=json.loads(read(OLD/'contract.json'))
read(OLD/'handoff.json');read(OLD/'manifest.json')
for r in review['preserved_author_origins']:read(r['path'])
for r in contract['existing_consumers'].values():
    if type(r) is dict:
        b=read(r['path']);assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']
pure=read(contract['source_predicate']['original_ref']['path'])
assert hashlib.sha256(pure).hexdigest()=='6ff7a907980da9ffe50a7a2f3ba5669820cd1d99a820be476e5327abd0dec782'
old=b"    for item in grant['runtime_observation_refs']:"
new=b'''    observations = grant.get('runtime_observation_refs')
    expected_paths = scope.get('expected_runtime_observation_paths')
    require(type(expected_paths) is list and expected_paths and
            all(type(path) is str and path for path in expected_paths),
            'Root frozen ordered runtime observation paths are missing or empty')
    require(type(observations) is list and observations and len(observations) == len(expected_paths),
            'Runtime observations must be a nonempty complete list')
    require(prelaunch.get('runtime_observation_refs') == observations,
            'Grant runtime observations differ from sealed prelaunch selection')
    observation_paths = set()
    for expected_path, item in zip(expected_paths, observations):
        require(type(item) is dict and set(item) == {'path','sha256','bytes'} and
                type(item['path']) is str and type(item['sha256']) is str and
                len(item['sha256']) == 64 and all(c in '0123456789abcdef' for c in item['sha256']) and
                type(item['bytes']) is int and item['bytes'] >= 0, 'Runtime observation exact ref required')
        path = bounded_path(item['path'])
        expected_path_object = bounded_path(expected_path)
        require(Path(item['path']).is_absolute() and Path(expected_path).is_absolute() and
                str(path) == item['path'] == expected_path and
                str(path.resolve()) == str(path) == str(expected_path_object.resolve()) and path.parent == root,
                'Runtime observation foreign path, alias or order mismatch')
        identity = os.path.normcase(str(path))
        require(identity not in observation_paths, 'Duplicate runtime observation')
        observation_paths.add(identity)
    for item in observations:'''
assert base.count(old)==1
candidate=base.replace(old,new,1)
assert candidate.replace(new,old,1)==base
ast.parse(candidate)
put('authorization_adapter.v2.proposed.py',candidate)
save('edit.inverse.json',{'baseline_ref':ref(OLD/'authorization_adapter.final.proposed.py'),'candidate_ref':ref(OUT/'authorization_adapter.v2.proposed.py'),'old':old.decode(),'new':new.decode(),'whole_inverse_exact':True})
put('source.diff',''.join(difflib.unified_diff(base.decode().splitlines(True),candidate.decode().splitlines(True),fromfile=str(OLD/'authorization_adapter.final.proposed.py'),tofile=str(OUT/'authorization_adapter.v2.proposed.py'))).encode())
scope['authorization_verifier_ref']=ref(OUT/'authorization_adapter.v2.proposed.py')
scope['expected_runtime_observation_paths']=None
save('scope.v2.proposed.json',scope)
contract['schema']='researchos.desktop58-authority-adapter-source-contract.v2'
contract['prior_contract_ref']=ref(OLD/'contract.json')
contract['revision_request_ref']=ref(REVIEW/'review.json')
contract['runtime_observation_contract']={
 'scope_field':'expected_runtime_observation_paths','future_value':None,
 'scope_value_rule':'Root freezes a nonempty ORDERED list of exact canonical ABS file paths under the unique new_authorization_root before full-scope review/registration. No hardcoded count2/3; NULL/empty/wrong type refuses.',
 'grant_value_rule':'runtime_observation_refs is a nonempty list of unique exact path/sha256/bytes refs, one per expected path, same order. Relative/foreign/case/alias/duplicate/missing/extra/reordered paths refuse. Each original observation read/hash/files/allowlist predicate remains unchanged.',
 'prelaunch_value_rule':'Actual sealed prelaunch_evidence_ref JSON contains runtime_observation_refs exactly equal to grant selection, including each digest/size. The prelaunch document is already verified by the original Reader and is part of the returned authorization inputs.',
 'no_hash_cycle':'Scope freezes future paths only. Root producer emits actual observation bytes after actual runtime observation, then freezes refs into prelaunch and grant. Scope does not contain digests of observations that could themselves depend on the full scope SHA.',
 'producer_status':'PROPOSED/OPEN until Root implements, adopts and independently freezes this field contract. No observation, grant, prelaunch, Root allocation or actual runtime field is manufactured in this revision.',
 'measurement_limit':'Point-in-time loaded input observations only; no continuous Python/OS lifecycle proof is implied.',
 'ordering_semantics':'Position + exact full path identifies the expected observation. No guessed role names or substituted count; Root must document its actual observations in the future concrete scope.'}
contract['grant_contract']['runtime_observation_refs']='Exact nonempty unique ordered refs matching scope.expected_runtime_observation_paths and prelaunch.runtime_observation_refs; original per-observation guards retained.'
contract['OPEN'].insert(0,'Root expected ordered observation paths and actual observation/prelaunch/grant refs remain NULL/absent and must be supplied honestly before execution.')
save('contract.v2.json',contract)
def defs(b):
    text=b.decode();lines=text.splitlines(True)
    return {n.name:(n,''.join(lines[n.lineno-1:n.end_lineno])) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
bd,nd,pd=defs(base),defs(candidate),defs(pure)
unchanged=[]
for name,(node,body) in bd.items():
    if name=='validate_grant':continue
    assert nd[name][1]==body and ast.dump(nd[name][0],include_attributes=False)==ast.dump(node,include_attributes=False)
    unchanged.append(name)
six=['require','strict_json','bounded_path','Reader','registration_refs','validate_current58_source']
for name in six:
    assert nd[name][1]==pd[name][1]
    assert ast.dump(nd[name][0],include_attributes=False)==ast.dump(pd[name][0],include_attributes=False)
# Static dominance: checks and validation pass occur before the original observation-read loop and success return.
g=nd['validate_grant'][0]
loops=[n for n in g.body if isinstance(n,ast.For)]
check_loop=next(n for n in loops if isinstance(n.iter,ast.Call) and isinstance(n.iter.func,ast.Name) and n.iter.func.id=='zip')
read_loop=next(n for n in loops if isinstance(n.iter,ast.Name) and n.iter.id=='observations')
ret=next(n for n in reversed(g.body) if isinstance(n,ast.Return))
assert check_loop.lineno < read_loop.lineno < ret.lineno
old_tail=base[base.index(b"        require(bounded_path(item['path']).parent == root, 'Runtime observation location')"):]
new_tail=candidate[candidate.index(b"        require(bounded_path(item['path']).parent == root, 'Runtime observation location')"):]
assert old_tail==new_tail
before=[{'path':k,'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for k,v in reads.items()]
save('inputs.before.json',before)
assert before==[ref(x['path']) for x in before]
save('inputs.after.json',[ref(x['path']) for x in before])
save('static-audit.json',{'AST_parse_only':True,'candidate_imported':False,'candidate_executed':False,'single_hunk_inverse_exact':True,
 'unchanged_definitions':unchanged,'six_6ff_definitions_byte_AST_equal':six,'original_observation_read_loop_body_and_success_tail_bytes_equal':True,
 'dominance_lines':{'selection_validation_loop':check_loop.lineno,'original_observation_reader_loop':read_loop.lineno,'success_return':ret.lineno},
 'scope_only_added_field':'expected_runtime_observation_paths','field_value':None,'controller_launcher_byte_changes':0,
 'input_count':len(before),'input_drift':0,'future_controls':'NOT_RUN','new_failure_origins':[]})
save('future-controls.NOT_RUN.json',{'status':'NOT_RUN','cases':['Actual Root frozen complete ordered observations remains the positive path.',
 'Empty/missing/NULL/wrong-type scope expected list refuses.','Empty/missing/NULL/wrong-type grant refs refuses.',
 'Duplicate exact ref or same path with different hash refuses.','Missing/extra/reordered/foreign/relative/aliased observation refuses.',
 'Grant and prelaunch exact ref sequence mismatch refuses.','Invalid digest or boolean size refuses.',
 'Nonempty observation with missing/empty files, unpinned actual member or false all_observed_inputs_pre_pinned retains original refusal.'],
 'candidate_tests_executed':0,'synthetic_runtime_evidence_created':False})
print(json.dumps({'candidate':ref(OUT/'authorization_adapter.v2.proposed.py'),'scope':ref(OUT/'scope.v2.proposed.json'),'contract':ref(OUT/'contract.v2.json'),'input_count':len(before),'unchanged_definitions':len(unchanged)},ensure_ascii=False))
