from pathlib import Path
import hashlib,json,os,subprocess,sys
R=Path(__file__).resolve().parent
S=R.parent.parent/'product-v1-real-electron-harness-prepare-revision-02'
NODE=Path('C:/nvm4w/nodejs/node.exe')
PS=Path('C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
PINS={'FROZEN.json':'2abb3cda92212fd63dbe3d07d3e587c3c742b90650185f7bb04e400d3f78cd7a','MANIFEST.json':'2be6749a36eecfe2688c1187d75b0864bce94ab5b338408d99f37a4bac267862','real-electron-flow.mjs':'638c574c6ee3944b9b6ca955fd6f163d5efeb0663499164783e9b847bb5e8792','choose-owned-folder.ps1':'b5a826fab09c149f8affce7385c4d45efeb5ddc124a438fbb0677ee3f33bc38e'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,v):
 p=R/name;assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def prepare():
 for name,pin in PINS.items():assert sha(S/name)==pin,name
 manifest=json.loads((S/'MANIFEST.json').read_bytes())
 for item in manifest['files']:assert sha(S/item['path'])==item['sha256'],item['path']
 assert sha(NODE)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
 assert sha(PS)=='362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139'
 target=R/'source';target.mkdir(exist_ok=False)
 for name in ['FROZEN.json','MANIFEST.json','real-electron-flow.mjs','choose-owned-folder.ps1','preparation-purechecks.mjs','path-evidence-purechecks.ps1','DIAGNOSTICS.json','scope.template.json']:(target/name).write_bytes((S/name).read_bytes())
 # Reuse only the AST extraction + pure assertion helpers, not author's cases.
 before=(target/'path-evidence-purechecks.ps1').read_text(encoding='utf-8').split("$expected = ")[0]
 cases=r'''
$expected='C:\Users\synthetic\owned\workspace'
Check-Fail 'old P1 wrong reliable value plus same-name cannot pass' { Test-UiaPathCandidate 'workspace' 'workspace' @((Reading ValuePattern 'D:\other\workspace'),(Reading Name 'workspace')) $expected } 'CONTRADICTORY'
Check-Fail 'later wrong provider cannot hide behind two earlier correct facts' { Assert-UiaPathEvidence @((Reading Name $expected),(Reading ValuePattern $expected),(Reading LegacyIAccessiblePattern 'D:\other\workspace')) $expected $true } 'CONTRADICTORY'
Check-Fail 'later Name conflict cannot hide behind two reliable correct providers' { Assert-UiaPathEvidence @((Reading ValuePattern $expected),(Reading LegacyIAccessiblePattern $expected),(Reading Name 'D:\other\workspace')) $expected $true } 'CONTRADICTORY'
Check-Fail 'arbitrary provider label does not grant reliable evidence' { Assert-UiaPathEvidence @((Reading UnknownProvider $expected),(Reading Name $expected)) $expected $true } 'MISSING'
Check-Fail 'empty evidence cannot authorize final OK' { Assert-UiaPathEvidence @() $expected $true } 'MISSING'
Check-Fail 'relative display chain cannot authorize final OK' { Assert-UiaPathEvidence @((Reading Name 'workspace'),(Reading Name 'owned'),(Reading ValuePattern 'workspace')) $expected $true } 'MISSING'
Check-Pass 'two reliable providers and Name normalized to same absolute path pass' { $proof=Assert-UiaPathEvidence @((Reading Name $expected),(Reading ValuePattern $expected),(Reading LegacyIAccessiblePattern 'c:/Users/synthetic/owned/workspace')) $expected $true; Assert-True ($proof.reliable_count -eq 2) }
Check-Pass 'an unrelated valid absolute path with no name match is not a candidate' { Assert-False (Test-UiaPathCandidate 'different' 'workspace' @((Reading ValuePattern 'D:\other\workspace')) $expected) }
@{status='INDEPENDENT_ACTUAL_PURE_PATH_COUNTEREXAMPLES_PASS';passed=$script:passed;cases=@($script:cases);helper_body=0;add_type=0;uia=0;gui=0;native=0;model=0}|ConvertTo-Json -Depth 12 -Compress
'''
 (target/'independent-path.ps1').write_text(before+cases,encoding='utf-8')
 save('inputs.json',{'source_root':str(S),'pins':PINS,'manifest_files':len(manifest['files']),'node_sha256':sha(NODE),'powershell':str(PS),'powershell_sha256':sha(PS),'pure_path_test_sha256':sha(target/'independent-path.ps1'),'source_copies':{p.name:sha(p) for p in target.iterdir()},'formal_increment':0})
 print(json.dumps({'prepared':True,'metadata_and_source_pins':True,'manifest_files':len(manifest['files'])}))
def run(name,argv):
 env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if k in os.environ}
 env['PATH']=str(NODE.parent)+os.pathsep+str(Path(env['SystemRoot'])/'System32')
 save(name+'.command.json',{'argv':argv,'environment':env,'cwd':str(R/'source'),'controller_sha256':sha(Path(__file__)),'classification':'AST_EXTRACTED_PURE_STRING_FUNCTIONS_ONLY_NO_HELPER_BODY_SDK_GUI_NATIVE_MODEL','policy_override':False})
 with (R/(name+'.stdout.raw')).open('xb') as out,(R/(name+'.stderr.raw')).open('xb') as err:
  p=subprocess.run(argv,cwd=R/'source',env=env,stdout=out,stderr=err,timeout=30)
 save(name+'.result.json',{'exit_code':p.returncode,'stdout_sha256':sha(R/(name+'.stdout.raw')),'stderr_sha256':sha(R/(name+'.stderr.raw')),'formal_increment':0})
 print(json.dumps({'phase':name,'exit_code':p.returncode}));return p.returncode
if __name__=='__main__':
 cmd=sys.argv[1]
 if cmd=='prepare':prepare()
 elif cmd=='path':sys.exit(run('independent-path',[str(PS),'-NoLogo','-NoProfile','-NonInteractive','-File',str(R/'source/independent-path.ps1')]))
 elif cmd=='node':sys.exit(run('independent-node',[str(NODE),str(R/'independent-node.mjs')]))
