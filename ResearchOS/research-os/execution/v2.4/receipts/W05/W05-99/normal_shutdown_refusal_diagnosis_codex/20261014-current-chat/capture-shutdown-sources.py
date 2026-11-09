import pathlib, subprocess, hashlib, json, datetime
E=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/normal_shutdown_refusal_diagnosis_codex/20261014-current-chat')
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os'); OLD='b955c8665281193d5cbf90a146f936c9212c7940'; UI='5ddc0abb8c6d95e9ca071a4eb41a7e12b8559456'
S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014'); P=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-status-combined-5ddc0abb-20261014')
checks=[]
for name in ['apps/control/main.go','apps/control/drain_windows.go','internal/host/desktop_management_windows.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_drain_windows.go','internal/domain/runtime_qualification_confirmation_windows.go','internal/domain/client_runtime_coding_windows.go']:
 raw=subprocess.check_output(['git','-C',str(ROOT),'show',OLD+':'+name]); out=E/'old-core-source'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
 equal=raw==(S/name).read_bytes(); checks.append({'path':name,'commit':OLD,'sha256':hashlib.sha256(raw).hexdigest(),'read_current_combined_source_same_bytes':equal,'evidence':str(out.relative_to(E))})
for name in ['apps/desktop/main/lib/desktop-management.js','apps/desktop/main/main.js']:
 raw=(P/name).read_bytes(); expected=subprocess.check_output(['git','-C',str(ROOT),'show',UI+':'+name]);assert raw==expected
 out=E/'installed-desktop-source'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
 checks.append({'path':name,'commit':UI,'sha256':hashlib.sha256(raw).hexdigest(),'installed_package_matches_commit':True,'evidence':str(out.relative_to(E))})
(E/'shutdown-source-binding.json').write_text(json.dumps(checks,ensure_ascii=True,indent=2),encoding='utf8')
print(json.dumps(checks))
