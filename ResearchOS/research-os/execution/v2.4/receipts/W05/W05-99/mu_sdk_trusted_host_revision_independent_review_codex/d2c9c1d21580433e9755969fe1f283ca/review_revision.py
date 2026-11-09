from pathlib import Path, PureWindowsPath
import hashlib, json, difflib
O=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
P=R/"execution/v2.4/receipts/W05/W05-99"
S=P/"mu_sdk_trusted_qualification_host_source_revision_codex/797a5659dec64d55a16915d1aea6e46c"
OLD=P/"mu_sdk_trusted_qualification_host_source_codex/991a41da6cb146d9a5fae91c438f6d07"
PRIOR=P/"mu_sdk_trusted_host_independent_source_review_codex/a23894ca628e4e2c85ead05c283d73aa"
V9=P/"mu_model_sdk_real_trial_v9_source_codex/8c135404809b41a5a795574699bd0249"
def m(p,raw=None):
 if raw is None:raw=p.read_bytes()
 return dict(path=p.as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def put(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
mf=m(S/"manifest.json");assert (mf["sha256"],mf["bytes"])==("a86da829b9ac3e54140815bbc599d7e19735e838efa50c22d63ae71aea5ed653",11882)
man=json.loads((S/"manifest.json").read_bytes())
refs=man["source_files"]+man["current_source_evidence"]+man["derivation_evidence"]
previous=json.loads((PRIOR/"intake.json").read_bytes())
snapshots={}
def capture(p,ref=None):
 raw=p.read_bytes();x=m(p,raw)
 if ref is not None:assert x["sha256"]==ref["sha256"] and x["bytes"]==ref["bytes"],p
 dest=O/"snapshots"/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 x["snapshot"]=dest.relative_to(O).as_posix();snapshots[x["path"]]=x
 return x
for ref in refs:capture(Path(ref["path"]),ref)
# Reuse prior semantic analysis and revalidate its exact evidence without repeating that review.
for ref in previous["files"]:capture(Path(ref["path"]),ref)
for name in ["HANDOFF.md","REVIEW.md","manifest.json","intake.json"]:capture(PRIOR/name)
capture(S/"manifest.json",mf)
capture(V9/"mu_sdk_trial.v9.proposed.py",dict(sha256="cbfa40e8376ad284df6521b43d64380488017ee41c7411a339dae853ed77a98f",bytes=90096))
capture(V9/"handoff.json",dict(sha256="33696532a57d47cd8bd7f644c85dd2eee91e96dfec7c073e696f37441d44babb",bytes=3136))
for name in ["forward.v8-to-v9.diff","manifest.json"]:capture(V9/name)
main=(S/"main.go").read_text(encoding="utf-8")
prep=(S/"prepare.go").read_text(encoding="utf-8")
exe=(S/"execute.go").read_text(encoding="utf-8")
v9=(V9/"mu_sdk_trial.v9.proposed.py").read_text(encoding="utf-8")
changed=["main.go","prepare.go","execute.go","profile.template.json"]
for filename,before,after in [("revision.old-to-new.diff",OLD,S),("revision.new-to-old.diff",S,OLD)]:
 delta="".join(line for n in changed for line in difflib.unified_diff((before/n).read_text(encoding="utf-8").splitlines(True),(after/n).read_text(encoding="utf-8").splitlines(True),fromfile=("a/" if before==OLD else "b/")+n,tofile=("b/" if after==S else "a/")+n))
 assert (S/filename).read_text(encoding="utf-8")==delta
for n in ["hostapi.go","seed.template.json","go.authority.template.json"]:assert (S/n).read_bytes()==(OLD/n).read_bytes()
# Compare untouched semantic bodies exactly, without importing any candidate.
def fn(text,name,nextname):
 return text.split("func "+name,1)[1].split("func "+nextname,1)[0]
oldexe=(OLD/"execute.go").read_text(encoding="utf-8")
assert fn(exe,"verifyGOEvidence(","sealedProfile(")==fn(oldexe,"verifyGOEvidence(","sealedProfile(")
assert "raw,err:=verifiedBytes(p)" in fn(exe,"readPinnedObject(","verifyGOEvidence(")
for field in ["RootGrant","OnceMarker","OuterJobContract","HostJobProbe"]:assert "readPinnedObject(a."+field+")" in exe
checks={
"R1_same_buffer_hash_length_decode":'raw,err:=os.ReadFile(p.Path)' in exe and 'int64(len(raw))!=p.Bytes' in exe and 'hashBytes(raw)' in exe and 'return domain.Decode(raw)' in fn(exe,"readPinnedObject(","verifyGOEvidence("),
"R1_all_four_semantic_bodies_preserved":True,
"R2_same_buffer_seed_to_profile":all("s."+x+"Raw" in main for x in ["Profile","Node","Bundle"]) and "json.Unmarshal(s.ProfileRaw,&profile)" in prep and "node,bundle:=s.NodeRaw,s.BundleRaw" in prep and all("os.ReadFile(s."+x+")" not in prep for x in ["ProfileFile","NodeExecutable","BundleFile"]),
"R3_exact_workspace_child":'filepath.Clean(filepath.Join(s.DataRoot,"workspace"))' in main and 'pathInside(filepath.Join(s.RepoRoot,".local"),s.DataRoot)' in main,
"R3_vault_disjoint":'pathInside(s.ReadOnlyVaultDir,s.DataRoot) || pathInside(s.DataRoot,s.ReadOnlyVaultDir)' in main,
"R4_frozen_policy":'policy["max_calls"]=1;policy["max_read_bytes"]=4096;policy["max_write_bytes"]=4096' in prep and 'policy["write_paths"]=domain.Empty()' in prep and 'policy.get("write_paths") == []' in v9,
"S1_prepare_after_lease":prep.index("openEnvironment(ctx,s)")<prep.index("os.Stat(statePath(s))")<prep.index("saveState(s,v)"),
"limited_diff_exact_both_directions":True,
"unchanged_nonfix_files":True,
}
assert all(checks.values())
# Independent expectation models only: these do not execute Go and are not runtime tests.
def checked(raw,pin):
 if len(raw)!=pin["bytes"] or hashlib.sha256(raw).hexdigest()!=pin["sha256"]:raise ValueError("pin")
 return json.loads(raw)
raw=b'{"approved":true}';pin=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
assert checked(raw,pin)["approved"] is True
negatives={}
for label,value in [("changed_same_length",b'{"approved":null}'),("changed_length",b'{"approved":false}'),("truncated",raw[:-1])]:
 try:checked(value,pin)
 except ValueError:negatives[label]="REJECTED_BY_REVIEWER_MODEL"
 else:raise AssertionError(label)
repo=PureWindowsPath("D:/repo");data=repo/".local"/"trial";workspace=data/"workspace";vault=PureWindowsPath("D:/private/vault")
assert data.is_relative_to(repo/".local") and workspace.is_relative_to(data) and workspace!=data
assert not data.is_relative_to(vault) and not vault.is_relative_to(data)
policy=json.loads((S/"profile.template.json").read_bytes())["tool_policy"]
assert (policy["max_calls"],policy["read_paths"],policy["write_paths"],policy["max_read_bytes"],policy["max_write_bytes"])==(1,["evidence.txt"],[],4096,4096)
put("intake.json",dict(status="PASS_PIN_IDENTITY",source_manifest=mf,new_manifest_refs_checked=len(refs),prior_refs_rechecked=len(previous["files"]),files=list(snapshots.values())))
put("controls.json",dict(status="PASS_SOURCE_FIX_SCOPE",source_checks=checks,expectation_model_negative_controls=negatives,scope="Text inspection plus independent reviewer expectation models only. No candidate import, Go execution, native action, DB action, or provider call.",schema_limit_advisory='prepare.go:91 still declares limit maximum 65536; Main enforces policy 4096.'))
print(json.dumps(dict(status="PASS_PIN_AND_SOURCE_FIX_CONTROLS",new_refs=len(refs),prior_refs=len(previous["files"]),unique_snapshots=len(snapshots),static_checks=len(checks),negative_model_controls=len(negatives))))

