import sys
sys.dont_write_bytecode=True
import json,hashlib,ast
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
N8=B/"integration_codex/native-temp-compile-unit-root-1791508539969/revision-list-manifest"
P=B/"integration_codex/attach-fixture-two-parent-sparse-root-source-1791516205000/revision-exact-paths"
CL=B/"native_retained_cleanup_context_revision_codex/cl-1a11e7f5205729390aaee9f47b28ce6"
CLR=B/"native_retained_cleanup_context_independent_review_codex/clr-20261009-source-review"
T=R/".local/worktrees/n12s-1791516889000";ISO=B/"integration_codex/native-cleanup-sparse-isolation-root-1791516889000"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
def transform(name,base,expected,replacements):
 raw=base.read_bytes();assert (pin(base)["sha256"],pin(base)["bytes"])==expected
 s=raw.decode("utf-8");changes=[]
 for old,new,count in replacements:
  assert s.count(old)==count,(name,old,s.count(old),count)
  s=s.replace(old,new);changes.append(dict(before=old,after=new,count=count))
 ast.parse(s,filename=name)
 inverse=s
 for c in reversed(changes):
  assert inverse.count(c["after"])==c["count"],"inverse count"
  inverse=inverse.replace(c["after"],c["before"])
 assert inverse.encode("utf-8")==raw
 with (O/name).open("xb") as f:f.write(s.encode("utf-8"))
 return dict(base_ref=pin(base),new_ref=pin(O/name),exact_inverse=True,sequential_replacements=changes)
pchanges=transform("prepare_native_cleanup_sparse.actual_owned.py",P/"prepare_attach_fixture_two_parent.actual_owned.py",("62fd1a7a3e947a4a922e4b36b31913ab215ed25e38abf708bba7105e74e93647",8806),[
 ("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/attach-fixture-two-parent-sparse-isolation-root-1791516205000",str(ISO).replace("\\","/"),1),
 ("D:/作品集/ResearchOS/research-os/.local/worktrees/t11s-1791516205000",str(T).replace("\\","/"),1)])
repls=[
 ('T=R/".local/worktrees/codex-w0599-native-temp-1791506570123"','T=R/".local/worktrees/n12s-1791516889000"',1),
 ('P=R/".local/worktrees/codex-w0599-native-ttl-c54ba9df088e45ea94adb56457af2979"','P=R/".local/worktrees/codex-w0599-native-temp-1791506570123"',1),
 ('A=B/"integration_codex/native-ttl-compile-root-458f017f3c294bb6"','A=B/"integration_codex/native-temp-compile-unit-root-1791508539969/revision-list-manifest"',1),
 ('V=B/"native_migration_broker_temp_revision_codex/9beca53ced874c93a6101f451eb33491"','V=B/"native_retained_cleanup_context_revision_codex/cl-1a11e7f5205729390aaee9f47b28ce6"',1),
 ('Z=B/"native_temp_independent_review_codex/20261009-01a11e22"','Z=B/"native_retained_cleanup_context_independent_review_codex/clr-20261009-source-review"',1),
 ('ISO=B/"integration_codex/native-temp-isolation-root-1791506570123"','ISO=B/"integration_codex/native-cleanup-sparse-isolation-root-1791516889000"',1),
 ('e9dab1b8ca436384733a256501aa21ca2a1b3429859a80368810cc65b741ed2b','def8d9e965e4a3c38fb6082c965ac59bfb199b8c4c986cde3063ac98f11bd269',1),
 ('c3f3e98bee9a3f2879b1cf07ca49927f9c894bed4534aaa38f2775d514bec301','675fd9ab068cf2403df5986ad75215ab2b73a210bf748953ee58fbcaabfe4e53',1),
 ('7ed8bc9380c2ef4a7acbd74c402213a43b072be6d2e810fad1d03cf865be6c0f','7e0b451fed4eeae20941c285721a8b8f982993fecd8651b4f46b41e6353ae6c6',1),
 ('5cf3fa351a1ce624d22e85440ced5d3b319a44caf44ba91a734dac86cbd36c98','2f8acd3e7bb5a9df58c26add65174f55884923ee47bf2a7da912c3b7f92db387',1),
 ('json.loads((Z/"HDF.json").read_bytes())["decision"]=="SOURCE_ACCEPTED_WITH_ROOT_EXECUTION_PREREQUISITES"','json.loads((Z/"HDF.json").read_bytes())["status"]=="SOURCE_ACCEPTED_PENDING_RESOURCE_PREREQUISITE_AND_ROOT_ACTUAL"',1),
 ('37f8fce8fd17225d60147f4b753b2dc946252cc87762ad1141dd8d89bd156bcc',''+pin(N8/"formatted.source-members.json")["sha256"],1),
 ('"e696dccc00a24e1a0eb0872327e351a6b92ac14ab7bea8692780f9f70aa8ef4d" and len(old_bytes)==29516','"972166b2744d1048dc747e8a5b4991cd0b06cbbdc8a523c90fef12e27e02e0e9" and len(old_bytes)==35845',1),
 ('"eaa745bb2ea461a875bda13bef2495e7a8fb3375446a687e15108021b883ae90" and len(new_bytes)==35845','"bbccac67b4143632160defb5ecf2c1697a062e448e793d8fbfed8070d3b68f73" and len(new_bytes)==38972',1),
 ('before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==361\nassert pin(canonical[0])["sha256"]=="27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845"',
  'before={p:p.read_bytes() for p in canonical}\nassert len(sys.argv)==6, "usage: ready_SHA ready_BYTES checkpoint_SHA checkpoint_BYTES checkpoint_REV"\ncp_sha,cp_bytes,cp_rev=sys.argv[3],int(sys.argv[4]),int(sys.argv[5])\nassert json.loads(before[canonical[0]])["revision"]==cp_rev and pin(canonical[0])["sha256"]==cp_sha and pin(canonical[0])["bytes"]==cp_bytes',1),
 ('checkpoint_revision=361','checkpoint_revision=cp_rev',1),
 ('scratch=R/".local/native-temp-compile-env-1791508539969-revision1"','scratch=R/".local/native-cleanup-compile-env-1791516889000"',1),
 ('unit_parents=("TestNativeHarnessBrokerIsolatedTempEnvironment","TestNativeHarnessBrokerTempBoundaryComparison")','unit_parents=("TestNativeHarnessBrokerIsolatedTempEnvironment","TestNativeHarnessBrokerTempBoundaryComparison","TestNativeHarnessCleanupReviewContext")',1),
 ('assert len(actions)==30 and sum("/" in n for n in actions)==28','assert len(actions)==35 and sum("/" in n for n in actions)==32',1),
 ('parent_count=2,leaf_count=28','parent_count=3,leaf_count=32',1),
 ('NATIVE_TEMP43_FOUR_PROGRAMS_TAGGED_TEST_AND_28_TEMP_UNITS_PASS_COMPONENT_ONLY_NATIVE_ACTUAL_PENDING','NATIVE_CLEANUP43_FOUR_PROGRAMS_TAGGED_TEST_AND32_LEAVES_PASS_COMPONENT_ONLY_NATIVE_ACTUAL_PENDING',1)]
