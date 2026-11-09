from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
P=R/"execution/v2.4/receipts/W05/W05-99"
B=P/"sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r346-actual-canonical-pair-v2"
checks=[];pins={};snapshots=[]
def check(name,ok,evidence=None):
    checks.append(dict(name=name,passed=bool(ok),evidence=evidence))
def pin(p,raw=None):
    raw=p.read_bytes() if raw is None else raw
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):
    raw=p.read_bytes()
    ref=pin(p,raw)
    if str(p) not in pins:
        pins[str(p)]=ref
        relative=p.relative_to(R)
        dest=O/"input-snapshots"/relative
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("xb") as f:f.write(raw)
        snapshots.append(dict(source_ref=ref,snapshot_path=str(dest.relative_to(O))))
    return raw
def doc(p):return json.loads(read(p))
def verify(ref):
    actual=pin(Path(ref["path"]),read(Path(ref["path"])))
    check("exact pin "+ref["path"],actual==ref)
    return actual
h=doc(B/"handoff.json");mf=doc(B/"manifest.json")
check("Root handoff exact assigned pin",pin(B/"handoff.json")==dict(path=str(B/"handoff.json"),sha256="67e2047bf3207a124c36cf8dc2dba14593c3bbcb91301322031416490230ada5",bytes=2354))
check("Root manifest exact assigned pin",pin(B/"manifest.json")==dict(path=str(B/"manifest.json"),sha256="b36453ca2335551de9c2361ffbb4799a504b7e7990f11dc52c90960eed5a5da7",bytes=5155))
check("Root manifest13members",len(mf["members"])==13)
for ref in mf["members"]:verify(ref)
inventory={str(p) for p in B.rglob("*") if p.is_file()}
check("Root namespace inventory closed",inventory=={x["path"] for x in mf["members"]}|{str(B/"manifest.json"),str(B/"handoff.json")})
for name in ["manifest_ref","proof_ref","closed_ref","original_tool_io_ref","source_guard_cleanup_ref"]:verify(h[name])
proof=doc(B/"canonical_pair.actual.json");closed=doc(B/"checkpoint.closed.json")
io=doc(B/"root-execution.original-tool-io.json")
records={x["key"]:x for x in io["records"]}
ok=records["sdk_checkpoint_r346_actual_pair_v2_once"]
success=json.loads(ok["result"]["output"])
check("Original980105shellandPythonexit0",ok["result"]["chunk_id"]=="980105" and ok["result"]["exit_code"]==0 and "exit $LASTEXITCODE" in ok["input"]["cmd"] and "-I -S -X utf8" in ok["input"]["cmd"])
for name,target in [("closed_ref",B/"checkpoint.closed.json"),("proof_ref",B/"canonical_pair.actual.json"),("resume_ref",B/"RESUME.r346.original.json"),("checkpoint_ref",R/"execution/v2.4/checkpoint.json")]:
    check("Originalstdoutlinks "+name,success[name]==pin(target,read(target)))
