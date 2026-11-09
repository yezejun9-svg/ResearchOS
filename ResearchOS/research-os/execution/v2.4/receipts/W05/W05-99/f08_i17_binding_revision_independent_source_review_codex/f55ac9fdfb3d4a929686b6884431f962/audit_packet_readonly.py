from pathlib import Path
import hashlib,json,re,collections,base64
ROOT=Path("D:/作品集/ResearchOS/research-os")
PACK=ROOT/"execution/v2.4/receipts/W05/W05-99/f08_i17_binding_revision_preparation_codex/b918c16361bb4744bc7fffb6434d6849"
OWN=ROOT/"execution/v2.4/receipts/W05/W05-99/f08_i17_binding_revision_independent_source_review_codex/f55ac9fdfb3d4a929686b6884431f962"
def ref(p):
 b=p.read_bytes()
 return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def dump(n,d):
 p=OWN/n
 if p.exists():raise RuntimeError("new-only path exists")
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def strict(b):
 def pairs(rows):
  d={}
  for k,v in rows:
   if k in d:raise ValueError("duplicate metadata key")
   d[k]=v
  return d
 return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
mf=strict((PACK/"manifest.json").read_bytes())
if len(mf["members"])!=431:raise RuntimeError("fixed membership drift")
all_refs=[ref(PACK/"manifest.json")]+mf["members"]
records=[];raws={}
for i,r in enumerate(all_refs):
 p=Path(r["path"]);a=ref(p)
 if a["sha256"]!=r["sha256"] or a["bytes"]!=r["bytes"]:raise RuntimeError("author member hash mismatch")
 relative=p.relative_to(PACK).as_posix()
 b=p.read_bytes();dst=OWN/"snapshots"/relative
 if dst.exists():raise RuntimeError("snapshot duplicate")
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
 if hashlib.sha256(b).hexdigest()!=a["sha256"]:raise RuntimeError("read race")
 records.append({"source":a,"copy":ref(dst),"relative":relative});raws[relative]=b
dump("inputs.before.json",records)
def load(n):return strict(raws[n])
def funcs(raw):
 text=raw.decode("utf-8");masked=list(text);i=0
 while i<len(text):
  if text.startswith("//",i):j=text.find("\n",i);j=len(text) if j<0 else j
  elif text.startswith("/*",i):j=text.find("*/",i+2);assert j>=0;j+=2
  elif text[i] in ['"', "'",chr(96)]:
   q=text[i];j=i+1
   while j<len(text):
    if q!=chr(96) and text[j]=="\\":j+=2;continue
    if text[j]==q:break
    j+=1
   assert j<len(text);j+=1
  else:i+=1;continue
  for k in range(i,j):
   if text[k] not in "\r\n":masked[k]=" "
  i=j
 masked="".join(masked);stack=[];ends={}
 for i,c in enumerate(masked):
  if c=="{":stack.append(i)
  elif c=="}":
   assert stack
   ends[stack.pop()]=i
 assert not stack
 out={}
 for m in re.finditer(r"(?m)^func\s*(?:\([^\n]*?\)\s*)?(\w+)\s*\(",masked):
  brace=masked.find("{",m.end());assert brace in ends
  out[m[1]]=text[m.start():ends[brace]+1].encode("utf-8")
 return out
def apply_patch_bytes(original,patch):
 src=original.decode("utf-8").splitlines(keepends=True);ls=patch.decode("utf-8").splitlines(keepends=True);result=[];cursor=0;i=2
 while i<len(ls):
  m=re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",ls[i]);assert m
  start,count=int(m[1]),int(m[2] or 1);idx=start-1 if count else start
  assert idx>=cursor;result.extend(src[cursor:idx]);cursor=idx;i+=1;old=0;new=0
  while i<len(ls) and not ls[i].startswith("@@"):
   kind,body=ls[i][0],ls[i][1:]
   if kind in " -":assert cursor<len(src) and src[cursor]==body;cursor+=1;old+=1
   if kind in " +":result.append(body);new+=1
   assert kind in " +-";i+=1
  assert old==count and new==int(m[4] or 1)
 result.extend(src[cursor:]);return "".join(result).encode("utf-8")
