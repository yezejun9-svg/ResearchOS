import sys
sys.dont_write_bytecode=True
import replay,os,json,subprocess,time
out=replay.OUT
run=out/"delta-native-v2";run.mkdir(exist_ok=False)
env=dict(os.environ,GOTOOLCHAIN="local",GOENV="off",RESEARCHOS_GO=str(replay.GO),RESEARCHOS_C22_EVIDENCE=str(run),C22_INDEPENDENT_CHILD_SOURCE=str(out/"network_handle_child_v2.go"),PYTHONDONTWRITEBYTECODE="1")
command=[str(replay.GO),"test","-overlay",str(out/"overlay.json"),"./internal/domain","-run","^TestIndependentC22NativeNetworkAndHandle$","-count=1","-timeout=120s","-json"]
started=time.time()
result=subprocess.run(command,cwd=replay.ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
(run/"go.stdout.jsonl").write_bytes(result.stdout);(run/"go.stderr.log").write_bytes(result.stderr)
replay.save("command-native-v2.json",{"command":command,"cwd":str(replay.ROOT),"source":replay.SOURCE,"head":replay.RAW,"environment":{k:env[k] for k in ("GOTOOLCHAIN","GOENV","RESEARCHOS_GO","RESEARCHOS_C22_EVIDENCE","C22_INDEPENDENT_CHILD_SOURCE","PYTHONDONTWRITEBYTECODE")},"exit_code":result.returncode,"elapsed_seconds":time.time()-started,"stdout":"delta-native-v2/go.stdout.jsonl","stderr":"delta-native-v2/go.stderr.log","supersedes_native_harness_failure":"delta/go.stdout.jsonl; Windows rejected invalid handle before output; V2 checks GetHandleInformation on same single fixture handle before ReadFile"})
events=[json.loads(s) for s in result.stdout.decode().splitlines() if s]
lines="".join(e.get("Output","") for e in events).splitlines()
assertions=[json.loads(line[len("C22_INDEPENDENT_ASSERTION "):]) for line in lines if line.startswith("C22_INDEPENDENT_ASSERTION ")]
replay.save("native-v2-assertions.json",{"assertions":assertions,"fail_events":[e for e in events if e.get("Action")=="fail"]})
print(json.dumps({"exit_code":result.returncode,"assertions":len(assertions),"failures":[a for a in assertions if a["status"]!="PASS"]}))
sys.exit(result.returncode)

