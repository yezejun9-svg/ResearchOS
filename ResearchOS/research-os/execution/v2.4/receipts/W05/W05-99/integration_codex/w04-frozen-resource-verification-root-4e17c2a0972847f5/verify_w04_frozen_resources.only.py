import sys, pathlib, json, hashlib, importlib.util
sys.dont_write_bytecode = True
R = pathlib.Path(r"D:/作品集/ResearchOS/research-os")
B = R / "execution/v2.4/receipts/W05/W05-99"
NS = pathlib.Path(__file__).resolve().parent
K = pathlib.Path(r"D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4")
F = B / "queue_executor_codex/frozen-package-input"
G = B / "source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
EXPECTED = "4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964"
PYTHON = pathlib.Path(r"C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe")
def ref(path):
    path = path.resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
def write_new(name, value):
    with (NS/name).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, indent=2)
        stream.write("\n")
    return ref(NS/name)
assert pathlib.Path(sys.executable).resolve() == PYTHON.resolve()
assert ref(PYTHON)["sha256"] == "cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
assert ref(G)["sha256"] == "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert ref(K/"PACKAGE_MANIFEST.json")["sha256"] == EXPECTED
assert ref(F/"PACKAGE_MANIFEST.json")["sha256"] == EXPECTED
manifest = json.loads((K/"PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
pairs = []
for item in manifest["files"]:
    relative = pathlib.PurePosixPath(item["path"])
    assert not relative.is_absolute() and ".." not in relative.parts
    for base in (K,F):
        path = base.joinpath(*relative.parts)
        pin = ref(path)
        assert pin["sha256"] == item["sha256"] and pin["bytes"] == item["size_bytes"], str(path)
        pairs.append(pin)
refs = {p["path"].casefold():p for p in pairs}
for path in (K/"PACKAGE_MANIFEST.json",F/"PACKAGE_MANIFEST.json",G,PYTHON,pathlib.Path(__file__)):
    refs[str(path.resolve()).casefold()] = ref(path)
# CopyFS reads the complete existing snapshot, so include all actual files.
snapshot_files = sorted(p for p in F.rglob("*") if p.is_file())
for path in snapshot_files:
    refs[str(path.resolve()).casefold()] = ref(path)
before = [ref(R/"execution/v2.4"/n) for n in
          ("checkpoint.json","path_ownership.json","step_state.json","commands.json")]
spec = importlib.util.spec_from_file_location("root_w04_resource_guard", G)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
guard = mod.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
error = None
cleanup = None
try:
    guard.acquire(list(refs.values()))
    for pin in refs.values():
        assert ref(pathlib.Path(pin["path"])) == pin
finally:
    cleanup = guard.close()
write_new("source-guard.cleanup.actual.json",cleanup)
assert cleanup["closed"] and not cleanup["errors"]
after = [ref(pathlib.Path(p["path"])) for p in before]
assert before == after
receipt = {
    "schema":"researchos.root-w04-frozen-resource-verification.v1",
    "status":"EXISTING_FROZEN_PACKAGE_CLOSURE_VERIFIED_RESOURCE_ONLY",
    "manifest_sha256":EXPECTED,
    "package_input":str(F.resolve()),
    "manifest_member_count":len(manifest["files"]),
    "snapshot_file_count":len(snapshot_files),
    "guarded_reference_count":len(refs),
    "python_ref":ref(PYTHON),
    "required_environment":{"RESEARCHOS_W04_PACKAGE_INPUT":str(F.resolve()),
                            "PATH_python_directory":str(PYTHON.parent.resolve())},
    "source_refs":list(refs.values()),
    "canonical_unchanged_refs":before,
    "go_or_native_cases_executed":0,
    "model_requests":0,
    "formal_acceptance":False}
write_new("resource-closure.actual.json",receipt)
print(json.dumps({k:receipt[k] for k in
      ("status","manifest_member_count","snapshot_file_count","guarded_reference_count","formal_acceptance")}))
