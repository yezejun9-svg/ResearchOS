from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent;B=O.parent.parent
anchors=[
('integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller.public.config.json','5f956dd27e9818b5e8ffa043d04317ea37d028c5d9dac3ffb241c22a2b0549c5',1095627),
('integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller-runtime/review-snapshot-fixture-retained-7fa2cdeac67644fa8426ac16e2d2edce.json','addfebdcba1f3798fadd2b2487959d1c59675d77022572556e7a12285da706c4',5057),
('integration_codex/native-positive-ttl-root-api-a4a432c97c744d98/inspection-positive.json','38c3799bf9d0dc29af4971f2e467138b7dd7841adb515dfa33a717d760a2d27b',98629),
('integration_codex/native-positive-ttl-serve-root-052db2c7da5645f6/serve-outer.closed.json','d2d784b18f3af3801d6825b4bd3f894af21c3f38913f95d5b6e875762168aba9',1065047),
('integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller-runtime/controller.closed.json','be57a1205ee93b43d89ff8010829b647e49acd1b370abd90bc899870aeecc3d6',1145897),
('integration_codex/native-positive-ttl-failed-root-release-1791505647184/root-concrete-release.approval.json','a248d35b060fe482daea6dce0638699535c22eb4506348158d8dff9139475d5e',925),
('integration_codex/native-positive-ttl-failed-root-release-1791505647184/original-tool-io.json','3ca20bff142ac6fa9c945991269068f3d74ffd39c91da02e279077ca0405b82f',76361),
('integration_codex/native-positive-ttl-failed-root-release-1791505647184/failure-origin.835.json','c28570436e23f8ad4594895bcfcd35ee93f5cf13e5ad6c369687560e5a259c8a',868),
('integration_codex/native-positive-ttl-failed-root-release-1791505647184/failure-origin.836.json','190e41b78fb39ebabdb12329685f2f4e40322581aa3b1b69d85caf709aa8f295',3780),
('integration_codex/native-positive-ttl-failed-root-release-1791505647184/failure-origin.837.json','fee81c9d666f3d149e83395241136ba47dd588b606326925a6b0fa8048306e98',95182)]
rows=[]
for rel,sha,size in anchors:
 raw=(B/rel).read_bytes();rows.append(dict(path=str(B/rel),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),expected_sha256=sha,expected_bytes=size,match=hashlib.sha256(raw).hexdigest()==sha and len(raw)==size))
(O/'root-delivered-anchor-checks.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
guards=json.loads((O/'guard-closure-checks.json').read_text(encoding='utf-8'))
t=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-ttl-c54ba9df088e45ea94adb56457af2979')
sources=[(t/'internal/domain/backup_prepared_abandonment_upgrade.go',370,405),(t/'internal/domain/native_migration_authority_harness_windows_test.go',315,350)]
excerpts=[]
for p,a,b in sources:
 lines=p.read_text(encoding='utf-8').splitlines()
 excerpts.append(dict(path=str(p),start=a,end=min(b,len(lines)),text='\n'.join(str(i+1)+': '+lines[i] for i in range(a-1,min(b,len(lines))))))
(O/'failure-source-excerpts.json').write_text(json.dumps(excerpts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(anchor_count=len(rows),mismatches=[r for r in rows if not r['match']],guards=[{k:v for k,v in r.items() if k!='invalid_entries'} for r in guards],excerpts=excerpts),ensure_ascii=False))

