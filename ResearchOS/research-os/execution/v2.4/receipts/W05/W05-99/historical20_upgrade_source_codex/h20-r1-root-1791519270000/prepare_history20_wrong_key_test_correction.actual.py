import sys
sys.dont_write_bytecode=True
import json,hashlib,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
A=B/"historical20_upgrade_source_codex/h20-1a11ebe661670a1a49d0ea22092604a"
V=B/"historical20_upgrade_source_independent_review_codex/h20r-20261009-source-review"
G=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 q=pin(v["path"]);assert q["sha256"]==v["sha256"].removeprefix("sha256:") and q["bytes"]==v["bytes"];return q
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
def obj(p):return json.loads(Path(p).read_bytes())
assert (pin(A/"HDF.json")["sha256"],pin(A/"HDF.json")["bytes"])==("f3e1a18b047e1d36370efdd489145725655fe119faa69eb98a157776c6376493",4438)
assert (pin(A/"MF.json")["sha256"],pin(A/"MF.json")["bytes"])==("2be232566a2f59acad0d968439ab836e5cd05618740c3fd3b7f8bfafbed40958",5565)
assert (pin(V/"HDF.json")["sha256"],pin(V/"HDF.json")["bytes"])==("6b2b486eb56f7a53c5656e8858580456dc997c26c5c3a518304fba0dcdd28fb2",2585)
assert pin(G)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
hd=obj(A/"HDF.json"); refs=[pin(__file__),pin(sys.executable),pin(G),pin(A/"HDF.json"),pin(A/"MF.json"),pin(V/"HDF.json"),pin(V/"MF.json")]
for p in (A/"MF.json",V/"MF.json"):
 members=obj(p)["members"];members=members.values() if isinstance(members,dict) else members
 refs.extend(verify(x) for x in members)
baseline=obj(A/"input-pins.json");assert len(baseline)==66; refs.extend(verify(x) for x in baseline)
m=types.ModuleType("h20r1_source_guard");m.__file__=str(G);sys.modules[m.__name__]=m;exec(compile(G.read_bytes(),str(G),"exec"),m.__dict__)
for mod in list(sys.modules.values()):
 for field in ("__file__","__cached__"):
  p=getattr(mod,field,None)
  if p and Path(p).is_file():refs.append(pin(p))
unique={}
for v in refs:
 k=v["path"].casefold();assert k not in unique or unique[k]==v;unique[k]=v
guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024);guard.acquire(list(unique.values()))
try:
 root=O/"candidate-root";root.mkdir()
 oldblock=''' contracts,err := LoadContracts(filepath.Join(opt.SourceRoot,"spec/v2.0/contracts"))
 if err != nil { t.Fatal(err) }
 wrong := append([]byte(nil),key...); wrong[0] ^= 1
 _,err = RestoreBackup(context.Background(),opt.Snapshot,filepath.Join(t.TempDir(),"wrong-key"),RestoreOptions{Key:wrong,SupportedMigrations:upgradeVersions(20),Contracts:contracts})
 if err == nil { t.Fatal("encrypted snapshot accepted wrong key") }
'''
 newblock=''' defer clear(key)
 raw,err := os.ReadFile(filepath.Join(opt.Snapshot,"manifest.json"))
 if err != nil { t.Fatal(err) }
 var manifest BackupManifest
 if err = json.Unmarshal(raw,&manifest); err != nil { t.Fatal(err) }
 plan,ok := manifest.Purpose["plan"].(map[string]any)
 if !ok || plan["id"] != History20SchemaUpgradePlan || manifest.Format != localUpgradeFormat { t.Fatal("wrong snapshot plan or format") }
 policy := &backupPolicy{format:localUpgradeFormat,databaseName:"researchos.sqlite",purpose:manifest.Purpose}
 verified,files,err := readBackupPolicy(opt.Snapshot,key,policy)
 if err != nil { t.Fatalf("correct key rejected under matching upgrade policy: %v",err) }
 if len(files["state.sqlite"]) == 0 || Hash(verified.Migrations) != Hash(upgradeVersions(20)) { t.Fatal("authenticated snapshot missing historical20 database or migrations") }
 if _,ok := files["portable.json"]; ok { t.Fatal("upgrade snapshot contains a portable export") }
 wrong := append([]byte(nil),key...); defer clear(wrong); wrong[0] ^= 1
 _,wrongFiles,err := readBackupPolicy(opt.Snapshot,wrong,policy)
 if err == nil || err.Error() != "BACKUP_MANIFEST_INVALID" || wrongFiles != nil { t.Fatalf("wrong key did not fail snapshot authentication: %v",err) }
'''
 candidates=[];unchanged=[];testdelta=None
 for v in hd["candidate_files"]:
  source=Path(v["path"]);raw=guard.get_buffer(str(source));assert pin(source)==verify(v)
  rel=source.relative_to(Path(hd["candidate_root"]));target=root/rel;target.parent.mkdir(parents=True,exist_ok=True)
  if rel.as_posix()=="internal/domain/backup_history20_upgrade_test.go":
   assert hashlib.sha256(raw).hexdigest()=="551fe9ce8092d241e90006a2654697ab63dc3926746750d26fb4bba913a73ba1"
   text=raw.decode("utf-8");assert text.count(' "context"\n')==1 and text.count(oldblock)==1
   changed=text.replace(' "context"\n',' "context"\n "encoding/json"\n').replace(oldblock,newblock)
   inverse=changed.replace(newblock,oldblock).replace(' "context"\n "encoding/json"\n',' "context"\n')
   assert inverse.encode()==raw
   assert changed.count("func TestHistory20")==5
   assert "RestoreBackup(context.Background(),opt.Snapshot" not in changed
   testdelta=dict(source_ref=v,old_block=oldblock,new_block=newblock,full_inverse_equal=True,positive_read_precedes_wrong_key=True,same_snapshot_and_policy=True,only_key_varies=True,required_wrong_key_error="BACKUP_MANIFEST_INVALID",correct_key_required_file="state.sqlite",source_test_parents=5,Go_compile_or_runtime=False)
   raw=changed.encode()
  else:unchanged.append(dict(source_ref=v,new_path=str(target),bytes_equal=True))
  with target.open("xb") as f:f.write(raw)
  candidates.append(pin(target))
 assert len(candidates)==5 and len(unchanged)==4 and testdelta is not None
 for v in unchanged:assert Path(v["source_ref"]["path"]).read_bytes()==Path(v["new_path"]).read_bytes()
 save("test-only-correction.provenance.json",dict(finding_id="H20R-001",old_source_handoff_ref=pin(A/"HDF.json"),old_source_manifest_ref=pin(A/"MF.json"),independent_request_changes_ref=pin(V/"HDF.json"),test_delta=testdelta,other_four_candidates_byte_equal=unchanged,baseline66_pins=baseline,production_paths_unchanged=True,historical_templates_unchanged=True,formal_acceptance=False))
finally:
 cleanup=guard.close();save("guard.final.json",cleanup);assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
mf=save("MF.json",dict(members=[pin(p) for p in O.rglob("*") if p.is_file()]))
hdf=save("HDF.json",dict(schema="researchos.history20-upgrade-source-test-correction-handoff.v1",status="H20R001_SOURCE_FIXED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_GO_SQL",candidate_root=str(root),candidate_files=candidates,old_handoff_ref=pin(A/"HDF.json"),old_manifest_ref=pin(A/"MF.json"),review_ref=pin(V/"HDF.json"),manifest_ref=mf,correction_ref=pin(O/"test-only-correction.provenance.json"),guard_ref=pin(O/"guard.final.json"),only_test_source_changed=True,other4_candidates_byte_equal=True,baseline66_pins_unchanged=True,Go_SQL_native_execution=False,Main_adopted=False,overall20_to24="OPEN",formal_acceptance=False))
print(json.dumps(dict(handoff_ref=hdf,manifest_ref=mf,candidates=candidates,guard_closed=True)))