producer=read(B/"checkpoint_actual_pair.v2.py").decode("utf-8")
patch=records["sdk_checkpoint_r346_actual_pair_v2_patch"]["input"]
rebuilt="\n".join(x[1:] for x in patch.splitlines() if x.startswith("+") and not x.startswith("+++"))
check("ExecutedproducerexactRootoriginalpatch",rebuilt.rstrip()==producer.rstrip())
txpath=Path(proof["source_transaction_ref"]["path"])
guardpath=Path(proof["source_guard_ref"]["path"])
verify(proof["source_transaction_ref"]);verify(proof["source_guard_ref"])
tx=read(txpath).decode("utf-8");guard=read(guardpath).decode("utf-8")
ast.parse(producer);ast.parse(tx);ast.parse(guard)
check("Exactpinnedsourcehelper094e",proof["source_transaction_ref"]["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9" and proof["source_transaction_ref"]["bytes"]==6877)
check("Exactpinnedsourceguardv2",proof["source_guard_ref"]["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and proof["source_guard_ref"]["bytes"]==11404)
check("Actualsourcebytebufferstrpathbeforehelperexec",'exec(compile(guard.get_buffer(str(tx_path)),str(tx_path),"exec"),tm.__dict__)' in producer)
check("CanonicalPATHSnotmonkeypatched","tm.PATHS" not in producer and 'PATHS=(ROOT/"execution/v2.4/checkpoint.json",ROOT/"execution/v2.4/path_ownership.json")' in tx)
check("Sourceholdsbothhandlesbeforetransform",tx.index("handles.append(handle)")<tx.index("before=[raw_read(h) for h in handles]")<tx.index("result=transform(") and "0x80000000|0x40000000,0,None,3,0x80,None" in tx)
check("Staleexpectedcomparedbeforetransformandjournal",tx.index('raise RuntimeError("canonical expected bytes changed under exclusive ownership")')<tx.index("result=transform(")<tx.index("journal.mkdir()"))
check("Journalfsyncandcommitunderhold",'out.write(raw);out.flush();os.fsync(out.fileno())' in tx and tx.index('exclusive(journal/"intent.json"')<tx.index("for i,(handle,raw) in enumerate(zip(handles,after))")<tx.index('exclusive(journal/"committed.json"')<tx.index("for handle in reversed(handles)") and "checked(flush(handle))" in tx)
J=Path(proof["transaction"]["transaction_journal"])
intent=doc(J/"intent.json");committed=doc(J/"committed.json")
before=[read(J/(str(i)+".before.json")) for i in (0,1)]
after=[read(J/(str(i)+".after.proposed.json")) for i in (0,1)]
oldcp,newcp=map(json.loads,[before[0],after[0]])
oldow,newow=map(json.loads,[before[1],after[1]])
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json"
current=[read(cp),read(ow)]
check("RealcanonicalCP346OW168byteexact",current==after and newcp["revision"]==346 and newow["revision"]==168)
check("PrestateCP345OW168",oldcp["revision"]==345 and oldow["revision"]==168)
check("Ownershipbyteunchanged",before[1]==after[1])
check("Journalexpectedactualpaths",intent["expected_refs"]==[pin(p,raw) for p,raw in zip([cp,ow],before)])
check("Journalbeforeafterpins",intent["before_refs"]==[pin(J/(str(i)+".before.json"),before[i]) for i in (0,1)] and intent["after_refs"]==[pin(J/(str(i)+".after.proposed.json"),after[i]) for i in (0,1)])
check("Durablecommittedactualrefs",committed["after_refs"]==[pin(p,raw) for p,raw in zip([cp,ow],after)] and committed["written_indices"]==[0,1] and committed["both_verified_while_exclusively_held"] is True and intent["mandatory_share_mode"]==0 and intent["automatic_inverse"] is False)
check("Nofailedpartialjournal",not (J/"failed.partial.json").exists())
controls=proof["controls"];held=doc(B/"transform.controls.before-write.actual.json")
check("7actualcontrols",len(controls)==7 and held["controls"]==controls[:5] and held["actual_pid"]==proof["actual_parent_pid"]==h["actual_pid"]==9184)
check("Stalerefnegativeactual",controls[0]==dict(control="stale expected ref rejected before transform/write",observed_error="canonical expected bytes changed under exclusive ownership",expected_negative=True))
expected_pairs=[(str(p),access) for p in (cp,ow) for access in ("READ","WRITE")]
check("FourrawCreateFileWsharingdenials32",[(x["path"],x["access"]) for x in controls[1:5]]==expected_pairs and all(x["succeeded"] is False and x["winerror"]==32 and x["expected_negative"] is True for x in controls[1:5]))
check("Bothreadopensrestoredaftertransaction",[x["path"] for x in controls[5:]]==[str(cp),str(ow)] and all(x["succeeded"] is True and x["winerror"]==0 for x in controls[5:]))
check("ControlsourcecallsactualWinAPI","k=ctypes.WinDLL" in producer and "h=create(str(path),access,7,None,3,0x80,None)" in producer and producer.index('save("transform.controls.before-write.actual.json"')<producer.index("transaction_result=tm.update_pair(expected,transform"))
oldf=oldcp["failure_counters"];newf=newcp["failure_counters"];delta=newf[702:]
check("Old702counterrecordspreserved",len(oldf)==702 and newf[:702]==oldf)
check("Only703to707addedonce",len(newf)==707 and [x["original_payload"]["observed_ordinal"] for x in delta]==list(range(703,708)) and all(x["counted_once"] is True and x["counter_reset"] is False and x["automatic_retry"] is False for x in delta))
check("Neworiginkeysnotduplicated",len({x["origin_key"] for x in delta})==5 and not ({x["origin_key"] for x in delta}&{x.get("origin_key") for x in oldf}))
origins={}
for e in delta:
    ref=e["evidence_ref"];verify(ref)
    ordinal=e["original_payload"]["observed_ordinal"];origins[ordinal]=doc(Path(ref["path"]))
    check("Originbinding"+str(ordinal),e["original_payload"]["immutable_origin_ref"]==ref and e["origin_key"]==hashlib.sha256((ref["sha256"]+"#"+str(ordinal)).encode()).hexdigest() and e["original_payload"]["actual_native_exit"] is None)
check("703oneactualInternalError",origins[703]["ordinal"]==703 and "Internal Error" in origins[703]["result"] and delta[0]["original_payload"]["actual_outer_exit"] is None)
check("704actualrgfailure",origins[704]["result"]["exit_code"]==1 and "os error 123" in origins[704]["result"]["output"] and delta[1]["original_payload"]["actual_python_exit"] is None)
check("705nonterminatingouter0preserved",origins[705]["original_result"]["exit_code"]==0 and "Cannot find path" in origins[705]["original_result"]["output"] and delta[2]["original_payload"]["actual_python_exit"] is None)
f706=doc(P/"mu_sdk_c6_author_control_failure_origin_codex/723ec91a795a400393a09266887da115/handoff.json")
verify(f706["original_command_execution_ref"])
check("706storedprojectionexplicitgap",origins[706]["type"]=="commandExecution" and origins[706]["exitCode"]==1 and "Root must pass the current process-resident Source owner explicitly" in origins[706]["aggregatedOutput"] and "no raw console bytes or split stdout/stderr" in f706["capture_gap"] and "outer JS/raw-console split unavailable" in delta[3]["original_payload"]["diagnostic"])
failed=B.parent/"checkpoint-r346-actual-canonical-pair"
failedsource=read(failed/"checkpoint_actual_pair.py").decode("utf-8")
check("707failurebeforetxmoduleexecution",origins[707]["result"]["chunk_id"]=="59df35" and origins[707]["result"]["exit_code"]==1 and "guard.get_buffer(tx_path)" in origins[707]["result"]["output"] and "guard.get_buffer(tx_path)" in failedsource and failedsource.index("guard.get_buffer(tx_path)")<failedsource.index("tm.update_pair("))
check("707canonunchangedfollowingerror",not any(failed.glob("activate.transaction.*")) and origins[707]["actual_canonical_pair_calls"]==0 and origins[707]["explicit_source_guard_cleanup_receipt_available"] is False)
oldread=records["c6_first_failure_and_canon_after_707_read"]["result"]
facts=[]
for line in oldread["output"].splitlines():
    if line.startswith('{"name":'):
        facts.append(json.loads(line))
facts={f["name"]:f for f in facts}
check("707postfailurecanonicalreadmatchesbefore",oldread["exit_code"]==0 and facts["checkpoint"]["sha256"]==pin(cp,before[0])["sha256"] and facts["path_ownership"]["sha256"]==pin(ow,before[1])["sha256"])
for name in ("step_state","commands"):
    p=R/"execution/v2.4"/(name+".json");actual=pin(p,read(p))
    check(name+"unchangedfrompreexecution",actual["sha256"]==facts[name]["sha256"] and actual["bytes"]==facts[name]["bytes"])
cleanup=doc(B/"source_guard.cleanup.actual.json")
check("Threeactualsourcehandlesclosed",cleanup["closed"] is True and cleanup["retained_handles_count"]==0 and cleanup["errors"]==[] and cleanup["failure"] is None and len(cleanup["entries"])==3 and all(x["closed"] is True and x["verified"] is True and x["final_path_match"] is True for x in cleanup["entries"]))
check("Guardentrypinsbindexactexecutedtriple",[{k:e[k] for k in ("path","sha256","bytes")} for e in cleanup["entries"]]==[proof["source_guard_ref"],proof["source_transaction_ref"],pin(B/"checkpoint_actual_pair.v2.py")])
allowed={"failure_counters","revision","expected_previous_revision","updated_at","updated_by","work_in_progress","note"}
changed=[k for k in set(oldcp)|set(newcp) if oldcp.get(k)!=newcp.get(k)]
check("Checkpointchangeslimitedauthorizedmetadata",set(changed)<=allowed and newcp["expected_previous_revision"]==345 and newcp["updated_by"]=="codex:/root")
resume=doc(B/"RESUME.r346.original.json")
check("Noformalorqualificationclaim",proof["formal_acceptance"] is False and proof["runtime_qualification"] is False and proof["provider_requests"]==0 and resume["formal_cases_current_accepted"]==0 and resume["accepted_parents"]==6 and resume["execution_grant"] is False and resume["completion_asserted"] is False)
check("Registered346cut707exact",closed["registered_failures"]==closed["observed_failures"]==h["failures_preserved"]==707)
report=dict(schema="researchos.canonical-pair-independent-component-review.v1",actor_id="codex:/root/w05_merge_review",producer_actor="codex:/root",decision="PASS_ACTUAL_COMPONENT" if all(c["passed"] for c in checks) else "NEEDS_WORK",scope="Root actual canonical exclusive-pair component evidence only",root_handoff_ref=pin(B/"handoff.json"),root_manifest_ref=pin(B/"manifest.json"),proof_ref=pin(B/"canonical_pair.actual.json"),live_canonical_refs=[pin(p,raw) for p,raw in zip([cp,ow],current)],checked_inputs=list(pins.values()),snapshots=snapshots,checks=checks,findings=[c for c in checks if not c["passed"]],actual_root_tool_chunk="980105",actual_root_outer_exit=0,actual_root_python_exit=0,actual_product_native_exit=None,independence=dict(review_actor_is_not_producer=True,review_actor_did_not_author_transaction_helper_or_source_guard=True,observer_O4_authorship_is_unrelated_to_actual_component_review=True),evidence_limits=["Competing opens were real raw CreateFileW calls in producer PID9184 while both canonical handles were held, not separate-process contention.","The 706 record is the original stored commandExecution projection with exitCode1/aggregatedOutput. Raw console bytes, split stdout/stderr and a separately observed Python exit are unavailable; no reconstruction is claimed.","The 707 attempt has no explicit guard cleanup receipt; failure is preserved before transaction module execution. Successful v2 has its own actual three-handle cleanup.","Failure708 occurred during this later independent read-only review. CP346 cut707 is correct and remains immutable; Root must register708 in a later checkpoint."],verification_execution=dict(candidate_imports=0,canonical_mutations=0,real_winapi_calls=0,native_product_calls=0,provider_requests=0),runtime_qualification=False,formal_acceptance=False,scope_complete=True)
(O/"review.json").write_bytes((json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8"))
(O/"HANDOFF.md").write_text("独立结论："+report["decision"]+"\n\n本审查只覆盖 Root 在真实 CP/OW 上执行的 canonical pair component。核验原始调用980105、固定Source、13-member包、7项真实controls、durable journal、当前CP346/OW168、SS/CM不变及失败计数702→707。未运行候选、WinAPI、provider或canonical mutation。\n\n706仅有原始commandExecution投影，保留raw/split捕获缺口；Python exit并无单独观测。707在tx模块执行前失败，未把成功v2 cleanup补写给失败尝试。708是本次后续只读审查错误，CP346 cut707仍正确，待Root后续登记。此次通过不产生runtime qualification、formal acceptance或执行授权。\n",encoding="utf-8")
print(json.dumps(dict(decision=report["decision"],checks=len(checks),failed=report["findings"],inputs=len(pins),review_ref=pin(O/"review.json")),ensure_ascii=False))

