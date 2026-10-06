import pathlib,json,subprocess,os,datetime
MAIN=pathlib.Path("D:/作品集/ResearchOS/research-os");WT=MAIN/".local/worktrees/codex-w0599-model-stream";OUT=pathlib.Path(__file__).parent
script=(OUT/"audit_integrity.py").read_text(encoding="utf8").replace('scope=="worktree"','scope=="repo"')
(OUT/"audit_integrity_v2.py").write_text(script,encoding="utf8")
(OUT/"audit_attempt1.json").write_text(json.dumps({"exit":1,"tool_chunk":"8139c1","failure":"ValueError repo:.local/model-stream/mu-worker.mjs; reviewer locator recognized worktree prefix but actual frozen input uses repo; no input drift conclusion made. Original audit_integrity.py retained."},indent=2),encoding="utf8")
a=subprocess.run([os.sys.executable,str(OUT/"audit_integrity_v2.py")],cwd=MAIN,capture_output=True)
(OUT/"audit_v2.stdout").write_bytes(a.stdout);(OUT/"audit_v2.stderr").write_bytes(a.stderr)
print("integrity",a.returncode,a.stdout.decode(errors="replace"))
env=os.environ.copy()
for k in list(env):
 if k.startswith("RESEARCHOS_"):del env[k]
env.update(json.loads((WT/"execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/closure-e4e653dccd104937898e4096a3669e4e/environment.json").read_bytes()))
env["RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"]=str(OUT/"replay-fixtures")
env["PATH"]=str(pathlib.Path(env["RESEARCHOS_NODE"]).parent)+os.pathsep+env.get("PATH","")
overlay={"Replace":{str(WT/"internal/domain/reviewer_stream_probe_test.go"):str(OUT/"quarantine_probe_test.go")}}
(OUT/"overlay.json").write_text(json.dumps(overlay),encoding="utf8")
commands=[
("quarantine-alias-probe",[env["RESEARCHOS_GO"],"test","-overlay",str(OUT/"overlay.json"),"-count=1","-v","-timeout=60s","-run","^TestIndependentModelQuarantineReasoningAliasSplit$","./internal/domain"]),
("core-controls",[env["RESEARCHOS_GO"],"test","-count=1","-v","-timeout=150s","-run","^(TestModelStream|TestClientStreamTranscriptPartialCASAndFullRecovery)","./adapters/runtime","./internal/domain"]),
("actual-causal-cancel",[env["RESEARCHOS_GO"],"test","-count=1","-v","-timeout=180s","-run","^TestCLIModelStream(CausalDurableJSONL|CancelObservedPrefix|DurableCommitFailure)$","./apps/cli"])
]
for name,argv in commands:
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (OUT/(name+".stdout")).open("wb") as o,(OUT/(name+".stderr")).open("wb") as e:
  p=subprocess.run(argv,cwd=WT,env=env,stdout=o,stderr=e)
 (OUT/(name+".invocation.json")).write_text(json.dumps({"argv":argv,"cwd":str(WT),"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit":p.returncode,"mode":"LOCAL_FIXTURE_NO_PAID_PROVIDER","env":{k:v for k,v in env.items() if k.startswith("RESEARCHOS_") or k in ["GOROOT","GOENV","GOPATH","GOCACHE","GOSUMDB","GOPROXY","GOTOOLCHAIN"]}},indent=2),encoding="utf8")
 print(name,p.returncode,flush=True)

