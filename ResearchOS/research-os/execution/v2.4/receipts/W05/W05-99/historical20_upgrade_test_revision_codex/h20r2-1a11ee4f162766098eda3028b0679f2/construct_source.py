import difflib, hashlib, json, re, sys
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).parent
B=N.parents[1]
R1=B/"historical20_upgrade_source_codex/h20-r1-root-1791519270000-scoped-check"
BASE=B/"historical20_upgrade_source_codex/h20-1a11ebe661670a1a49d0ea22092604a"
ACT=B/"integration_codex/history20-five-parent-sparse-target-root-h20v-1a11ebe6616"
C=N/"candidate-root"
def pin(p):
 raw=p.read_bytes()
 return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def emit(name,v):
 p=N/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
baseline=json.loads((BASE/"input-pins.json").read_bytes())
assert len(baseline)==66
assert [pin(Path(v["path"])) for v in baseline]==baseline
hdf=json.loads((R1/"HDF.json").read_bytes())
inputs=baseline+[pin(R1/"HDF.json"),pin(R1/"MF.json"),pin(BASE/"input-pins.json"),
 pin(ACT/"validation.closed.json"),pin(ACT/"history20-five-parent-jsonl.stdout.raw")]
assert inputs[-2]["sha256"].startswith("8bab") and inputs[-2]["sha256"].endswith("e20fc") and inputs[-2]["bytes"]==26709
for v in hdf["candidate_files"]:
 assert pin(Path(v["path"]))==v
 inputs.append(v)
old=(R1/"candidate-root/internal/domain/backup_history20_upgrade_test.go").read_bytes()
assert len(old)==9082 and hashlib.sha256(old).hexdigest()=="6e9d53b0663294488e07009109e20a9a2ec6a32b0bbb4ab4fcec995f418fada5"
text=old.decode("utf-8")
edits=[]
def replace(a,b):
 global text
 assert text.count(a)==1,a
 text=text.replace(a,b)
 edits.append({"old":a,"new":b})
replace(' "encoding/json"\n',' "encoding/json"\n "errors"\n')
replace('Source: filepath.Join(base,"source.sqlite")','Source: filepath.Join(base,"source","source.sqlite")')
replace('KeyFile: filepath.Join(base,"recovery.key")','KeyFile: filepath.Join(base,"key","recovery.key")')
replace(' for path, data := range map[string][]byte{opt.KeyFile:',
 ' for _, dir := range []string{filepath.Dir(opt.Source),filepath.Dir(opt.KeyFile)} {\n  if err = os.MkdirAll(dir,0700); err != nil { t.Fatal(err) }\n }\n for path, data := range map[string][]byte{opt.KeyFile:')
replace('   if err==nil {t.Fatal("source/release drift accepted")}',
 '   expectedError := map[string]string{\n    "migration-hash":"UPGRADE_RELEASE_HASH: 0021_research_pending_windows.sql",\n    "extra-numbered-migration":"UPGRADE_RELEASE_MIGRATIONS: require exact 1..20",\n    "foreign-table":"UPGRADE_SOURCE_SCHEMA",\n    "session-addon":"UPGRADE_SOURCE_SCHEMA",\n   }[tc]\n   if err==nil || err.Error()!=expectedError {t.Fatalf("expected %s for %s, got %v",expectedError,tc,err)}')
replace(' _,err=RestoreBackup(context.Background(),opt.Snapshot,opt.Destination,RestoreOptions{',
 ' // This is a generic RestoreBackup component failure, not the public UpgradeLocal failure path.\n backupManifestBefore,err:=os.ReadFile(filepath.Join(opt.Snapshot,"manifest.json"));if err!=nil {t.Fatal(err)}\n callbackCalled:=false\n _,err=RestoreBackup(context.Background(),opt.Snapshot,opt.Destination,RestoreOptions{')
replace('  if _,err:=target.ExecContext(ctx,"CREATE TABLE fixture_unpublished(value TEXT)");err!=nil{return err}',
 '  callbackCalled=true\n  if _,err:=target.ExecContext(ctx,"CREATE TABLE fixture_unpublished(value TEXT)");err!=nil{return err}')
replace(' if err==nil {t.Fatal("injected migration failure accepted")}',
 ' if !callbackCalled || !errors.Is(err,context.Canceled) {t.Fatalf("expected invoked migration callback and context.Canceled, called=%t err=%v",callbackCalled,err)}')
replace(' if _,err=os.Stat(opt.Snapshot);err!=nil {t.Fatal("backup lost",err)}',
 ' if _,err=os.Stat(opt.Snapshot);err!=nil {t.Fatal("backup lost",err)}\n backupManifestAfter,err:=os.ReadFile(filepath.Join(opt.Snapshot,"manifest.json"));if err!=nil {t.Fatal(err)}\n if !bytes.Equal(backupManifestBefore,backupManifestAfter){t.Fatal("retained backup manifest changed")}')