changes=load("changes.json");patch_results=[]
for x in changes:
 names={k:Path(x[k]["path"]).relative_to(PACK).as_posix() for k in ["before","after","forward","inverse"]}
 before,after=raws[names["before"]],raws[names["after"]]
 assert apply_patch_bytes(before,raws[names["forward"]])==after
 assert apply_patch_bytes(after,raws[names["inverse"]])==before
 patch_results.append({"change":names,"whole_forward_inverse_exact":True})
handoff=load("handoff.json");hchange=handoff["new_harness_change"]
harness=raws[Path(hchange["after"]["path"]).relative_to(PACK).as_posix()]
assert apply_patch_bytes(b"",raws[Path(hchange["forward"]["path"]).relative_to(PACK).as_posix()])==harness
assert apply_patch_bytes(harness,raws[Path(hchange["inverse"]["path"]).relative_to(PACK).as_posix()])==b""
tb,ta=funcs(raws["client_cancel_finalization_test.v4.go.before.txt"]),funcs(raws["client_cancel_finalization_test.v4.go.proposed.txt"])
db,da=funcs(raws["innocuous_test.go.before.txt"]),funcs(raws["innocuous_test.go.proposed.txt"])
testnames=sorted(k for k in tb if k.startswith("Test"))
raw_changed=[k for k in testnames if tb[k]!=ta[k]]
normalized_same=[k for k in testnames if tb[k].replace(b"\r\n",b"\n")==ta[k].replace(b"\r\n",b"\n")]
other_driver=[f"TestDriverI{i:02d}" for i in range(1,19) if i!=17]
assert all(db[k]==da[k] for k in other_driver)
dump("diff-and-body-audit.json",{"whole_changes":patch_results,"new_harness_forward_inverse_exact":True,"old_Test_count":len(testnames),"old_Test_raw_byte_changed":raw_changed,"old_Test_only_normalized_equal":normalized_same,"driver_other17_raw_byte_equal":other_driver,"test_before_CRLF":raws["client_cancel_finalization_test.v4.go.before.txt"].count(b"\r\n"),"test_after_CRLF":raws["client_cancel_finalization_test.v4.go.proposed.txt"].count(b"\r\n"),"Go_AST_or_compile":False})
vectors=load("vector-manifest.json")
names=vectors["names"];counts=collections.Counter();details=[];arg_ref_count=0
def verify_embedded(r):
 p=Path(r["path"]);relative=p.relative_to(PACK).as_posix();b=raws[relative]
 assert len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"]
 return b
def args(values):
 global arg_ref_count
 out=[]
 for a in values:
  if a["kind"]=="BLOB":arg_ref_count+=1;out.append(verify_embedded(a["ref"]))
  elif a["kind"]=="INTEGER":assert type(a["integer"]) is int;out.append(a["integer"])
  elif a["kind"]=="NULL":out.append(None)
  elif a["kind"]=="TEXT":assert isinstance(a["text"],str);out.append(a["text"])
  else:raise RuntimeError("unknown argument kind")
 return out
proof_action_only=0;seen=set();large=[]
for v in vectors["vectors"]:
 assert v["id"] not in seen;seen.add(v["id"]);assert v["function"] in names
 counts[v["function"]]+=1;good,bad=args(v["valid"]),args(v["corrupt"])
 assert len(good)==len(bad)==[2,5,2][names.index(v["function"])]
 assert good!=bad and v["valid_expected"]=={"driver_type":"int64","value":1}
 assert v["corrupt_kind"]=="CALLBACK_ERROR" and v["expected_sqlite_primary_code"]==1
 assert v["provenance"]["predicate_executions"]==0 and v["status"]=="SOURCE_DERIVED_NOT_RUN"
 changed=[i for i,(x,y) in enumerate(zip(good,bad)) if x!=y]
 d={"id":v["id"],"function":v["function"],"changed_argument_indices":changed,"fixed_error":v["fixed_callback_error"],"mutation":v["mutation"]}
 if v["function"]==names[2]:
  g=strict(good[1]);b=strict(bad[1]);assert set(g)==set(b)=={"action","row","old","sources"}
  delta=[k for k in g if g[k]!=b[k]]
  assert delta==["action"] and b["action"]=="unbound.action" and v["fixed_callback_error"]=="F08_MODE"
  proof_action_only+=1;d["object_differences"]=delta
 if v["function"]==names[1] and isinstance(good[3],bytes) and len(good[3])>1048576:
  large.append({"id":v["id"],"response_bytes":len(good[3]),"title_char_count":len(strict(good[3])["result"]["snapshot"]["title"])})
 details.append(d)
