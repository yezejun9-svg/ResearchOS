import ast, hashlib, json, re, difflib
from pathlib import Path
N=Path(__file__).resolve().parent
R=N.parents[6]
assert R.name=="research-os"
B=R/"execution/v2.4/receipts/W05/W05-99"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"].removeprefix("sha256:") and actual["bytes"]==ref["bytes"],str(ref)
 return actual
def save(name,obj):
 p=N/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def rawsave(name,raw):
 p=N/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(raw)
 return pin(p)
def vals(ref):
 verify(ref);m=json.loads(Path(ref["path"]).read_bytes())["members"];return list(m.values()) if isinstance(m,dict) else m
ip=B/"integration_codex/current-attach-q5-leg2-isolation-root-1791509207371/prepare_current_composition_isolation.actual_owned.py"
tp=B/"integration_codex/current-attach-q5-leg2-targeted-root-1791510290800/validate_current_attach_q5_legacy.actual_owned.py"
cp=tp.parent/"source.integration.choice.json"
known=[(ip,"5563b98d14c1c9e0c8ec045b1857e13a6959ea5bf2fb33e70a1d8e43b2932a10",6798),(tp,"37aaba0dce22ba4397882ba886bf9063af891f58aabd0a4ebdfec659028527bc",15696),(cp,"8fee24f844dbb06581ea15b7f8665844ce4335fc93a0532d096433a810cea343",5610)]
refs=[verify(dict(path=str(p),sha256=h,bytes=z)) for p,h,z in known]
choice=json.loads(cp.read_bytes())
oldchoice=json.loads(cp.read_bytes())
af=B/"session_attach_contract_fixture_revision_codex/af-1a11e3e93437fe089b15fdf6a164840"
ar=B/"session_attach_contract_fixture_independent_review_codex/afr-20261009-attach-fixture-source-review"
afrefs=[verify(dict(path=str(p),sha256=h,bytes=z)) for p,h,z in [(af/"HDF.json","e28f505265ff2dc2e0b95e8060dd535c888fd8665fc0e70fd2c60389c2798947",7391),(af/"MF.json","e4431fc8c311ecae055e180c5dbf0b7c2a255d484745a116812936a483e51823",11861),(ar/"HDF.json","d69d12f0519944ccfebf462857cc8788f94071a5c3a930e008a9abda25ee8e8b",2151),(ar/"MF.json","fb6b79fce15c85865e78b2e5c784e0dd9658f1baae930a9aac045c740bea49a6",80404)]]
assert json.loads((ar/"HDF.json").read_bytes())["status"]=="SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL"
choice["schema"]="researchos.root-attach-fixture-current-two-parent-integration-choice.v1"
choice["source_components"].append(dict(component="AF",candidate_namespace=af.relative_to(B).as_posix(),source_handoff=afrefs[0],source_manifest=afrefs[1],independent_handoff=afrefs[2],independent_manifest=afrefs[3]))
del choice["include_old25_parents"]
selected=["TestClientAttachSettledAcquisitionCompletesAndReplays","TestClientAttachPreservesStaleAndBindingGates"]
choice.update(exact_parent_names=selected,base25_parent_sources_preserved_not_selected=True,all_other_parent_sources_preserved_not_executed_or_newly_accepted=True,expected_source_count=58,base_driver_refs=list(refs))
for item in choice["source_components"]:
 for key in ("source_handoff","source_manifest","independent_handoff","independent_manifest"):refs.append(verify(item[key]))
 for key in ("source_manifest","independent_manifest"):refs.extend(verify(r) for r in vals(item[key]))
oldactual=Path(choice["base_current49"]);oa=pin(oldactual)
assert oa["sha256"]=="d2fd6c15fcdb727fff91aa7bd3c53275230ebc42bd2017a544ff8f17becfb113"
refs.append(oa);base=json.loads(oldactual.read_bytes());pr=verify(base["formatted_source_ref"]);refs.append(pr)
P=R/".local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1"
sources={}
for ref in json.loads(Path(pr["path"]).read_bytes()):
 ref=verify(ref);refs.append(ref);sources[Path(ref["path"]).relative_to(P).as_posix()]=ref
