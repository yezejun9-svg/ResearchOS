"""Pure IO/text/fixture reconstruction. No Go, SQL engine, HTTP, SDK or model."""
from pathlib import Path
import ast
import base64
import copy
import difflib
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[6]
MAP = ROOT / 'execution/v2.4/receipts/W05/W05-99/f08_i17_binding_source_mapping_codex/83077264f7f748daa7c9452e22c5c2d0'
V3 = ROOT / 'execution/v2.4/receipts/W05/W05-99/f08_fence_semantics_revision_preparation_codex/65c17a2368284d90beec9526fba58a44'
PEER = ROOT / 'execution/v2.4/receipts/W05/W05-99/f08_fence_semantics_independent_source_review_codex/9dbd54518abc4d18ba53261413b8cba5'
FORK = ROOT / 'execution/v2.4/receipts/W05/W05-99/f08_sqlite_complete_fork_resource_codex/29646a104712459fb211fc6f80545bf0'
assert ROOT.name == 'research-os', ROOT

def raw_hash(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()

def ref(p):
    raw = p.read_bytes()
    return {'path': p.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def emit(name, value):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8') + b'\n')
    return ref(p)

def go_json(value, ordered=False):
    # Restricted fixture alphabet: ASCII map keys, finite small integers, Unicode
    # title. encoding/json sorts map keys and escapes HTML and U+2028/U+2029.
    def check(x):
        if isinstance(x, dict):
            assert all(isinstance(k, str) and k.isascii() for k in x)
            for v in x.values(): check(v)
        elif isinstance(x, list):
            for v in x: check(v)
        else:
            assert x is None or isinstance(x, (str, bool, int)), type(x)
            if type(x) is int: assert abs(x) < 2**53
    check(value)
    text = json.dumps(value, ensure_ascii=False, sort_keys=not ordered, separators=(',', ':'))
    for a, b in [('<', '\\u003c'), ('>', '\\u003e'), ('&', '\\u0026'), ('\u2028', '\\u2028'), ('\u2029', '\\u2029')]:
        text = text.replace(a, b)
    return text.encode('utf-8')

def jcs_hash(value):
    # Source f08ValueHash/Hash: JCS of Go JSON. All keys ASCII and numbers small
    # integers here, so differences in UTF16 sorting/float formatting cannot occur.
    return raw_hash(go_json(value))

def hx(value):
    return go_json(value).hex().upper()

def clone(value):
    return copy.deepcopy(value)

pins_expected = {
    'handoff.json': ('54b94bcfe95093dcd2c6d72f82be3fc7af78597569b24beb8a9b7f2122781e26', 5354),
    'mapping.json': ('0ceaed9f5a62938d9ae709f43bd40c090ef1f5c0113b8c5879d889ec88e93e5c', 34931),
    'REVIEW.md': ('284a4b771d7956cbffd249b3cdaae90b227f43f30dcb3b60506734de7b7c450b', 6261),
}
inputs = []
for name, (sha, size) in pins_expected.items():
    p = MAP / name
    r = ref(p)
    assert r['sha256'] == sha and r['bytes'] == size, r
    inputs.append(r)
for p in sorted((MAP / 'source-snapshots').iterdir()):
    assert p.is_file()
    inputs.append(ref(p))
for p in [V3/'handoff.json', PEER/'handoff.json', FORK/'handoff.json', FORK/'module/modernc_sqlite_v1_60_1_researchos_innocuous/sqlite.go', ROOT/'AGENTS.md', ROOT/'spec/v2.0/00_START_HERE.md', ROOT/'spec/v2.0/08_AGENT_EXECUTION_GOAL.md', ROOT/'execution/project_identity.json']:
    inputs.append(ref(p))
emit('inputs.before.json', inputs)
for i, r in enumerate(inputs):
    p = Path(r['path'])
    dest = OUT/'inputs'/f'{i:03d}-{p.name}'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(p.read_bytes())
    assert ref(dest)['sha256'] == r['sha256']

source = (MAP/'source-snapshots/01-client_cancel_finalization.v3.go.proposed.txt').read_text(encoding='utf-8')
tests = (MAP/'source-snapshots/02-client_cancel_finalization_test.v3.go.proposed.txt').read_text(encoding='utf-8')
driver = (MAP/'source-snapshots/00-innocuous_test.go.proposed.txt').read_text(encoding='utf-8')
assert raw_hash((MAP/'source-snapshots/00-innocuous_test.go.proposed.txt').read_bytes()) == 'sha256:5df920564f6213954e9202895a69001f42debb056ac264b652e0afe743171e50'
assert raw_hash((MAP/'source-snapshots/01-client_cancel_finalization.v3.go.proposed.txt').read_bytes()) == 'sha256:73fe76a6b83ebed9e84db090a479a87b87760f714164f6c3220e5ccfd3c9d603'
assert raw_hash((MAP/'source-snapshots/02-client_cancel_finalization_test.v3.go.proposed.txt').read_bytes()) == 'sha256:55c2e4a806475a6ff4498e18994e9f4d036fa72131ce9357f42e0d503bfce5a5'

def once(text, old, new):
    assert text.count(old) == 1, old[:80]
    return text.replace(old, new)

driver_new = once(driver,
    'type driver18F08Vector struct { Valid []driver.Value; Corrupt []driver.Value }',
    '''type driver18F08Vector struct {
 Valid []driver.Value; Corrupt []driver.Value
 CorruptKind string
 FixedCallbackError string
 ExpectedSQLitePrimaryCode int // source inference; verify in future controlled run
}''')
driver_new = once(driver_new,
    'if len(v.Valid)!=n||len(v.Corrupt)!=n||reflect.DeepEqual(v.Valid,v.Corrupt){t.Fatal("I17 vector arity or missing corruption")}',
    '''if len(v.Valid)!=n||len(v.Corrupt)!=n||reflect.DeepEqual(v.Valid,v.Corrupt)||v.CorruptKind!="CALLBACK_ERROR"||v.FixedCallbackError==""||v.ExpectedSQLitePrimaryCode!=1{t.Fatal("I17 vector arity, callback error contract or corruption incomplete")}
            direct,directErr:=b.Impl.Scalar(nil,v.Corrupt)
            if direct!=nil||directErr==nil||directErr.Error()!=v.FixedCallbackError{t.Fatalf("I17 direct callback result=%T error=%v",direct,directErr)}''')
driver_new = once(driver_new,
    'f.integer(t,query,1,valid...);f.integer(t,query,0,bad...)',
    '''f.integer(t,query,1,valid...)
            var rejected any
            err:=f.conn.QueryRowContext(f.ctx,query,bad...).Scan(&rejected)
            driver18Error(t,err,v.ExpectedSQLitePrimaryCode,v.FixedCallbackError)''')
driver_new = once(driver_new,
    '_,err:=f.conn.ExecContext(f.ctx,"INSERT INTO "+table+" VALUES("+strings.Join(marks,",")+")",bad...);driver18Error(t,err,275,"CHECK constraint failed")',
    '''var before int64; if err:=f.conn.QueryRowContext(f.ctx,"SELECT count(*) FROM "+table).Scan(&before);err!=nil{t.Fatal(err)}
            _,err=f.conn.ExecContext(f.ctx,"INSERT INTO "+table+" VALUES("+strings.Join(marks,",")+")",bad...)
            driver18Error(t,err,v.ExpectedSQLitePrimaryCode,v.FixedCallbackError)
            f.integer(t,"SELECT count(*) FROM "+table,before)''')

# Keep existing unit-test bodies/assertions. Split fixture construction from
# callback execution; replay only after all immutable per-step bytes exist.
test_new = once(tests,
    '''\tfunctions, err := f08BuildCallbacks(backupConfigurationProtocol, backupConfigurationDomain)
\tif err != nil { t.Fatal(err) }
\traw := []byte(''',
    ''' f := f08TestDataSetup(t)
 functions, err := f08BuildCallbacks(backupConfigurationProtocol, backupConfigurationDomain)
 if err != nil { t.Fatal(err) }; f.functions=functions; return f
}
func f08TestDataSetup(t *testing.T) f08TestFixture {
 t.Helper()
 raw := []byte(''')
test_new = once(test_new,
    'return f08TestFixture{functions, f08TestHeader(t, raw), f08TestJSON(t, identity), identity}',
    'return f08TestFixture{[3]f08Scalar{}, f08TestHeader(t, raw), f08TestJSON(t, identity), identity}')
test_new = once(test_new, '\tv *f08ProofValidator\n\tf f08TestFixture', '\tv *f08ProofValidator\n entities *SchemaDoc\n frames []f08I17CapturedFrame\n\tf f08TestFixture')
test_new = once(test_new,
    'func f08FixtureClone(t *testing.T,m map[string]any) map[string]any {t.Helper();x,_,e:=f08Strict(f08TestJSON(t,m));if e!=nil{t.Fatal(e)};return x.(map[string]any)}',
    '''func f08FixtureClone(t *testing.T,m map[string]any) map[string]any {t.Helper();d:=json.NewDecoder(bytes.NewReader(f08TestJSON(t,m)));d.UseNumber();var x map[string]any;if e:=d.Decode(&x);e!=nil{t.Fatal(e)};return x}''')
test_new = once(test_new, 'f.v.entities.ValidateDefInput(kind,body)', 'f.entities.ValidateDefInput(kind,body)')
test_new = once(test_new,
    '\tresult,e:=f.v.evaluate(mode,raw);if e!=nil||result!=int64(1){f.t.Fatalf("actual pure step %s mode%d: value=%v err=%v",action,mode,result,e)}',
    '\tf.frames=append(f.frames,f08I17CapturedFrame{Mode:mode,Action:action,Raw:bytes.Clone(raw)}) // freeze BEFORE any SUT or transition')
test_new = once(test_new,
    '''func f08FullJournalFixture(t *testing.T,withACK bool,bodyType string)*f08JournalFixture {
\tt.Helper();f:=&f08JournalFixture{t:t,v:f08AbsenceValidator(t),f:f08TestSetup(t),rows:[]any{},versions:map[string]f08Version{},edges:map[string][]any{}}''',
    '''type f08I17CapturedFrame struct {Mode int64;Action string;Raw []byte}
func f08FullJournalFixture(t *testing.T,withACK bool,bodyType string)*f08JournalFixture {
 t.Helper();f:=f08FullJournalDataFixture(t,withACK,bodyType);f.v=f08AbsenceValidator(t)
 for _,frame:=range f.frames{result,e:=f.v.evaluate(frame.Mode,frame.Raw);if e!=nil||result!=int64(1){t.Fatalf("actual pure step %s mode%d: value=%v err=%v",frame.Action,frame.Mode,result,e)}}
 return f
}
func f08FullJournalDataFixture(t *testing.T,withACK bool,bodyType string)*f08JournalFixture {
 t.Helper();entities,e:=LoadSchema(backupConfigurationDomain);if e!=nil{t.Fatal(e)}
 f:=&f08JournalFixture{t:t,entities:entities,f:f08TestDataSetup(t),rows:[]any{},versions:map[string]f08Version{},edges:map[string][]any{}}''')

def write_change(name, before, after):
    bp = OUT/(name+'.before.txt')
    ap = OUT/(name+'.proposed.txt')
    # Retain source whole bytes separately from newline-normalized text diffs.
    bp.write_bytes(before)
    ap.write_bytes(after)
    old, new = before.decode('utf-8').splitlines(keepends=True), after.decode('utf-8').splitlines(keepends=True)
    forward = ''.join(difflib.unified_diff(old, new, fromfile=name+'.before', tofile=name+'.after'))
    inverse = ''.join(difflib.unified_diff(new, old, fromfile=name+'.after', tofile=name+'.before'))
    (OUT/(name+'.forward.patch')).write_bytes(forward.encode('utf-8'))
    (OUT/(name+'.inverse.patch')).write_bytes(inverse.encode('utf-8'))
    # Whole-byte inverse is an explicit before image, never patch guessing.
    return {'before':ref(bp),'after':ref(ap),'forward':ref(OUT/(name+'.forward.patch')),'inverse':ref(OUT/(name+'.inverse.patch'))}

changes = []
changes.append(write_change('innocuous_test.go', (MAP/'source-snapshots/00-innocuous_test.go.proposed.txt').read_bytes(), driver_new.encode('utf-8')))
changes.append(write_change('client_cancel_finalization_test.v4.go', (MAP/'source-snapshots/02-client_cancel_finalization_test.v3.go.proposed.txt').read_bytes(), test_new.replace('\n','\r\n').encode('utf-8')))
emit('changes.json', changes)

# Parse actual v3 source masks and actual v5 DDL; no guessed tuples/schema.
rules = dict(re.findall(r'^\s*"([a-z_]+)": \{mask:"([A-Za-z]+)"', source, re.M))
assert len(rules) == 34
ddlraw = (MAP/'source-snapshots/32-044-candidate.sql.txt').read_bytes()
ddl = ddlraw.decode('utf-8')
tuplelines = []
for line, text in enumerate(ddl.splitlines(), 1):
    if re.match(r' (?:SELECT|UNION ALL SELECT) \'[a-z_]+\',json_array', text):
        category = re.search(r"SELECT '([a-z_]+)'", text).group(1)
        tuplelines.append({'category':category,'line':line,'sql':text,'mask':rules[category]})
assert len(tuplelines)==34 and {x['category'] for x in tuplelines}==set(rules)
emit('v5-source-tuples.exact.json', {'schema':'researchos.f08.v5-source-tuples.v1','source':ref(MAP/'source-snapshots/32-044-candidate.sql.txt'),'actual_sql_execution':False,'tuples':tuplelines})
(OUT/'v5-candidate.sql.unchanged.txt').write_bytes(ddlraw)

# Request raw literal and header: Go struct field order is preserved exactly.
raw_match = re.search(r'raw := \[\]byte\(`([^`]+)`\)', tests)
assert raw_match
envelope_raw = raw_match.group(1).encode('utf-8')
envelope = json.loads(envelope_raw)
request_hash = raw_hash(go_json(envelope)) # actual Envelope.ContentHash for this restricted fixture
header = go_json({'schema':'researchos.private-command-envelope.v1','encoding':'base64','raw_envelope_base64':base64.b64encode(envelope_raw).decode('ascii')}, ordered=True)
identity = {'format':'researchos.f08.cancel-identity/1','principal':'owner-one','project':'project-one','operation':'v2:session.control','key':'cancel-one','request_hash':request_hash,'command_id':'cancel-one','method':'session.control','client_id':'client-one','session_id':'session-one','writer_epoch':3,'expected_revision':7,'target_id':'goal-one'}
when = '2026-01-01T00:00:00Z'
later = '2026-01-01T00:00:01Z'
protocol = 'researchos-client/2'

def response(status, revision, result):
    return go_json({'protocol_version':protocol,'command_id':'cancel-one','method':'session.control','status':status,'session_id':'session-one','revision':revision,'error_code':None,'error':None,'result':result})

ack = response('ACKNOWLEDGED',7,{'accepted_at':when,'operation_id':'op-cancel-one','after_sequence':12,'related_resource_ref':None})
snapshot = {'session_id':'session-one','project_id':'project-one','workspace_ref':'workspace-one','native_session_ref':'native-one','core_build_id':'build-one','protocol_version':protocol,'revision':8,'title':'fixture','archived_at':None,'created_at':when,'updated_at':later,'model_config_ref':'configuration-one','goal_id':'goal-one','active_run_id':None,'run_status':None,'goal_status':'CANCELLED','writer':None,'event_sequence':13,'earliest_event_sequence':0,'checkpoint_artifact_ref':None,'pending_command_ids':['other-command'],'pending_permissions':[],'resume_requires_explicit_user':False,'messages':[],'transcript_artifact_ref':None,'has_earlier_messages':False}

def completed(snap):
    return response('COMPLETED',8,{'action':'CANCEL','target_id':'goal-one','control_request_id':'ctrl-cancel-one','settled':True,'children_stopped':True,'queue_empty':True,'snapshot':snap})

def binding(old,current,snap):
    proof = {'admitted_root_hash':'sha256:'+'a'*64,'original_response_digest':raw_hash(old if old is not None else current),'final_root_hash':None,'final_response_digest':None,'final_snapshot_binding':None}
    if snap is not None:
        proof.update(final_root_hash='sha256:'+'b'*64,final_response_digest=raw_hash(current),final_snapshot_binding={'session_id':'session-one','project_id':'project-one','revision':snap['revision'],'event_sequence':snap['event_sequence'],'pending_command_ids_digest':jcs_hash(snap['pending_command_ids'])})
    return go_json({'identity':identity,'response_proof':proof})

def write_raw(name,raw):
    p=OUT/'raw'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    return ref(p)

def arg(value):
    if isinstance(value,bytes):
        r=write_raw(hashlib.sha256(value).hexdigest()+'.bin',value)
        return {'kind':'BLOB','ref':r}
    if value is None:return {'kind':'NULL'}
    if type(value) is int:return {'kind':'INTEGER','integer':value}
    if isinstance(value,str):return {'kind':'TEXT','text':value}
    raise AssertionError(type(value))

vectors=[]
def vector(name,function,valid,corrupt,code,mutation,provenance):
    assert len(valid)==len(corrupt) and valid!=corrupt
    v={'id':name,'function':function,'valid':[arg(x) for x in valid],'corrupt':[arg(x) for x in corrupt],'corrupt_kind':'CALLBACK_ERROR','fixed_callback_error':code,'expected_sqlite_primary_code':1,'sqlite_code_evidence':'SOURCE_INFERENCE_NOT_NATIVE_RUN','mutation':mutation,'provenance':provenance,'status':'SOURCE_DERIVED_NOT_RUN','valid_expected':{'driver_type':'int64','value':1}}
    vectors.append(v);return v

names=['researchos_f08_cancel_request_v1','researchos_f08_cancel_response_v1','researchos_f08_proof_v1']
base_provenance={'producer_ref':ref(MAP/'source-snapshots/02-client_cancel_finalization_test.v3.go.proposed.txt'),'data_builder':'f08TestSetup / f08TestACK / f08TestCompleted / f08TestBinding','predicate_executions':0}
bad_identity=clone(identity);bad_identity['project']='changed'
vector('request-project-single-field',names[0],[header,go_json(identity)],[header,go_json(bad_identity)],'F08_ORIGINAL_BINDING',{'path':'identity/project','before':'project-one','after':'changed'},base_provenance)
vector('request-BLOB-to-TEXT',names[0],[header,go_json(identity)],[header.decode(),go_json(identity)],'F08_ARGUMENT_TYPE_OR_ARITY',{'argument':0,'kind_before':'BLOB','kind_after':'TEXT','same_utf8_bytes':True},base_provenance)
for suffix, invalid in [('nul',b'\x00'),('invalid-utf8',b'\xff')]:
    vector('request-header-'+suffix,names[0],[header,go_json(identity)],[invalid,go_json(identity)],'F08_STRICT_JSON',{'argument':0,'raw_before':'frozen complete original header','raw_after_hex':invalid.hex().upper(),'same_sql_kind':'BLOB'},base_provenance)
complete=completed(snapshot)
for mode,old,cur,snap in [(0,None,ack,None),(1,None,complete,snapshot),(2,ack,complete,snapshot)]:
    valid=[header,binding(old,cur,snap),old,cur,mode]
    corrupt=list(valid)
    corrupt[2]=ack if mode in (0,1) else None
    vector('response-mode'+str(mode)+'-old-nullness',names[1],valid,corrupt,'F08_ARGUMENT_TYPE_OR_ARITY',{'argument':2,'kind_before':'NULL' if old is None else 'BLOB','kind_after':'BLOB' if old is None else 'NULL'},base_provenance)
badack=ack.replace(b'op-cancel-one',b'op-other')
vector('response-mode0-operation',names[1],[header,binding(None,ack,None),None,ack,0],[header,binding(None,badack,None),None,badack,0],'F08_ORIGINAL_BINDING',{'path':'response/result/operation_id','before':'op-cancel-one','after':'op-other','transport_digest_recomputed':True},base_provenance)
large=clone(snapshot);large['title']='界'*400000;large_raw=completed(large)
assert len(large_raw)>1048576
vector('response-large-legal-BLOB-type',names[1],[header,binding(None,large_raw,large),None,large_raw,1],[header,binding(None,large_raw,large),None,large_raw.decode(),1],'F08_ARGUMENT_TYPE_OR_ARITY',{'argument':3,'kind_before':'BLOB','kind_after':'TEXT','same_utf8_bytes':True},base_provenance)
write_raw('request.original-envelope.json',envelope_raw)
write_raw('request.private-header.json',header)

class Version:
    def __init__(self,project,kind,body):
        self.project,self.kind,self.body=project,kind,clone(body)
        self.id,self.revision=body['id'],body['revision']
        self.raw=go_json(body)
        self.content_hash=body.get('receipt_hash') if kind=='EventEnvelope' else None
    def ref(self):return {'entity_type':self.kind,'id':self.id,'revision':self.revision,'content_hash':self.content_hash}
    def anchor(self):return {'project':self.project,'version_ref':self.ref(),'body_digest':raw_hash(self.raw)}
    def key(self):return (self.project,self.kind,self.id,self.revision)
    def order(self):return (self.project,self.kind,self.id,self.revision,self.content_hash or '')

def tuple_order(row):
    return tuple((0,'') if x is None else ((1,x) if type(x) is int else (2,x)) for x in row)

class Fixture:
    def __init__(self):self.rows=[];self.versions={};self.edges={};self.frames=[]
    def add(self,category,row):self.rows.append([category,clone(row)])
    def replace(self,category,old,row):
        for i,(cat,r) in enumerate(self.rows):
            if cat==category and r==old:self.rows[i]=[category,clone(row)];return
        raise AssertionError(('missing old',category))
    def put(self,project,kind,body,head=True):
        v=Version(project,kind,body);self.versions[v.key()]=v
        row=[project,kind,v.id,v.revision,v.raw.hex().upper(),v.content_hash]
        self.add('domain_versions',row)
        if head:
            self.rows=[p for p in self.rows if not(p[0]=='domain_objects' and p[1][:3]==row[:3])]
            self.add('domain_objects',row+[0])
        return v
    def edge(self,o,field,t):
        row=[o.project,o.kind,o.id,o.revision,field,t.project,t.kind,t.id,t.revision]
        self.add('domain_refs',row);self.edges.setdefault(o.key(),[]).append(row)
    def graph(self,*roots):
        pending=list(roots);seen=set();anchors={};closure=[]
        while pending:
            o=pending.pop(0)
            if o.key() in seen:continue
            seen.add(o.key());anchors[o.key()]=o
            rows=clone(self.edges.get(o.key(),[]));targets={}
            for row in rows:
                t=self.versions[(row[5],row[6],row[7],row[8])];targets[t.key()]=t;pending.append(t)
            closure.append({'owner_project':o.project,'owner_ref':o.ref(),'owner_body_digest':raw_hash(o.raw),'rows':sorted(rows,key=tuple_order),'targets':[t.anchor() for t in sorted(targets.values(),key=lambda x:x.order())]})
        closure.sort(key=lambda x:(x['owner_project'],x['owner_ref']['entity_type'],x['owner_ref']['id'],x['owner_ref']['revision'],x['owner_ref']['content_hash'] or ''))
        pins=[{'project':v.project,'kind':v.kind,'id':v.id,'revision':v.revision,'content_hash':v.content_hash} for v in sorted(anchors.values(),key=lambda x:x.order())]
        return closure,pins
    def step(self,mode,action,old,row,category):
        # Pure transition recorder. Expected values never come from evaluator.
        frame={'action':action,'row':clone(row),'old':clone(old),'sources':clone(self.rows)}
        self.frames.append({'mode':mode,'action':action,'frame':frame,'raw':go_json(frame)})
        self.add(category,row) if old is None else self.replace(category,old,row)
    def materialize(self,row,member,pins,phase):
        child=row[:4]+['task-one',0,row[6],jcs_hash(member),hx(member)]
        action,category='admitted_member.insert','admitted_members'
        if phase=='FINALIZED':child[6]=jcs_hash(self.member);action,category='final_member.insert','final_members'
        self.step(7,action,None,child,category)
        for p in pins:self.step(7,'pin.insert',None,row[:4]+[phase,p['project'],p['kind'],p['id'],p['revision'],p['content_hash']],'pins')

def no_run_fixture(with_ack,body_type):
    f=Fixture()
    bind={'route':'MU_FORK','upstream_project_id':None,'upstream_goal_id':None,'upstream_task_id':None}
    contract={'contract_hash':'sha256:'+'a'*64,'contract_revision':1,'checks':[{'check_id':'check','kind':'DETERMINISTIC','required':True,'expected':'finite fixture','command_key':'fixture','rubric_ref':None,'qualification_id':None,'not_applicable_reason':None}],'require_independent_verifier':True,'version_policy':'EXACT','frozen_at':when}
    task_body={'id':'task-one','project_id':'project-one','revision':1,'created_at':when,'updated_at':when,'goal_id':'goal-one','title':'fixture','task_type':'fixture','stage':'review','status':'DRAFT','dependency_task_ids':[],'requirement_refs':[],'input_refs':[],'context_bundle_id':None,'acceptance_contract':contract,'assigned_principal_id':None,'active_run_id':None,'output_artifact_ids':[],'acceptance_id':None,'blocking_conflict_ids':[],'no_progress_record_id':'progress-one','stop_policy':{'wall_time_seconds':1,'max_attempts':1,'max_parallel_runs':1,'stop_conditions':['fixture']},'binding':bind}
    req=f.put('project-one','Requirement',{'id':'requirement-one','project_id':'project-one','revision':1,'created_at':when,'updated_at':when,'requirement_key':'fixture','text':'cancel finite task','basis':'USER_STATED','status':'ACCEPTED','source_refs':[],'rationale':'fixture','supersedes_id':None,'acceptance_check_ids':[]})
    goal_body={'id':'goal-one','project_id':'project-one','revision':1,'created_at':when,'updated_at':when,'title':'fixture','original_intent':'fixture','scope':'PROJECT','status':'ACTIVE','requirement_refs':[req.ref()],'problem_ids':['problem-one'],'task_ids':['task-one'],'deliverables':['fixture'],'acceptance_contract':contract,'budget_policy_id':'budget-one','outcome':None,'acceptance_id':None,'binding':bind}
    np=f.put('project-one','NoProgressRecord',{'id':'progress-one','project_id':'project-one','revision':1,'created_at':when,'updated_at':when,'origin_problem_id':'problem-one','candidate_id':'candidate-one','input_hash':'sha256:'+'1'*64,'key_hash':'sha256:'+'2'*64,'same_failure_count':0,'no_progress_iterations':0,'best_accepted_artifact_ref':None,'last_effective_progress_at':None,'resume_conditions':['fixture'],'status':'ACTIVE'})
    policy={'id':'budget-global','project_id':None,'revision':1,'created_at':when,'updated_at':when,'scope_type':'GLOBAL','scope_id':'global','parent_policy_id':None,'mode':'UNLIMITED_AMOUNT','cap':None,'enforcement':'ACCOUNTING_ONLY','period':'LIFETIME','timezone':'Asia/Shanghai','effective_from':when,'unknown_cost_action':'ALLOW_AND_RECORD'}
    glob=f.put('','BudgetPolicy',policy);policy=clone(policy);policy.update(id='budget-one',project_id='project-one',scope_type='PROJECT',scope_id='project-one',parent_policy_id='budget-global')
    budget=f.put('project-one','BudgetPolicy',policy);f.edge(budget,'/parent_policy_id',glob)
    task=f.put('project-one','Task',task_body);goal=f.put('project-one','Goal',goal_body)
    for o,field,t in [(task,'/goal_id',goal),(task,'/no_progress_record_id',np),(goal,'/task_ids',task),(goal,'/requirement_refs/0',req),(goal,'/budget_policy_id',budget)]:f.edge(o,field,t)
    q=request_hash;f.add('identities',['owner-one','cancel-one',protocol,'project-one','session.control','v2:session.control',q,when])
    session=['session-one','project-one',7,when,when,'goal-one',None,None,3,'client-one','2026-01-01T01:00:00Z',12,'native-one',None,None,'workspace-one','fixture','configuration-one','build-one',None,0,None,None,protocol];f.add('sessions',session)
    queue={'variant':'NO_SESSION','session_id':None,'generation':None,'revision':None,'state':None,'accepted_through':None,'sealed_through':None,'run_id':None,'runtime_epoch':None,'dispatch_key':None,'manifest_hash':None,'process_identity':None,'restore_fenced':None}
    root={'format':'researchos.cancel-finalization/1','phase':'ADMITTED','principal':'owner-one','project':'project-one','command_id':'cancel-one','method':'session.control','operation':'v2:session.control','key':'cancel-one','request_hash':q,'client_id':'client-one','session_binding':{'session_id':'session-one','accepted_revision':7,'writer_client_id':'client-one','writer_epoch':3,'lease_expires_at':session[10],'event_watermark':12},'target_binding':{'kind':'Goal','id':'goal-one','version_ref':goal.ref()},'private_header_digest':raw_hash(header),'member_task_ids':['task-one'],'member_count':1}
    rh=jcs_hash(root);closure,pins=f.graph(task,goal)
    f.member={'format':'researchos.cancel-finalization/1','phase':'ADMITTED','admitted_root_ref':{'phase':'ADMITTED','task_id':None,'content_hash':rh},'task_ref':task.ref(),'goal_ref':goal.ref(),'run_ref':None,'runtime_binding':None,'dispatch_stage':'NO_RUN','dispatch_origin_ref':None,'queue_admission':queue,'reference_closure':closure}
    mh=jcs_hash(f.member);gh=jcs_hash([{'task_id':'task-one','member_hash':mh}])
    admitted=['owner-one','project-one','cancel-one',q,'v2:session.control',header.hex().upper(),rh,gh,hx({'root':root,'members':[f.member],'pins':pins})]
    f.step(0,'admitted.insert',None,admitted,'admitted');f.materialize(admitted,f.member,pins,'ADMITTED')
    control=['owner-one','project-one','cancel-one','session-one','ctrl-cancel-one',q,'goal-one',hx(['task-one']),'REQUESTED',None,None,when]
    f.step(6,'control.insert',None,control,'controls')
    journal=None
    if with_ack:
        nxt=clone(control);nxt[9]=ack.hex().upper();f.step(6,'control.update',control,nxt,'controls');control=nxt
        journal=['owner-one','project-one','v2:session.control','cancel-one',q,200,nxt[9],admitted[5],when,body_type,'text'];f.step(5,'journal.insert',None,journal,'idempotency')
    final_task_body=clone(task_body);final_task_body.update(revision=2,status='CANCELLED',updated_at=later);final_task=f.put('project-one','Task',final_task_body)
    final_goal_body=clone(goal_body);final_goal_body.update(revision=2,status='CANCELLED',updated_at=later);final_goal=f.put('project-one','Goal',final_goal_body)
    for o,field,t in [(final_task,'/goal_id',final_goal),(final_task,'/no_progress_record_id',np),(final_goal,'/task_ids',final_task),(final_goal,'/requirement_refs/0',req),(final_goal,'/budget_policy_id',budget)]:f.edge(o,field,t)
    event_body={'id':'event-one','project_id':'project-one','revision':1,'created_at':later,'receipt_hash':'sha256:'+'0'*64,'sequence':13,'event_type':'TASK_CHANGED','aggregate_ref':final_task.ref(),'actor_id':'owner-one','correlation_id':'cancel-one','causation_id':None,'event_data_artifact_ref':None}
    event_body['receipt_hash']=jcs_hash({k:v for k,v in event_body.items() if k!='receipt_hash'})
    event=f.put('project-one','EventEnvelope',event_body,False);f.edge(event,'/aggregate_ref',final_task);f.add('outbox',['project-one',13,'event-one',event.raw.hex().upper(),0])
    snap=clone(snapshot);snap['pending_command_ids']=[];complete=completed(snap)
    ns=clone(session);ns[2]=8;ns[4]=later;ns[9]='';ns[10]=None;ns[11]=13;f.replace('sessions',session,ns)
    original=raw_hash(ack if with_ack else complete)
    final_root={'format':'researchos.cancel-finalization/1','phase':'FINALIZED','admitted_root_ref':{'phase':'ADMITTED','task_id':None,'content_hash':rh},'principal':'owner-one','project':'project-one','command_id':'cancel-one','request_hash':q,'control_request_id':'ctrl-cancel-one','completion_mode':'ACK_TO_COMPLETED' if with_ack else 'ORIGINAL_COMPLETED','original_response_digest':original,'final_response_digest':raw_hash(complete),'final_snapshot_binding':{'session_id':'session-one','project_id':'project-one','revision':8,'event_sequence':13,'pending_command_ids_digest':jcs_hash([])},'member_count':1}
    fq=clone(queue);fq.update(entry_refs=[],receipt_refs=[]);closure,pins=f.graph(task,goal,final_task,event)
    final_member={'format':'researchos.cancel-finalization/1','phase':'FINALIZED','admitted_member_ref':{'phase':'ADMITTED','task_id':'task-one','content_hash':mh},'proof_kind':'NO_EXECUTION','task_admitted_ref':task.ref(),'run_admitted_ref':None,'run_before_settlement_ref':None,'run_final_ref':None,'task_final_ref':final_task.ref(),'dispatch_origin_ref':None,'dispatch_final_binding':None,'queue_final_binding':fq,'effect_closure':{'run_id':None,'epoch':None,'histories':[],'non_effect_reservations':[]},'observation_ref':None,'native_artifact_refs':[],'sdk_receipt_refs':[],'run_event_ref':None,'task_event_ref':{'version_ref':event.ref(),'outbox_id':'event-one','sequence':13,'body_digest':raw_hash(event.raw)},'reference_closure':closure,'prior_epoch_closure':[],'prelaunch_checkpoint_carry':None}
    frh=jcs_hash(final_root);fmh=jcs_hash(final_member);fgh=jcs_hash([{'task_id':'task-one','member_hash':fmh}]);final=['owner-one','project-one','cancel-one',q,rh,frh,fgh,hx({'root':final_root,'members':[final_member],'pins':pins})]
    f.step(1,'final.insert',None,final,'final');f.materialize(final,final_member,pins,'FINALIZED')
    nxt=clone(control);nxt[10]=complete.hex().upper()
    if not with_ack:nxt[9]=nxt[10]
    f.step(6,'control.update',control,nxt,'controls');control=nxt
    nxt=clone(control);nxt[8]='CONFIRMED';f.step(6,'control.update',control,nxt,'controls');control=nxt
    cj=['owner-one','project-one','v2:session.control','cancel-one',q,200,nxt[10],admitted[5],when,body_type,'text']
    f.step(5,'journal.update' if with_ack else 'journal.insert',journal,cj,'idempotency')
    f.step(5,'commit.insert',None,['owner-one','project-one','cancel-one',q,frh,original,raw_hash(complete)],'commits')
    return f

sequences=[]
for with_ack in [False,True]:
    for body_type in ['text','blob']:
        fixture=no_run_fixture(with_ack,body_type)
        seqid=f'ack_{str(with_ack).lower()}_{body_type}'
        assert len(fixture.frames)>=20
        frames=[]
        for i,frame in enumerate(fixture.frames):
            raw=frame['raw'];valid=frame['frame'];bad=clone(valid);bad['action']='unbound.action'
            rawref=write_raw(f'{seqid}/{i:03d}-{frame["action"]}.go-producer-frame.json',raw)
            sqlrecipe=write_raw(f'{seqid}/{i:03d}-{frame["action"]}.sql-key-order-recipe.json',go_json({'action':valid['action'],'row':valid['row'],'old':valid['old'],'sources':valid['sources']},ordered=True))
            provenance={'producer_ref':ref(MAP/'source-snapshots/02-client_cancel_finalization_test.v3.go.proposed.txt'),'data_builder':'f08FullJournalFixture lines 492..537, independently ported; no SUT','transition_index':i,'sequence':seqid,'predicate_executions':0,'ddl_native_capture':False}
            vector(seqid+'-'+str(i),names[2],[frame['mode'],raw],[frame['mode'],go_json(bad)],'F08_MODE',{'path':'frame/action','before':valid['action'],'after':'unbound.action'},provenance)
            for category,row in valid['sources']:
                assert category in rules and len(row)==len(rules[category]),(category,len(row),rules[category])
            original_classes={cat:[] for cat in rules}
            for cat,row in valid['sources']:
                # Hex projection strings retain original BLOB bytes, but original
                # storage class is a separate producer fact from tuple mask.
                original_classes[cat].append(['null' if x is None else 'integer' if type(x) is int else 'text' for x in row])
            counts={cat:sum(1 for c,r in valid['sources'] if c==cat) for cat in rules}
            frames.append({'index':i,'mode':frame['mode'],'action':frame['action'],'go_producer_raw':rawref,'sql_key_order_recipe':sqlrecipe,'sql_native_bytes_proven':False,'row_width':len(valid['row']),'old_is_sql_null':valid['old'] is None,'category_counts_all34':counts,'projected_json_scalar_types':original_classes,'original_journal_body_type':body_type,'original_journal_headers_type':'text','storage_types_before_cast_runtime_proven':False})
        sequences.append({'id':seqid,'with_ack':with_ack,'body_type':body_type,'frames':frames,'pretransition_freeze':True,'actual_sql_native_capture':False,'expected_results':'source-derived int64(1) NOT_RUN; independent future review required','final_source_rows_ref':write_raw(seqid+'/final.sources.json',go_json(fixture.rows))})
emit('raw-sequences.json',{'schema':'researchos.f08.i17.raw-sequences.v1','sequences':sequences,'construction':'independent Python reconstruction of exact source explicit producer data; never evaluator output','future_reconstruction_crosscheck_required':True})
emit('vector-manifest.json',{'schema':'researchos.f08.i17.vector-manifest.v1','names':names,'source_ref':ref(MAP/'source-snapshots/01-client_cancel_finalization.v3.go.proposed.txt'),'producer_ref':ref(MAP/'source-snapshots/02-client_cancel_finalization_test.v3.go.proposed.txt'),'vectors':vectors,'formal_acceptance':False,'SQL24_complete':False,'all_expected_results':'SOURCE_INFERENCE_NOT_RUN'})
emit('fixture-provenance.json',{'schema':'researchos.f08.i17.fixture-provenance.v1','source_ref':ref(MAP/'source-snapshots/02-client_cancel_finalization_test.v3.go.proposed.txt'),'raw_envelope_line':44,'private_header_lines':[31,39],'request_hash_actual_contract':'Envelope.ContentHash -> canonicalBytes sorted source map, not raw-envelope digest','request_hash':request_hash,'raw_envelope_digest':raw_hash(envelope_raw),'hashes_are_distinct':request_hash!=raw_hash(envelope_raw),'header_bytes':ref(OUT/'raw/request.private-header.json'),'full_graph_data_lines':[365,388,447,481,492,537],'canonical_helpers':{'f08Encode':'encoding/json.Marshal, source line226','f08ValueHash':'strict JCS then SHA, line232','Receipt':'Hash excluding receipt_hash, contracts line105'},'port_subset':'ASCII keys, small finite integers, no float lexeme; encoding/json HTML/U+2028/U+2029 escaping','source_order':'ordered multiset retained; duplicates never deduplicated','sql_view_order':'unproven until actual native SELECT; key-order recipes are not native captures','construction_predicate_calls':0,'schema_validation_execution':False,'callback_execution':False,'native_capture':False})
emit('raw-digest-controls.json',{'schema':'researchos.f08.i17.raw-digest-controls.v1','authorization':False,'status':'SOURCE_DERIVED_NOT_RUN','controls':[{'mode':-2,'raw':write_raw('digest-nul-invalid-utf8.bin',b'\x00\xff\x61'),'expected_raw_sha256':raw_hash(b'\x00\xff\x61'),'expected_driver_kind':'string'},{'mode':9,'raw':write_raw('mode9-storage-class.bin',b'F08_STORAGE_CLASS'),'expected_callback_error':'F08_STORAGE_CLASS'}]})

assert set(rules)=={t['category'] for t in tuplelines}
assert source.count('func init()')==1
for body in re.findall(r'func (Test\w+)\(t \*testing\.T\)\s*\{', tests):
    # All prior test function names remain present; later static byte audit checks bodies.
    assert ('func '+body+'(t *testing.T)') in test_new
emit('preparation-summary.json',{'status':'SOURCE_PREPARED_NOT_RUN','input_count':len(inputs),'vector_count':len(vectors),'sequence_count':len(sequences),'transition_counts':[len(x['frames']) for x in sequences],'source34_unchanged':True,'production_source_changed':False,'Go_SQL_gofmt_native_SDK_HTTP_model_calls':0,'large_response_bytes':len(large_raw),'remaining_FATAL_OPEN':['independent source/vector review and real Go compile/module closure','actual DDL34 source/trigger capture, typeof-before-CAST and same-transaction parent-child-pin closure','initial auth/current validity/profile authority facts','ordinary native/SDK/history and later-epoch producer','mode3 authentic caller','legal >1MiB complete solejournal completion and replay']})
after=[]
for r in inputs:
    a=ref(Path(r['path']));assert a==r,(a,r);after.append(a)
emit('inputs.after.json',after)
print(json.dumps({'status':'SOURCE_PREPARED_NOT_RUN','vectors':len(vectors),'frames':[len(x['frames']) for x in sequences],'changes':len(changes),'inputs_unchanged':len(inputs)},ensure_ascii=False))
