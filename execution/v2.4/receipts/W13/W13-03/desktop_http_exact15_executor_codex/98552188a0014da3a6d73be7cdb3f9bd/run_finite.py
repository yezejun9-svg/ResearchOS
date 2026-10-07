import pathlib,json,subprocess,datetime,hashlib,os,sys,uuid,re
ROOT=pathlib.Path.cwd();MAIN=pathlib.Path("D:/作品集/ResearchOS/research-os")
NS=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd"
cohort=sys.argv[1];directory=NS/("cohort-"+cohort);build=json.loads((directory/"build/result.json").read_text(encoding="utf-8"));assert build["status"]=="BUILT_NOT_TESTED" and not build["drift"]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=json.loads((directory/"build/inputs.before.json").read_text(encoding="utf-8"));source=json.loads((directory/"source-exact15.before.json").read_text(encoding="utf-8"))
assert all(sha(pathlib.Path(x["path"]))==x["sha256"] for x in inputs)
assert all(sha(ROOT/x["path"])==x["sha256"] for x in source)
roster_path=MAIN/"execution/v2.4/receipts/W13/W13-03/desktop_http_first_branch_revision_codex/a8e573ecbd20499c8bff9d4222dd9ffc/finite_roster.expanded.json"
roster=json.loads(roster_path.read_text(encoding="utf-8"));leaves=roster["leaves"]
if len(sys.argv)>2:leaves=[x for x in leaves if re.search(sys.argv[2],x["name"])]
assert leaves
run=directory/("finite-"+uuid.uuid4().hex);run.mkdir();rows=[]
node="C:/nvm4w/nodejs/node.exe";electron=str(MAIN/"apps/desktop/node_modules/electron/dist/electron.exe")
app=ROOT/".local/desktop-wire"/cohort/"apps/desktop"
env={**os.environ,"RESEARCHOS_DESKTOP_WIRE_ROOT":str(app),"RESEARCHOS_DESKTOP_ELECTRON":electron}
(run/"invocation.json").write_text(json.dumps({"actualargv":sys.argv,"cwd":str(ROOT),"runner_sha256":sha(pathlib.Path(__file__)),"roster_sha256":sha(roster_path),"selected_names":[x["name"] for x in leaves],"all_source_current":True,"build_input_digest":build["build_input_digest"],"binary_sha256":build["binary_sha256"],"environment":{"RESEARCHOS_DESKTOP_WIRE_ROOT":str(app),"RESEARCHOS_DESKTOP_ELECTRON":electron}},ensure_ascii=False,indent=2),encoding="utf-8")
for index,leaf in enumerate(leaves):
 case=run/(str(index).zfill(3)+"-"+re.sub("[^a-zA-Z0-9._-]","_",leaf["name"]));case.mkdir();env["RESEARCHOS_DESKTOP_CASE_RECEIPT"]=str(case/"evidence")
 argv=[node,"--test","--test-name-pattern","^"+re.escape(leaf["name"])+"$","tests/ui/desktop/http-wire-boundary.test.mjs"]
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,timeout=120);code=p.returncode;out=p.stdout;err=p.stderr
 except subprocess.TimeoutExpired as e:code=124;out=e.stdout or b"";err=e.stderr or b""
 (case/"stdout").write_bytes(out);(case/"stderr").write_bytes(err)
 observations=[json.loads(p.read_text(encoding="utf-8")) for p in (case/"evidence").rglob("observations.json")] if (case/"evidence").is_dir() else []
 http=sum(len(x.get("http",[])) for x in observations);children=sum(len(x.get("children",[])) for x in observations)
 row={"name":leaf["name"],"actualargv":argv,"cwd":str(ROOT),"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit":code,"http_count":http,"child_count":children,"http_cap":leaf["http_request_cap"],"child_cap":leaf["pure_child_cap"],"stdout_sha256":sha(case/"stdout"),"stderr_sha256":sha(case/"stderr"),"status":"PASS" if code==0 and http<=leaf["http_request_cap"] and children<=leaf["pure_child_cap"] else "FIRST_UNEXPECTED","relative_evidence":str(case.relative_to(ROOT)),"external":0,"model":0}
 (case/"invocation.json").write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding="utf-8");rows.append(row);print(json.dumps({"name":row["name"],"exit":code,"status":row["status"],"http":http,"children":children}),flush=True)
 if row["status"]!="PASS":break
current=[{**x,"current_sha256":sha(pathlib.Path(x["path"]))} for x in inputs];drift=[x for x in current if x["sha256"]!=x["current_sha256"]]
(run/"inputs.after.json").write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding="utf-8")
summary={"rows":rows,"drift":drift,"source_acceptance":False,"selected":len(leaves),"executed":len(rows),"pass":sum(r["status"]=="PASS" for r in rows),"not_run":len(leaves)-len(rows),"first_unexpected":next((r for r in rows if r["status"]!="PASS"),None)}
(run/"result.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps({"run":str(run),"executed":len(rows),"pass":summary["pass"],"drift":len(drift)}),flush=True)
