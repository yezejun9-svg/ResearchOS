import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os")
O=Path(__file__).resolve().parent
W05=R/"execution/v2.4/receipts/W05/W05-99"
W09=R/"execution/v2.4/receipts/W09/W09-99"
SCOPE= W09/"integration_codex/w09c19v7-root-scope-20261009"
OLD_SCOPE=W09/"integration_codex/w09c19-root-scope-1791524400000"
CALLER=W09/"w09_c19_caller_v7_source_codex/w09c19r3-1a11f30"
PUB=W05/"original_provider_public_audit_resource_codex/opa-01a11f3f"
NATIVE=W09/"w09c19_actual_independent_review_codex/review-9125f15c751245e287e1eb3b17ba84eb"
ONE=W05/"integration_codex/native-cleanup-root-one-spec-source-1791517434000"
def pin(p):
 p=Path(p).resolve(strict=True)
 with p.open("rb") as f:data=f.read(64*1024*1024+1)
 assert len(data)<=64*1024*1024
 return {"path":str(p),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
def locked(p,sha,size):
 ref={"path":str(Path(p).resolve(strict=True)),"sha256":sha,"bytes":size}
 assert pin(p)==ref
 return ref
def read(ref):
 with Path(ref["path"]).open("rb") as f:raw=f.read(ref["bytes"]+1)
 assert len(raw)==ref["bytes"] and hashlib.sha256(raw).hexdigest()==ref["sha256"]
 return json.loads(raw)
def save(p,obj):
 p=Path(p)
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(p)
def pair(n,hsha,hsize,msha,msize):
 return {"handoff_ref":locked(n/"HDF.json",hsha,hsize),"manifest_ref":locked(n/"MF.json",msha,msize)}
assert len(sys.argv)==7,"REVIEW_HDF_PATH SHA BYTES REVIEW_MF_PATH SHA BYTES"
r3review={"handoff_ref":locked(sys.argv[1],sys.argv[2],int(sys.argv[3])),
          "manifest_ref":locked(sys.argv[4],sys.argv[5],int(sys.argv[6]))}
r3=pair(CALLER,"1ad85d20080d9ad8c0fb5cd4220a04646f3d1a6d2f04296713dbe1b24520e0f3",7985,
        "991592e7cccb49947dabc63cbeb0d76c656ae73568d1f7da97c3e3ecc87f04a1",9297)
v7=pair(W09/"w09_evidence_v7_fragment_source_codex/fragv7-1a11f30",
        "bb664f6f7c248b35836b95e36c079aa0bdb45d649a49898163f477cd627bfd39",4934,
        "a6b18e560edb37fb14c372f6d20e5760cf03b3d2ad11bd8d4e7ecbfed17dcda7",4199)
v7review=pair(W09/"v7_fragment_independent_review_codex/v7r-01a11f3f",
        "dc5eaea8d4b7c8a74db392b9a4782af7075e657d607c42a79ce1e61b8e979ef6",2660,
        "0b30564210352839b4bb435e6086b74828e06b9172d7b802817329e043eb6f0f",3555)
native=pair(NATIVE,"f090e9d33cb52f5ede999d5db33312e3a3b29e0a740a4df00c78b1a15f263e10",4551,
        "ab8d44dba6a7c9e0e4bb1d509972dd3d24edfcb9fcd901a88d36110ab367bd3b",21560)
public=pair(PUB,"33f94193879f7e3d2712467474c6719d6caa0d7b7d15b7a206cf05fa0c6efdf8",2981,
        "6cfb4d0f7779c027cd051a9d247242258359b267104d51f278305156d80ad1b0",14988)
v3review=pair(W05/"checkpoint_r366_v7_v3_independent_review_codex/review-20261009-01a11f5b",
        "1bf0f97d8f7d1ee88d22ec1b589a659a9e43cbedff16dbd6e0f0aa6b3285bad7",1610,
        "2709042121433cae9d9537c498d46963d7ffdf63733d83af3a002555b8888606",2484)
reviews=[r3,r3review,v7,v7review,native,public,v3review]
canonical=[pin(R/"execution/v2.4"/(x+".json")) for x in ("checkpoint","path_ownership","step_state","commands")]
expected=[("2862e018e00c9a12a1e9ad88fb85d12c69cefd9098114fe9f29b05f863b5a725",4279163),
("3ba05515053b60ba36ae3f09a2dc88d4af9861e86112b9ac7bcb33f3f8efbef5",196536),
("fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149",257446),
("b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129",68156)]
assert [(x["sha256"],x["bytes"]) for x in canonical]==expected
oldScopeRef=locked(OLD_SCOPE/"scope-registration.root.json",
 "17b5ebc80477f6ed9012eb751758a8ef9724956cd5f999ee3dd65f37cfa100f7",4891)
writerRef=locked(O/"checkpoint_w09_v7.v3.atomic.py",
 "36028517ff07c2e1c96b4b7b3a69c4373a28b28cc9bf1e22accefd47c7d32848",17360)
origins={
926:pin(ONE/"postseal-failure-origin.926-web-readonly-resource.json"),
927:locked(NATIVE/"failure-origin.927.original-tool-io.json","cbb02a6cd5c00a54f414bf19683592d22c6debd47c6fb3848314fe3e52818b64",2130),
928:locked(PUB/"failure-origin.928.original-tool-io.json","eb71b08d9e2ba9bee92997e2ab0e61059cb64135f31a178a63e7a61d0e2a3bf9",5311),
929:locked(PUB/"failure-origin.929.original-tool-io.json","6bc3d70eb929f79cf8f05e093da4717da63871e99767aee1c9963d5354ab9339",1177),
930:pin(OLD_SCOPE/"postseal-failure-origin.930.original-tool-io.json"),
931:locked(PUB/"failure-origin.931.original-tool-io.json","4ad0cd2a1c19793403d55d3567d77bf9e1b5d514bd3b168297b0f3761bf4aa42",705),
932:pin(OLD_SCOPE/"postseal-failure-origin.932.read-query.json"),
933:locked(CALLER/"failure-origin.933.original-tool-io.json","3a9d761bde3a869557406fe73aa7f093237c9e4610041cca89dd8e9adc5cb39d",1115),
934:locked(CALLER/"failure-origin.934.original-tool-io.json","2d48eee15da96fbb4f3e47c1c233538684916c4aea616a1d66b5fcc81b319c81",1259)}
origins[935]=locked(Path(r3review["handoff_ref"]["path"]).parent/"failure-origin.935.original-tool-io.json",
 "ae6ce0f875e3cae54e0112af91779e89ae67c2eb1ac2e38c6ca79079483cdf5b",2437)
origins[936]=locked(W05/"restored21_session_profile_source_codex/r21s-1a11f5e/failure-origin.936.original-tool-io.json",
 "c1a12a7b852140731265a079d5556ff5feba028604cec2b1351d14ffb656b38c",1837)
descriptions={
926:("Public web read partly failed supplied Zen Go URL open, one original call",None,None),
927:("Independent original Native packet reviewer parsed a split Go Output event as complete JSON; originalNative success preserved",1,1),
928:("Public resource read Get-Item parent AGENTS absent; same call child AGENTS exists",1,None),
929:("Public web read two official API URLs returned Internal Error in one original call",None,None),
930:("Root read batch rg guessed absent ops/ci/dispatcher.py then rg --files succeeded; original outer0 retained",0,None),
931:("Public docs Edit page click robots denied in one original web call",None,None),
932:("Root read query ended1 on rg no matches in apps/control apps/cli; excerpt read succeeded, no product test",1,None),
933:("Caller Source read omitted research-os path level; no Python/native/model ran",1,None),
934:("Unsealed Caller Source choice builder indentation error; no choice produced",1,1)}
descriptions[935]=("Original independent Caller Source checker located the helper success assertion rather than the producer report success check; candidate unchanged; corrected review retained separately",1,1)
descriptions[936]=("Source read rg guessed backup_restore.go absent; same call later read succeeded; origin retains error slice and explicit partial stdout disclosure",0,None)
gp=locked(W05/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py",
 "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85",11404)
raw=Path(gp["path"]).read_bytes();assert hashlib.sha256(raw).hexdigest()==gp["sha256"]
gm=types.ModuleType("facts_source_guard");gm.__file__=gp["path"];exec(compile(raw,gp["path"],"exec"),gm.__dict__)
refs=[*canonical,oldScopeRef,writerRef,gp,pin(__file__),pin(sys.executable),*origins.values()]
for entry in reviews:
 refs.extend(entry.values())
 members=read(entry["manifest_ref"])["members"]
 for v in (members.values() if isinstance(members,dict) else members):
  ref={k:v[k] for k in ("path","sha256","bytes")}
  ref["sha256"]=ref["sha256"].removeprefix("sha256:")
  assert pin(ref["path"])==ref
  refs.append(ref)
uniq={}
for ref in refs:
 key=ref["path"].casefold()
 assert key not in uniq or uniq[key]==ref
 uniq[key]=ref
guard=gm.SourceReadGuard(per_file_cap=64*1024*1024,total_cap=512*1024*1024)
guard.acquire(list(uniq.values()))
try:
 oldC=json.loads(guard.get_buffer(canonical[0]["path"]))
 oldO=json.loads(guard.get_buffer(canonical[1]["path"]))
 oldScope=json.loads(guard.get_buffer(oldScopeRef["path"]))
 scope=copy.deepcopy(oldScope)
 candidate="D:/作品集/ResearchOS/research-os/.local/worktrees/w09c19v7-1a11f30"
 fixed={
 "candidate":candidate,
 "isolation_receipt":str(W09/"integration_codex/w09c19v7-isolation-1a11f30").replace("\\","/"),
 "producer_receipt":str(W09/"integration_codex/w09c19v7-producer-1a11f30").replace("\\","/"),
 "prepare_environment":str(R/".local/w09c19v7-isolation-env-1a11f30").replace("\\","/"),
 "producer_environment":str(R/".local/w09c19v7-producer-env-1a11f30").replace("\\","/")}
 assert all(not Path(p).exists() for p in fixed.values())
 assert not SCOPE.exists()
 SCOPE.mkdir(parents=True)
 scope.update(candidate_root=candidate,source_handoff_ref=r3["handoff_ref"],source_manifest_ref=r3["manifest_ref"],
  independent_source_review_ref=r3review["handoff_ref"],independent_source_manifest_ref=r3review["manifest_ref"],
  permitted_candidate_source_paths=[p.replace("w09c19-1a11f08","w09c19v7-1a11f30")
                                     for p in oldScope["permitted_candidate_source_paths"]],
  fixed_write_roots=fixed)
 scopeRef=save(SCOPE/"scope-registration.root.json",scope)
 vectorSource=(OLD_SCOPE/"seal_canonical_vector.actual.py").read_bytes()
 assert hashlib.sha256(vectorSource).hexdigest()=="0b656ff022ab291dd6a07664f529af3ff3c682c1b01ea96b7c3a1030125293db"
 vectorText=vectorSource.decode("utf-8").replace("cp_rev==365 and ow_rev==169","cp_rev==366 and ow_rev==170")
 vectorText=vectorText.replace('"17b5ebc80477f6ed9012eb751758a8ef9724956cd5f999ee3dd65f37cfa100f7",4891',
                '"'+scopeRef["sha256"]+'",'+str(scopeRef["bytes"]))
 ast.parse(vectorText)
 with (SCOPE/"seal_canonical_vector.actual.py").open("xb") as f:f.write(vectorText.encode("utf-8"))
 vectorRef=pin(SCOPE/"seal_canonical_vector.actual.py")
 owner=copy.deepcopy(oldO["card_path_bindings"]["W09-99"]["subtasks"]["c19_fixture_producer"])
 owner.update(scope_ref=scopeRef,source_handoff_ref=r3["handoff_ref"],source_manifest_ref=r3["manifest_ref"],
  independent_source_review_ref=r3review["handoff_ref"],independent_source_manifest_ref=r3review["manifest_ref"],
  source_paths=scope["permitted_candidate_source_paths"],worktree_root=candidate,fixed_write_roots=fixed)
 worker=copy.deepcopy(next(w for w in oldC["workers"] if w.get("step_id")=="W09-99" and w.get("slice_id")=="C19_FIXTURE_PRODUCER"))
 worker.update(worktree=candidate,scope_ref=scopeRef,independent_source_review_ref=r3review["handoff_ref"])
 diagnostics=[{"ordinal":n,"origin_ref":origins[n],"description":descriptions[n][0],
 "actual_outer_exit":descriptions[n][1],"actual_python_exit":descriptions[n][2],
 "actual_native_exit":None,"origin_selector":"One original invocation retained per ordinal",
 "exit_qualification":"Only explicit shell/Python marker recorded; all product/native exits NULL"} for n in range(926,937)]
 facts={
 "schema":"researchos.root-cp366-w09-v7-facts.v1","formal_acceptance":False,
 "canonical_refs":canonical,"diagnostics":diagnostics,"reviews":reviews,
 "actual_refs":[scopeRef,vectorRef,writerRef,
  pin(OLD_SCOPE/"postseal-native-success-consumer-parser-blocker.resume.json"),
  pin(W09/"integration_codex/w09c19-producer-1a11f08/validation.closed.json"),
  pin(W09/"integration_codex/w09c19-producer-1a11f08/native-packet.public-index.json")],
 "registered_before":923,"registered_after":934,"highest_observed_ordinal":936,"next_failure_ordinal":937,
 "w09_scope_registration":{"scope_ref":scopeRef,"owner_subtask":owner,"worker":worker},
 "work_in_progress":{"mu_sdk_r366":{
  "old_v6_native_fixture":{"decision":"QUALIFIED","consumer_readiness":"BLOCKED_SOURCE_JSONL_FRAGMENT_ASSEMBLY",
                          "actual_review_ref":native["handoff_ref"],"old_packet_unchanged":True},
  "v7_closure":{"source_ref":pin(W09/"w09_evidence_v7_fragment_source_codex/fragv7-1a11f30/w09_evidence_closure.v7.proposed.py"),
    "independent_review_ref":v7review["handoff_ref"],"source_checks":181,"independent_checks":1505,
    "actual_new_producer":"NOT_RUN","actual_consumer":"NOT_RUN","fresh_source21_and_mode_review_required":True},
  "r3_caller":{"source_handoff_ref":r3["handoff_ref"],"independent_review_ref":r3review["handoff_ref"],
                "explicit_same_future_vector_required":True},
  "public_provider_audit":{"handoff_ref":public["handoff_ref"],"financial_coverage":"NOT_PROVEN"},
  "source_writer_v1_v2":"REQUEST_CHANGES_NOT_EXECUTED","writer_v3_source":v3review["handoff_ref"],
  "original_trial_once_consumed":True,"original_trial_business":"OPEN","provider_requests":None,
  "financial_closed":False,"historical_accepted_parents":6,"current_formal_accepted":0,
  "required_parents":22,"required_formal":42,"Main_adopted":False,"counter_reset":False}},
 "checkpoint_note":"Preserve original v6 Native QUALIFIED packet and P1 parser blocker. Register isolated v7 producer only after Source reviews. All old923 failures retained; original926..936 appended once at this Source cutoff; later originals remain pending in Root resume, never reset. No Main/formal/financial acceptance.",
 "next_action":"Root after facts nonauthor review saves CP366/OW170, seals four-file vector, invokes r3 prepare then one new v7 producer; independent actual qualification then two bounded component consumers."}
 fr=save(O/"checkpoint.execution.facts.json",facts)
 writer=types.ModuleType("pure_cp366_preview");writer.__file__=writerRef["path"]
 exec(compile(guard.get_buffer(writerRef["path"]),writerRef["path"],"exec"),writer.__dict__)
 previewC,previewO=writer.transform(copy.deepcopy(oldC),copy.deepcopy(oldO),facts,fr,oldC,oldO,scope,oldScope)
 assert previewC["revision"]==366 and previewO["revision"]==170 and len(previewC["failure_counters"])==934
 assert previewC["failure_counters"][:923]==oldC["failure_counters"]
 assert previewC["parent_tasks_accepted"]==oldC["parent_tasks_accepted"]
 assert previewC["current_effective_formal_status"]==oldC["current_effective_formal_status"]
 pc=save(O/"checkpoint.proposed.source-only.json",previewC)
 po=save(O/"ownership.proposed.source-only.json",previewO)
 proof=save(O/"source-concrete-preview.json",{"status":"PURE_TRANSFORM_PASS_NO_CANONICAL_MUTATION",
  "facts_ref":fr,"writer_ref":writerRef,"scope_ref":scopeRef,"vector_sealer_source_ref":vectorRef,
  "canonical_before_refs":canonical,"checkpoint_preview_ref":pc,"ownership_preview_ref":po,
  "old923_semantic_equal":True,"original_ordinals":list(range(926,937)),
  "registered_after":934,"next_failure_ordinal_at_cutoff":937,"formal_acceptance":False,
  "actual_writer_executed":False,"actual_new_producer_executed":False})
 assert [pin(Path(x["path"])) for x in canonical]==canonical
finally:
 cleanup=guard.close()
 cleanupRef=save(O/"facts-source-guard.cleanup.actual.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
mf=save(O/"MF.json",{"members":[pin(p) for p in O.iterdir() if p.is_file()]})
hdf=save(O/"HDF.json",{"schema":"researchos.cp366-v7-source-handoff.v1",
 "status":"SOURCE_PREPARED_PENDING_NONAUTHOR_CONCRETE_BINDING_REVIEW",
 "writer_ref":writerRef,"facts_ref":fr,"scope_ref":scopeRef,"vector_source_ref":vectorRef,
 "preview_proof_ref":proof,"manifest_ref":mf,"actual_source_guard_cleanup_ref":cleanupRef,
 "canonical_actual":False,"new_native_actual":False,"formal_acceptance":False,"next_failure_ordinal_at_cutoff":937})
print(json.dumps({"handoff_ref":hdf,"manifest_ref":mf,"facts_ref":fr,"scope_ref":scopeRef,
                  "vector_source_ref":vectorRef,"preview_proof_ref":proof,"guard_cleanup_ref":cleanupRef},ensure_ascii=False))
