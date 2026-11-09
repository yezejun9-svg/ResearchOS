import sys
sys.dont_write_bytecode=True
import json,hashlib,ast
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
A=B/"integration_codex/attach-fixture-current-two-parent-root-source-t11-1a11e7f5205729390aaee9f47b28ce6"
ISO=B/"integration_codex/attach-fixture-two-parent-sparse-isolation-root-1791516205000"
OUT=B/"integration_codex/attach-fixture-two-parent-sparse-target-root-1791516205000"
T=R/".local/worktrees/t11s-1791516205000"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
expected={"prepare_attach_fixture_two_parent.actual_owned.py":("4694aa929b27da960e23511be26da59a016e4a9b4f7296667335ebe6edca6020",7263),"validate_attach_fixture_two_parent.actual_owned.py":("05c9c83463c8abd58d7ca4f92c56a8ed96e5a3a0a1cd22036613043f41ba3229",17560),"source.integration.choice.json":("44afd8c086194419cc2f6f12ba01916adb2f8846345c7989e3fe071d046f79fc",19864)}
inputs=[]
for name,(sha,size) in expected.items():
 ref=pin(A/name);assert (ref["sha256"],ref["bytes"])==(sha,size);inputs.append(ref)
 assert not (O/name).exists()
old_iso=str(A).replace("root-source","isolation")
old_out=str(A).replace("root-source","targeted")
old_t=str(R/".local/worktrees/codex-w0599-attach-fixture-current-two-parent-t11-1a11e7f5205729390aaee9f47b28ce6").replace("\\","/")
changes=[]
for name in ("prepare_attach_fixture_two_parent.actual_owned.py","validate_attach_fixture_two_parent.actual_owned.py"):
 raw=(A/name).read_bytes();text=raw.decode("utf-8");replacements=[]
 for before,after in ((old_iso.replace("\\","/"),str(ISO).replace("\\","/")),(old_out.replace("\\","/"),str(OUT).replace("\\","/")),(old_t,str(T).replace("\\","/"))):
  count=text.count(before)
  if count:
   text=text.replace(before,after);replacements.append({"before":before,"after":after,"count":count})
 if name.startswith("prepare"):
  old='create=invoke("create-worktree",[str(git),"-c","core.hooksPath="+str(scratch/"empty-hooks"),"worktree","add","--detach",str(T),expected],180)'
  new='create=invoke("create-worktree",[str(git),"-c","core.hooksPath="+str(scratch/"empty-hooks"),"worktree","add","--no-checkout","--detach",str(T),expected],180)'
  assert text.count(old)==1;text=text.replace(old,new);replacements.append({"before":old,"after":new,"count":1})
  anchor=' verify_after=invoke("head-after"'
  insert=''' # Only this newly created detached worktree's metadata receives patterns.
 git_file=(T/".git").read_text(encoding="utf-8").strip()
 assert git_file.startswith("gitdir: ")
 metadata=Path(git_file[8:]).resolve()
 assert metadata.is_relative_to((R/".git/worktrees").resolve()) and (metadata/"gitdir").read_text(encoding="utf-8").strip().replace("\\\\","/").casefold()==str(T/".git").replace("\\\\","/").casefold()
 sparse=metadata/"info/sparse-checkout";assert not sparse.exists();sparse.parent.mkdir(exist_ok=True)
 product_dirs=("adapters","apps","bootstrap","contracts","docs","evaluation","internal","migrations","ops","qualification","release","scripts","spec","tests","third_party")
 patterns="/*\\\\n!/*/\\\\n"+"".join("/"+name+"/\\\\n" for name in product_dirs)+"/execution/\\\\n!/execution/*/\\\\n/execution/toolchains/\\\\n"
 with sparse.open("x",encoding="utf-8",newline="\\\\n") as stream:stream.write(patterns)
 sparse_ref=save("sparse-checkout.patterns.public.json",dict(worktree=str(T),metadata=str(metadata),pattern_ref=pin(sparse),patterns=patterns,excluded_history_receipts=True,shared_git_config_mutated=False))
 checkout=invoke("checkout-product-source",[str(git),"-C",str(T),"-c","core.hooksPath="+str(scratch/"empty-hooks"),"-c","core.sparseCheckout=true","-c","core.sparseCheckoutCone=false","read-tree","-mu","HEAD"],180)
 assert not (T/"execution/v2.4/receipts").exists() and not (T/"execution/verifier").exists()
 assert (T/"execution/toolchains/locked.json").is_file() and all((T/name).is_dir() for name in product_dirs)
'''
  # Generated inner script needs actual escapes, not doubled literal line breaks.
  insert=insert.replace('\\\\n','\\n')
  assert text.count(anchor)==1;text=text.replace(anchor,insert+anchor)
  replacements.append({"before":anchor,"after":insert+anchor,"count":1})
  for before,after in (('invocation_refs=[verify,tracked,staged,create,verify_after]','invocation_refs=[verify,tracked,staged,create,checkout,verify_after],sparse_checkout_ref=sparse_ref,checkout_strategy="SOURCE_AND_REQUIRED_CONFIG_ONLY"'),('owned_jobs=5','owned_jobs=6')):
   assert text.count(before)==1;text=text.replace(before,after);replacements.append({"before":before,"after":after,"count":1})
 ast.parse(text,filename=name)
 inverse=text
 for item in reversed(replacements):
  assert inverse.count(item["after"])==item["count"];inverse=inverse.replace(item["after"],item["before"])
 assert inverse.encode("utf-8")==raw
 with (O/name).open("xb") as f:f.write(text.encode("utf-8"))
 changes.append(dict(name=name,old_ref=pin(A/name),new_ref=pin(O/name),exact_inverse=True,sequential_replacements=replacements))
with (O/"source.integration.choice.json").open("xb") as f:f.write((A/"source.integration.choice.json").read_bytes())
assert pin(O/"source.integration.choice.json")["sha256"]==expected["source.integration.choice.json"][0]
proof=save("adaptation.provenance.json",dict(schema="researchos.root-t11-sparse-source-adaptation.v1",old_source_inputs=inputs,changes=changes,choice_bytes_unchanged=True,main_and_canonical_written=False,actual_ran=False,formally_accepted=False,new_worktree=str(T),new_isolation=str(ISO),new_target=str(OUT),owned_Git_jobs=6,all_original_validation_guards_and_compiler_inventory_unchanged=True))
mf=save("MF.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
hd=save("HDF.json",dict(status="SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL",manifest_ref=mf,provenance_ref=proof,required_review="Exact inverse and new sparse checkout scope, own metadata only, original five guards/compiler inputs unchanged",formal_acceptance=False))
print(json.dumps(dict(handoff_ref=hd,manifest_ref=mf)),flush=True)

