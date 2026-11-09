"""Keep v1 immutable; restore exact registrar guards and hold Main dependencies."""
from pathlib import Path
import hashlib
S=Path(__file__).resolve().parent;p=S/'append_w09_owner.source.root.py';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='bf391cd9531988a02b4fbd0f7b43d80f33ae719e0f7bf7e39b0f1f1040d034df'
replacements=[
 (b'from pathlib import Path\n',b'from pathlib import Path,PureWindowsPath\n'),
 (b'per_file_cap=64*1024*1024,total_cap=256*1024*1024',b'per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024'),
 (b"runtime.actual_audit(req['approval_actual_audit_ref'],'codex:/root/backup_regression_resources',req['approval_ref']['sha256'])",b"audit_refs=runtime.actual_audit(req['approval_actual_audit_ref'],'codex:/root/backup_regression_resources',req['approval_ref']['sha256'])"),
 (b"nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('atomic_state','writer_lock')];need(len(nodes)==2,'TWO_EXACT_BASE_FUNCTIONS',len(nodes))",b"names={'atomic_state','writer_lock','path_in','exclusive','need','sha'};nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in names) or (isinstance(n,ast.ClassDef) and n.name=='Refusal')];need(len(nodes)==7,'SEVEN_EXACT_BASE_DEFINITIONS',len(nodes))"),
 (b'env=dict(Path=Path,contextmanager=contextmanager,os=os,uuid=uuid,need=need,path_in=path_in,exclusive=exclusive,sha=sha,STATE=',b'env=dict(Path=Path,PureWindowsPath=PureWindowsPath,hashlib=hashlib,contextmanager=contextmanager,os=os,uuid=uuid,STATE='),
 (b'refs=[request_ref,',b"refs=[pin(Path(__file__).resolve()),pin(S/'append_w09_owner.source.root.py'),request_ref,"),
 (b"refs=list({str(checked(ref)[0]):pin(checked(ref)[0]) for ref in refs}.values());out.mkdir()",b"refs.extend(audit_refs)\n+ for evidence in owner['evidence']:refs.append(dict(evidence,path='execution/v2.4/'+evidence['path']))\n+ for path,digest in check['dependency_snapshot']['files'].items():\n+  if Path(path)!=V/'step_state.json':refs.append(dict(path=path,sha256=digest))\n+ normalized={}\n+ for ref in refs:\n+  path,body=checked(ref);wanted=dict(path=str(path),sha256=ref['sha256'],bytes=len(body))\n+  need(Path(path)!=V/'step_state.json','EXACT_SS_EXCLUSION',path)\n+  need(str(path) not in normalized or normalized[str(path)]==wanted,'CONFLICTING_EXPECTED_PIN',path);normalized[str(path)]=wanted\n+ refs=list(normalized.values());out.mkdir()".replace(b'\n+',b'\n')),
 (b"guard.acquire(refs)\n  with env['writer_lock'](R):",b"guard.acquire(refs)\n  checked(req['approval_ref']);checked(req['prospective_owner_ref']);checked(req['precheck_result_ref'])\n  runtime.actual_audit(req['approval_actual_audit_ref'],'codex:/root/backup_regression_resources',req['approval_ref']['sha256'])\n  with env['writer_lock'](R):")
]
fixed=raw
for old,new in replacements:assert fixed.count(old)==1;fixed=fixed.replace(old,new)
inverse=fixed
for old,new in reversed(replacements):assert inverse.count(new)==1;inverse=inverse.replace(new,old)
assert inverse==raw
exec(compile(fixed,str(Path(__file__).resolve()),'exec'),dict(__name__='__main__',__file__=str(Path(__file__).resolve())))