seqs=load("raw-sequences.json")
seq_results=[]
rules={r["category"]:r["mask"] for r in load("v5-source-tuples.exact.json")["tuples"]}
assert len(rules)==34
for seq in seqs["sequences"]:
 frames=[]
 for j,f in enumerate(seq["frames"]):
  raw=verify_embedded(f["go_producer_raw"]);recipe=verify_embedded(f["sql_key_order_recipe"]);g=strict(raw);s=strict(recipe)
  assert g==s and list(s)==["action","row","old","sources"]
  assert f["index"]==j and g["action"]==f["action"] and len(g["row"])==f["row_width"]
  assert set(g)=={"action","row","old","sources"} and (g["old"] is None)==f["old_is_sql_null"]
  if g["action"].endswith(".update"):assert g["old"] is not None and len(g["old"])==len(g["row"])
  else:assert g["old"] is None
  catcounts=collections.Counter(cat for cat,row in g["sources"])
  assert all(f["category_counts_all34"][k]==catcounts[k] for k in rules)
  for cat,row in g["sources"]:
   assert cat in rules and len(row)==len(rules[cat])
   if cat=="idempotency":assert row[9]==seq["body_type"] and row[10]=="text"
  assert not f["sql_native_bytes_proven"] and not f["storage_types_before_cast_runtime_proven"]
  vv=next(v for v in vectors["vectors"] if v["id"]==seq["id"]+"-"+str(j))
  assert args(vv["valid"])==[f["mode"],raw]
  expected=[list(p) for p in g["sources"]]
  category={"admitted.insert":"admitted","admitted_member.insert":"admitted_members","pin.insert":"pins","control.insert":"controls","control.update":"controls","journal.insert":"idempotency","journal.update":"idempotency","final.insert":"final","final_member.insert":"final_members","commit.insert":"commits"}[g["action"]]
  if g["old"] is None:expected.append([category,g["row"]])
  else:
   indices=[i for i,p in enumerate(expected) if p==[category,g["old"]]]
   assert len(indices)==1;expected[indices[0]]=[category,g["row"]]
  if j+1<len(seq["frames"]):
   nxt=strict(verify_embedded(seq["frames"][j+1]["go_producer_raw"]))["sources"]
   if seq["frames"][j+1]["action"]=="final.insert":
    omitted=["domain_versions","domain_objects","domain_refs","sessions","outbox"]
    assert [p for p in expected if p[0] not in omitted]==[p for p in nxt if p[0] not in omitted]
   else:assert expected==nxt
  else:assert expected==strict(verify_embedded(seq["final_source_rows_ref"]))
  frames.append({"index":j,"mode":f["mode"],"action":f["action"],"raw_ref":f["go_producer_raw"],"raw_original_null":g["old"] is None,"source_rows":len(g["sources"]),"next_transition_source_match":True})
 seq_results.append({"id":seq["id"],"with_ack":seq["with_ack"],"body_type":seq["body_type"],"frame_count":len(frames),"frames":frames})
env=raws["raw/request.original-envelope.json"];header=strict(raws["raw/request.private-header.json"])
assert base64.b64decode(header["raw_envelope_base64"],validate=True)==env
assert header=={"schema":"researchos.private-command-envelope.v1","encoding":"base64","raw_envelope_base64":base64.b64encode(env).decode("ascii")}
dump("raw-vector-audit.json",{"vector_count":len(seen),"function_counts":dict(counts),"BLOB_argument_refs_verified":arg_ref_count,"proof_action_only_corruption_count":proof_action_only,"vectors":details,"large_legal_response_source_vectors":large,"pretransition_total":sum(r["frame_count"] for r in seq_results),"sequences":seq_results,"source34_mask_arity_checked":True,"actual_Go_producer_crosscheck":False,"SQL_native_DDL_types_or_capture":False,"all_expected_outcomes":"SOURCE_INFERENCE_NOT_RUN"})
print(json.dumps({"members":431,"members_plus_manifest":432,"total_member_bytes":sum(r["bytes"] for r in mf["members"]),"raw_vectors":len(seen),"proof_action_only_corruptions":proof_action_only,"frames":[r["frame_count"] for r in seq_results],"old_Test_raw_changed":len(raw_changed),"normalized_only_equal":len(normalized_same),"other17driver_raw_equal":len(other_driver),"all_product_targets_run":0},ensure_ascii=False))
