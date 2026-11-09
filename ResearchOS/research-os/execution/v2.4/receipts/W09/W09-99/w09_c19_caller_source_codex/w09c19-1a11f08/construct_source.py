import ast,hashlib,json,sys
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
S=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/history20-five-parent-sparse-root-source-h20v-1a11ebe661670a1a49d0ea22092604a')
E=R/'execution/v2.4/receipts/W09/W09-99/independent_next_slice_readonly_codex/w09-slice-01a11ee7'
B=R/'execution/v2.4/receipts/W05/W05-99'
W=R/'execution/v2.4/receipts/W09/W09-99'
T=R/'.local/worktrees/w09c19-1a11f08'
ISO=W/'integration_codex/w09c19-isolation-1a11f08'
O=W/'integration_codex/w09c19-producer-1a11f08'
PREPENV=R/'.local/w09c19-isolation-env-1a11f08'
ENV=R/'.local/w09c19-producer-env-1a11f08'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def put(n,b):
 b=b if isinstance(b,bytes) else b.encode('utf-8')
 with (N/n).open('xb') as f:f.write(b)
 return pin(N/n)
def js(n,v):return put(n,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
nt=json.loads((E/'next-task.json').read_bytes())
sources={x['target']:x['candidate_ref'] for x in nt['source_files']}
for ref in sources.values():
 actual=pin(ref['path']);assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
assert len(sources)==6
cp=pin(R/'execution/v2.4/checkpoint.json');assert cp['sha256']=='6ed349c5b8380ad6b099ae2237c33513f4e2717afc7789398968366a8cddf6dd' and cp['bytes']==4237636
assert json.loads(Path(cp['path']).read_bytes())['revision']==364
guarded_paths=[E/'next-task.json',Path(nt['original_review_ref']['path']),S/'prepare_history20_five_parent.actual_owned.py',S/'validate_history20_five_parent.actual_owned.py',R/'execution/toolchains/locked.json',R/'AGENTS.md']+[Path(x['path']) for x in sources.values()]+[R/'execution/v2.4'/(x+'.json') for x in ('checkpoint','path_ownership','step_state','commands')]
before={str(p):p.read_bytes() for p in guarded_paths}
js('original-input-pins.json',[pin(p) for p in guarded_paths])
def replace_once(text,old,new):
 assert text.count(old)==1,old[:100]
 return text.replace(old,new,1)
prep_old=(S/'prepare_history20_five_parent.actual_owned.py').read_text(encoding='utf-8')
prep=prep_old.replace('history20-five-parent-sparse-isolation-root-h20v-1a11ebe6616','w09c19-isolation-1a11f08').replace('h20s-1a11ebe6616','w09c19-1a11f08')
prep=replace_once(prep,"O=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/w09c19-isolation-1a11f08')",'O=Path('+repr(str(ISO))+')')
prep=replace_once(prep,'assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision','assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision==364\nassert checkpoint_sha=="'+cp['sha256']+'" and checkpoint_bytes==4237636\nassert pin(git if "git" in globals() else Path("C:/Program Files/Git/cmd/git.exe"))["sha256"]=="da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f"')
prep=replace_once(prep,'scratch=R/".local"/("history20-five-parent-isolation-toolenv-"+uuid.uuid4().hex);scratch.mkdir()','scratch=Path('+repr(str(PREPENV))+');assert not scratch.exists();scratch.mkdir()')
prep=replace_once(prep,'"GIT_TERMINAL_PROMPT":"0"','"GIT_TERMINAL_PROMPT":"0","GIT_OPTIONAL_LOCKS":"0"')
put('prepare_w09_c19.actual_owned.py',prep)
old=(S/'validate_history20_five_parent.actual_owned.py').read_text(encoding='utf-8')
text=old
start=text.index('R=Path(');end=text.index('\ndef pin',start)
text=text[:start]+'R=Path('+repr(str(R))+');B=R/"execution/v2.4/receipts/W05/W05-99";O=Path('+repr(str(O))+')\nT=Path('+repr(str(T))+')\nISO=Path('+repr(str(ISO))+')\n'+text[end:]
text=replace_once(text,'import hashlib,json,types,re','import hashlib,json,types,re,os,subprocess,platform,signal,time,uuid\nfrom datetime import datetime,timezone')
text=replace_once(text,'researchos.root-history20-five-parent-integration-choice.v1','researchos.root-w09-c19-integration-choice.v1')
start=text.index('sources={};input_refs=');end=text.index('canonical=[',start)
text=text[:start]+'''sources={relative:verify(ref) for relative,ref in choice["sources"].items()}
assert len(sources)==6 and set(sources)==set(choice["exact_six_targets"])
input_refs=[verify(choice_ref),pin(__file__),isolation_ref]+[verify(ref) for ref in choice["base_driver_refs"]+choice["review_refs"]]
input_refs += [verify(ref) for ref in choice["original_input_refs"]]
new_tests=list(choice["selected_tests"]);review_refs=choice["review_refs"]
assert new_tests==["TestW09C19ChainInvalidation","TestW09C19ExplicitOriginAndUnknown"]
''' +text[end:]
text=replace_once(text,'assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision','assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision==364\nassert verify(choice["checkpoint_ref"])["sha256"]==checkpoint_sha and choice["checkpoint_ref"]["bytes"]==checkpoint_bytes')
start=text.index('main_before=');end=text.index('\ngp=',start)
text=text[:start]+'''main_before={R/n:(R/n).read_bytes() for n in sources if (R/n).is_file()}
main_before.update({R/n:(R/n).read_bytes() for n in ("go.mod","go.sum","internal/domain/store.go")})
''' +text[end:]
start=text.index('go=R/');end=text.index('\ngm=module',start)
text=text[:start]+'''go=R/".local/tools/go1.27.1/go/bin/go.exe";git=Path("C:/Program Files/Git/cmd/git.exe")
for path,digest in ((Path(sys.executable),"cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"),(gp,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"),(hp,"6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"),(go,"d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"),(git,"da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f")):
 assert pin(path)["sha256"]==digest
input_refs.extend(list(sources.values())+[pin(p) for p in main_before]+[pin(p) for p in (gp,hp,go,git,Path(sys.executable),go.parent.parent/"VERSION",go.parent.parent/"src/go.mod")])
''' +text[end:]
start=text.index('runtime_guard=candidate_guard=');end=text.index('\ndef invoke',start)
text=text[:start]+'''runtime_guard=candidate_guard=compiler_guard=None
scratch=Path('''+repr(str(ENV))+''');assert not scratch.exists();scratch.mkdir()
for name in ("profile","temp"):(scratch/name).mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";"+str(git.parent)+";C:/Windows/System32","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(scratch/"profile"),"LOCALAPPDATA":str(scratch/"profile"),"APPDATA":str(scratch/"profile"),"TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),"GOENV":"off","GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2","RESEARCHOS_GO":str(go),"RESEARCHOS_TASK_ID":"W09","RESEARCHOS_CHECK_ID":"","RESEARCHOS_CASE_ID":"C19","RESEARCHOS_RETRIEVAL_MODE":"fixture","GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":"NUL","GIT_TERMINAL_PROMPT":"0","GIT_OPTIONAL_LOCKS":"0"}
invocations=[];closed_jobs=[];formatted_ref=inventory_ref=overlay_ref=packet_ref=None
''' +text[end:]
start=text.index('def closed(');end=text.index('\ntry:',start)
text=text[:start]+'''def closed(status,error=None):
 assert all(path.read_bytes()==raw for path,raw in before.items()) and all(path.read_bytes()==raw for path,raw in main_before.items())
 ref=save("validation.closed.json",dict(status=status,error=error,source_count=len(sources),source_overlay_ref=overlay_ref,exact_source_members_ref=formatted_ref,compiler_inventory_ref=inventory_ref,native_packet_ref=packet_ref,selected_tests=new_tests,expected_native_ids=choice["expected_native_ids"],formal_consumers="NOT_RUN_REGISTRY_UNBOUND",same_native_report_required_for_both_consumers=True,canonical_pre_run_ref=canonical_pre_run_ref,invocation_refs=invocations,all_owned_jobs_closed=all(closed_jobs),independent_Source_review_refs=review_refs,Main_canonical_unchanged=True,Main_adopted=False,original_trial_DB_touched=False,external_model_provider_requests=0,formal_acceptance=False))
 print(json.dumps({"closed_ref":ref,"status":status}),flush=True)
''' +text[end:]
text=replace_once(text,' success("format",[str(fmt),"-w",*[str(T/name) for name in sources if name.endswith(".go")]],45)\n','')
text=replace_once(text,'"formatted.source-members.json"','"exact.source-members.json"')
text=text.replace('tagged-compiler-input-list','compiler-input-list').replace(',"-tags=researchos_native_recovery_harness"','')
text=replace_once(text,'"actual-tagged-compiler-input-inventory.json"','"actual-compiler-input-inventory.json"')
text=replace_once(text,'"build_tag":"researchos_native_recovery_harness","test2json_executable_ref":pin(test2json),','"build_tag":None,')
start=text.index(' binary=scratch/');end=text.index('\nexcept BaseException as error:',start)
text=text[:start]+''' # This single owned Python process and every git/go child inherit the exclusive Job.
 result=invoke("w09-c19-producer",[str(Path(sys.executable)),"-I","-S","-B","-X","utf8",str(T/"ops/ci/retrieval.py")],420,T)
 raw=(O/"w09-c19-producer.stdout.raw").read_text(encoding="utf-8")
 emitted=json.loads(raw)
 report_path=(T/emitted["report_reference"]).resolve();tool_path=(T/emitted["tool_run_reference"]).resolve()
 base=(T/"execution/receipts/W09/retrieval").resolve()
 assert report_path.is_relative_to(base) and tool_path.parent==report_path.parent and report_path.name=="report.json" and tool_path.name=="native-tool-run.json"
 assert re.fullmatch(r"run-[0-9a-f]{32}",report_path.parent.name)
 packet_dir=report_path.parent
 report=json.loads(report_path.read_bytes());tool=json.loads(tool_path.read_bytes())
 # Preserve originals before evaluating any producer success claim; no latest/glob selection.
 archive=O/"native-packet";archive.mkdir()
 mapping=[]
 for path in sorted(packet_dir.rglob("*")):
  assert not path.is_symlink() and path.resolve().is_relative_to(packet_dir)
  if path.is_file():
   relative=path.relative_to(packet_dir);dest=archive/relative;dest.parent.mkdir(parents=True,exist_ok=True)
   with dest.open("xb") as stream:stream.write(path.read_bytes())
   a,b=pin(path),pin(dest);assert (a["sha256"],a["bytes"])==(b["sha256"],b["bytes"])
   mapping.append(dict(original_ref=a,archive_ref=b))
 packet_ref=save("native-packet.public-index.json",dict(run_id=report["run_id"],original_report_ref=pin(report_path),original_tool_run_ref=pin(tool_path),raw_copy_mapping=mapping,consumer_source_root=str(T),formal_acceptance=False,immutable_original_bytes=True))
 assert result["actual_exit"]==0 and report["status"]=="PASS" and report["exit_code"]==0 and report["timed_out"] is False
 assert report["task_id"]=="W09" and report["check_id"] is None and report["case_id"]=="C19"
 assert report["formal_construction_acceptance"]=="NOT_RUN_POSTRUN_REVIEW_PENDING" and report["formal_case_accepted_delta"]==0
 assert report["selected_tests"]==new_tests and set(report["passed_tests"])==set(new_tests)
 expected_argv=[str(go),"test","-count=1","-json","-run","^(?:"+"|".join(new_tests)+")$","./internal/domain"]
 assert report["actual_invocation"]==tool["actual_invocation"]==expected_argv
 assert sorted(report["assertion_ids"])==choice["expected_native_ids"] and report["assertions"]==5 and report["owned_export"]["complete"] is True
 assert tool["report_sha256"]==pin(report_path)["sha256"] and tool["run_id"]==report["run_id"] and tool["native_exit_code"]==0
 assert all(pin(T/relative)["sha256"]==ref["sha256"] and pin(T/relative)["bytes"]==ref["bytes"] for relative,ref in sources.items())
 closed("C19_NATIVE_PRODUCER_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW")
''' +text[end:]
text=text.replace('FAILED_HISTORY20_FIVE_PARENT_COMPILE_OR_TARGET_EXECUTION_CLOSED','FAILED_C19_LIST_OR_SINGLE_PRODUCER_CLOSED')
text=replace_once(text,'((binary_guard,"binary"),(compiler_guard,"compiler"),','((compiler_guard,"compiler"),')
put('run_w09_c19.actual_owned.py',text)
base_refs=[pin(S/'prepare_history20_five_parent.actual_owned.py'),pin(S/'validate_history20_five_parent.actual_owned.py')]
choice=dict(schema='researchos.root-w09-c19-integration-choice.v1',Root_source_adoption_only=True,execution_grant=False,sources=sources,exact_six_targets=list(sources),selected_tests=['TestW09C19ChainInvalidation','TestW09C19ExplicitOriginAndUnknown'],expected_native_ids=['C19-01','C19-02','C19-03','C19-04','C19-05'],expected_formal_ids=['C19-01','C19-02','C19-03'],base_driver_refs=base_refs,review_refs=[nt['original_review_ref']],original_input_refs=[pin(p) for p in guarded_paths],checkpoint_ref=cp,checkpoint_revision=364,fixed_paths=dict(candidate=str(T),isolation_receipt=str(ISO),producer_receipt=str(O),prepare_environment=str(PREPENV),producer_environment=str(ENV)),native_producer_runs=1,formal_consumers='NOT_RUN_REGISTRY_UNBOUND',main_adopted=False)
js('source.integration.choice.json',choice)
for p,raw in before.items():assert Path(p).read_bytes()==raw
for name in ('prepare_w09_c19.actual_owned.py','run_w09_c19.actual_owned.py'):ast.parse((N/name).read_bytes(),filename=name)
js('source-construction.result.json',dict(status='SOURCE_ONLY_CONSTRUCTION_AND_AST_PARSE_PASS',exact_six_pins_preserved=True,original_inputs_unchanged=True,native_executed=False,producer_executed=False,go_executed=False,git_executed=False,formal_acceptance=False,caller_refs=[pin(N/n) for n in ('prepare_w09_c19.actual_owned.py','run_w09_c19.actual_owned.py')]))
print(json.dumps(dict(status='SOURCE_ONLY',namespace=str(N),source_count=6),ensure_ascii=False))
