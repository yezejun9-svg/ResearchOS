import sys
sys.dont_write_bytecode=True
import replay,os,json,pathlib,subprocess,time
out=replay.OUT
run=out/"delta"
run.mkdir(exist_ok=False)
env=dict(os.environ,GOTOOLCHAIN="local",GOENV="off",RESEARCHOS_GO=str(replay.GO),RESEARCHOS_C22_EVIDENCE=str(run),C22_INDEPENDENT_CHILD_SOURCE=str(out/"network_handle_child.go"),PYTHONDONTWRITEBYTECODE="1")
command=[str(replay.GO),"test","-overlay",str(out/"overlay.json"),"./internal/domain","-run","^TestIndependentC22","-count=1","-timeout=120s","-json"]
started=time.time()
result=subprocess.run(command,cwd=replay.ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
(run/"go.stdout.jsonl").write_bytes(result.stdout);(run/"go.stderr.log").write_bytes(result.stderr)
replay.save("command-delta.json",{"command":command,"cwd":str(replay.ROOT),"source":replay.SOURCE,"head":replay.RAW,"environment":{k:env[k] for k in ("GOTOOLCHAIN","GOENV","RESEARCHOS_GO","RESEARCHOS_C22_EVIDENCE","C22_INDEPENDENT_CHILD_SOURCE","PYTHONDONTWRITEBYTECODE")},"exit_code":result.returncode,"elapsed_seconds":time.time()-started,"stdout":"delta/go.stdout.jsonl","stderr":"delta/go.stderr.log"})
events=[json.loads(line) for line in result.stdout.decode("utf-8").splitlines() if line]
lines="".join(e.get("Output","") for e in events).splitlines()
assertions=[json.loads(line[len("C22_INDEPENDENT_ASSERTION "):]) for line in lines if line.startswith("C22_INDEPENDENT_ASSERTION ")]
failures=[e for e in events if e.get("Action")=="fail"]
replay.save("delta-assertions.json",{"assertions":assertions,"fail_events":failures})
print(json.dumps({"exit_code":result.returncode,"assertions":len(assertions),"fail_events":failures,"stderr":result.stderr.decode("utf-8")}))
sys.exit(result.returncode)

