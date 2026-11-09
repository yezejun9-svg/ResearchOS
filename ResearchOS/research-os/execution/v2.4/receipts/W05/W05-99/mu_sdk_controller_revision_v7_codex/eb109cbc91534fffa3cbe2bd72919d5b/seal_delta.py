"""One-shot metadata seal for the C7 four-field Source-only correction."""
from pathlib import Path
import difflib
import hashlib
import json
import os
import subprocess
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
C6=BASE/"mu_sdk_controller_revision_v6_codex/c309fe6cec1c400ea212065fbd484e73"
REVIEW=BASE/"mu_sdk_controller_v6_observer_v4_independent_review_codex/0f31d8d476354698b0e1e72859265612"
O4=BASE/"mu_sdk_job_observer_revision_v4_codex/cbb82ea19cf84175baf61427251b983c"
ORIGIN706=BASE/"mu_sdk_c6_author_control_failure_origin_codex/723ec91a795a400393a09266887da115"

def pin(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def write(name,raw):
    path=HERE/name
    with path.open("xb") as out:out.write(raw)
    return pin(path)

def jwrite(name,value):
    return write(name,(json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))

def diff(a,b,old,new):
    return "".join(difflib.unified_diff(
        a.decode("utf-8").splitlines(keepends=True),
        b.decode("utf-8").splitlines(keepends=True),
        fromfile=old,tofile=new)).encode("utf-8")

assert HERE.name=="eb109cbc91534fffa3cbe2bd72919d5b"
assert all(not (HERE/name).exists() for name in
           ("handoff.json","manifest.json","delta-controls.stdout.raw"))
helper_names=("canonical_transactions.py","owned_job_hooks.py","phase_worker.py",
              "job_deadline_watchdog.py","job_probe_worker.py",
              "held_job_cleanup_producer.py")
for name in helper_names:
    assert (HERE/name).read_bytes()==(C6/name).read_bytes(),name
for name in ("controller.py","delta_controls.py"):
    compile((HERE/name).read_bytes(),str(HERE/name),"exec")

inputs={
    "c6_handoff":pin(C6/"handoff.json"),
    "c6_manifest":pin(C6/"manifest.json"),
    "c6_o4_independent_review_handoff":pin(REVIEW/"handoff.json"),
    "c6_o4_independent_review_findings":pin(REVIEW/"findings.json"),
    "o4_handoff":pin(O4/"handoff.json"),
    "first_failure_706_origin_handoff":pin(ORIGIN706/"handoff.json")}
assert json.loads((REVIEW/"handoff.json").read_bytes())["decision"]=="REQUEST_CHANGES"
findings=json.loads((REVIEW/"findings.json").read_bytes())["findings"]
assert len(findings)==1 and findings[0]["id"]=="C6-O4-R01"
sources={
    "controller":pin(HERE/"controller.py"),
    "canonical_transactions":pin(HERE/"canonical_transactions.py"),
    "owned_job_hooks":pin(HERE/"owned_job_hooks.py"),
    "phase_worker":pin(HERE/"phase_worker.py"),
    "job_watchdog":pin(HERE/"job_deadline_watchdog.py"),
    "job_probe_worker":pin(HERE/"job_probe_worker.py"),
    "held_job_cleanup_producer":pin(HERE/"held_job_cleanup_producer.py"),
    "o4_observer":pin(O4/"mu_sdk_job_observer.v4.proposed.py")}
source_pins=jwrite("source-pins.json",{
    "schema":"researchos.mu-sdk-controller-c7-source-pins.v1",
    "inputs":inputs,"sources":sources,
    "unmodified_helper_bytes":list(helper_names)})

old=(C6/"controller.py").read_bytes();new=(HERE/"controller.py").read_bytes()
forward=write("controller.forward.diff",diff(old,new,"C6/controller.py","C7/controller.py"))
inverse=write("controller.inverse.diff",diff(new,old,"C7/controller.py","C6/controller.py"))

argv=[sys.executable,str(HERE/"delta_controls.py")]
run=subprocess.run(argv,cwd=str(HERE),capture_output=True,check=False,
                   env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
stdout=write("delta-controls.stdout.raw",run.stdout)
stderr=write("delta-controls.stderr.raw",run.stderr)
tool_io=jwrite("delta-controls.original-tool-io.json",{
    "schema":"researchos.mu-sdk-controller-c7-delta-tool-io.v1",
    "argv":argv,"cwd":str(HERE),"exit_code":run.returncode,
    "stdout_ref":stdout,"stderr_ref":stderr,
    "scope":"AST_AND_SOURCE_PIN_METADATA_ONLY"})
assert run.returncode==0 and run.stderr==b""
controls=json.loads(run.stdout)
assert controls["status"]=="PASS" and len(controls["checks"])==5
assert all(controls[k]==0 for k in
           ("real_winapi_calls","native_process_starts","threads_started",
            "provider_calls","canonical_writes"))

report=write("report.md",("""# C7 narrow Source correction

C6/O4 independent review returned REQUEST_CHANGES with one P1,
C6-O4-R01: the actual before_resume context lacked four reviewed Source pins.
C7 adds exactly canonical_transactions_source, job_watchdog_source,
source_guard_source and base_owned_process_source to that actual context Dict.

The delta control extracts the real Dict AST, evaluates it with C7's current
hard pins, and passes it through O4's extracted 11-role provenance helper.
Removing exactly those four text lines restores C6 controller text and AST.
All six helper Source files are byte-identical to C6; HERE-local hard paths
relocate to this C7 namespace with unchanged content hashes.

This packet is Source-only. It has not imported O4 as a candidate, launched
Windows processes, created threads, queried WinAPI, contacted providers,
written Canonical state, or self-issued READY. C6's first pure-control failure
remains ordinal 706 and is pinned separately.
""").encode("utf-8"))

members=[pin(p) for p in sorted(HERE.iterdir(),key=lambda p:p.name)
         if p.is_file() and p.name not in ("manifest.json","handoff.json")]
manifest=jwrite("manifest.json",{
    "schema":"researchos.mu-sdk-controller-c7-source-manifest.v1",
    "actor":"codex:/root/live_resource_lookup",
    "decision":"SOURCE_PROPOSED_UNEXECUTED",
    "directory":str(HERE),
    "derived_from_c6":inputs["c6_manifest"],
    "independent_c6_o4_findings":inputs["c6_o4_independent_review_findings"],
    "members":members,
    "native_calls":0,"threads_started":0,"provider_calls":0,
    "canonical_writes":0})
handoff=jwrite("handoff.json",{
    "schema":"researchos.mu-sdk-controller-c7-source-handoff.v1",
    "actor":"codex:/root/live_resource_lookup",
    "decision":"SOURCE_PROPOSED_UNEXECUTED",
    "controller_source_ref":sources["controller"],
    "manifest_ref":manifest,
    "source_pins_ref":source_pins,
    "forward_diff_ref":forward,"inverse_diff_ref":inverse,
    "delta_controls_original_tool_io_ref":tool_io,
    "delta_checks":controls["checks"],
    "independent_c6_o4_review_ref":inputs["c6_o4_independent_review_handoff"],
    "first_failure_706_origin_ref":inputs["first_failure_706_origin_handoff"],
    "report_ref":report,
    "formal_acceptance":False,
    "open":["Independent C7/O4 exact-tuple review",
            "Root same-PID caller and actual Windows lifecycle validation",
            "No product qualification or provider permission from this packet"]})
print(json.dumps({"handoff_ref":handoff,"manifest_ref":manifest,
                  "controller_source_ref":sources["controller"],
                  "delta_checks":controls["checks"]},ensure_ascii=True))
