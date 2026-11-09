import hashlib,json,re,subprocess
from pathlib import Path
EXE='C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
OUT=Path(__file__).resolve().parent/'product-v1-codex-config-observation-01.json'
assert not OUT.exists(), 'Inspect prior observation before repeating'
base=['-c','features.hooks=false','-c','features.plugins=false','-c','features.remote_plugin=false','-c','features.skill_mcp_dependency_install=false']
def run(args):return subprocess.run([EXE,*args],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
first=run([*base,'mcp','list','--json']);assert first.returncode==0
names=[r['name'] for r in json.loads(first.stdout)]
safe=all(isinstance(n,str) and re.fullmatch('[A-Za-z0-9_-]{1,255}',n) for n in names)
assert safe,'Unexpected server key syntax; no unsafe argv constructed'
disable=[]
for name in names:disable.extend(['-c','mcp_servers.'+name+'.enabled=false'])
second=run([*base,*disable,'mcp','list','--json'])
rows=json.loads(second.stdout) if second.returncode==0 else []
error=second.stderr.decode('utf-8',errors='replace')
for name in sorted(names,key=len,reverse=True):error=error.replace(name,'[SERVER_NAME]')
error=re.sub(r'(?i)(bearer\s+|sk-)[A-Za-z0-9._~+/=-]+','[REDACTED]',error)
result=dict(kind='CLI_METADATA_ONLY_NOT_EXEC_RUNTIME_OR_MODEL_QUALIFICATION',version='0.166.0',
 initial_count=len(names),override_count=len(names),verification_exit=second.returncode,entries=len(rows),
 enabled_count=sum(row.get('enabled') is True for row in rows),unknown_enabled_count=sum(not isinstance(row.get('enabled'),bool) for row in rows),
 raw_mcp_or_names_persisted=False,stdout_sha256=hashlib.sha256(second.stdout).hexdigest(),
 error_sanitized=error[:300] if second.returncode else None,model_requests_sent=0,
 limitation='This command loads ordinary config. It does not prove exec --ignore-user-config behavior, managed policy, project mutation races or runtime enforcement.')
OUT.write_bytes((json.dumps(result,indent=2)+'\n').encode('utf-8'))
print(json.dumps(result))
