"""Author Source05 only. No real Root stage or Canonical/product invocation."""
from pathlib import Path
from datetime import datetime, timezone
import ast, copy, difflib, json, types, uuid

R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
OLD=D.parent/'bridge-20261010-04'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
AUTHOR='codex:/root/full_w09_source_review';BACKEND='/root/full_w09_source_review'
GEN='bridge-20261010-05'
g=s.guard();checks=[];blocks=[];failure=None;built={};source_uuid=uuid.uuid4().hex
def write_raw(name,raw):
    with (D/name).open('xb') as f:f.write(raw)
    return s.pin(D/name)
def check(name,ok,detail=None):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    if not ok:raise ValueError(name)
def change(before,after):
    global revised
    a=before.encode();b=after.encode()
    if revised.count(a)!=1:raise ValueError('EXACT_SINGLE_PATCH_ANCHOR')
    revised=revised.replace(a,b,1);blocks.append(dict(before=before,after=after))
helpers='''def canonical_identity(path):
    """Identify the fixed Canon files without reading their historical live bytes."""
    value = Path(path)
    return value if value.is_absolute() else ROOT / value

def validate_persistent_snapshot(data):
    need(type(data) is dict and type(data.get("files")) is dict,
         "DEPENDENCY_SNAPSHOT_REQUIRED")
    need(not any(canonical_identity(path) in CANON for path in data["files"]),
         "HISTORICAL_SNAPSHOT_CONTAINS_CANON")
    return data

def freeze_current4(req, out):
    """Called only by propose inside its current4 SourceReadGuard."""
    need(type(req["current4"]) is list and len(req["current4"]) == 4
         and [canonical_identity(r["path"]) for r in req["current4"]] == CANON,
         "ARCHIVE_EXACT_CANON_ORDER")
    archives = []
    for index, ref in enumerate(req["current4"]):
        need(set(ref) == {"path", "sha256", "bytes"} and type(ref["bytes"]) is int
             and Path(ref["path"]).is_absolute(), "ARCHIVE_EXACT_CANON_REF")
        raw = checked(ref)
        archive = save(out / ("canonical-" + CANON[index].stem + ".original.json"), raw, raw=True)
        need(archive["sha256"] == ref["sha256"] and archive["bytes"] == ref["bytes"],
             "ARCHIVE_ORIGINAL_BYTES")
        archives.append(archive)
    return {"schema":"researchos.w09-bridge-historical-current4.v1",
            "meaning":"ARCHIVED_HISTORICAL_CURRENT4_NOT_LIVE_AUTHORITY",
            "canonical_refs":copy.deepcopy(req["current4"]),"archive_refs":archives}

def proposal_archive_refs(proposal, proposal_ref, req):
    """Retain historical identity only with four exact immutable original archives."""
    need(proposal.get("schema") == "researchos.w09-bridge-proposal.v1"
         and proposal.get("generation") == BRIDGE_GENERATION
         and proposal.get("source_ref") == req["bridge_source_ref"]
         and proposal.get("source_review_ref") == req["source_review_ref"],
         "HISTORICAL_PROPOSAL_IDENTITY")
    proof = proposal.get("historical_current4")
    need(type(proof) is dict and set(proof) == {"schema","meaning","canonical_refs","archive_refs"}
         and proof["schema"] == "researchos.w09-bridge-historical-current4.v1"
         and proof["meaning"] == "ARCHIVED_HISTORICAL_CURRENT4_NOT_LIVE_AUTHORITY",
         "EXPLICIT_HISTORICAL_CURRENT4_PROOF")
    old, archives = proof["canonical_refs"], proof["archive_refs"]
    need(type(old) is list and type(archives) is list and len(old) == len(archives) == 4
         and old == proposal.get("current4")
         and [canonical_identity(ref["path"]) for ref in old] == CANON,
         "HISTORICAL_CURRENT4_ORDER_AND_IDENTITY")
    need(old[2:] == req["current4"][2:], "HISTORICAL_SS_CM_DRIFT")
    home = physical(proposal_ref["path"]).parent
    for index, (identity, archive) in enumerate(zip(old, archives)):
        need(type(identity) is dict and set(identity) == {"path","sha256","bytes"}
             and Path(identity["path"]).is_absolute() and type(identity["bytes"]) is int,
             "HISTORICAL_EXACT_CANON_REF")
        need(type(archive) is dict and set(archive) == {"path","sha256","bytes"}
             and type(archive["bytes"]) is int
             and physical(archive["path"]) == home / ("canonical-" + CANON[index].stem + ".original.json")
             and archive["sha256"] == identity["sha256"] and archive["bytes"] == identity["bytes"],
             "HISTORICAL_ARCHIVE_SAME_PROPOSAL_AND_BYTES")
        checked(archive)
    validate_persistent_snapshot(proposal["dependency_snapshot"])
    return archives

def historical_dependency_refs(value, ref, req, name):
    """The one archive-covered current4 field is exempt; other Canon refs are refused."""
    cleaned = copy.deepcopy(value)
    archives = []
    if name == "proposal_ref":
        archives = proposal_archive_refs(value, ref, req)
        del cleaned["current4"]
        del cleaned["historical_current4"]
    if "dependency_snapshot" in cleaned:
        validate_persistent_snapshot(cleaned["dependency_snapshot"])
    refs = list(references(cleaned))
    need(not any(canonical_identity(item["path"]) in CANON for item in refs),
         "UNDECLARED_HISTORICAL_CANONICAL_REFERENCE")
    return refs + archives

def request_dependency_refs(req):
    """Every direct request Canon ref must equal the fresh authority vector."""
    refs = list(references(req))
    authority = {canonical_identity(ref["path"]):ref for ref in req["current4"]}
    for ref in refs:
        path = canonical_identity(ref["path"])
        if path in CANON:
            need(ref == authority.get(path), "REQUEST_CANONICAL_AUTHORITY_CONFLICT")
    return refs


'''
try:
    oh=json.loads((OLD/'HDF.json').read_bytes());om=json.loads((OLD/'MF.json').read_bytes())
    refs=[s.pin(__file__),s.pin(HELPER),s.pin(OLD/'HDF.json'),s.pin(OLD/'MF.json'),*om['members'],
          s.pin(R/'execution/v2.4/formal_case_index.py'),s.pin(R/'execution/v2.4/formal_profile_w09.py')]
    g.acquire(list({r['path']:r for r in refs}.values()))
    before=g.get_buffer(oh['source_ref']['path']);revised=before
    change('BRIDGE_GENERATION = "bridge-20261010-04"','BRIDGE_GENERATION = "bridge-20261010-05"')
    change('def snapshot(api, reader, context=None):\n    data = {"files": {str(k):v for k,v in reader.read_hashes.items()},',
           'def snapshot(api, reader, context=None, authority=False):\n    data = {"files": {str(k):v for k,v in reader.read_hashes.items()\n                      if authority or canonical_identity(k) not in CANON},')
    change('\n\ndef native_inputs(req, eng):','\n\n'+helpers+'def native_inputs(req, eng):')
    change('    common = {"issued_by": ROOT_ACTOR, "source_actor": AUTHOR_BACKEND,',
           '    historical = freeze_current4(req, out)\n    common = {"issued_by": ROOT_ACTOR, "source_actor": AUTHOR_BACKEND,')
    change('    return {"schema": "researchos.w09-bridge-proposal.v1", "documents": docs,',
           '    return {"schema": "researchos.w09-bridge-proposal.v1", "generation":BRIDGE_GENERATION,\n            "historical_current4":historical, "documents": docs,')
    change('    need(api.recheck_inputs(proposal["dependency_snapshot"])["status"] == "PASS", "PROPOSAL_DRIFT")',
           '    proposal_archive_refs(proposal, req["proposal_ref"], req)\n    need(proposal["current4"] == req["current4"], "ACTIVATION_PROPOSAL_CURRENT4")\n    need(api.recheck_inputs(proposal["dependency_snapshot"])["status"] == "PASS", "PROPOSAL_DRIFT")')
    change('    proposal = document(ref)\n    need(proposal["c19_policy"] == req["c19_policy"], "REGISTERED_C19_POLICY")',
           '    proposal = document(ref)\n    proposal_archive_refs(proposal, ref, req)\n    need(proposal["c19_policy"] == req["c19_policy"], "REGISTERED_C19_POLICY")')
    change('    need(api.recheck_inputs(publication["dependency_snapshot"])["status"] == "PASS", "PUBLICATION_CAS")',
           '    validate_persistent_snapshot(publication["dependency_snapshot"])\n    need(api.recheck_inputs(publication["dependency_snapshot"])["status"] == "PASS", "PUBLICATION_CAS")')
    change('        for ref in references(req):','        for ref in request_dependency_refs(req):')
    change('        authority_snapshot = snapshot(eng[0],eng[1])',
           '        authority_snapshot = snapshot(eng[0],eng[1],authority=True)\n        authority_snapshot["files"].update({str(path):ref["sha256"] for path,ref in zip(CANON,req["current4"])})')
    change('                for ref in references(document(req[name])):',
           '                for ref in historical_dependency_refs(document(req[name]),req[name],req,name):')
    change('        for path,digest in eng[1].read_hashes.items():\n            raw=Path(path).read_bytes()',
           '        for path,digest in eng[1].read_hashes.items():\n            if args.stage in {"activate","publish-registration"} and canonical_identity(path) in CANON[:2]:\n                need(digest == req["current4"][CANON.index(canonical_identity(path))]["sha256"], "TP_AUTHORITY_DIGEST_CONFLICT")\n                continue\n            raw=Path(path).read_bytes()')
    restored=revised
    for block in reversed(blocks):
        check('inverse_unique_'+str(len(checks)),restored.count(block['after'].encode())==1)
        restored=restored.replace(block['after'].encode(),block['before'].encode(),1)
    check('complete_Source04_exact_byte_inverse',restored==before)
    oldnodes={x.name:x for x in ast.parse(before).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
    newnodes={x.name:x for x in ast.parse(revised).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
    changed=[k for k in oldnodes if ast.dump(oldnodes[k],include_attributes=False)!=ast.dump(newnodes[k],include_attributes=False)]
    check('only_history_snapshot_and_registration_boundaries_changed',set(changed)=={'snapshot','propose','registration','registered','publish_registration','main'},changed)
    unchanged=('root_request','current4','source_review','transact','native_inputs','consumer_plan','consume','roles','assemble','capture','check','derive')
    check('authority_TP_lease_native_six_mode_and_Main_stage_gates_unchanged',all(ast.dump(oldnodes[k],include_attributes=False)==ast.dump(newnodes[k],include_attributes=False) for k in unchanged),list(unchanged))
    built['source_ref']=write_raw('w09_root_bridge.source.py',revised)
    built['consumer_launcher_ref']=write_raw('consumer_launch.source.py',g.get_buffer(oh['consumer_launcher_ref']['path']))
    m=s.inert(D/'w09_root_bridge.source.py');fixture={};reads=[]
    def mock_path(p):p=Path(p);return p if p.is_absolute() else R/p
    def mock_checked(ref):
        key=str(mock_path(ref['path']));reads.append(key);data=fixture[key]
        m.need(m.sha(data)==ref['sha256'] and len(data)==ref.get('bytes',len(data)),'PIN_CHANGED');return data
    m.physical=mock_path;m.checked=mock_checked
    def fixture_ref(p,raw):
        key=str(mock_path(p));fixture[key]=raw;return dict(path=key,sha256=m.sha(raw),bytes=len(raw))
    current=[fixture_ref(path,m.encoded(dict(revision=j))) for j,path in enumerate(m.CANON)]
    fresh=copy.deepcopy(current)
    for j in (0,1):fresh[j]=fixture_ref(m.CANON[j],m.encoded(dict(revision=j+1)))
    source=built['source_ref'];review=dict(path=str(D/'MOCK-source-review.json'),sha256='a'*64,bytes=0)
    pref=dict(path=str(D/'MOCK-proposal'/'result.json'),sha256='b'*64,bytes=0)
    archives=[fixture_ref(Path(pref['path']).parent/('canonical-'+path.stem+'.original.json'),m.encoded(dict(revision=j))) for j,path in enumerate(m.CANON)]
    stable=fixture_ref(D/'MOCK-stable-dependency.json',b'stable')
    proposal=dict(schema='researchos.w09-bridge-proposal.v1',generation=GEN,source_ref=source,source_review_ref=review,
        current4=current,historical_current4=dict(schema='researchos.w09-bridge-historical-current4.v1',
        meaning='ARCHIVED_HISTORICAL_CURRENT4_NOT_LIVE_AUTHORITY',canonical_refs=copy.deepcopy(current),archive_refs=archives),
        dependency_snapshot=dict(files={stable['path']:stable['sha256']},inventories=[],audit_ranges=[]),documents={},c19_policy='RUN_CURRENT_CM40')
    req=dict(current4=fresh,bridge_source_ref=source,source_review_ref=review,proposal_ref=pref)
    for stage in ('consume','roles','assemble','publish-registration'):
        reads.clear();got=m.historical_dependency_refs(proposal,pref,req,'proposal_ref')
        check(stage+'_history_after_simulated_activation_uses_archives_only',all(r in got for r in archives) and not any(str(path) in reads for path in m.CANON),dict(Source_fixture_only=True,actual_Root_stage_called=False))
    def rejects(label,func):
        error=None
        try:func()
        except (ValueError,KeyError) as exc:error=str(exc)
        check(label,error is not None,error)
    bad=copy.deepcopy(proposal);bad['historical_current4']['archive_refs'][0]['sha256']='0'*64
    rejects('bad_archive_digest_rejected',lambda:m.proposal_archive_refs(bad,pref,req))
    bad=copy.deepcopy(proposal);bad['historical_current4']['archive_refs'].pop()
    rejects('missing_archive_rejected',lambda:m.proposal_archive_refs(bad,pref,req))
    bad=copy.deepcopy(proposal);bad['historical_current4']['archive_refs'][1]=bad['historical_current4']['archive_refs'][0]
    rejects('duplicate_archive_rejected',lambda:m.proposal_archive_refs(bad,pref,req))
    bad=copy.deepcopy(proposal);bad['historical_current4']['canonical_refs'][0]['path']=stable['path']
    rejects('foreign_canonical_identity_rejected',lambda:m.proposal_archive_refs(bad,pref,req))
    rejects('archives_cannot_be_borrowed_by_replaced_proposal_path',lambda:m.proposal_archive_refs(proposal,dict(pref,path=str(D/'OTHER-proposal/result.json')),req))
    bad=copy.deepcopy(proposal);bad['undeclared']=current[0]
    rejects('extra_historical_Canon_ref_not_globally_skipped',lambda:m.historical_dependency_refs(bad,pref,req,'proposal_ref'))
    for name in ('publication_ref','role_registry_input_ref'):
        rejects(name+'_undeclared_Canon_rejected',lambda name=name:m.historical_dependency_refs(dict(undeclared=current[0]),pref,req,name))
    bad=copy.deepcopy(proposal);bad['dependency_snapshot']['files'][str(m.CANON[0])]=current[0]['sha256']
    rejects('old_polluted_persistent_snapshot_rejected',lambda:m.historical_dependency_refs(bad,pref,req,'proposal_ref'))
    for index in (2,3):
        badreq=copy.deepcopy(req);badreq['current4'][index]['sha256']='c'*64
        rejects('historical_'+m.CANON[index].stem+'_drift_rejected',lambda badreq=badreq:m.proposal_archive_refs(proposal,pref,badreq))
    reads.clear();rejects('fresh_stale_request_still_PIN_CHANGED',lambda:m.current4(current))
    rejects('request_inline_old_Canon_conflict_rejected',lambda:m.request_dependency_refs(dict(req,extra=current[0])))
    class MockReader:
        read_hashes={**{path:ref['sha256'] for path,ref in zip(m.CANON,fresh)},Path(stable['path']):stable['sha256']}
        w09_owned_inventories=[];w09_audit_ranges=[]
    class MockAPI:
        @staticmethod
        def recheck_inputs(snap):
            return dict(status='PASS' if all(m.sha(fixture[path])==digest for path,digest in snap['files'].items()) else 'INVALID')
    persisted=m.snapshot(MockAPI(),MockReader());authority=m.snapshot(MockAPI(),MockReader(),authority=True)
    check('persistent_snapshot_only_immutable_but_authority_keeps_fresh_four',not any(str(path) in persisted['files'] for path in m.CANON) and all(str(path) in authority['files'] for path in m.CANON))
    fixture[str(m.CANON[0])]=b'changed-after-guard-fixture'
    check('fresh_authority_CAS_fails_after_simulated_revision_change',MockAPI.recheck_inputs(authority)['status']=='INVALID' and MockAPI.recheck_inputs(persisted)['status']=='PASS')
    # Existing exact registration-slot and TP compare behavior are retained as source predicates.
    slot=[n for n in ast.walk(newnodes['registered']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='REGISTERED_PROPOSAL'][0].args[0]
    expr=compile(ast.Expression(slot),'<Source-mock-registered-slot>','eval')
    check('registered_exact_proposal_slot_rejects_replacement',eval(expr,{},dict(ref=pref,req=req)) and not eval(expr,{},dict(ref=dict(pref,sha256='d'*64),req=req)))
    check('TP_pair_CAS_and_mandatory_SS_CM_guard_retained',ast.dump(oldnodes['transact'],include_attributes=False)==ast.dump(newnodes['transact'],include_attributes=False))
    built['inverse_ref']=s.write('exact-inverse.json',dict(original_ref=oh['source_ref'],candidate_ref=built['source_ref'],replacement_blocks=blocks,
        complete_inverse=True,changed_existing_functions=changed,added_functions=[k for k in newnodes if k not in oldnodes]))
    built['patch_ref']=write_raw('bridge05.patch',''.join(difflib.unified_diff(before.decode().splitlines(True),revised.decode().splitlines(True),fromfile='BR4/w09_root_bridge.source.py',tofile='BR5/w09_root_bridge.source.py')).encode())
    built['inputs_ref']=s.write('source-inputs.json',dict(base_hdf_ref=s.pin(OLD/'HDF.json'),base_mf_ref=s.pin(OLD/'MF.json'),
        base_source_ref=oh['source_ref'],base_launcher_ref=oh['consumer_launcher_ref'],base_contract_ref=oh['root_calling_contract_ref'],
        preserved_Attach_contribution=oh['original_Attach_contribution'],held_refs=refs,live_Canon_refs_held=[],
        old_controls_reused_without_rerun=[oh['delta_controls_ref']],historical_BR3_controls_rerun=False))
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc));raise
finally:
    built['source_guard_ref']=s.write('source-guard.closed.json',g.close())
    s.write('delta-controls.json',dict(schema='researchos.w09-bridge-historical-canon-source-controls.v1',checks=checks,
        passed=sum(x['passed'] for x in checks),count=len(checks),failure=failure,built=built,source_revision_uuid=source_uuid,
        all_controls_Source_mock_only=True,actual_Root_stages=0,actual_Main_calls=0,actual_Native_Go_SQL_TP_model_calls=0,
        Root_scope_grant_created=False,formal_acceptance=False,source_self_acceptance=False))
print(json.dumps(dict(Source_built=built,checks=len(checks),passed=sum(x['passed'] for x in checks),failure=failure,guards_closed=True),ensure_ascii=False))
