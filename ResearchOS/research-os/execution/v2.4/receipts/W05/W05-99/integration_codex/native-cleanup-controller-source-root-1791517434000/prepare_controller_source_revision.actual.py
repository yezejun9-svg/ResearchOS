import sys
sys.dont_write_bytecode=True
import hashlib,json,ast
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
BASE=B/"integration_codex/native-broker4-controller-config-root-1791513411000/prepare_native_broker4_controller_public_config.actual.py"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
raw=BASE.read_bytes();assert (pin(BASE)["sha256"],len(raw))==("4e4a698a91a3d03dc98d8cd6efa2770e7a7207078acfa7ba3af40d385c3d39f7",11133)
s=raw.decode("utf-8");repls=[
 ("integration_codex/native-temp-compile-unit-root-1791508539969/revision-list-manifest","integration_codex/native-cleanup-compile-source-root-1791516889000",1),
 ("native_migration_controller_temp_env_revision_codex/e6a4d23ff0a84a6d9c2905181d97c2e4","native_controller_retained_window_revision_codex/ctl4-1a11e7f5205729390aaee9f47b28ce6",1),
 ("native_migration_controller_temp_env_independent_review_codex/b6af18c92e674ec19d8cd0cd0721a3f4","native_ctl4_n12_independent_review_codex/cn-20261009-source-review",1),
 ("a1f53e223f47c5d8ecdb7edc5f94fec0bcc36beae9774d16ad9d0002b6ef638a","e7538c580d2e07217512e036e00272b3be94cb11551ace6885cc46316a67b3b3",1),
 ("089068f4ffe780c6553e40ddb79fee868f033bb2ba9aa9b872d066b371c65163","9b335e2099575e3737b038ba212315bf4d4f1e2311614961d20bf8770cc578cc",1),
 ("6869d577ec8429c4f217bc429d4350ef24eab7831f08ee874052a2cdc8652e32","14a6d3df02728fcc2b675658d4c2247a66f07d271826fd7bbe54c0ac7ad2de03",1),
 ("e60c15edbe089e4da258d32ea2d5a43d678ea0fd9fbd5836878f6b455c54835c","32ddc6d38de6708304127045f738adac3959d9c225b0aec35e8666dacdd51412",1),
 ("ab048b3bbbf2dfee080c6e4fa83f34706726f27987fd3b872d40cb463b2d7b22","122de2bf58c17ec8a05a8fd7bcd3d79580c7bf3a8576e6740004a0d1241ca8a2",1),
 ('json.loads((Z/"HDF.json").read_bytes())["decision"]=="SOURCE_ACCEPTED_PENDING_ROOT_FRESH_CONTEXT_AND_ACTUAL"','json.loads((Z/"HDF.json").read_bytes())["CTL4_decision"]=="SOURCE_ACCEPTED_PENDING_FRESH_CONFIG_AND_ROOT_ACTUAL"',1),
 ("9ecbf95ad3c89757479f611742a081d31aff0bbffbd1277aa1d10e0e82d52f5d","cb2459bafde88bf99ab33bd34212fd2986e93e287fab1ad940437be9e3531d67",1),
 ("NATIVE_TEMP43_FOUR_PROGRAMS_TAGGED_TEST_AND_28_TEMP_UNITS_PASS_COMPONENT_ONLY_NATIVE_ACTUAL_PENDING","NATIVE_CLEANUP43_FOUR_PROGRAMS_TAGGED_TEST_AND32_LEAVES_PASS_COMPONENT_ONLY_NATIVE_ACTUAL_PENDING",1),
 ('actual["unit_pass_count"]==30','actual["unit_pass_count"]==35',1),
 ('assert before[0]["sha256"]=="84c970d86ab96b78a7621595839005f68a440fc9a540d3b619500c7cbed2669b"',
  'assert len(sys.argv)==4, "usage: checkpoint_SHA checkpoint_BYTES checkpoint_REV"\nassert before[0]["sha256"]==sys.argv[1] and before[0]["bytes"]==int(sys.argv[2]) and json.loads(canonical[0].read_bytes())["revision"]==int(sys.argv[3])',1),
 ('hc["CaseID"]="t10b4c239054ab67"','hc["CaseID"]="t12cl149d6f49321"',1),
 ('"native-broker4-controller-env-1791513411000"','"native-cleanup-controller-env-1791517434000"',1),
 ("FRESH_CTL3_BROKER4_FIXED_PROOF_TEMP_CONTEXT_VALIDATED_NO_NATIVE_LAUNCH","FRESH_CTL4_CLEANUP_BROKER4_PROOF_CONTEXT_VALIDATED_NO_NATIVE_LAUNCH",1)]