assert len(sources)==49
oldmap=None
for item in choice["source_components"]:
 candidate=B/item["candidate_namespace"]/"candidate-root"
 for ref in vals(item["source_manifest"]):
  path=Path(ref["path"]).resolve()
  if path.is_relative_to(candidate):sources[path.relative_to(candidate).as_posix()]=verify(ref)
 if item["component"]=="EXPIRED":oldmap=dict(sources)
assert len(sources)==58
assert {k for k in sources if sources[k]!=oldmap[k]}=={"internal/domain/client_protocol_attach_contract_windows_test.go"}
parents=set(base["exact_25_parent_names"])
for rel,ref in sources.items():
 if rel.endswith("_test.go"):parents.update(re.findall(r"^func (Test[A-Za-z0-9_]+)\(",Path(ref["path"]).read_text(encoding="utf-8"),re.MULTILINE))
assert set(selected).issubset(parents)
choice["source_preserved_parent_names"]=sorted(parents)
choice["source_preserved_parent_count"]=len(parents)
choice["source_preserved_nonselected_parent_count"]=len(parents-set(selected))
refs=list({r["path"].casefold():r for r in refs}.values())
save("sourceguard.initial.json",dict(method="exact_read_and_hash_source_only",refs=refs))
rawsave("base/prepare.py",ip.read_bytes());rawsave("base/validate.py",tp.read_bytes());rawsave("base/choice.json",cp.read_bytes())
choice_ref=save("source.integration.choice.json",choice)
suffix="t11-1a11e7f5205729390aaee9f47b28ce6"
T=R/(".local/worktrees/codex-w0599-attach-fixture-current-two-parent-"+suffix)
ISO=B/("integration_codex/attach-fixture-current-two-parent-isolation-root-"+suffix)
OUT=B/("integration_codex/attach-fixture-current-two-parent-targeted-root-"+suffix)
SCRATCH=R/(".local/attach-fixture-current-two-parent-run-env-"+suffix)
for p in (T,ISO,OUT,SCRATCH):assert not p.exists()
replacements={}
def replace(text,old,new,key):
 assert text.count(old)==1,(key,old,text.count(old));replacements.setdefault(key,[]).append(dict(old=old,new=new));return text.replace(old,new,1)
