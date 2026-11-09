import pathlib,hashlib,json
B=pathlib.Path(__file__).parent
W=pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025')
out=B/'MUTABLE-boot6-fence-snapshot';out.mkdir(exist_ok=False)
paths=['internal/recoveryboundary/contract.go','internal/recoveryboundary/boot_windows.go','ops/qualification_recovery_boundary/main_windows.go','ops/qualification_recovery_boundary/main_nonwindows.go','internal/recoveryboundary/boot_windows_test.go','ops/qualification_recovery_boundary/main_windows_test.go']
entries=[]
for rel in paths:
 raw=(W/rel).read_bytes(); p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 entries.append({'path':rel,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
(out/'snapshot.json').write_text(json.dumps({'status':'MUTABLE_PER_FILE_READ_NOT_ATOMIC_SOURCE_FREEZE','entries':entries},indent=2),encoding='utf-8')
print(json.dumps(entries,indent=2))
for rel,ranges in [('internal/recoveryboundary/contract.go',[(147,192)]),('internal/recoveryboundary/boot_windows.go',[(81,150),(182,249),(423,465),(508,585),(997,1027),(1136,1388)])]:
 lines=(out/rel).read_text(encoding='utf-8').splitlines()
 print(rel)
 for a,b in ranges:
  for n in range(a,min(b,len(lines))+1):print(f'{n}:{lines[n-1]}')