changes=[]
for old,new,count in repls:
 assert s.count(old)==count,(old,s.count(old),count);s=s.replace(old,new);changes.append(dict(before=old,after=new,count=count))
# Bind reviewed per-phase helper Sources and their independent final decision.
anchor='bootstrap_refs += [plain(p) for p in original.runtime_resource_paths()]\n'
extra='''phase_source=B/"root_native_concrete_phase_helpers_revision_codex/nhr1-1a11e7f5205729390aaee9f47b28ce6"
phase_review=B/"root_native_concrete_helpers_independent_review_codex/nhr1r-20261009-source-review"
assert plain(phase_source/"HDF.json")["sha256"]=="151045d795d4ac73a7e00f74a290f051583f11582017c608ac8a526c6051b328"
assert plain(phase_source/"MF.json")["sha256"]=="f545b924574565a8141bc5a42761cee6f2b1efca5b08b3dea418f0a30a0ec5c5"
assert plain(phase_review/"HDF.json")["sha256"]=="4e4702c5f27e365b8bfc16d73226bd5a5f9fb53a70e9064b4659d44aaf357c6b"
assert plain(phase_review/"MF.json")["sha256"]=="e116cb0ec170d1248c03747df76ae38ed9ef408a61f0a450c2aa521f349c3fc7"
for d in (phase_source,phase_review):
 bootstrap_refs += [plain(d/"HDF.json"),plain(d/"MF.json")]
 m=json.loads((d/"MF.json").read_bytes())["members"];m=m.values() if isinstance(m,dict) else m
 bootstrap_refs += [verify(v) for v in m]
'''
assert s.count(anchor)==1;s=s.replace(anchor,anchor+extra);changes.append(dict(before=anchor,after=anchor+extra,count=1))
ast.parse(s)
inverse=s
for v in reversed(changes):
 assert inverse.count(v["after"])==v["count"];inverse=inverse.replace(v["after"],v["before"])
assert inverse.encode()==raw
with (O/"prepare_native_cleanup_controller_public_config.actual.py").open("xb") as f:f.write(s.encode("utf-8"))
proof=save("adaptation.provenance.json",dict(schema="researchos.root-c12-controller-public-config-source.v1",base_ref=pin(BASE),new_ref=pin(O/"prepare_native_cleanup_controller_public_config.actual.py"),exact_inverse=True,changes=changes,case_id="t12cl149d6f49321",new_binary_namespace="D:/作品集/ResearchOS/research-os/.local/native-cleanup-compile-env-1791516889000/programs",expected_ControllerSource_SHA="e7538c580d2e07217512e036e00272b3be94cb11551ace6885cc46316a67b3b3",expected_43_Source_count=43,actual_unit_terminal_count=35,retention_context_cleanup_seconds=240,inner_deadline_seconds=1560,controller_loop_seconds=1570,Go_global_timeout_seconds=1500,main_context_seconds=1200,grant_seconds=240,Root_outer_seconds=1800,native_cases_executed=0,no_automatic_sign_or_approval=True,formal_acceptance=False))
mf=save("MF.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
hd=save("HDF.json",dict(status="ROOT_PUBLIC_CONFIG_BUILDER_SOURCE_PENDING_INDEPENDENT_REVIEW_AND_ROOT_PREPARE",manifest_ref=mf,proof_ref=proof,native_cases_executed=0,formal_acceptance=False))
print(json.dumps(dict(handoff_ref=hd,manifest_ref=mf)),flush=True)

