import pathlib,json,hashlib,difflib,re
N=pathlib.Path(__file__).parent
data=json.loads((N/'source-input.json').read_text(encoding='utf-8'))
A=pathlib.Path(data['att3']);T=pathlib.Path(data['t9']);R=pathlib.Path(data['actual'])
rel='internal/domain/client_protocol_attach_contract_windows_test.go'
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(p,ref):
 got=pin(p);assert got['sha256']==ref['sha256'] and got['bytes']==ref['bytes'],str(p);return got
def write(name,body):
 p=N/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(body if isinstance(body,bytes) else body.encode('utf-8'))
def js(name,obj):write(name,json.dumps(obj,ensure_ascii=True,indent=2)+'\n')
refs={}
for name,key in [('HDF.json','hdf'),('MF.json','mf')]:
 p=A/name;refs[str(p)]=verify(p,data[key])
for name,ref in json.loads((A/'MF.json').read_text(encoding='utf-8'))['members'].items():
 p=A/name;refs[str(p)]=verify(p,ref)
for name in data['actualFiles']:
 p=R/name;refs[str(p)]=pin(p)
for ref in json.loads((R/'source-overlay.json').read_text(encoding='utf-8-sig'))['sources'].values():
 p=pathlib.Path(ref['path']);refs[str(p)]=verify(p,ref)
formatted=json.loads((R/'formatted.source-members.json').read_text(encoding='utf-8-sig'))
for ref in formatted:
 p=pathlib.Path(ref['path']);refs[str(p)]=verify(p,ref)
for name in data['directT9']:
 p=T/name;refs[str(p)]=pin(p)
base=verify(A/'candidate-root'/rel,data['base'])
raw=(A/'candidate-root'/rel).read_bytes()
old=raw.decode('utf-8');new=old
for replacement in data['replacements']:
 assert new.count(replacement['old'])==1
 new=new.replace(replacement['old'],replacement['new'],1)
inverse=new
for replacement in reversed(data['replacements']):
 assert inverse.count(replacement['new'])==1
 inverse=inverse.replace(replacement['new'],replacement['old'],1)
assert inverse.encode()==raw
raw_string=chr(96)+'[^'+chr(96)+']*'+chr(96)
pattern=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|'+raw_string+r'|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_][A-Za-z_0-9]*|\d+(?:\.\d+)?|==|!=|:=|>=|<=|&&|\|\||\+\+|--|\S')
def tokens(source):
 return [x for x in pattern.findall(source) if not x.startswith('//') and not x.startswith('/*')]
assert tokens(old)==tokens((T/rel).read_text(encoding='utf-8'))
stack=[];pairs={')':'(',']':'[','}':'{'}
for token in tokens(new):
 if token in ['(','[','{']:stack.append(token)
 elif token in pairs:assert stack and stack.pop()==pairs[token]
assert not stack
names=lambda s:re.findall(r'^func (Test\w+)\(',s,re.M)
assert names(old)==names(new) and len(names(new))==5
assert 'case "stale-revision": env.ExpectedRevision = revPtr(before.revision + 1)' in new
assert 'case "wrong-project": env.ProjectID = strptr("wrong-project"); want = "FORBIDDEN"' in new
common='if deref(response.Status) != "REJECTED" || deref(response.ErrorCode) != want || attachContractRead(t, f, sid) != before'
assert common in old and common in new
assert '[]string{"unowned", "expired-same-owner", "other-client"}' in new
assert '[]string{"stale-revision", "claimed-epoch", "wrong-project"}' in new
assert new.count('func ')==old.count('func ')
write('base-root/'+rel,raw);write('candidate-root/'+rel,new)
js('sourceguard.initial.json',{'refs':list(refs.values()),'scope':'ATT3, current Root A9 inputs/58Source composition, T9 formatted members and directly read contract/producer code; Root canonical excluded'})
js('source-replacements.json',data['replacements'])
write('two-fixtures.patch',''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='base/'+rel,tofile='candidate/'+rel)))
js('static-preservation.json',{'exact_inverse':True,'T9_formatted_base_lexical_tokens_equal':True,'five_original_test_names':names(new),'original_case_names_preserved':True,'common_REJECTED_and_state_assertion_byte_equal':True,'changes':2,'outside_replacements_byte_equal':True,'lexical_delimiters_balanced':True,'Go_AST_parser_executed':False,'Go_SQL_native_model_executed':False,'source_only':True})
for name in data['directT9']:
 write('contract-inputs/T9/'+name,(T/name).read_bytes())
js('failure-origin.876.json',data['failure'])
# Preserve the actual prior failed output as evidence, not a newly executed result.
events=[]
for line in (R/'current-attach-q5-leg2-parent-jsonl.stdout.raw').read_text(encoding='utf-8-sig').splitlines():
 record=json.loads(line)
 if record.get('Test') in ['TestClientAttachSettledAcquisitionCompletesAndReplays/unowned','TestClientAttachPreservesStaleAndBindingGates']:events.append(record)
js('prior-actual-failures.json',{'source_ref':pin(R/'current-attach-q5-leg2-parent-jsonl.stdout.raw'),'events':events,'historical_actual_retained':True,'new_actual_executed':False})
print(json.dumps({'status':'SOURCE_PREPARED_PENDING_REVIEW','candidate':pin(N/'candidate-root'/rel),'inputs':len(refs),'static':pin(N/'static-preservation.json'),'failures':[876]}))

