from pathlib import Path
import json,hashlib,subprocess
r=Path(r"D:\作品集\ResearchOS\research-os")
scope=r/"execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp517-retry02/owned-core-stop-r3-independent-review-scope.json"
print("scope_sha",hashlib.sha256(scope.read_bytes()).hexdigest())
s=json.loads(scope.read_text(encoding="utf-8"))
for item in s["inputs"]:
 p=r/item["path"]; actual=hashlib.sha256(p.read_bytes()).hexdigest(); print(item["path"],actual,actual==item["sha256"]); assert actual==item["sha256"]
for args in (["status","--porcelain"],["rev-parse","HEAD","HEAD^{tree}"],["diff","--name-only",s["base"],s["candidate"]]):
 p=subprocess.run(["git",*args],capture_output=True);print(p.stdout.decode(),p.stderr.decode(),"native_exit",p.returncode);assert p.returncode==0
for name in ["internal/ownedcorestop/proof_windows.go","internal/ownedcorestop/journal_windows.go","internal/ownedcorestop/journal_windows_test.go","internal/ownedcorestop/proof_windows_test.go","internal/ownedcorestop/stop_windows.go","ops/supervisor/owned_core_handle_windows.go","ops/owned_core_stop/main_windows.go"]:
 print("FILE",name)
 for i,l in enumerate(Path(name).read_text(encoding="utf-8").splitlines(),1): print(f"{i}: {l}")
