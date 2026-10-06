import sys
sys.dont_write_bytecode=True
import replay,os,json,subprocess,time
out=replay.OUT
run=out/"delta-network-v2";run.mkdir(exist_ok=False)
env=dict(os.environ,GOTOOLCHAIN="local",GOENV="off",RESEARCHOS_GO=str(replay.GO),RESEARCHOS_C22_EVIDENCE=str(run),C22_INDEPENDENT_CHILD_SOURCE=str(out/"network_only_child.go"),PYTHONDONTWRITEBYTECODE="1")
command=[str(replay.GO),"test","-overlay",str(out/"overlay-network-v2.json"),"./internal/domain","-run","^TestIndependentC22NativeNetworkOnly$","-count=1","-timeout=120s","-json"]
started=time.time()
result=subprocess.run(command,cwd=replay.ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
(run/"go.stdout.jsonl").write_bytes(result.stdout);(run/"go.stderr.log").write_bytes(result.stderr)
replay.save("command-network-v2.json",{"command":command,"cwd":str(replay.ROOT),"source":replay.SOURCE,"head":replay.RAW,"environment":{k:env[k] for k in ("GOTOOLCHAIN","GOENV","RESEARCHOS_GO","RESEARCHOS_C22_EVIDENCE","C22_INDEPENDENT_CHILD_SOURCE","PYTHONDONTWRITEBYTECODE")},"exit_code":result.returncode,"elapsed_seconds":time.time()-started,"stdout":"delta-network-v2/go.stdout.jsonl","stderr":"delta-network-v2/go.stderr.log","separate_network_probe_reason":"delta/go.stdout.jsonl; Windows rejected invalid handle before output; Handle probes terminate on OS invalid-handle guard; network runs separately without private paths or handles"})
events=[json.loads(s) for s in result.stdout.decode().splitlines() if s]
lines="".join(e.get("Output","") for e in events).splitlines()
assertions=[json.loads(line[len("C22_INDEPENDENT_ASSERTION "):]) for line in lines if line.startswith("C22_INDEPENDENT_ASSERTION ")]
replay.save("network-v2-assertions.json",{"assertions":assertions,"fail_events":[e for e in events if e.get("Action")=="fail"]})
print(json.dumps({"exit_code":result.returncode,"assertions":len(assertions),"failures":[a for a in assertions if a["status"]!="PASS"]}))
sys.exit(result.returncode)



