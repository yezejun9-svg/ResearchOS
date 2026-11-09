# New receipt-subset inventory; original protected Main references remain metadata-only.
import base64,hashlib,json,re,stat,zipfile
from pathlib import Path, PurePosixPath
ROOT=Path("D:/作品集/ResearchOS/research-os")
RECEIPTS=ROOT/"execution/v2.4/receipts/W05/W05-99"
OWN=ROOT/"execution/v2.4/receipts/W05/W05-99/f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af"
AUTHOR=RECEIPTS/"f08_sqlite_driver18_validation_preparation_codex/a84ef66a214346e4891e569c55bc6d9b"
ZIPNS=RECEIPTS/"f08_sqlite_mirror_zip_resource_codex/fc99cb027905472881ba5de3ecd6df84"
SOURCE=RECEIPTS/"f08_sqlite_complete_fork_resource_codex/29646a104712459fb211fc6f80545bf0"
seen={}
errors=[]
def meta(p):
 p=Path(p)
 resolved=p.resolve(strict=True)
 if not resolved.is_relative_to(RECEIPTS.resolve()): raise ValueError("outside frozen receipt scope: "+str(p))
 for a in [p,*p.parents]:
  if a==ROOT.parent:break
  s=a.lstat()
  if a.is_symlink() or getattr(s,"st_file_attributes",0)&0x400:raise ValueError("symlink/reparse input: "+str(a))
 if not stat.S_ISREG(p.stat().st_mode):raise ValueError("non-regular input")
 b=p.read_bytes();d={"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
 seen[d["path"]]=d
 return d,b
def refcheck(r):
 a,b=meta(r["path"])
 if a["sha256"]!=r["sha256"] or a["bytes"]!=r["bytes"]:errors.append({"expected":r,"actual":a})
 return b
def refs(o):
 if isinstance(o,dict):
  if {"path","sha256","bytes"}<=o.keys():yield o
  else:
   for v in o.values():yield from refs(v)
 elif isinstance(o,list):
  for v in o:yield from refs(v)
def jload(p):return json.loads(meta(p)[1])
def write(name,obj):
 p=OWN/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="\n") as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write("\n")
packets=[]
for ns,label in [(AUTHOR,"author-packet"),(ZIPNS,"mirror-packet")]:
 mf=jload(ns/"manifest.json")
 for r in mf["files"]:
  b=refcheck(r);rel=Path(r["path"]).relative_to(ns)
  if rel.as_posix()!="response.body":
   dst=OWN/"snapshots"/label/rel;dst.parent.mkdir(parents=True,exist_ok=True)
   if dst.exists():
    if dst.read_bytes()!=b:raise ValueError("existing snapshot byte drift")
   else:
    with dst.open("xb") as f:f.write(b)
 actual={p.relative_to(ns).as_posix() for p in ns.rglob("*") if p.is_file()}
 listed={Path(r["path"]).relative_to(ns).as_posix() for r in mf["files"]}
 packets.append({"label":label,"manifest":meta(ns/"manifest.json")[0],"listed":len(listed),"actual":len(actual),"missing":sorted(listed-actual),"extras":sorted(actual-listed-{"manifest.json"})})
 dst=OWN/"snapshots"/label/"manifest.json";dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():
  if dst.read_bytes()!=(ns/"manifest.json").read_bytes():raise ValueError("existing manifest snapshot drift")
 else:
  with dst.open("xb") as f:f.write((ns/"manifest.json").read_bytes())
 for o in [jload(ns/"handoff.json")]:
  for r in refs(o):refcheck(r)
proposal=jload(AUTHOR/"proposal.json")
for r in refs(proposal):refcheck(r)
pairs=jload(AUTHOR/"inputs.before.json")+jload(AUTHOR/"inputs.additional.json")
after=jload(AUTHOR/"inputs.after.json")
pair_report=[]
for x in pairs:
 copy=refcheck(x["copy"])
 if Path(x["original"]["path"]).is_relative_to(RECEIPTS):
  original=refcheck(x["original"]);equal=original==copy;observation="ACTUAL_RECEIPT_BYTES"
 else:
  original=None;equal=None;observation="MAIN_ORIGINAL_NOT_READ_COPY_HASH_ONLY"
 pair_report.append({"original":x["original"],"copy":x["copy"],"bytes_equal":equal,"original_observation":observation})
