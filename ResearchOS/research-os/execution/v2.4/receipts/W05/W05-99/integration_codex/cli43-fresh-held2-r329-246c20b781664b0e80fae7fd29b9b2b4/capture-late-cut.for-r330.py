"""Root fixed capture of 21 distinct late origins; metadata IO only, no canonical mutation."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json
ROOT=Path(r"D:\作品集\ResearchOS\research-os")
BASE=ROOT/"execution/v2.4/receipts/W05/W05-99"
OUT=Path(__file__).absolute().parent
SPECS=json.loads(r'''[["f08_i17_binding_revision_preparation_codex/b918c16361bb4744bc7fffb6434d6849/original-parser-failure.json","426fbd654057f11215518768cc22b13ad42efa783aaa881b3b95ea032a2dc609"],["cli43_current_bound_scope_independent_review_codex/2770189c101441f39fcbe8fd83d98ffd/failure-origin.89547b.json","1426ec637e324b5a822979f000d89205b56ff08e343a9f3d5c4827e46cccf890"],["f08_i17_binding_revision_independent_source_review_codex/f55ac9fdfb3d4a929686b6884431f962/origin.metadata-js-parser.json","c5f4a5b97a61e2f9cab5974ea063649fdbe1590f3aece3a30861437044dfbc7e"],["integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4/failure-origin.96b781.json","ca09bee2f6d818a616cb564ff6b2f772e574a7bb0d0857e2723acff7e7ebc3d3"],["integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4/failure-origin.df2508.json","e8c0ce3833632ab277f03495099112572acb0066e0f9f52a2cd879ee72c50cca"],["integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4/failure-origin.f00142.json","61350d9438eef65b9a2c8ae31a63bda68569b0e0e8bedfa4359e3f7806b7c159"],["f08_driver18_controller_v3_independent_source_review_codex/3b5ae723087647b6a884329c2ff8518c/origin.I18-regex-shape.json","aeb849e1d573fa9bfd0f6bb4add88d520982e4a3e20ed285c3806632c1404138"],["f08_driver18_controller_v3_independent_source_review_codex/3b5ae723087647b6a884329c2ff8518c/origin.I17-diagnostic-literal.json","32bcbb68a177a67e48b2039d4f84b7328bbeaa55c47da6c7ce99b0e14142549d"],["f08_i17_binding_revision_preparation_codex/66ec5753ea3249d0940b157e51a87968/origin.rg-absent-specs.json","7ebfbda64e9ab56e353f554be8ffcc9908fb2e9c2e9aff6de5d55e8c4dc8c402"],["f08_i17_binding_revision_preparation_codex/66ec5753ea3249d0940b157e51a87968/origin.metadata-membership.json","1845128f399bb1ccbe2ad0955cfebed40aaec99f2a8298ca229c52d6624c737e"],["f08_i17_binding_revision_preparation_codex/66ec5753ea3249d0940b157e51a87968/origin.metadata-vector-newline.json","c811e59595cea0f8432e2b5674f143a25030f2cec6bd610a64571a2a682e4229"],["f08_i17_binding_revision_preparation_codex/66ec5753ea3249d0940b157e51a87968/origin.metadata-BLOB-occurrence-count.json","01d4897df58375a303f1a500989336a8f2c93330cf617aab814f2b748632bf34"],["cli43_transport_entity_binding_mapping_codex/146dc642b6c64db3a2d08dc47da10764/origin.rg-missing-cmd.json","baff0eeb363c306f7afdb6249d1723615c6fcc58a10250769c1ae5af0b865a0a"],["cli43_transport_entity_binding_mapping_codex/146dc642b6c64db3a2d08dc47da10764/origin.rg-missing-handler.json","2630c9dbe28e59a892a3abb2ab2f783d8bfc205fe4276b7c79d381695a519b88"],["cli43_transport_entity_binding_mapping_codex/146dc642b6c64db3a2d08dc47da10764/origin.null-base64-shape.json","7575ca15f0d6a9ec02f0649ddc34e52f03fa594613a4b8820c1d0bbb6e7236c5"],["cli43_fresh_compiler_executor_codex/246c20b781664b0e80fae7fd29b9b2b4/failure.origin.json","6da76d8b2958f08c6aba95d471149c137f3f25dcd4ac74e4081e9ffc16c44d23"],["f08_i17_revision_source_independent_review_codex/7e084f8c6c9b45afa1ad9c50b4a650da/failure.origin.json","85d1a3c70900b73450646e522caec23c1d38f47d62f78582431081fe36517f23"],["f08_i17_revision_source_independent_review_codex/7e084f8c6c9b45afa1ad9c50b4a650da/failure.origin.vector-classification.json","4eee6789c44646c2b9b2c41a7a032c250c13ca636de452998a59e8a8f1bdf77c"],["cli43_transport_binding_preparation_codex/b69ddf4c7d564a33b017dff4b1a48f2e/diagnostic.origin.null-property.json",null],["cli43_transport_binding_preparation_codex/b69ddf4c7d564a33b017dff4b1a48f2e/diagnostic.origin.absent-client-protocol.json",null],["cli43_transport_binding_preparation_codex/b69ddf4c7d564a33b017dff4b1a48f2e/failure.origin.newline-assumption.json",null]]''')
def need(v,m):
 if not v:raise RuntimeError(m)
def pin(p):
 raw=p.read_bytes();return {"path":p.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def doc(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,"isolated metadata")
cp=doc(ROOT/"execution/v2.4/checkpoint.json");ow=doc(ROOT/"execution/v2.4/path_ownership.json")
need([cp["revision"],ow["revision"],len(cp["failure_counters"])]==[329,157,481],"actual before tuple")
closed=doc(OUT/"root-launch.outer-completion.json")
for row in closed["canonical_refs_at_completion"]:
 actual=pin(Path(row["path"]));need(actual["sha256"]==row["sha256"] and actual["bytes"]==row["bytes"],"canonical actual closure guard")
origins=[]
for rel,digest in SPECS:
 p=BASE/rel;ref=pin(p)
 if digest is not None:need(ref["sha256"]==digest,"original origin pin "+rel)
 need(all(old.get("evidence_ref",{}).get("sha256")!=ref["sha256"] for old in cp["failure_counters"]),"already registered")
 origins.append({"evidence_ref":ref,"original_payload":doc(p),"classification":"LATE_DISTINCT_ORIGINAL_FAILURE_NULL_AND_PROPAGATION_PRESERVED","counter_reset":False,"automatic_same_input_retry":False})
need(len(origins)==21 and len({r["evidence_ref"]["sha256"] for r in origins})==21,"exact distinct cut")
cut={"schema":"researchos.root-late-origin-cut.v1","actor":"codex:/root","before":[329,157,481],"after":[330,158,502],"registered_origin_count":481,"captured_late_origin_count":21,"fixed_cut_observed_origin_count":502,"observed_including_later_pending_at_capture":502,"origins":origins,"native_NULL_and_original_payloads_preserved":True,"nested_exit_propagations_counted_once":True,"nonterminating_outer_zero_diagnostics_preserved":True,"canonical_writes":0,"automatic_retry":False,"counter_reset":False,"formal_increment":0}
save(OUT/"late-origins.capture.for-r330.json",cut)
print(json.dumps({"capture_ref":pin(OUT/"late-origins.capture.for-r330.json"),"before":cut["before"],"after":cut["after"],"captured_late_origins":21,"canonical_unchanged":True},ensure_ascii=False))