inverse=text
for edit in reversed(edits):
 assert inverse.count(edit["new"])==1
 inverse=inverse.replace(edit["new"],edit["old"])
assert inverse.encode("utf-8")==old
parents=re.findall(r"^func (TestHistory20\w+)\(",text,re.M)
oldparents=re.findall(r"^func (TestHistory20\w+)\(",old.decode(),re.M)
assert len(parents)==5 and parents==oldparents
leaves=["migration-hash","extra-numbered-migration","foreign-table","session-addon"]
assert '[]string{"migration-hash","extra-numbered-migration","foreign-table","session-addon"}' in text
assert 'if err==nil {t.Fatal("source/release drift accepted")}' not in text
positiveStart=text.index("func TestHistory20PublicUpgrade")
positiveEnd=text.index("func TestHistory20RejectsRelease")
oldPositive=old.decode()[old.decode().index("func TestHistory20PublicUpgrade"):old.decode().index("func TestHistory20RejectsRelease")]
assert text[positiveStart:positiveEnd]==oldPositive
for candidate in hdf["candidate_files"]:
 oldp=Path(candidate["path"])
 rel=oldp.relative_to(R1/"candidate-root")
 dest=C/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 raw=text.encode("utf-8") if oldp.name=="backup_history20_upgrade_test.go" else oldp.read_bytes()
 with dest.open("xb") as f:f.write(raw)
 if oldp.name!="backup_history20_upgrade_test.go":assert raw==oldp.read_bytes()
patch="".join(difflib.unified_diff(old.decode().splitlines(keepends=True),text.splitlines(keepends=True),
 fromfile="R1/internal/domain/backup_history20_upgrade_test.go",tofile="R2/internal/domain/backup_history20_upgrade_test.go"))
(N/"test-only.patch").write_text(patch,encoding="utf-8",newline="\n")
emit("exact-inverse.json",{"old_test_ref":pin(R1/"candidate-root/internal/domain/backup_history20_upgrade_test.go"),
 "new_test_ref":pin(C/"internal/domain/backup_history20_upgrade_test.go"),"edits":edits,
 "reverse_edits_produce_identical_old_bytes":True,"R1_correct_key_policy_positive_block_identical":True})
events=[json.loads(line) for line in (ACT/"history20-five-parent-jsonl.stdout.raw").read_text(encoding="utf-8").splitlines() if line]
terminal=[e for e in events if e.get("Test") and e.get("Action") in ("pass","fail","skip")]
assert len(terminal)==9 and sum(e["Action"]=="pass" for e in terminal)==8 and sum(e["Action"]=="fail" for e in terminal)==1
emit("actual914-provenance.json",{"validation_closed_ref":pin(ACT/"validation.closed.json"),
 "jsonl_ref":pin(ACT/"history20-five-parent-jsonl.stdout.raw"),"test_terminal_events":terminal,
 "old_actual_result":"8_PASS_1_FAIL","old_public_upgrade_error":"UPGRADE_PATH_OVERLAP",
 "old_drift_negative_passes_do_not_prove_intended_error":True,"old_evidence_rewritten":False})
assert [pin(Path(v["path"])) for v in inputs]==inputs
emit("guard.final.json",{"schema":"researchos.source-readonly-pin-guard.v1","before":inputs,"after":inputs,
 "unchanged":True,"baseline66_unchanged":True,"four_production_candidates_unchanged":True,
 "source_hash_recheck_only":True,"native_win32_guard_executed":False})
emit("source-controls.json",{"schema":"researchos.h20-r2-source-controls.v1","full_inverse":"PASS",
 "four_production_byte_equal":"PASS","baseline66_pins":"PASS","five_parent_names":parents,
 "four_leaf_names":leaves,"expected_total_terminal_tests":9,
 "exact_negative_errors":{"migration-hash":"UPGRADE_RELEASE_HASH: 0021_research_pending_windows.sql",
 "extra-numbered-migration":"UPGRADE_RELEASE_MIGRATIONS: require exact 1..20",
 "foreign-table":"UPGRADE_SOURCE_SCHEMA","session-addon":"UPGRADE_SOURCE_SCHEMA"},
 "callback_called_required":True,"errors_Is_context_Canceled_required":True,
 "destination_unpublished_and_source_whole_rows_equal_required":True,
 "backup_manifest_raw_bytes_retained_required":True,"correct_key_policy_positive_block":"BYTE_IDENTICAL",
 "Go_SQL_Git_native_model_executed":False})
print("H20R2_SOURCE_CONSTRUCT_OK "+json.dumps({"candidate_test":pin(C/"internal/domain/backup_history20_upgrade_test.go"),
 "edits":len(edits),"baseline":66,"production":4,"parents":5,"leaves":4,"native_exit":None}))

