import pathlib,subprocess,json,os,datetime
MAIN=pathlib.Path("D:/作品集/ResearchOS/research-os");WT=MAIN/".local/worktrees/codex-w0599-model-stream";OUT=pathlib.Path(__file__).parent
s=(OUT/"audit_integrity_v2.py").read_text(encoding="utf8")
s=s.replace('and not low.endswith((".sqlite",".db",".sqlite3"))','and (not low.endswith((".sqlite",".db",".sqlite3")) or k in ["repo:execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/test-53a6e07436494837878a09393994fdce/failed-fixture.sqlite","repo:execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/test-f4a65b87734641c8a39d7060dd8b24fb/actual-fixtures/TestCLIModelStreamInterruptedPrefix/fixture.sqlite"])')
(OUT/"audit_integrity_v3.py").write_text(s,encoding="utf8")
env=os.environ.copy()
for k in list(env):
 if k.startswith("RESEARCHOS_"):del env[k]
env.update(json.loads((WT/"execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/closure-e4e653dccd104937898e4096a3669e4e/environment.json").read_bytes()))
overlay={"Replace":{str(WT/"internal/domain/reviewer_semantic_probe_test.go"):str(OUT/"quarantine_semantic_probe_test.go")}}
(OUT/"semantic_overlay.json").write_text(json.dumps(overlay),encoding="utf8")
for name,cmd,cwd in [
 ("audit-v3",[os.sys.executable,str(OUT/"audit_integrity_v3.py")],MAIN),
 ("semantic-quarantine-probe",[env["RESEARCHOS_GO"],"test","-overlay",str(OUT/"semantic_overlay.json"),"-v","-count=1","-timeout=60s","-run","^TestIndependentModelQuarantineSDKSemanticMerges$","./internal/domain"],WT),
 ("actual-sdk-semantic-probe",[env["RESEARCHOS_NODE"],str(OUT/"sdk_semantic_probe.mjs")],MAIN)]:
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 p=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True)
 (OUT/(name+".stdout")).write_bytes(p.stdout);(OUT/(name+".stderr")).write_bytes(p.stderr)
 (OUT/(name+".invocation.json")).write_text(json.dumps({"argv":cmd,"cwd":str(cwd),"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit":p.returncode,"mode":"SYNTHETIC_LOCAL_OR_READONLY_NO_NETWORK"},indent=2),encoding="utf8")
 print(name,p.returncode,p.stdout.decode(errors="replace")[:1600],flush=True)

