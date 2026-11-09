"""Pure source construction only. No candidate import or SQL/native/model call."""
import ast,difflib,hashlib,json
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os")
OLD=ROOT/"execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_preparation_codex/a61c549b78aa4f2ea3ccf4857e44838e"
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_revision_codex/02b58e39e08c457a8c48d10ce764fb94")
def put(name,raw):
 with (BASE/name).open("xb") as f:f.write(raw)
 return pin(BASE/name)
def pin(p):
 raw=p.read_bytes();return {"path":str(p).replace("\\","/"),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def edit(text,before,after):
 if text.count(before)!=1:raise ValueError("Source anchor count: "+before[:70])
 return text.replace(before,after)
def replace_fn(text,name,body):
 node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
 lines=text.splitlines(keepends=True)
 return "".join(lines[:node.lineno-1])+body+"\n"+"".join(lines[node.end_lineno:])
fragment=(BASE/"original_evidence.fragment.py").read_text(encoding="utf-8")
fragment=fragment.replace("b'SQLite format 3\\\\x00'","(b'SQLite format 3' + bytes((0,)))")
fragment=edit(fragment,"def _nonempty(value, label, kind=str):","def _native_exit(value, label):\n    if type(value) is not int:\n        raise ValueError('OPEN_TYPED_NATIVE_EXIT:' + label)\n    return value\n\n\ndef _nonempty(value, label, kind=str):")
for before in ("_integer(terminal['result'].get('exit_code'), 'actual outer exit')","_integer(closed[0]['actual_launcher_native_exit'], 'actual launcher native exit')","_integer(final.get('exit_code'), 'actual CLI exit')","_integer(invocation.get('native_exit'), 'actual invocation exit')","_integer(invocation.get('native_exit'), 'refusal native exit')"):
 fragment=edit(fragment,before,before.replace("_integer(","_native_exit(",1))
fragment=edit(fragment,"type(refusal.get('negative_condition')) is not str or not refusal['negative_condition']","refusal.get('negative_condition') != row['expected']")
# Preserve a lack of semantic decoders as OPEN instead of assigning a synthetic PASS.
profile=(OLD/"formal_profile_w05.proposed.py").read_text(encoding="utf-8")
profile=edit(profile,"'tests/runtime/check/main.go', 'tests/runtime/check/legacy.go'}","'tests/runtime/check/main.go', 'tests/runtime/check/legacy.go',\n                  'ops/ci/export_a04_live.py'}")
profile=edit(profile,"'stderr_ref', 'root_grant_ref'), label='actual invocation')","'stderr_ref', 'root_grant_ref', 'initial_tool_input',\n                            'producer_ref'), label='actual invocation')")
profile=edit(profile,"by_lane[row['lane']] = actual","by_lane[row['lane']] = dict(actual, _scope=scope)")
profile=edit(profile,"'raw_evidence_refs', 'refusal_evidence_refs', 'command_keys'),","'raw_evidence_refs', 'refusal_evidence_refs', 'command_keys',\n                     'product_identity', 'original_witness_ref',\n                     'negative_invocation_ref'),")
profile=edit(profile,"row['lane'] in invocations and\n                (row['id'] not in EXTRA or row['lane'] == EXTRA[row['id']])","row['lane'] in invocations and row['lane'] == ASSERTION_LANES[row['id']]")
profile=edit(profile,"values = [_raw(api, reader, ref) for ref in api.sequence(","_live_gate(api, reader, context, row, invocations[row['lane']])\n    values = [_raw(api, reader, ref) for ref in api.sequence(")
for key in ('owned_tool_processes_after','pending_requests_after','late_launches','blind_retry_count','manual_admin_commands','tests_native_exit'):
 anchor="facts.get('"+key+"') == 0"
 repl="type(facts.get('"+key+"')) is int and facts['"+key+"'] == 0"
 profile=edit(profile,anchor,repl)
profile=edit(profile,"for ref in api.sequence(row['refusal_evidence_refs'], row['id'] + ' negative receipts'):\n        _raw(api, reader, ref)","doc, raw = _profile_io(api, reader, context)\n    verify_refusal(doc, raw, context, row)")
profile=edit(profile,"grant = _doc(api, reader, context['root_grant_ref'])","_grant_original(api, reader, context)\n    grant = _doc(api, reader, context['root_grant_ref'])")
profile=edit(profile,"message = _doc(api, reader, issuance['delivery_ref'])","_delivery_original(api, reader, issuance, review)\n    message = _doc(api, reader, issuance['delivery_ref'])")
support="""
def _profile_io(api, reader, context):
    paths = context['product_original_paths']
    def raw(reference):
        if type(reference) is not dict or set(reference) != {'path', 'sha256'} or reference['path'] not in paths:
            raise ValueError('OPEN_ROOT_CAPTURED_WHOLE_ORIGINAL')
        return _ref(api, reader, reference).read_bytes()
    def doc(reference):
        return _json_original(raw(reference))
    return doc, raw


def _live_gate(api, reader, context, row, invocation):
    doc, raw = _profile_io(api, reader, context)
    return verify_live_originals(doc, raw, context, row, invocation, invocation['_scope'])


def _grant_original(api, reader, context):
    observation = _doc(api, reader, context['root_grant_issuance_ref'])
    api.require(observation.get('schema') == 'researchos.w05.original-root-grant-issuance.v2' and
                observation.get('actor_id') == 'codex:/root' and
                observation.get('run_id') == context['run_id'] and
                observation.get('grant_ref') == context['root_grant_ref'],
                'OPEN_ORIGINAL_ROOT_GRANT', 'A04')
    api.require(type(observation.get('original_input')) is dict and
                type(observation.get('original_result')) is dict and
                type(observation['original_result'].get('exit_code')) is int and
                observation['original_result']['exit_code'] == 0,
                'OPEN_ORIGINAL_ROOT_GRANT_TOOL_RESULT', 'A04')
    output = api.text(observation['original_result'].get('output'), 'original Root grant output')
    rows = [_json_original(line) for line in output.splitlines() if line.startswith('{')]
    api.require(len(rows) == 1 and rows[0].get('grant_ref') == context['root_grant_ref'],
                'OPEN_ORIGINAL_ROOT_GRANT_OUTPUT', 'A04')
    producer = _ref(api, reader, observation['producer_ref'])
    api.require(any(reader.ref(ref) == producer for ref in context['version_vector']['tool_files']),
                'OPEN_ROOT_GRANT_PRODUCER_PIN', 'A04')


def _delivery_original(api, reader, issuance, review):
    observation = _doc(api, reader, issuance['original_delivery_observation_ref'])
    api.require(observation.get('schema') == 'researchos.w05.original-review-delivery.v2' and
                observation.get('actor_id') == review['reviewer_id'] and
                observation.get('tool') == 'collaboration.send_message' and
                observation.get('review_ref') == issuance['review_ref'],
                'OPEN_ORIGINAL_NONAUTHOR_DELIVERY', 'A04')
    original_input = api.obj(observation.get('original_input'), 'original delivery input')
    original_result = api.obj(observation.get('original_result'), 'original delivery result')
    api.require(original_input.get('target') in ('/root', 'codex:/root') and
                original_result and not original_result.get('isError') and
                issuance['review_ref']['sha256'] in api.text(original_input.get('message'), 'original delivery message'),
                'OPEN_ORIGINAL_NONAUTHOR_DELIVERY_RESULT', 'A04')


def verify_capture_bundle(doc, raw, bundle, selector):
    if selector not in ('A04', *GATES):
        raise ValueError('OPEN_EXACT_SELECTOR')
    if type(bundle) is not dict or bundle.get('schema') != 'researchos.w05.live-dispatch-bundle.v1' or bundle.get('mode') != 'LIVE_WINDOWS' or bundle.get('task_id') != 'W05' or bundle.get('case_id') != 'A04':
        raise ValueError('OPEN_CURRENT_LIVE_BUNDLE')
    context = dict(bundle, product_original_paths={ref['path'] for ref in bundle['product_original_refs']})
    grant = doc(bundle['root_grant_ref'])
    issuance = doc(bundle['root_grant_issuance_ref'])
    if grant.get('run_id') != bundle['run_id'] or grant.get('decision') != 'GRANTED' or grant.get('mode') != 'LIVE_WINDOWS' or grant.get('selected_runtime') != bundle['selected_runtime'] or grant.get('fixed_model') != bundle['fixed_model'] or issuance.get('grant_ref') != bundle['root_grant_ref']:
        raise ValueError('OPEN_ROOT_ORIGINAL_GRANT')
    originals = context['product_original_paths']
    if not originals or len(originals) != len(bundle['product_original_refs']):
        raise ValueError('OPEN_WHOLE_ORIGINALS')
    def whole_raw(reference):
        if type(reference) is not dict or set(reference) != {'path', 'sha256'} or reference['path'] not in originals:
            raise ValueError('OPEN_WHOLE_ORIGINAL_MEMBERSHIP')
        return raw(reference)
    def whole_doc(reference):
        return _json_original(whole_raw(reference))
    by_lane = {}
    for item in bundle['invocations']:
        lane = item['lane']
        if lane in by_lane:
            raise ValueError('OPEN_DUPLICATE_LANE')
        invocation, scope = doc(item['invocation_ref']), doc(item['scope_ref'])
        if invocation.get('schema') != 'researchos.w05.live-invocation.v1' or invocation.get('run_id') != bundle['run_id'] or invocation.get('lane') != lane or invocation.get('root_grant_ref') != bundle['root_grant_ref'] or scope.get('schema') != 'researchos.w05.a04-live-scope.v1' or scope.get('root_grant_ref') != bundle['root_grant_ref']:
            raise ValueError('OPEN_CURRENT_INVOCATION')
        by_lane[lane] = (invocation, scope)
    if set(by_lane) != set(SCENARIOS) | set(EXTRA.values()):
        raise ValueError('OPEN_EIGHT_ACTUAL_LANES')
    rows = bundle['assertions']
    if len(rows) != 6 or {row['id'] for row in rows} != set(IDS):
        raise ValueError('OPEN_SIX_FROZEN_ASSERTIONS')
    for row in rows:
        if row['lane'] != ASSERTION_LANES[row['id']]:
            raise ValueError('OPEN_FROZEN_ASSERTION_LANE')
        invocation, scope = by_lane[row['lane']]
        verify_live_originals(whole_doc, whole_raw, context, row, invocation, scope)
        verify_refusal(whole_doc, whole_raw, context, row)
    # These four LIVE decoders are intentionally unsupported until their
    # real producer ABI is frozen; verify_live_originals returns OPEN first.
    # A generic raw gate PASS list can never substitute for them.
    raise ValueError('OPEN_H08_P01_U02_CURRENT_RAW_GATE_DECODERS_REQUIRED')
"""
profile += "\n\n"+fragment+"\n"+support
p_ref=put("formal_profile_w05.v2.proposed.py",profile.encode("utf-8"))
handler=(OLD/"runtime_w05_live.proposed.py").read_text(encoding="utf-8")
body="""def verify_bundle(bundle, selector):
    require(selector in ('A04', *GATES), 'OPEN_EXACT_SELECTOR')
    module = REPO / 'execution/v2.4/formal_profile_w05.py'
    require(module.is_file() and not module.is_symlink() and not module.is_junction(),
            'OPEN_FIXED_MAIN_PROFILE')
    for parent in module.parents:
        if parent == REPO.parent:
            break
        require(not parent.is_symlink() and not parent.is_junction(), 'OPEN_PROFILE_REPARSE')
    code = module.read_bytes()
    require(hashlib.sha256(code).hexdigest() == 'PROFILE_SHA_PLACEHOLDER',
            'OPEN_CURRENT_PROFILE_SOURCE')
    namespace = {'__name__': 'researchos_trusted_w05_live_semantics',
                 '__file__': str(module)}
    exec(compile(code, str(module), 'exec'), namespace)
    require(hashlib.sha256(module.read_bytes()).hexdigest() == 'PROFILE_SHA_PLACEHOLDER',
            'OPEN_PROFILE_CHANGED')
    return namespace['verify_capture_bundle'](
        lambda ref: read_ref(ref)[0], lambda ref: pin_raw(ref)[0], bundle, selector)
"""
body=body.replace("PROFILE_SHA_PLACEHOLDER",p_ref["sha256"])
handler=replace_fn(handler,"verify_bundle",body)
handler=edit(handler,"'status': 'NOT_RUN', 'reason':","'status': 'OPEN', 'reason':")
h_ref=put("runtime_w05_live.v2.proposed.py",handler.encode("utf-8"))
exporter=(OLD/"export_a04_live.proposed.py").read_text(encoding="utf-8")
exporter=edit(exporter,"'root_grant_ref': bundle['root_grant_ref'],\n        'acceptance_baseline_ref'","'root_grant_ref': bundle['root_grant_ref'],\n        'root_grant_issuance_ref': bundle['root_grant_issuance_ref'],\n        'acceptance_baseline_ref'")
e_ref=put("export_a04_live.v2.proposed.py",exporter.encode("utf-8"))
copies={}
for old,new in (("formal_case_index.w05.proposed.py","formal_case_index.w05.v2.proposed.py"),("runtime.w05.route.proposed.py","runtime.w05.route.v2.proposed.py")):
 copies[new]=put(new,(OLD/old).read_bytes())
targets={"execution/v2.4/formal_profile_w05.py":p_ref,"ops/ci/runtime_w05_live.py":h_ref,"ops/ci/export_a04_live.py":e_ref,"execution/v2.4/formal_case_index.py":copies["formal_case_index.w05.v2.proposed.py"],"ops/ci/runtime.py":copies["runtime.w05.route.v2.proposed.py"]}
oldh=json.loads((OLD/"handoff.json").read_bytes());inverse=[]
for target,after in targets.items():
 before=oldh["source_pins"][target];oldraw=(ROOT/before["path"]).read_bytes();newraw=Path(after["path"]).read_bytes()
 a,b=oldraw.decode("utf-8"),newraw.decode("utf-8");ast.parse(newraw)
 nd=list(difflib.ndiff(a.splitlines(keepends=True),b.splitlines(keepends=True)))
 if "".join(difflib.restore(nd,1)).encode()!=oldraw or "".join(difflib.restore(nd,2)).encode()!=newraw:raise ValueError("Byte inverse failed")
 inverse.append({"target":target,"before_ref":before,"after_ref":after,"exact_copy":oldraw==newraw,"inverse_unified_diff":"".join(difflib.unified_diff(b.splitlines(keepends=True),a.splitlines(keepends=True),fromfile=after["path"],tofile=before["path"])),"raw_bidirectional_restore_exact":True})
iv=put("source.inverse.v2.json",(json.dumps({"schema":"researchos.a04-source-revision-inverse.v1","entries":inverse,"main_modified":False},ensure_ascii=False,indent=2)+"\n").encode())
summary=put("construction.actual.json",(json.dumps({"source_pins":targets,"inverse_ref":iv,"five_sources_ast_parse":True,"product_calls":0,"sql_calls":0,"actual_root_authority":None,"status":"SOURCE_PROPOSAL_WITH_OPEN"},ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({"construction_ref":summary,"source_pins":targets,"inverse_ref":iv},ensure_ascii=False))

