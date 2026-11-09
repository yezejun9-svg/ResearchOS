"""Pure IO / AST source preparation. Does not import or execute any candidate."""
import ast, difflib, hashlib, json
from pathlib import Path
OUT = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
P13 = ROOT/'execution/v2.4/receipts/W13/W13-03'
OLD = P13/'fresh58_cli2_controller_preparation_codex/86d71652d03649879b13e03a974456d9'
ENGINE = P13/'desktop58_forward_head_metadata_preparation_revision_codex/756f86f1976e4f80b6d006b5549c2370/forward_head_engine.final.proposed.py'
SCOPE = ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf/scope_registration.json'
CLOSURE = P13/'desktop58_source_execution_independent_review_codex/a76cb528a87f45529adb3da26418eabb/review.json'
def need(x,m):
    if not x: raise RuntimeError(m)
def ref(p):
    b=p.read_bytes(); return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,obj):
    b=obj if isinstance(obj,bytes) else (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
    with (OUT/name).open('xb') as f:f.write(b)
inputs=[OLD/'handoff.json',OLD/'manifest.json',OLD/'authorization_gate.current58.proposed.py',OLD/'runner.current58.proposed.py',OLD/'scope.current58.proposed.json',OLD/'binding-contract.json',ENGINE,SCOPE,CLOSURE]
before=[ref(p) for p in inputs]
need(ref(inputs[2])['sha256']=='fed62ded28902f2533597a18aef7d336f780fe0c81ae05f8478bace87fbc87f5','Original gate')
need(ref(ENGINE)['sha256']=='1a8596d923d4fee0f3cde0b69cc2f4e74d62c370f4dc90e48704dc5bab348955','Actual engine schema')
need(ref(SCOPE)['sha256']=='62d704e9add7294f11ecfd8dc2ba35238a37b285fa32febfe8977b266142daba','Source scope')
source=inputs[2].read_bytes(); nl=b'\r\n' if b'\r\n' in source else b'\n'; candidate=source; edits=[]
def change(old,new):
    global candidate
    a=old.replace('\n',nl.decode()).encode();b=new.replace('\n',nl.decode()).encode()
    need(candidate.count(a)==1,'Exact source anchor '+old[:70])
    candidate=candidate.replace(a,b,1);edits.append({'old':a.decode(),'new':b.decode()})
change("    require(set(closure['source_paths']).issubset(seen), 'Desktop15 absent from actual58 source set')\n",
"    require(set(closure['source_paths']).issubset(seen), 'Desktop15 absent from actual58 source set')\n"
"    source_scope = reader.doc(closure['scope_ref'])\n"
"    require(len(source_scope['shared38_paths']) == 38 and len(source_scope['cli8_paths']) == 8 and\n"
"            len(closure['source_paths']) == 15, 'Original source-set cardinalities')\n"
"    expected_paths = set(source_scope['shared38_paths'] + source_scope['cli8_paths'] + closure['source_paths'])\n"
"    require(len(expected_paths) == 58 and seen == expected_paths, 'Exact original38 plus CLI8 plus Desktop15 union')\n")
change("    reader.verify(audit['request_ref'])\n", "    request = reader.doc(audit['request_ref'])\n")
change("    require([verified['checkpoint'],verified['ownership'],verified['failure_origins']] == audit['after'] and\n"
"            verified['intent_ref'] == audit['intent_ref'] and\n"
"            audit['after'][0] <= cp['revision'] and audit['after'][1] <= ow['revision'],\n"
"            'Forward registered tuple does not precede current authorization')\n",
"    before, after = audit['before'], audit['after']\n"
"    require(all(type(t) is list and len(t) == 3 and all(type(x) is int for x in t)\n"
"                for t in [before, after, request['before_tuple'], request['after_tuple']]),\n"
"            'Forward tuples require exactly three actual integers')\n"
"    require(request['schema'] == 'researchos.desktop58-forward-head-request.v1' and\n"
"            request['actor'] == 'codex:/root' and request['before_tuple'] == before and request['after_tuple'] == after and\n"
"            request['head_before'] == PARENT and request['head_after'] == SOURCE and\n"
"            intent['actor'] == 'codex:/root' and intent['Main_head'] == SOURCE, 'Forward request/audit/intent origin pairing')\n"
"    transition = intent['transition']\n"
"    require(type(transition) is dict and set(transition) == {'checkpoint','ownership','failures'} and\n"
"            all(type(transition[k]) is list and len(transition[k]) == 2 and\n"
"                all(type(x) is int for x in transition[k]) and transition[k] == [before[i],after[i]]\n"
"                for i,k in enumerate(['checkpoint','ownership','failures'])), 'Forward intent exact tuple transition')\n"
"    current = [cp['revision'],ow['revision'],len(cp['failure_counters'])]\n"
"    require(all(type(x) is int for x in current) and all(after[i] <= current[i] for i in range(3)) and\n"
"            [verified['checkpoint'],verified['ownership'],verified['failure_origins']] == after and\n"
"            all(type(verified[k]) is int for k in ['checkpoint','ownership','failure_origins']) and\n"
"            verified['intent_ref'] == audit['intent_ref'],\n"
"            'Forward registered tuple does not precede current authorization')\n")
reverse=candidate
for e in reversed(edits):
    need(reverse.count(e['new'].encode())==1,'Inverse anchor'); reverse=reverse.replace(e['new'].encode(),e['old'].encode(),1)
need(reverse==source,'Whole inverse')
oldtree=ast.parse(source);newtree=ast.parse(candidate)
oldfunc={n.name:ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
newfunc={n.name:ast.dump(n,include_attributes=False) for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
changed=[k for k in oldfunc if oldfunc[k]!=newfunc.get(k)]
need(changed==['validate_current58_source'] and oldfunc.keys()==newfunc.keys(),'Only authorized function differs')
sc=json.loads(SCOPE.read_bytes());cl=json.loads(CLOSURE.read_bytes());union=set(sc['shared38_paths']+sc['cli8_paths']+cl['source_paths'])
need((len(sc['shared38_paths']),len(sc['cli8_paths']),len(cl['source_paths']),len(union))==(38,8,15,58),'Actual closed source union')
engine=ENGINE.read_text(encoding='utf-8');required=["q['before_tuple']", "q['after_tuple']", "'transition': {'checkpoint':", "'ownership':", "'failures':", "'request_ref': p['request_ref']"]
need(all(s in engine for s in required),'Actual producer spelling')
save('authorization_gate.current58.v2.proposed.py',candidate)
save('gate.edits.json',edits)
save('gate.diff',''.join(difflib.unified_diff(source.decode().splitlines(True),candidate.decode().splitlines(True),fromfile=str(inputs[2]),tofile='authorization_gate.current58.v2.proposed.py')).encode())
save('inputs.before.json',before)
after=[ref(p) for p in inputs];need(after==before,'Input drift');save('inputs.after.json',after)
save('static-audit.json',{'schema':'researchos.fresh58-cli2-gate-static-revision.v1','whole_byte_inverse':True,'AST_parse':True,'changed_functions':changed,'unchanged_functions_and_classes':len(oldfunc)-1,'source_union':{'original38':38,'CLI8':8,'Desktop15':15,'unique':58,'paths':sorted(union)},'producer_field_evidence':{'request':['before_tuple','after_tuple','head_before','head_after'],'intent':['actor','Main_head','transition.checkpoint','transition.ownership','transition.failures'],'audit':['before','after','request_ref','intent_ref','verified_ref']},'candidate_imported':False,'candidate_executed':False,'future_controls':'NOT_RUN','actual_target_calls':0,'new_failure_origins':[],'input_drift':0})
print(json.dumps({'gate':ref(OUT/'authorization_gate.current58.v2.proposed.py'),'static_audit':ref(OUT/'static-audit.json'),'hunks':len(edits),'unchanged_functions_and_classes':len(oldfunc)-1},ensure_ascii=False))
