from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys

Q=Path(__file__).resolve().parent
M=json.loads((Q/'stage01-manifest.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
node=Path(M['node']['path']);assert sha(node)==M['node']['sha256']
attempt=Q/(sys.argv[1] if len(sys.argv)>1 else 'checks01');attempt.mkdir(exist_ok=False)
before={n:sha(Q/'stage01'/n) for n in M['files']}
assert before=={n:v['sha256'] for n,v in M['files'].items()}
env={k:v for k,v in os.environ.items() if not k.upper().startswith(('RESEARCHOS_','PI_','MU_','OPENAI_','ANTHROPIC_','CODEX_')) and k.upper() not in ['NODE_OPTIONS','NODE_PATH']}
private=Q/'runtime'
settings={'USERPROFILE':str(private/'profile'),'APPDATA':str(private/'profile/roaming'),'LOCALAPPDATA':str(private/'profile/local'),'TEMP':str(private/'tmp'),'TMP':str(private/'tmp'),'NO_UPDATE_NOTIFIER':'1'}
for n in ['USERPROFILE','APPDATA','LOCALAPPDATA','TEMP']:Path(settings[n]).mkdir(parents=True,exist_ok=True)
env.update(settings)
commands=[('independent-ui',[str(node),'--require',str(Q/'guard.cjs'),str(Q/'independent-ui.mjs')]),
 ('independent-bridge',[str(node),'--require',str(Q/'guard.cjs'),str(Q/'independent-bridge.cjs')]),
 ('author-ui-replay',[str(node),'--require',str(Q/'guard.cjs'),str(Q/'stage01/tests/ui/desktop/harness-workbench.test.mjs')]),
 ('author-bridge-replay',[str(node),'--require',str(Q/'guard.cjs'),str(Q/'stage01/tests/ui/harness-bridge-fixture.cjs')]),
 ('legacy-activity-replay',[str(node),'--require',str(Q/'guard.cjs'),str(Q/'stage01/tests/ui/desktop/activity-projection.test.mjs')])]
def save(n,v):
    with (attempt/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
save('input.json',{'stage_manifest_sha256':sha(Q/'stage01-manifest.json'),'frozen_exact10':M['source_sha256_exact10'],
 'node':M['node'],'cwd':str(Q),'environment_overrides':settings,
 'independent_test_sha256':{n:sha(Q/n) for n in ['independent-ui.mjs','independent-bridge.cjs','guard.cjs']},
 'real_operations':'NO_SOCKET_LISTENER_OR_CONNECT_NO_CHILD_PROCESS_NATIVE_CLI_OR_MODEL','product_acceptance_increment':0})
results=[]
for name,argv in commands:
 print(json.dumps({'phase':name,'status':'STARTED'}),flush=True)
 with (attempt/(name+'.stdout.raw')).open('wb') as out,(attempt/(name+'.stderr.raw')).open('wb') as err:
  try:exitcode=subprocess.run(argv,cwd=Q,env=env,stdout=out,stderr=err,timeout=90).returncode
  except subprocess.TimeoutExpired:exitcode=124
 row={'phase':name,'argv':argv,'cwd':str(Q),'exit_code':exitcode,'stdout_sha256':sha(attempt/(name+'.stdout.raw')),'stderr_sha256':sha(attempt/(name+'.stderr.raw')),'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 save(name+'.command.json',row);results.append(row)
 print(json.dumps({'phase':name,'exit_code':exitcode}),flush=True)
after={n:sha(Q/'stage01'/n) for n in M['files']}
assert before==after
save('results.json',{'commands':results,'stage_inputs_unchanged':before==after,'source_sha256_exact10':M['source_sha256_exact10'],'product_acceptance_increment':0,'real_gui_or_model_runs':0})
sys.exit(0 if all(x['exit_code']==0 for x in results) else 1)
