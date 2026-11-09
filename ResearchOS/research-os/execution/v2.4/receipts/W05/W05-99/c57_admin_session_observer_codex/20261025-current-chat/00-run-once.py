import datetime,hashlib,json,pathlib,subprocess,sys
out=pathlib.Path(__file__).resolve().parent
argv=[sys.executable,'-X','utf8',str(out/'01-readonly-session-probe.py')]
pre={'schema':'researchos.C57-session-observer-recipe.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'source_commit_context':'03aa4d687dfaa541d9b18d4c766805307a537d1d','checkpoint_context':'CP558','user_preparation_state':'preparing','writes_scope':str(out),'query_access':'PROCESS_QUERY_LIMITED_INFORMATION and TOKEN_QUERY only','single_snapshot':True,'denied_query_policy':'UNKNOWN; no elevation or bypass','excluded':['command lines','credentials','business DB','original files','privilege adjustment','UAC','account creation','login or switching','sandbox borrowing','C57 execution','Main/shared checkpoint writes']}
(out/'00-pre-registered-recipe.json').write_text(json.dumps(pre,indent=2,ensure_ascii=False),encoding='utf-8')
p=subprocess.run(argv,capture_output=True)
(out/'01-probe.stdout.raw').write_bytes(p.stdout)
(out/'01-probe.stderr.raw').write_bytes(p.stderr)
(out/'01-probe.exit.txt').write_text(str(p.returncode),encoding='ascii')
print(json.dumps({'exit':p.returncode,'stdout_bytes':len(p.stdout),'stderr_bytes':len(p.stderr),'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()}))
sys.exit(p.returncode)
