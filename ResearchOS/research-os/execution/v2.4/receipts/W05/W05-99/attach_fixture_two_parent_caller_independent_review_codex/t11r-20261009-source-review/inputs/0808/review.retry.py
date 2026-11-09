import pathlib,json,hashlib,difflib,re
N=pathlib.Path(__file__).parent
A=N.parent.parent/'session_attach_contract_fixture_revision_codex'/'af-1a11e3e93437fe089b15fdf6a164840'
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def js(n,o):
 p=N/n
 if p.exists():
  assert load(p)==o,'immutable existing evidence mismatch: '+n
  return
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=True,indent=2);f.write('\n')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
checks=[]
def check(name,value):checks.append(dict(name=name,passed=bool(value)))
def verify(r):
 p=pathlib.Path(r['path']);v=pin(p);check('hash:'+str(p),v['sha256']==r['sha256'] and v['bytes']==r['bytes']);return v
h=load(A/'HDF.json');m=load(A/'MF.json')
check('HDF pin',pin(A/'HDF.json')['sha256']=='e28f505265ff2dc2e0b95e8060dd535c888fd8665fc0e70fd2c60389c2798947' and (A/'HDF.json').stat().st_size==7391)
check('MF pin',pin(A/'MF.json')['sha256']=='e4431fc8c311ecae055e180c5dbf0b7c2a255d484745a116812936a483e51823' and (A/'MF.json').stat().st_size==11861)
check('30 members',len(m['members'])==30)
refs={str(A/'HDF.json'):pin(A/'HDF.json'),str(A/'MF.json'):pin(A/'MF.json')}
for rel,r in m['members'].items():
 check('AF member location '+rel,pathlib.Path(r['path']).resolve()==(A/rel).resolve())
 refs[str(pathlib.Path(r['path']))]=verify(r)
gi=load(A/'sourceguard.initial.json');gf=load(A/'sourceguard.final.json')
check('140 declared',len(gi['refs'])==140 and len(gf['checks'])==140 and gf['inputs']==140)
for r in gi['refs']:refs[str(pathlib.Path(r['path']))]=verify(r)
check('sourceguard closes same 140', {str(pathlib.Path(x['before']['path'])) for x in gf['checks']}=={str(pathlib.Path(x['path'])) for x in gi['refs']})
for c in gf['checks']:check('author closure '+c['before']['path'],c['before']==c['after'] and c['equal'])
initial=list(refs.values());js('guard.initial.json',initial)
for i,r in enumerate(initial):
 p=pathlib.Path(r['path']);dest=N/'input-snapshots'/str(i).zfill(4)/p.name;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists() or dest.read_bytes()==p.read_bytes()
 if not dest.exists():dest.write_bytes(p.read_bytes())
rel='internal/domain/client_protocol_attach_contract_windows_test.go'
base=(A/'base-root'/rel).read_bytes();candidate=(A/'candidate-root'/rel).read_bytes()
check('candidate pin',hashlib.sha256(candidate).hexdigest()=='5eb5f17345aeb53bd462614eaa77bdb347ba2e7592cf1d8739ba6d48fa597bc5' and len(candidate)==11724)
check('sole candidate',list((A/'candidate-root').rglob('*go'))==[A/'candidate-root'/rel])
data=load(A/'source-input.json');att=pathlib.Path(data['att3'])
check('base exact ATT3',base==(att/'candidate-root'/rel).read_bytes() and len(base)==10682)
rep=load(A/'source-replacements.json')
forward=base
for item in rep:
 old=item['old'].encode();new=item['new'].encode();check('unique old edit',forward.count(old)==1);forward=forward.replace(old,new,1)