if pairs!=after["pairs"] or after["drift"]:errors.append({"pair_vector_metadata_changed":True})
fork=jload(SOURCE/"fork.file-lock.json")
for r in fork["files"]:refcheck(r)
fork_root=Path(fork["root"])
actual_fork={p.relative_to(fork_root).as_posix() for p in fork_root.rglob("*") if p.is_file()}
listed_fork={r["relative_path"] for r in fork["files"]}
if actual_fork!=listed_fork:errors.append({"fork_directory_delta":sorted(actual_fork^listed_fork)})
original=jload(SOURCE/"module.before.json")
original_index={r["relative_path"]:r for r in original["files"]}
fork_index={r["relative_path"]:r for r in fork["files"]}
actual_delta=[n for n in sorted(fork_index) if (fork_index[n]["sha256"],fork_index[n]["bytes"])!=(original_index[n]["sha256"],original_index[n]["bytes"])]
archive_ref=jload(ZIPNS/"handoff.json")["archive_ref"]
archive=refcheck(archive_ref)
stated=jload(ZIPNS/"zip-members.verified.json")
stated_index={r["relative_path"]:r for r in stated}
ziprows=[];unsafe=[];total=0
with zipfile.ZipFile(Path(archive_ref["path"])) as z:
 infos=z.infolist();names=[i.filename for i in infos]
 if len(names)!=len(set(names)):unsafe.append("duplicate names")
 for i in infos:
  pp=PurePosixPath(i.filename)
  if i.is_dir() or not i.filename.startswith("modernc.org/sqlite@v1.60.1/") or pp.is_absolute() or ".." in pp.parts or "\\" in i.filename or stat.S_ISLNK(i.external_attr>>16):
   unsafe.append(i.filename);continue
  rel=i.filename[len("modernc.org/sqlite@v1.60.1/"):]
  b=z.read(i);total+=len(b)
  row={"relative_path":rel,"zip_name":i.filename,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
  ziprows.append(row)
  o=original_index.get(rel);s=stated_index.get(rel)
  if o is None or s is None or row!=s or (row["sha256"],row["bytes"])!=(o["sha256"],o["bytes"]):
   errors.append({"zip_original_or_stated_mismatch":row})
digest=hashlib.sha256()
for r in sorted(ziprows,key=lambda r:r["zip_name"].encode("utf-8")):
 digest.update((r["sha256"]+"  "+r["zip_name"]+"\n").encode("utf-8"))
h1="h1:"+base64.b64encode(digest.digest()).decode()
expected_h1="h1:/blz53O951KWFOso4QQvEs/Fq6cDBKLtMVrYNSeJVKw="
if h1!=expected_h1:errors.append({"zip_h1_mismatch":h1})
if set(r["relative_path"] for r in ziprows)!=set(original_index):errors.append({"zip_inventory_mismatch":True})
for ns in [SOURCE]:
 for r in refs(jload(ns/"handoff.json")):refcheck(r)
origin_files=[
RECEIPTS/"f08_sqlite_upstream_zip_resource_codex/8c2f06c01895426ea1e31317664a7748/failure-origins.json",
RECEIPTS/"f08_sqlite_complete_fork_resource_codex/29646a104712459fb211fc6f80545bf0/failure-origin.4024a7.json",
RECEIPTS/"f08_sqlite_complete_fork_resource_independent_review_codex/dd62b57442844767ac22716ffefe5061/failure-origin.send-message-thread-limit.json",
RECEIPTS/"f08_sqlite_innocuous_driver_independent_source_review_codex/734ee12d8b8d404798c2ec6e6e1f56bc/REVIEW.md",
SOURCE/"origin/dirhash-hash.go",
SOURCE/"consumer-and-driver-validation.contract.proposed.json"
]
origin_refs=[]
for i,p in enumerate(origin_files):
 m,b=meta(p);origin_refs.append(m)
 dst=OWN/"snapshots"/"linked-evidence"/(str(i).zfill(2)+"-"+p.name);dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open("xb") as f:f.write(b)
report={"schema":"researchos.driver18-independent-input-verification.v1","packets":packets,"pairs":pair_report,"author_vectors":{"before":len(pairs),"after":len(after["pairs"]),"metadata_equal":pairs==after["pairs"],"author_drift":after["drift"]},"fork":{"lock":meta(SOURCE/"fork.file-lock.json")[0],"count":len(fork["files"]),"bytes":sum(r["bytes"] for r in fork["files"]),"actual_delta_vs_original_frozen_metadata":actual_delta,"actual_directory_equal":actual_fork==listed_fork},"ZIP":{"archive":archive_ref,"actual_members":len(ziprows),"actual_uncompressed_bytes":total,"unsafe":unsafe,"all_original_frozen_metadata_and_stated_rows_match":not any("zip_original_or_stated_mismatch" in e for e in errors),"actual_h1":h1,"expected_h1":expected_h1,"cache_read":False,"HTTP_called":False,"archive_extracted":False,"upstream_or_sumdb_authentication":"OPEN"},"linked_evidence":origin_refs,"errors":errors,"scope":{"only_public_receipt_inputs":True,"author_helper_execution":False,"Go_AST_compile_SQL_HTTP_driver":False}}
write("input-verification.json",report)
write("input-vector.before.json",sorted(seen.values(),key=lambda r:r["path"]))
write("zip-members.independent.json",ziprows)
print(json.dumps({"packets":packets,"author_pairs":len(pairs),"full_fork":report["fork"],"ZIP":report["ZIP"],"actual_frozen_inputs":len(seen),"errors":errors},ensure_ascii=False))

