"""Pure IO finalization of the source preparation; no candidate imports."""
import ast,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
old=(ROOT/'prepare.py').read_bytes()
text=old.decode()
pairs=[
 ("OUT=Path(__file__).resolve().parent\nBASE=OUT.parent.parent", "OUT=Path(__file__).resolve().parent/'selected'\nOUT.mkdir(exist_ok=False)\nBASE=OUT.parent.parent.parent"),
 ("  if a!=b:raise Stop('Root authority mismatch: '+label)", "  if type(a) is not type(b) or json.dumps(a,sort_keys=True,allow_nan=False)!=json.dumps(b,sort_keys=True,allow_nan=False):raise Stop('Root authority mismatch: '+label)"),
 (" eq(invocation['actualargv'],request['argv'],'actual argv');eq(invocation['cwd'],request['cwd'],'actual cwd')", " eq(invocation['actualargv'],request['argv'],'actual argv');eq(invocation['cwd'],request['cwd'],'actual cwd')\n for key in ['stdout_ref','stderr_ref']:\n  verified_raw(invocation[key]);consumed.append(invocation[key])\n  if invocation[key] not in members:raise Stop('Unsealed actual registration raw')"),
 (" if len({r['original_path'].casefold() for r in canonical})!=4:raise Stop('Canonical original path collision')", " if len({r['original_path'].casefold() for r in canonical})!=4:raise Stop('Canonical original path collision')\n eq([r['original_path'] for r in canonical],binding['canonical_original_paths'],'actual canonical target paths')")
]
for a,b in pairs:
 if text.count(a)!=1:raise RuntimeError('Unique exact static refinement anchor required')
 text=text.replace(a,b,1)
ast.parse(text)
inverse=text
for a,b in reversed(pairs):inverse=inverse.replace(b,a,1)
if inverse.encode()!=old:raise RuntimeError('Refinement inverse drift')
with (ROOT/'prepare.selected.py').open('xb') as f:f.write(text.encode())
with (ROOT/'refinement-audit.json').open('x',encoding='utf-8') as f:json.dump({'original_sha256':hashlib.sha256(old).hexdigest(),'selected_builder_sha256':hashlib.sha256(text.encode()).hexdigest(),'edits':pairs,'whole_inverse':True,'AST':'PASS_STATIC_ONLY','candidate_execution':0},f,ensure_ascii=False,indent=2)
print('SOURCE_BUILDER_AST_AND_INVERSE_ONLY')
