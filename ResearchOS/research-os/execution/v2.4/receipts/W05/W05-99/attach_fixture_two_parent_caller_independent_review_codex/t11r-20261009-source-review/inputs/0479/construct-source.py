import pathlib,json,hashlib,difflib
N=pathlib.Path(__file__).parent
data=json.loads((N/'source-input.json').read_text(encoding='utf-8'))
T=pathlib.Path(data['t6'])
rel='internal/domain/client_protocol_control_windows_test.go'
def pin(p):
 b=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(p,expected):
 got=pin(p)
 assert got['sha256']==expected['sha256'] and got['bytes']==expected['bytes'],str(p)
 return got
def write(name,body):
 p=N/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(body if isinstance(body,bytes) else body.encode('utf-8'))
def js(name,obj):write(name,json.dumps(obj,ensure_ascii=True,indent=2)+'\n')
pins={}
for package in data['packages']:
 P=pathlib.Path(package['path'])
 for name in ['HDF','MF']:
  p=P/(name+'.json');pins[str(p)]=verify(p,package[name])
 for name,ref in json.loads((P/'MF.json').read_text(encoding='utf-8'))['members'].items():
  p=P/name;pins[str(p)]=verify(p,ref)
files=[rel,'AGENTS.md','internal/domain/workbench_mixed_events_test.go','internal/domain/client_protocol_journal.go','internal/domain/client_protocol_history_test.go','internal/domain/v24_sessions.go','internal/domain/contracts.go','internal/domain/client_protocol.go','internal/domain/contracts/client.protocol.schema.json','internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json']
for name in files:
 p=T/name;pins[str(p)]=pin(p)
base=verify(T/rel,data['before_pin'])
raw=(T/rel).read_bytes()
text=raw.decode('utf-8')
start=text.index('func TestClientSameWriterRenewsExpiredLease(')
end=text.index('\nfunc TestClientResumeNeverRestartsPreviousRun(',start)
old=text[start:end]
new=old.replace('UPDATE client_sessions SET lease_expires_at=? WHERE id=?', "UPDATE client_sessions SET workspace_ref='fixture-workspace',model_config_ref='fixture-model',core_build_id='mixed-fixture',lease_expires_at=? WHERE id=?",1)
anchor='\tsourceTx(t, f.db, func(tx *sql.Tx) error {'
new=new.replace(anchor,data['add']+anchor,1)
oldAssert='\t\tif deref(res.Status) != "ACKNOWLEDGED" {\n\t\t\tt.Fatalf("renewal refused: %s", Bytes(res))\n\t\t}\n'
assert new.count(oldAssert)==1
new=new.replace(oldAssert,data['assertion'],1)
new=new.replace('\tenv.CommandID = strptr(ID())\n',data['publicRead']+'\tenv.CommandID = strptr(ID())\n',1)
candidate=text[:start]+new+text[end:]
assert candidate.replace(new,old,1).encode('utf-8')==raw
assert candidate[:start]==text[:start] and candidate[start+len(new):]==text[end:]
assert old.count('sourceTx(')==2 and new.count('sourceTx(')==3
# Existing epoch2/future lease and stale revision assertions are retained verbatim.
for original in ['if err != nil || !deadline.After(time.Now()) || epoch != 2 {\n\t\tt.Fatalf("new writer generation missing: epoch=%d until=%s %v", epoch, until, err)\n\t}',
'if deref(res.ErrorCode) != "VERSION_CONFLICT" {\n\t\t\tt.Fatalf("old renewal claim accepted: %s", Bytes(res))\n\t\t}']:
 assert original in old and original in new
write('base-root/'+rel,raw)
write('candidate-root/'+rel,candidate)
js('sourceguard.initial.json',{'pins':list(pins.values()),'scope':'explicit source inputs; canonical Root state excluded'})
js('source-replacement.json',{'path':rel,'old':old,'new':new})
write('test.patch',''.join(difflib.unified_diff(text.splitlines(True),candidate.splitlines(True),fromfile='base/'+rel,tofile='candidate/'+rel)))
js('static-preservation.json',{'exact_inverse':True,'outside_target_body_byte_equal':True,'imports_and_other_tests_byte_equal':True,'original_epoch2_future_lease_assertion_verbatim':True,'original_old_revision_VERSION_CONFLICT_assertion_verbatim':True,'original_test_name_unchanged':True,'production_files':0,'Go_parser_build_test_executed':False,'SQL_native_model_executed':False,'Q5_review':'NOT_ASSUMED_ACCEPTED','base_ref':base,'candidate_ref':pin(N/'candidate-root'/rel)})
for failure in data['failures']:js('failure-origin.'+str(failure['ordinal'])+'.json',failure)
print(json.dumps({'status':'SOURCE_PREPARED_NOT_ACCEPTED','candidate':pin(N/'candidate-root'/rel),'inputs':len(pins),'failures':[853,854]}))

