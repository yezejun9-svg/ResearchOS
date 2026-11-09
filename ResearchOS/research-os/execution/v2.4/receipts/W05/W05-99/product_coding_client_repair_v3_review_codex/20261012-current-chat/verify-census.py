from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;A=O.parents[1]/'product_coding_client_repair_v3_codex/20261012-current-chat';raw=A/'raw'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((A/'manifest.json').read_text(encoding='utf-8'))
rows=[[p.relative_to(raw).as_posix(),p.stat().st_size,sha(p)] for p in sorted((p for p in raw.rglob('*') if p.is_file()),key=lambda p:p.relative_to(raw).as_posix())]
digest=hashlib.sha256(json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
assert digest==m['raw_census_sha256'] and len(rows)==m['raw_files'] and sum(row[1] for row in rows)==m['raw_bytes']
(O/'raw-census-verification.json').write_text(json.dumps(dict(passed=True,author_manifest_sha256=sha(A/'manifest.json'),census_sha256=digest,files=len(rows),bytes=sum(row[1] for row in rows),algorithm="Sort exact raw-relative POSIX paths lexically. Compact UTF-8 JSON array of [path,bytes,sha256], ensure_ascii=False,separators=(',',':'), no trailing newline.",prior_legacy_algorithm_mismatch_resolved=True,rows=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,files=len(rows),bytes=sum(row[1] for row in rows),census_sha256=digest)))

