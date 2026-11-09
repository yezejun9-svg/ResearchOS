import collections
Q3=B/"typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49"
replacements=json.loads(data(Q/"source-replacements.json"))
pattern=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\x60[^\x60]*\x60|[A-Za-z_]\w*|[0-9][A-Za-z0-9_.]*|[^\s]')
def token_values(text):
 return [m.group() for m in pattern.finditer(text) if not m.group().startswith(("//","/*"))]
def delimiter_map(tokens):
 stack=[]; ends={}; match={")":"(","]":"[","}":"{"}
 for i,x in enumerate(tokens):
  if x in ("(","[","{"):stack.append((x,i))
  elif x in match:
   assert stack and stack[-1][0]==match[x],("unbalanced",i,x)
   _,j=stack.pop();ends[j]=i
 assert not stack
 return ends
def inventory(text):
 ts=token_values(text); end=delimiter_map(ts); calls=[]; nodes=[]; strict=[];names=[]
 for i,x in enumerate(ts):
  if x=="func" and i+1<len(ts) and ts[i+1].startswith("Test"):names.append(ts[i+1])
  if ts[i:i+2]==["t","."] and i+3<len(ts) and ts[i+2] in ("Fatal","Fatalf","Error","Errorf","Skip","Skipf") and ts[i+3]=="(":
   calls.append(ts[i:end[i+3]+1])
  if x=="if":
   j=i+1
   while j<len(ts):
    if ts[j] in ("(","["):j=end[j]+1;continue
    if ts[j]=="{":break
    j+=1
   assert j<len(ts)
   node=ts[i:end[j]+1]
   if any(v in ("Fatal","Fatalf","Error","Errorf") for v in node):
    nodes.append(node)
    if any(node[k:k+2]==["t","."] and k+2<len(node) and node[k+2] in ("Fatal","Fatalf","Error","Errorf") for k in range(len(node))):strict.append(node)
 return {"calls":calls,"ifs":nodes,"strict_ifs":strict,"test_names":names}
rows=[]
for name,edits in replacements.items():
 old=data(Q3/"candidate-root/internal/domain"/name).decode()
 new=data(Q/"candidate-root/internal/domain"/name).decode()
 forward=old
 for edit in edits:
  pos=edit['position'];before=edit['before'];after=edit['after']
  assert forward[pos:pos+len(before)]==before,(name,pos,'before')
  forward=forward[:pos]+after+forward[pos+len(before):]
 assert forward==new,(name,'forward')
 inverse=new
 for edit in reversed(edits):
  pos=edit['position'];after=edit['after'];before=edit['before']
  assert inverse[pos:pos+len(after)]==after,(name,pos,'after')
  inverse=inverse[:pos]+before+inverse[pos+len(after):]
 assert inverse==old,(name,"inverse")
 row={"file":name,"edit_count":len(edits),"forward_exact":True,"inverse_exact":True,"byte_equal":old.encode()==new.encode()}
 if name!="runtime_typed_client_fixture_windows_test.go":
  a=inventory(old);z=inventory(new);assert a==z,(name,"lexical_inventory")
  row.update({k:len(v) for k,v in a.items()});row["test_names"]=a["test_names"]
  row["all_assertion_tokens_equal"]=True
 else:
  position=edits[0]["position"];assert old[:position].encode()==new[:position].encode()
  row["unchanged_prefix_bytes"]=len(old[:position].encode())
  row["prefix_byte_equal"]=True
  tokens=token_values(new);delimiter_map(tokens)
 rows.append(row)
totals={k:sum((r[k] if k!="test_names" else len(r[k])) for r in rows if k in r) for k in ("calls","ifs","strict_ifs","test_names")}
expected={"calls":181,"ifs":196,"strict_ifs":190,"test_names":20}
assert totals==expected,(totals,expected)
goal=data(Q/"candidate-root/internal/domain/client_protocol_goal_test.go")
assert hashlib.sha256(goal).hexdigest()=="4809121015b1345adc4777385236cf692f2e4b53de2ab56cc97b89acffeb30e0" and len(goal)==16059
helper=data(Q/"candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go").decode()
newtests=helper[helper.index("func TestTypedRuntimeFixtureAttachRejectsAlteredTerminal"):]
case_lists=re.findall(r'for _, mode := range \[\]string\{(.*?)\}',newtests,re.S)
modes=[re.findall(r'"([^"]+)"',x) for x in case_lists]
assert [len(x) for x in modes]==[17,7]
result={"mode":"Independent Python lexical and exact byte checks; no Go execution","manifest_members_verified":len(mf["members"]),"input_count":len(references),"rows":rows,"totals":totals,"new_negative_modes":modes,"Go_native_SQL_executed":False,"authority":"NONE"}
(O/"static-independent-checks.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
copies=[]
selected=[r for r in references.values() if str(Path(r["path"])).startswith(str(Q)) or str(Path(r["path"])).endswith((".go",".md","client.protocol.schema.json"))]
(O/"input-copies").mkdir(exist_ok=True)
for i,r in enumerate(selected):
 target=O/"input-copies"/(str(i).zfill(4)+"-"+Path(r["path"]).name)
 blob=data(r["path"]);target.write_bytes(blob)
 copies.append({"source":r,"copy":{"path":str(target),"sha256":hashlib.sha256(blob).hexdigest(),"bytes":len(blob)}})
(O/"input-copy-index.json").write_text(json.dumps(copies,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,indent=2));print("INPUT_COPIES",len(copies))

