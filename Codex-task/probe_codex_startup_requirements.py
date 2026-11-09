import hashlib,json,subprocess
from pathlib import Path
EXE='C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
OUT=Path(__file__).resolve().parent/'product-v1-codex-startup-requirements-01.json'
assert not OUT.exists(),'Inspect prior probe before repeating'
p=subprocess.run([EXE,'app-server','--print-startup-config'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
value=json.loads(p.stdout) if p.returncode==0 else None
requirements=value.get('configRequirements') if isinstance(value,dict) else None
if requirements is None and isinstance(value,dict):requirements=value.get('config_requirements')
features=None
if isinstance(requirements,dict):
 f=requirements.get('featureRequirements',requirements.get('feature_requirements'))
 if isinstance(f,dict): features={k:v for k,v in f.items() if isinstance(v,bool)}
result=dict(status='METADATA_OBSERVATION_ONLY',exit_code=p.returncode,
 version=value.get('appServerVersion',value.get('app_server_version')) if isinstance(value,dict) else None,
 public_top_keys=list(value) if isinstance(value,dict) else None,
 requirements_present=requirements is not None,
 requirement_field_names=list(requirements) if isinstance(requirements,dict) else None,
 simple_feature_requirements=features,
 stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_bytes=len(p.stderr),
 raw_json_persisted=False,model_requests_sent=0,thread_started=False,
 limitation='Print-startup metadata is not full exec effective config, legacy config, filesystem enforcement or native task qualification.')
OUT.write_bytes((json.dumps(result,indent=2)+'\n').encode('utf8'))
print(json.dumps(result))