check('only two exact edits',len(rep)==2 and forward==candidate)
inverse=candidate
for item in reversed(rep):inverse=inverse.replace(item['new'].encode(),item['old'].encode(),1)
check('exact inverse',inverse==base)
if (N/'inverse.original.go').exists():assert (N/'inverse.original.go').read_bytes()==inverse
else:(N/'inverse.original.go').write_bytes(inverse)
bs=base.decode();cs=candidate.decode()
patch=''.join(difflib.unified_diff(bs.splitlines(True),cs.splitlines(True),fromfile='base/'+rel,tofile='candidate/'+rel))
check('patch exact',(A/'two-fixtures.patch').read_bytes()==patch.encode())
names=lambda s:re.findall(r'^func (Test\w+)\(',s,re.M)
check('all five tests',len(names(bs))==5 and names(bs)==names(cs))
check('all original case labels',re.findall(r'case "([^"]+)":',bs)==re.findall(r'case "([^"]+)":',cs))
check('all table cases',re.findall(r'\[\]string\{[^}]*\}',bs)==re.findall(r'\[\]string\{[^}]*\}',cs))
check('all original t.Run',re.findall(r't.Run\([^\n]+',bs)==re.findall(r't.Run\([^\n]+',cs))
common='if deref(response.Status) != "REJECTED" || deref(response.ErrorCode) != want || attachContractRead(t, f, sid) != before'
check('common rejection unchanged',common in bs and common in cs)
check('no skips','t.Skip' not in cs)
unowned=rep[0]['new'];claimed=rep[1]['new']
check('unowned only null lease',"SET lease_expires_at=NULL WHERE id=?" in unowned and "writer_client_id=" not in unowned)
check('session.get exact public null/schema checks',all(x in unowned for x in ['handlerCommand(t, f, service','strptr("session.get")','snapshot.Result["writer"]','!present || writer != nil','ValidateResultAgainstMethod("session.get", snapshot, service.Doc)']))
check('claimed precise decoder/refusal state/handoff',all(x in claimed for x in ['DecodeEnvelope(Bytes(env))','decoded != nil || err == nil || err.Error() != "ATTACKER_CLAIMED_EPOCH"','attachContractRead(t, f, sid) != before','attachContractEventCount(t, f, sid, deref(env.CommandID)) != 0','continue']))
t9=pathlib.Path(data['t9'])
for rel2 in data['directT9']:check('contract byteexact:'+rel2,(t9/rel2).read_bytes()==(A/'contract-inputs/T9'/rel2).read_bytes())
schema=load(A/'contract-inputs/T9/internal/api/contracts/client.protocol.schema.json')
defs=schema['$defs']
check('nullable public writer',{'type':'null'} in defs['SessionSnapshot']['properties']['writer']['anyOf'])
rules=defs['CommandEnvelope']['allOf']
match=[x for x in rules if x.get('if',{}).get('properties',{}).get('method',{}).get('const')=='session.attach' and x.get('if',{}).get('properties',{}).get('payload',{}).get('properties',{}).get('request_write_owner',{}).get('const') is True]
check('takeover envelope contract',len(match)==1 and match[0]['then']['properties']['writer_epoch']=={'type':'null'} and match[0]['then']['properties']['expected_revision']=={'type':'integer','minimum':1})
def text(rel):return (A/'contract-inputs/T9'/rel).read_text()
prod=text('internal/domain/client_protocol.go');http=text('internal/api/v2.go');journal=text('internal/domain/client_protocol_journal.go');migration=text('migrations/sqlite/next_v24_sessions.sql')
check('legal storage null/nonempty',re.search(r'writer_client_id\s+TEXT NOT NULL CHECK \(length\(writer_client_id\) >= 1\)',migration) and re.search(r'lease_expires_at\s+TEXT,',migration))
check('producer null writer','writer := any(nil)\n\tif leaseExpires.Valid {' in journal)
check('decoder precise nil','if claim && e.WriterEpoch != nil {\n\t\t\treturn nil, fmt.Errorf("ATTACKER_CLAIMED_EPOCH")' in prod)
decodebranch=http[http.index('if decErr != nil {'):http.index('tx, err := v.db.BeginTx')]
check('authenticated HTTP 400 INVALID_REQUEST mapping',all(x in decodebranch for x in ['code := "INVALID_REQUEST"','status := http.StatusBadRequest','return']) and http.index('if authErr != nil {')<http.index('if decErr != nil {'))
check('no decoder code in public whitelist','ATTACKER_CLAIMED_EPOCH' not in prod[prod.index('var protocolErrorCodes ='):prod.index('func hasResultPayload')] and 'ATTACKER_CLAIMED_EPOCH' not in json.dumps(schema))
prior=load(A/'prior-actual-failures.json');verify(prior['source_ref'])
events=[json.loads(s) for s in pathlib.Path(prior['source_ref']['path']).read_text(encoding='utf-8-sig').splitlines()]
selected=[x for x in events if x.get('Test') in ['TestClientAttachSettledAcquisitionCompletesAndReplays/unowned','TestClientAttachPreservesStaleAndBindingGates']]
check('A9 failures exact extracted events',selected==prior['events'] and sum(x.get('Action')=='fail' for x in selected)==2)
for ordinal in [876,878,882]:check('failure retained '+str(ordinal),load(A/('failure-origin.'+str(ordinal)+'.json'))['ordinal']==ordinal)
diff=list(difflib.unified_diff((A/'construct-source.failed.882.py').read_text().splitlines(),(A/'construct-source.py').read_text().splitlines()))
js('882-corrected-script.diff.json',diff)
# Independent lexical normalization removes whitespace/comments but preserves all punctuation and strings.
pattern=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|'+chr(96)+'[^'+chr(96)+']*'+chr(96)+r'|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_][A-Za-z_0-9]*|\d+(?:\.\d+)?|==|!=|:=|>=|<=|&&|\|\||\+\+|--|\S')
def tokens(s):return [x for x in pattern.findall(s) if not x.startswith('//') and not x.startswith('/*')]
normalized=bs
for error in ['INVALID_REQUEST','FORBIDDEN']:
 exact='; want = "'+error+'"';check('one exact gofmt site '+error,normalized.count(exact)==1);normalized=normalized.replace(exact,'\nwant = "'+error+'"',1)
check('only two gofmt token changes',tokens(normalized)==tokens((t9/rel).read_text()))
js('checks.json',checks)
final=[pin(pathlib.Path(r['path'])) for r in initial];js('guard.final.json',dict(unchanged=initial==final,before=initial,after=final))
result=dict(status='SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL' if all(x['passed'] for x in checks) and initial==final else 'REQUEST_CHANGES',checks=len(checks),failed=[x for x in checks if not x['passed']],source_inputs=140,total_guarded=len(initial),test_names=names(cs),Go=False,SQL=False,native=False,model=False,formal_acceptance=False)
js('result.json',result);print(json.dumps(result))