vchanges=transform("validate_native_cleanup_compile_units.actual_owned.py",N8/"validate_native_temp_compile_units_revision.actual_owned.py",("ee8a0918c7a7689b066974b1f378db78cff34293f1ed67dc9ddd31942200298e",16535),repls)
# Check meaningful Source and test scope before Root can execute any driver.
mf=json.loads((CL/"MF.json").read_bytes());entries=mf["members"].items() if isinstance(mf["members"],dict) else [(v["relative_path"],v) for v in mf["members"]]
candidate=[v for k,v in entries if k.startswith("candidate-root/")]
assert len(candidate)==1 and candidate[0]["sha256"]=="bbccac67b4143632160defb5ecf2c1697a062e448e793d8fbfed8070d3b68f73"
old_src=json.loads((N8/"formatted.source-members.json").read_bytes());assert len(old_src)==43
assert pin(CLR/"HDF.json")["sha256"]=="7e0b451fed4eeae20941c285721a8b8f982993fecd8651b4f46b41e6353ae6c6"
proof=save("adaptation.provenance.json",dict(schema="researchos.root-n12-cleanup-compile-source.v1",changes=[pchanges,vchanges],base43_source_ref=pin(N8/"formatted.source-members.json"),base_actual_closed_ref=pin(N8/"validation.closed.json"),cleanup_source_handoff_ref=pin(CL/"HDF.json"),cleanup_source_manifest_ref=pin(CL/"MF.json"),cleanup_independent_ref=pin(CLR/"HDF.json"),cleanup_independent_manifest_ref=pin(CLR/"MF.json"),expected_source_count=43,changed_Source_members=1,unchanged_Source_members=42,expected_unit_parents=3,expected_leaves=32,expected_terminal_tests=35,owned_compile_jobs=8,owned_Git_jobs=6,worktree=str(T),isolation=str(ISO),new_program_namespace=str(R/".local/native-cleanup-compile-env-1791516889000/programs"),production_adoption=False,actual_ran=False,formal_acceptance=False,prerequisite="Before nativecase must adopt separately independently-reviewed controller1560/1570 revision; compilation and pure units do not qualify live retention"))
manifest=save("MF.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
h=save("HDF.json",dict(status="SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL",manifest_ref=manifest,provenance_ref=proof,source_count=43,formal_acceptance=False))
print(json.dumps(dict(handoff_ref=h,manifest_ref=manifest)),flush=True)

