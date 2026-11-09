import sys,json,hashlib
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
old=B/"integration_codex/native-temp-controller-config-root-1791508950616/prepare_native_temp_controller_public_config.actual.py"
raw=old.read_bytes()
extra=b'''BP=B/"native_python_broker_temp_env_revision_codex/7bc2467624af477a8d55e0595ec4a7c2"
BR=B/"native_python_broker_temp_env_independent_review_codex/9e4f389d093d4ea58eb5ec06e102876d"
PU=B/"integration_codex/python-broker4-public-units-root-1791512710000/revision-explicit-binary-handles"
'''
before=b'ctl=V/"root_native_migration_controller.py"\n'
assert raw.count(before)==1;raw=raw.replace(before,before+extra)
raw=raw.replace(b'"27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845"',b'"84c970d86ab96b78a7621595839005f68a440fc9a540d3b619500c7cbed2669b"')
raw=raw.replace(b'"t8b41a23c5804b67"',b'"t10b4c239054ab67"')
raw=raw.replace(b'"native-temp-controller-env-1791508950616"',b'"native-broker4-controller-env-1791513411000"')
before=b'for m in list(sys.modules.values()):'
insert=b'''assert plain(BP/"root_only_native_broker.py")["sha256"]=="70b8eba1de168849d041488ac9268da60fd2ae8a059cc9518e9dc93d0cd4b87c"
assert plain(BP/"HDF.json")["sha256"]=="ed0f388870aef974f9577e6d5146637d5a1a77ce6b22c57e989227654de05824"
assert plain(BP/"MF.json")["sha256"]=="deab5d3bb0fc512c37808a4dcd9b66d370dcd0c1ae14b84e1949fcfdb915ebdc"
assert plain(BR/"HDF.json")["sha256"]=="7c0ad0872da573a5a6948b2c6e7d55a438e57e3cc2ba65b70329e9cea6dd2518"
assert plain(BR/"MF.json")["sha256"]=="8edd94cc087bf2f042fcec9a892f04687eb0898dc67c683e2fe710f85cbf58bb"
assert plain(PU/"validation.closed.json")["sha256"]=="9f9d17cfdcea867bf03bd1404ec1bd8b1824229add2a2b03d107c0ce2cb6c318"
unit_results=json.loads((PU/"units.results.json").read_bytes());assert unit_results["pass_count"]==17 and unit_results["fail_count"]==unit_results["skip_count"]==0
for d in (BP,BR):
 bootstrap_refs += [plain(d/"HDF.json"),plain(d/"MF.json")]
 members=json.loads((d/"MF.json").read_bytes())["members"];members=members.values() if isinstance(members,dict) else members
 bootstrap_refs += [verify(v) for v in members]
bootstrap_refs += [plain(BP/"root_only_native_broker.py"),plain(PU/"validation.closed.json"),plain(PU/"units.results.json"),plain(PU/"units.invocation.json"),plain(PU/"input-source-guard.cleanup.actual.json"),plain(PU/"runtime-source-guard.cleanup.actual.json")]
'''
assert raw.count(before)==1;raw=raw.replace(before,insert+before)
before=b' hc_ref=save("native-harness.public.config.json",hc)'
insert=b''' broker_source=verify(plain(BP/"root_only_native_broker.py"));hc["BrokerSource"]={"role":"broker-source",**broker_source,"sha256":"sha256:"+broker_source["sha256"]}
 assert set(hc["BrokerSource"])=={"role","path","sha256","bytes"}
'''
assert raw.count(before)==1;raw=raw.replace(before,insert+before)
raw=raw.replace(b'"FRESH_CTL3_FIXED_PROOF_TEMP_PUBLIC_CONTEXT_VALIDATED_NO_NATIVE_LAUNCH"',b'"FRESH_CTL3_BROKER4_FIXED_PROOF_TEMP_CONTEXT_VALIDATED_NO_NATIVE_LAUNCH"')
raw=raw.replace(b'source_review_refs=[ref(Z/"HDF.json"),ref(Z/"MF.json")]',b'source_review_refs=[ref(Z/"HDF.json"),ref(Z/"MF.json"),ref(BR/"HDF.json"),ref(BR/"MF.json")],broker_source_ref=ref(BP/"root_only_native_broker.py"),broker_public17_units_ref=ref(PU/"validation.closed.json")')
p=O/"prepare_native_broker4_controller_public_config.actual.py";compile(raw,str(p),"exec")
with p.open("xb") as f:f.write(raw)
def pin(p):
 r=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
with (O/"configuration-builder.adaptation.provenance.json").open("xb") as f:f.write((json.dumps(dict(base_source_ref=pin(old),new_source_ref=pin(p),changes=["fresh exact CP362 context","fresh CaseID/public scratch","HC BrokerSource role broker-source exact new pin","new Source/review MF closure","17 actual public boundary proof"],Go_program_binaries_and_compiler_inventory_unchanged=True,TTL_and_signing_rules_unchanged=True,native_started=False,formal_acceptance=False),indent=2)+"\n").encode())
print("ROOT_PYTHON_EXIT=0")


