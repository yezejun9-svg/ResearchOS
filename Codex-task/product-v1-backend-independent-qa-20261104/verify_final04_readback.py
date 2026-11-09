from pathlib import Path
import hashlib,json,datetime,difflib
R=Path(__file__).resolve().parent
A=R.parent/'product-v1-backend-author'
W=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-backend-20261104')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((R/'run-04/author/final-04/source-manifest.json').read_bytes())
previous=json.loads((R/'run-03/author/final-03/source-manifest.json').read_bytes())
old={v['path']:v['sha256'] for v in previous['pins']}
current={v['path']:v['sha256'] for v in m['pins']}
assert len(current)==18
for path,pin in current.items():
 assert sha(W/path)==pin and sha(R/'run-04/frozen-source'/path)==pin and sha(A/'final-04/source'/path)==pin,path
changes=[path for path,pin in current.items() if pin!=old[path]]
assert set(changes)=={'internal/domain/runtime_harness_windows.go','internal/domain/runtime_harness_windows_test.go'},changes
name='internal/domain/runtime_harness_windows.go'
before=(R/'run-03/frozen-source'/name).read_text(encoding='utf-8')
after=(R/'run-04/frozen-source'/name).read_text(encoding='utf-8')
start='func (c *RuntimeCoordinator) harnessUnknown('
end='func (c *RuntimeCoordinator) harnessTerminalEvent('
assert before[:before.index(start)]==after[:after.index(start)]
assert before[before.index(end):]==after[after.index(end):]
assert current['internal/domain/runtime_coordinator_windows.go']==old['internal/domain/runtime_coordinator_windows.go']
p=R/'run-04/no-drift.json';assert not p.exists()
p.write_text(json.dumps({'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':current,'all_18_author_snapshot_and_current_worktree_match':True,'changed_from_final03':changes,'only_production_change':'harnessUnknown body','old_mu_markUnknown_unchanged':True,'legacy_parser_compatibility_reusable':current['adapters/runtime/codex.go']==old['adapters/runtime/codex.go'],'formal_increment':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'no_drift':True,'sha256':sha(p),'changed_paths':changes}))
