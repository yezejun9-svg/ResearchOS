import sys
sys.dont_write_bytecode=True
import replay,base64,copy,importlib.util,json
out=replay.OUT
spec=importlib.util.spec_from_file_location("c22validator",replay.ROOT/"tests/security/c22_fixture.py")
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
events=[json.loads(s) for s in (out/"replay/go.stdout.jsonl").read_text(encoding="utf-8").splitlines()]
inventory=replay.read(replay.ROOT/"tests/security/c22_expected.json")
negative=[]
for name,mutated in [
 ("empty-events",[]),
 ("missing-test-pass",[e for e in events if not(e.get("Test")==v.TEST and e.get("Action")=="pass")]),
 ("test-fail",[dict(e,Action="fail") if e.get("Test")==v.TEST and e.get("Action")=="pass" else e for e in events]),
 ("missing-assertion-output",[e for e in events if "C22_ASSERTION " not in e.get("Output","")])
]:
 try:v.validate_evidence(out/"replay",mutated,inventory)
 except ValueError as e:negative.append({"probe":name,"rejected":True,"reason":str(e)})
 else:raise AssertionError(name+" improperly accepted")
audit=replay.read(out/"source-audit.json")
for f in audit["files"]:assert replay.sha(replay.ROOT/f["path"])==f["working_sha256"],f["path"]
assert replay.git("rev-parse","HEAD").decode().strip()==replay.RAW
assert replay.git("status","--porcelain").decode()==audit["baseline_status"]
assert replay.sha(replay.AUTHOR/"report.json")==audit["author_report_sha256"]
assert replay.sha(replay.AUTHOR/"evidence-index.json")==audit["author_index_sha256"]
authorsummary=replay.read(replay.ROOT/"execution/receipts/W17/c22/author-summary.json")
authornegative=replay.ROOT/"execution/receipts/W17/c22/validator-negative-probes.json"
assert "sha256:"+replay.sha(authornegative)==authorsummary["negative_probes_sha256"]
http=[]
for path in (out/"delta").glob("*-http.jsonl"):
 rows=[json.loads(s) for s in path.read_text().splitlines() if s]
 assert len(rows)==2 and rows[0]["status"]==200 and rows[1]["status"] in (401,404,503)
 assert v.MARKER in rows[0]["response_body"] and v.MARKER not in rows[1]["response_body"]
 assert all(r["transport"]=="HOST_ISSUED_REAL_LOOPBACK_HTTP" for r in rows)
 http.extend(rows)
delta=replay.read(out/"delta-assertions.json")
current=[a for a in delta["assertions"] if not a["assertion_id"].startswith("native-")]
assert len(current)==15 and all(a["status"]=="PASS" for a in current)
net=replay.read(out/"delta-network-v2/independent-network-output.json")
receipt=replay.read(out/"delta-network-v2/independent-network-receipt.json")
assert json.loads(base64.b64decode(receipt["stdout"]))==net
assert not base64.b64decode(receipt["stderr"])
assert receipt["exit_code"]==0 and receipt["children_stopped"] and not receipt["timed_out"] and receipt["capabilities"]==[]
assert receipt["pid"]==net["pid"] and receipt["appcontainer_sid"]
assert net["network_connected"] is False and net["network_code"]!=0
assert net["inherited_researchos_go"]==net["inherited_c22_evidence"]==""
handles=[]
for folder in ("delta","delta-native-v2"):
 r=replay.read(out/folder/"independent-network-handle-receipt.json")
 stderr=base64.b64decode(r["stderr"]).decode("utf-8")
 assert stderr.startswith("Exception 0xc0000008 ")
 assert r["exit_code"]==2 and r["children_stopped"] and not r["timed_out"]
 assert not base64.b64decode(r["stdout"]) and v.MARKER not in stderr
 handles.append({"folder":folder,"source":"network_handle_child.go" if folder=="delta" else "network_handle_child_v2.go","pid":r["pid"],"sid":r["appcontainer_sid"],"exit_code":r["exit_code"],"exception":"STATUS_INVALID_HANDLE 0xc0000008","stdout_bytes":0,"children_stopped":True,"verdict":"OS rejected the only synthetic canary handle; harness did not finish and is not reported as a normal passing test"})
replay.save("independent-audit.json",{"source_and_author_evidence_unchanged":True,"current_authority_http_count":len(http),"current_authority_assertions":current,"network_positive_http_count":1,"network_result":net,"network_receipt":{"pid":receipt["pid"],"sid":receipt["appcontainer_sid"],"capabilities":[],"exit_code":0},"network_scope":"Observed bounded TCP timeout/error against owned reachable loopback only. Does not claim a packet-capture proof for every network destination.","handle_probe_attempts":handles,"negative_validator_probes":negative,"author_negative_probes_hash_verified":replay.sha(authornegative),"source_files_reverified":len(audit["files"]),"author_status_after":audit["baseline_status"]})
print(json.dumps({"current_authority_assertions":len(current),"current_authority_http":len(http),"network_errno":net["network_code"],"validator_negatives":len(negative),"source_files_unchanged":len(audit["files"]),"author_evidence_unchanged":True}))

