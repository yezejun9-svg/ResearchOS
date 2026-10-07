from pathlib import Path
import json,hashlib,subprocess,re,datetime,sys
MAIN=Path("D:/作品集/ResearchOS/research-os")
WT=MAIN/".local/worktrees/codex-w0999-causal-controls-r320-9a15d49131e8"
OUT=Path(__file__).resolve().parent
PROPOSAL=MAIN/"execution/v2.4/receipts/W09/W09-99/test_only_causal_scope_proposal_codex/c64f2c8e07794f7183c8ef34325fdcbb"
S=json.loads((OUT/"root-w09_source_scope.json").read_text(encoding="utf-8"))
BASE=S["base_commit"]; HANDLER="22752a6a41732c8c158d7d7e1b8932ec958f8cb8"
def digest(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":digest(b),"bytes":len(b)}
def save(n,d):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8") as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write("\n")
def raw(n,b):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b)
 return ref(p)
def git(name,args):
 argv=["git","-c","core.quotepath=false",*args];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 p=subprocess.run(argv,cwd=WT,capture_output=True,timeout=30)
 so=raw("git-audit/"+name+".stdout.raw",p.stdout);se=raw("git-audit/"+name+".stderr.raw",p.stderr)
 save("git-audit/"+name+".invocation.json",{"actualargv":argv,"cwd":str(WT),"actual_native_exit":p.returncode,"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"stdout_ref":so,"stderr_ref":se})
 if p.returncode:raise SystemExit(p.returncode)
 return p.stdout
assert git("head",["rev-parse","HEAD"]).decode().strip()==BASE
assert git("branch",["branch","--show-current"]).decode().strip()==S["branch"]
assert not git("index-before",["diff","--cached","--name-only"])
changed=git("changed",["diff","--name-only"]).decode().splitlines();assert set(changed)==set(S["source_paths"])
handler_paths=git("handler-paths",["diff","--name-only",BASE,HANDLER]).decode().splitlines()
assert not set(handler_paths).intersection(S["source_paths"])
raw("SOURCE_DIFF.patch",git("source-diff",["diff","--no-ext-diff","--",*S["source_paths"]]))
git("status",["status","--short","--untracked-files=normal"])
rows=[];all_new_tests={};new_symbols=[]
for i,entry in enumerate(S["exact_source_preimages"]):
 path=entry["path"];old=(OUT/"preimages"/path).read_bytes();cur=(WT/path).read_bytes()
 assert digest(old)==entry["base_blob_sha256"]
 assert git(f"base-{i}",["show",BASE+":"+path])==old
 assert git(f"handler-{i}",["show",HANDLER+":"+path])==old
 marker=b"\n)\n";old_cut=old.index(marker)+len(marker);cur_cut=cur.index(marker)+len(marker)
 old_body=old[old_cut:];assert cur[cur_cut:cur_cut+len(old_body)]==old_body,path
 old_prefix=old[:old_cut].decode();cur_prefix=cur[:cur_cut].decode()
 old_imports=re.findall(r'^\s*(?:[a-zA-Z_]+\s+)?"([^"]+)"',old_prefix,re.M)
 cur_imports=re.findall(r'^\s*(?:[a-zA-Z_]+\s+)?"([^"]+)"',cur_prefix,re.M)
 assert all(x in cur_imports for x in old_imports)
 extra=[x for x in cur_imports if x not in old_imports]
 # Only import additions: removing their complete lines reconstructs original prefix.
 adjusted=cur_prefix
 for imp in extra:adjusted=re.sub(r'^[ \t]*"'+re.escape(imp)+r'"\n','',adjusted,flags=re.M)
 assert adjusted==old_prefix,(path,"non-import prefix mutation")
 tail=cur[cur_cut+len(old_body):].decode();syms=re.findall(r'^func ([A-Za-z0-9_]+)\(',tail,re.M)
 assert syms and all(x.startswith(("TestW09Causal","w09Causal")) for x in syms)
 assert not re.search(r'\bt\.(?:Skip|Skipf|SkipNow)\(',tail)
 tests=[x for x in syms if x.startswith("Test")];all_new_tests[path]=tests
 assert not re.search(r'(?i)DROP\s+TRIGGER|PRAGMA\s+writable_schema',tail)
 snap=raw("source-current/"+path,cur)
 rows.append({"path":path,"before_sha256":digest(old),"current_ref":snap,"protected_body_sha256":digest(old_body),"protected_body_bytes":len(old_body),"protected_current_byte_offset":cur_cut,"protected_exact":True,"added_imports":extra,"appended_symbols":syms,"new_top_functions":len(tests)})
 new_symbols.extend(syms)
assert len(new_symbols)==len(set(new_symbols)),"global test/helper collision within additions"
roster=json.loads((PROPOSAL/"finite-roster.json").read_text(encoding="utf-8"))
assert len(roster["rows"])==41
expanded=[]
for n,row in enumerate(roster["rows"],1):
 path=row["file"];parts=row["selector"].split('/');assert parts[0] in all_new_tests[path]
 source=(WT/path).read_text(encoding="utf-8")
 for x in parts[1:]:assert '"'+x+'"' in source,(path,x)
 line=source[:source.index("func "+parts[0]+"(")].count('\n')+1
 expanded.append({"ordinal":n,"selector":row["selector"],"exact_test_run":"/".join('^'+re.escape(x)+'$' for x in parts),"file":path,"top_function_line":line,"obligation":row["obligation"],"implementation":"WRITTEN_NOT_COMPILED","execution":"NOT_RUN","resource_conditional":row["selector"].endswith(("Symlink","Junction")),"source_ref":ref(WT/path),"frozen_requirement":row})
assert set(x["selector"].split('/')[0] for x in expanded)==set(sum(all_new_tests.values(),[]))
plan=json.loads((PROPOSAL/"future-execution-plan.json").read_text(encoding="utf-8"))
regressions=[]
for name in plan["preserved_regression_top_functions"]:
 hits=[p for p in S["source_paths"] if ('func '+name+'(') in (OUT/'preimages'/p).read_text(encoding='utf-8')]
 assert len(hits)==1
 regressions.append({"selector":name,"file":hits[0],"test_run":"^"+name+"$","old_body_exact":True,"execution":"NOT_RUN"})
save("implemented-roster.json",{"schema":"researchos.w09.implemented-roster.v1","source_only":True,"new_scenarios":41,"core":39,"conditional_OS":2,"new_top_functions":sum(map(len,all_new_tests.values())),"rows":expanded,"old_regressions":regressions,"counts_not_executed":True})
save("protected-source-audit.json",{"schema":"researchos.w09.exact4-static-protection.v1","base":BASE,"handler":HANDLER,"source_paths":changed,"handler_path_count":len(handler_paths),"intersection":[],"rows":rows,"all_old_bodies_and_comments_preserved":True,"format_invocations":2,"format_scope_corrections_ref":ref(OUT/'format-02.protected-reconciliation.json'),"semantic_compilation":"NOT_RUN","native_tests":"NOT_RUN"})
# Read only the exact public source/contract inputs previously inventoried; new test changes disclosed.
inputs=json.loads((PROPOSAL/'public-inputs.before-after.json').read_text(encoding='utf-8'))['before']
current=[]
for i,row in enumerate(inputs):
 p=Path(row['path'])
 if p.is_relative_to(MAIN):
  relative=p.relative_to(MAIN);actual=WT/relative;dest='public-inputs/'+relative.as_posix()
 else:
  actual=p;dest='frozen-external/'+str(i)+'-'+p.name
 b=actual.read_bytes();is_changed=actual.is_relative_to(WT) and actual.relative_to(WT).as_posix() in S['source_paths']
 if not is_changed:assert digest(b)==row['sha256'],str(actual)
 frozen=raw(dest,b)
 current.append({'original_proposal_ref':row,'actual_ref':ref(actual),'snapshot_ref':frozen,'authorized_test_change':is_changed})
save('public-inputs.before-after.json',{'phase':'FINAL_STATIC_SNAPSHOT_ONLY_NOT_COMPILED_GRAPH','before':current,'after':[ref(Path(x['actual_ref']['path'])) for x in current],'drift_during_capture':[]})
for row in current:assert ref(Path(row['actual_ref']['path']))==row['actual_ref']
plan['parent_proposal_ref']=ref(PROPOSAL/'future-execution-plan.json')
plan['candidate_status']='WRITTEN_NOT_COMPILED_NOT_EXECUTED'
plan['exact_roster_ref']=ref(OUT/'implemented-roster.json')
plan['controller_must_be_independently_reviewed']=True
plan['proposed_numeric_limits']={'compile_invocations':2,'compile_deadline_seconds_each':600,'go_list_invocations':2,'go_list_deadline_seconds_each':180,'new_leaf_or_old_top_test_invocations_max':49,'test_timeout_seconds_each':120,'outer_owned_job_deadline_seconds_each':150,'automatic_retries':0,'network_HTTP':0,'external_model_sdk_paid':0,'scope_total_deadline_seconds':9000}
plan['junction_resource_contract']={'creation':'NOT_AUTHORIZED_NOT_RUN; future pinned cmd /c mklink /J only in exclusive own receipt resource/A/outside pointing at own sibling B, wrapped in assigned-before-resume owned Job','test_process_env':'RESEARCHOS_W09_CAUSAL_LINK_RESOURCE=<absolute own exclusive fixture>','files':'A/same.txt and B/same.txt exact owned-public-marker; A/outside is actual irregular reparse mode','bounds':'Full lexical/resolve/ancestor/reparse and exact target audit by controller before granting directory. Test itself starts no child. Resource absence -> corresponding branch HOLD; never substitute symlink for junction or count skip as PASS.'}
plan['closed_copy_contract']={'helper':'w09CausalAttachEvidence','sequence':['checkpoint(TRUNCATE) busy=0','database_list main path','rows Close checked','DB Close checked','original WAL/SHM absent','exclusive closed.sqlite regular copy','byte comparison and digest','copy WAL/SHM absent'],'no_SQLite_reopen_in_test':True,'later_reader':'Only separately granted closed copy mode=ro&immutable=1; original never reopened. Current phase has no DB.','limits':['Original setup failure before helper registration cannot produce a completed closed-copy proof. Preserve raw failure and mark snapshot missing.','Implicit rowid is not separately exported; selected public table column rows are compared as multiplicity-preserving sorted multisets.','No hostile concurrent path adversary/TOCTOU claim. Future controller owns and pins receipt/resource paths.']}
plan['full_input_requirements']=['Freeze actual current source (all local package variants/tests, embeds, ASM/CGO), runtime schemas and migration SQL, go.mod/go.sum; pin Go/GOROOT stdlib/imports and complete dependency modules.','go list -deps -test -compiled -json -mod=readonly and fresh go test -c -work -x; preserve generated testmain/importcfg/WORK/archive/buildinfo/raw/exe and actual command env. Isolated GOCACHE/GOTMPDIR, no automatic network dependency acquisition.','Capture compiler/tool/Python/owned Job helper and actual loaded OS images; if fast child prevents complete loaded-image proof, disclose and obtain a bounded controller decision before execution. Static PE imports are not actual loaded modules.','Rehash same immutable inventory before/after every finite case and reject drift; preserve owned Job actual exit/stdio-close/idle/cleanup. A case prefix does not imply the whole matrix passed.','Future actual in-process recorder calls counted separately from network HTTP=0; no synthetic status interpreted as live provider qualification.']
save('future-execution-proposal.json',plan)
print(json.dumps({'sources':len(rows),'protected':all(x['protected_exact'] for x in rows),'new_top_functions':sum(map(len,all_new_tests.values())),'scenarios':len(expanded),'regressions':len(regressions),'public_inputs':len(current),'tests_executed':0,'handler_overlap':[]},ensure_ascii=False))
