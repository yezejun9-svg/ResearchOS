from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;A=O.parents[1]/'product_coding_client_repair_v2_codex/20261012-current-chat'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A/'supplement-01.json')=='4beb38bd06d9b819f553dc407dd3730116eb2b7b0c81ffb67f5e5fdbcefe974e'
s=json.loads((A/'supplement-01.json').read_text(encoding='utf-8')); files=sorted(p for p in (A/'raw/c-bound-all-desktop-cases').rglob('*') if p.is_file())
rows=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in files]
for p,row in zip(files,rows):assert sha(Path(s['bound_case_root'])/p.relative_to(A/'raw/c-bound-all-desktop-cases'))==row['sha256']
assert len(rows)==s['case_files'] and sum(r['bytes'] for r in rows)==s['case_bytes']
assert hashlib.sha256(''.join(f"{r['path']}\t{r['sha256']}\t{r['bytes']}\n" for r in rows).encode()).hexdigest()==s['case_census_sha256']
for suffix,key in [('invocation.json','run_invocation_sha256'),('stdout','stdout_sha256'),('stderr','stderr_sha256')]:assert sha(A/('raw/c-bound-all-desktop.'+suffix))==s[key]
(O/'supplement-verification.json').write_text(json.dumps(dict(passed=True,author_tests=211,independently_rerun=False,verified_case_files=len(rows),verified_case_bytes=s['case_bytes'],supplement_sha256=sha(A/'supplement-01.json'),files=rows),indent=2))
print('Supplement verified: 1663 source-bound author case files, 211 author tests; not independently rerun.')