prep=ip.read_text(encoding="utf-8")
prep=replace(prep,'O=Path(__file__).resolve().parent','O=Path('+repr(ISO.as_posix())+')',"prepare")
prep=replace(prep,'D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371',T.as_posix(),"prepare")
preold='before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==361\nassert pin(canonical[0])["sha256"]=="27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845"\nsave("canonical.pre-run.exact.json",dict(refs=[pin(p) for p in canonical],revision=361,formal_acceptance=False))'
prenew='before={p:p.read_bytes() for p in canonical}\nassert len(sys.argv)==4, "usage: prepare.py CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION"\ncheckpoint_sha,checkpoint_bytes,checkpoint_revision=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])\nassert pin(canonical[0])["sha256"]==checkpoint_sha and pin(canonical[0])["bytes"]==checkpoint_bytes\nassert json.loads(before[canonical[0]])["revision"]==checkpoint_revision\nassert not O.exists();O.mkdir()\nsave("canonical.pre-run.exact.json",dict(refs=[pin(p) for p in canonical],revision=checkpoint_revision,formal_acceptance=False))'
prep=replace(prep,preold,prenew,"prepare")
prep=replace(prep,'"prepared-abandonment-toolenv-"','"attach-fixture-current-two-parent-isolation-toolenv-"',"prepare")
driver=tp.read_text(encoding="utf-8")
driver=replace(driver,'O=Path(__file__).resolve().parent','O=Path('+repr(OUT.as_posix())+')',"validate")
driver=replace(driver,'D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371',T.as_posix(),"validate")
driver=replace(driver,'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/current-attach-q5-leg2-isolation-root-1791509207371',ISO.as_posix(),"validate")
driver=replace(driver,'choice_path=O/"source.integration.choice.json"','assert len(sys.argv)==8, "usage: validate.py CHOICE_SHA256 CHOICE_BYTES CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION ISOLATION_READY_SHA256 ISOLATION_READY_BYTES"\nchoice_path=Path(__file__).resolve().parent/"source.integration.choice.json"',"validate")
driver=replace(driver,'"researchos.root-current-attach-q5-legacy-integration-choice.v1"','"researchos.root-attach-fixture-current-two-parent-integration-choice.v1"',"validate")
driver=replace(driver,'sources={};input_refs=[verify(choice_ref),pin(__file__),pin(ISO/"isolation.ready.json")]','isolation_ref=verify({"path":str(ISO/"isolation.ready.json"),"sha256":sys.argv[6],"bytes":int(sys.argv[7])})\nisolation=json.loads(Path(isolation_ref["path"]).read_bytes())\nassert isolation["status"]=="DETACHED_CANDIDATE_WORKTREE_READY_NO_SOURCE_OVERLAY"\nassert Path(isolation["worktree_root"]).resolve()==T and Path(isolation["repository_root"]).resolve()==R\nassert isolation["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and isolation["all_owned_jobs_closed"] is True\nassert isolation["source_overlay"] is False and isolation["Main_canonical_unchanged"] is True if "Main_canonical_unchanged" in isolation else isolation["main_canonical_unchanged"] is True\nsources={};input_refs=[verify(choice_ref),pin(__file__),isolation_ref]+[verify(ref) for ref in choice["base_driver_refs"]]','validate')
driver=replace(driver,' input_refs.extend(verify(ref) for ref in members(item["source_manifest"]))',' input_refs.extend(verify(ref) for ref in members(item["source_manifest"]))\n input_refs.extend(verify(ref) for ref in members(item["independent_manifest"]))',"validate")
old='assert pin(ISO/"isolation.ready.json")["sha256"]=="b85d5bd711bc3fe23f8a092a5aa2c33a12a6825dcbb60a55d979f784e2dad4af"\nassert pin(ISO/"isolation.ready.json")["bytes"]==3340\nassert new_tests and set(old_actual["exact_25_parent_names"]).issubset(new_tests)'
new='assert len(sources)==58 and choice["expected_source_count"]==58\nassert new_tests and set(old_actual["exact_25_parent_names"]).issubset(new_tests)\npreserved_parent_sources=set(new_tests)\nassert preserved_parent_sources==set(choice["source_preserved_parent_names"])\nnew_tests=set(choice["exact_parent_names"])\nassert new_tests=='+repr(set(selected))+'\nassert new_tests.issubset(preserved_parent_sources)'
driver=replace(driver,old,new,"validate")
old='before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==361\nassert pin(canonical[0])["sha256"]=="27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845"\ncanonical_pre_run_ref=save("canonical.pre-run.exact.json",dict(refs=[pin(p) for p in canonical],revision=361,formal_acceptance=False))'
new='before={p:p.read_bytes() for p in canonical}\ncheckpoint_sha,checkpoint_bytes,checkpoint_revision=sys.argv[3],int(sys.argv[4]),int(sys.argv[5])\nassert pin(canonical[0])["sha256"]==checkpoint_sha and pin(canonical[0])["bytes"]==checkpoint_bytes\nassert json.loads(before[canonical[0]])["revision"]==checkpoint_revision\nassert not O.exists();O.mkdir()\ncanonical_pre_run_ref=save("canonical.pre-run.exact.json",dict(refs=[pin(p) for p in canonical],revision=checkpoint_revision,formal_acceptance=False))'
driver=replace(driver,old,new,"validate")
driver=replace(driver,'R/".local/current-attach-q5-leg2-run-env-1791510290800"','Path('+repr(SCRATCH.as_posix())+')',"validate")
driver=replace(driver,'base25_parents_retained=True','base25_parent_sources_preserved_not_execution_claim=True,preserved_parent_source_names=sorted(preserved_parent_sources),nonselected_parent_sources=sorted(preserved_parent_sources-new_tests),nonselected_parents_executed_or_newly_accepted=False,ordinary_history20_full_release_program_rehearsal_authority="BLOCKED"',"validate")
driver=replace(driver,'programs/current-attach-q5-leg2.test.exe','programs/attach-fixture-current-two-parent.test.exe',"validate")
# One label used both invocation and original stdout read, replaced as one exact bounded region.
driver=replace(driver,'result=invoke("current-attach-q5-leg2-parent-jsonl",','result=invoke("attach-fixture-current-two-parent-jsonl",',"validate")
driver=replace(driver,'(O/"current-attach-q5-leg2-parent-jsonl.stdout.raw")','(O/"attach-fixture-current-two-parent-jsonl.stdout.raw")',"validate")
driver=replace(driver,'CURRENT_ATTACH_Q5_LEGACY_EXPIRED_TARGET_SCOPE_PASSED_COMPONENT_ONLY_FULL_SCOPE_PENDING','ATTACH_FIXTURE_TWO_PARENT_TARGET_SCOPE_PASSED_COMPONENT_ONLY_FULL_SCOPE_BLOCKED',"validate")
driver=replace(driver,'FAILED_CURRENT_ATTACH_Q5_LEGACY_EXPIRED_COMPILE_OR_TARGET_EXECUTION_CLOSED','FAILED_ATTACH_FIXTURE_TWO_PARENT_COMPILE_OR_TARGET_EXECUTION_CLOSED',"validate")
# Verify exact inverse before writing either runnable artifact.
for key,text,original in (("prepare",prep,ip.read_text(encoding="utf-8")),("validate",driver,tp.read_text(encoding="utf-8"))):
 ast.parse(text)
 inverse=text
 for item in reversed(replacements[key]):
  assert inverse.count(item["new"])==1
  inverse=inverse.replace(item["new"],item["old"],1)
 assert inverse==original
 rawsave(key+"_attach_fixture_two_parent.actual_owned.py",text.encode())
 rawsave(key+".patch","".join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile="base/"+key,tofile="candidate/"+key)).encode())
