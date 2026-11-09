from pathlib import Path
import hashlib,json,os,subprocess,sys
R=Path(__file__).resolve().parent;S=R.parents[1]/'product-v1-real-electron-harness-prepare-revision-04';OLD=R.parent/'revision03/source'
PS=Path('C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PINS={'FROZEN.json':'7d54eac9c5c37a35a16fbd0f115df630575f74d77908dda51b0c1ebcb5147686','MANIFEST.json':'9c75f8c6df5c195f1bd11755fb66ecb1fc813b1964afdfabda0c132fc2827bcf','real-electron-flow.mjs':'68458e0ff59d091d2481356f19bec7d557a3dc9924ee3f91cc8c47e77b1d450b','choose-owned-folder.ps1':'8fa1b220c6e8624bc969bc149616d3838e521b999d7e9d13d703eabd576f1f82'}
def save(name,v):
 p=R/name;assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def prepare():
 for name,pin in PINS.items():assert sha(S/name)==pin,name
 m=json.loads((S/'MANIFEST.json').read_bytes())
 for row in m['files']:assert sha(S/row['path'])==row['sha256'],row['path']
 assert (S/'real-electron-flow.mjs').read_bytes()==(OLD/'real-electron-flow.mjs').read_bytes()
 new=(S/'choose-owned-folder.ps1').read_bytes().decode('utf-8')
 a=new.index('function Convert-NativeDeadlineUtc(');b=new.index('function Convert-UiaAbsolutePath(',a)
 fixed=new[:a]+new[b:]
 fixed=fixed.replace('# These functions are pure string/evidence predicates.','# These three functions are pure string/evidence predicates.')
 fixed=fixed.replace('$identity = Get-Content -LiteralPath $identityFile -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String','$identity = Get-Content -LiteralPath $identityFile -Raw -Encoding UTF8 | ConvertFrom-Json')
 fixed=fixed.replace('$actionDeadline = Convert-NativeDeadlineUtc $identity.action_deadline_utc','$actionDeadline = [DateTimeOffset]::Parse($identity.action_deadline_utc).UtcDateTime')
 assert fixed.encode('utf-8')==(OLD/'choose-owned-folder.ps1').read_bytes(),'Non-date delta'
 assert sha(PS)=='362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139'
 dest=R/'source';dest.mkdir(exist_ok=False)
 for name in ['FROZEN.json','MANIFEST.json','choose-owned-folder.ps1','real-electron-flow.mjs','helper.diff','DIAGNOSTICS.json','date-reproduction/REPRO.json']:
  q=dest/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((S/name).read_bytes())
 save('inputs.json',{'pins':PINS,'manifest_files':len(m['files']),'runner_byte_same_as_reviewed03':True,'reverse_date_changes_reconstructs03_exact_bytes':True,'powershell':str(PS),'powershell_sha256':sha(PS),'reused_review_sha256':'97538836b6104c82c076d9d189eb0b4a485cebeab8d86f67e2a17b0364d582cf','formal_increment':0})
 print(json.dumps({'prepared':True,'manifest_files':len(m['files']),'date_only_exact_byte_delta':True}))
def run():
 env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if k in os.environ};env['PATH']=str(PS.parent)
 command=[str(PS),'-NoLogo','-NoProfile','-NonInteractive','-File',str(R/'independent-deadline.ps1')]
 save('date.command.json',{'argv':command,'environment':env,'controller_sha256':sha(Path(__file__)),'test_sha256':sha(R/'independent-deadline.ps1'),'source_sha256':PINS['choose-owned-folder.ps1'],'powershell_sha256':sha(PS),'no_policy_override':True,'only_AST_pure_function':True})
 with (R/'date.stdout.raw').open('xb') as out,(R/'date.stderr.raw').open('xb') as err:code=subprocess.run(command,cwd=R,env=env,stdout=out,stderr=err,timeout=25).returncode
 for name,pin in PINS.items():assert sha(S/name)==pin,name
 save('date.result.json',{'exit_code':code,'stdout_sha256':sha(R/'date.stdout.raw'),'stderr_sha256':sha(R/'date.stderr.raw'),'frozen_source_no_drift':True,'formal_increment':0});print(json.dumps({'exit_code':code,'no_drift':True}));return code
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='date':sys.exit(run())
