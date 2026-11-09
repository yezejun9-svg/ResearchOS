import ast,hashlib,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent
P=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v7_source_codex/73cdde53fe0e4da2ae29fb6898d4b7ef/mu_sdk_trial.v7.final.proposed.py")
raw=P.read_bytes();sha=hashlib.sha256(raw).hexdigest();snap=O/('source-'+sha+'.raw')
if not snap.exists():
 with snap.open('xb') as f:f.write(raw)
else:assert snap.read_bytes()==raw
src=raw.decode('utf-8');tree=ast.parse(src);ls=src.splitlines()
groups={'authority':{'pin_file','canonical_dir','consumed_file_state','parse_pinned_json','os_job_membership','phase_basis','authority_binding'},'entry':{'validate_public_route','validate_input','cli_environment','guard_deadline','consume_once','main'},'execution':{'authorized_child','after_child_consumed_states','command_once','exact_qualification','wait_qualification','fact_refs'}}
which=sys.argv[1]
print(json.dumps({'source_path':str(P),'sha256':sha,'bytes':len(raw),'snapshot':str(snap),'group':which},ensure_ascii=False))
if which=='authority':
 for i in range(1,53):print(str(i)+':'+ls[i-1])
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in groups[which]:
  print('\nFUNCTION '+n.name)
  for i in range(n.lineno,n.end_lineno+1):print(str(i)+':'+ls[i-1])
assert P.read_bytes()==raw
with (O/('read-'+which+'.json')).open('xb') as f:f.write(json.dumps({'path':str(P),'sha256':sha,'bytes':len(raw),'snapshot':str(snap)},ensure_ascii=False,indent=2).encode()+b'\n')