save("source-replacements.json",replacements)
# Whole independent safety-critical AST functions and execution tail remain exact.
oldtree=ast.parse(tp.read_text(encoding="utf-8"));newtree=ast.parse(driver)
fn=lambda t,n:ast.dump(next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n),include_attributes=False)
for name in ("pin","verify","save","module","members","unique","invoke","success"):assert fn(oldtree,name)==fn(newtree,name),name
assert 'for guard,name in ((binary_guard,"binary"),(compiler_guard,"compiler"),(candidate_guard,"candidate"),(runtime_guard,"runtime"),(input_guard,"input")):' in driver
assert 'assert len(tracked_lines)==13 and sum(line.startswith(" D ") for line in tracked_lines)==11' in prep
assert 'selector="^("+("|".join(sorted(new_tests)))+")$"' in driver
assert "base25_parents_retained" not in driver and "==361" not in driver and "==361" not in prep
assert choice["source_components"][:4]==oldchoice["source_components"]
save("static-preservation.json",dict(source_only=True,python_AST_parse=True,exact_inverse=True,safety_functions_exact=True,five_guard_finally_exact=True,compiler_inventory_and_owned_invocation_preserved=True,base49_retained=True,source_count=len(sources),only_AF_overrides_one_member=True,preserved_parent_count=len(parents),selected_parents=selected,nonselected_parent_count=len(parents-set(selected)),nonselected_executed=False,old_four_components_exact=True,canonical_pins_explicit=True,isolation_ready_pin_explicit=True,actual_Git_Go_SQL_native_model=False))
save("composition.source-members.json",sources)
save("execution-contract.json",dict(status="SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL",worktree=str(T),isolation_output=str(ISO),target_output=str(OUT),scratch=str(SCRATCH),prepare_args=["CHECKPOINT_SHA256","CHECKPOINT_BYTES","CHECKPOINT_REVISION"],validate_args=["CHOICE_SHA256","CHOICE_BYTES","CHECKPOINT_SHA256","CHECKPOINT_BYTES","CHECKPOINT_REVISION","ISOLATION_READY_SHA256","ISOLATION_READY_BYTES"],choice_ref=choice_ref,selected_parents=selected,Root_actual_owned_git_jobs=5,actual_ran=False,ordinary_history20_full_release_program_rehearsal_authority="BLOCKED",formal_acceptance=False))
assert all(verify(ref)==ref for ref in refs)
save("sourceguard.final.json",dict(method="exact_read_and_hash_source_only",all_unchanged=True,refs=refs,canonical_not_read_or_written=True,future_actual_paths_not_created=True))
print(json.dumps(dict(status="SOURCE_PYTHON_COMPLETE",source_count=len(sources),preserved_parents=len(parents),selected_parents=selected,refs=[pin(N/"prepare_attach_fixture_two_parent.actual_owned.py"),pin(N/"validate_attach_fixture_two_parent.actual_owned.py"),choice_ref],actual_Git_Go_SQL_native_model=False)))

