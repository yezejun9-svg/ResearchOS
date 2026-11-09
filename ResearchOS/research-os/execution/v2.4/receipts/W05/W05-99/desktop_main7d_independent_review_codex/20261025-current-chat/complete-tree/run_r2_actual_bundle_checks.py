import hashlib,json,os,pathlib,subprocess,sys
E=pathlib.Path(__file__).parent
B=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-main7d-native-20261025/.local/desktop-complete-20261025-01')
S=E/'source-r2'
state=E/'never-created-r2-dryrun-state'
assert not state.exists()
temp=E/'r2-actual-test-temp';temp.mkdir(exist_ok=False)
env={k:v for k,v in os.environ.items() if k.upper() not in ['NODE_OPTIONS','NODE_PATH','PYTHONPATH','PYTHONHOME']}
env.update({'TEMP':str(temp),'TMP':str(temp),'TMPDIR':str(temp),'PYTHONDONTWRITEBYTECODE':'1','RESEARCHOS_DEVELOPMENT_BUNDLE':str(B)})
cases=[('actual-dry-run',['C:/nvm4w/nodejs/node.exe',str(B/'launch-development.mjs'),'--bundle',str(B),'--state',str(state),'--dry-run']),('actual-bundle-test',[sys.executable,'-B','-X','utf8',str(S/'tests/ui/desktop/development-bundle.test.py'),'DevelopmentBundleTest.test_actual_build_manifest_when_explicitly_supplied','-v'])]
results={}
for name,argv in cases:
    out=E/('r2-'+name);out.mkdir(exist_ok=False)
    (out/'recipe.json').write_text(json.dumps({'argv':argv,'cwd':str(S),'manifest_sha256':'288ac604fbcc09b11d04148c970df8830c59d1352431832b06640e30fbf82a3e','mode':'ACTUAL_BUNDLE_READ_ONLY_NO_ELECTRON_NO_CORE','temporary_root':str(temp)},indent=2),encoding='utf-8')
    p=subprocess.run(argv,cwd=S,env=env,capture_output=True)
    (out/'stdout.raw').write_bytes(p.stdout);(out/'stderr.raw').write_bytes(p.stderr)
    result={'native_exit':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()}
    (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    results[name]=result
    sys.stdout.buffer.write(p.stdout);sys.stderr.buffer.write(p.stderr)
assert not state.exists()
assert not list(temp.iterdir())
temp.rmdir()
assert all(row['native_exit']==0 for row in results.values())
summary={'results':results,'state_not_created':True,'built_manifest_skip_replaced_by_explicit_actual_check':True,'native_gui_or_core_starts':0}
(E/'R2-actual-bundle-test-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
