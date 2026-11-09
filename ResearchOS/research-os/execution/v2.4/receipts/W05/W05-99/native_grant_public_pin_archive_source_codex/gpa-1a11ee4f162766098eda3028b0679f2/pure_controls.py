import ast, copy, json, sys, types
from pathlib import Path
sys.dont_write_bytecode=True
n=Path(__file__).parent
raw=(n/"native_grant_public_pin_archive.py").read_bytes()
m=types.ModuleType("gpa_source_controls")
m.__file__=str(n/"native_grant_public_pin_archive.py")
exec(compile(raw,m.__file__,"exec"),m.__dict__)
real_canonical=m.canonical
m.canonical=lambda p,resolve=True:real_canonical(p,False)
results=[]
def check(name,fn,reject=False):
 try:
  fn()
 except (ValueError,KeyError,TypeError) as e:
  if not reject: raise
  results.append({"name":name,"result":"PASS","expected_rejection":type(e).__name__})
 else:
  assert not reject,name
  results.append({"name":name,"result":"PASS"})
def ensure(v):assert v
def rp(role,path,sha=None,size=5):
 return {"role":role,"path":path,"sha256":sha or "sha256:"+"a"*64,"bytes":size}
temp="D:/evidence/temp"
hc={"OutputDirectory":"D:/evidence/harness","BackupProgram":rp("backup-program","D:/resident/backup.exe"),
 "ControlProgram":rp("control-program","D:/resident/control.exe")}
cfg={"Environment":{"TEMP":temp}}
opt={"Plan":m.PLAN,"SourceRoot":temp+"/source","TargetRoot":temp+"/target",
 "Snapshot":temp+"/snapshot","Destination":temp+"/restore"}
pins=[rp("source-program",hc["BackupProgram"]["path"]),rp("target-program",hc["ControlProgram"]["path"])]
for role in sorted(m.inventory_roles()):
 prefix,name=role.split(":",1); root=opt["SourceRoot" if prefix=="source-inventory" else "TargetRoot"]
 value=m.INVENTORY[name]
 pins.append(rp(role,root+"/"+name,value["sha256"],value["bytes"]))
alias=copy.deepcopy(next(p for p in pins if p["role"]==m.ALIAS_TARGET));alias["role"]=m.ALIAS_ROLE;pins.insert(0,alias)
backup=rp("encrypted-backup-manifest",opt["Snapshot"]+"/manifest.json")
rehearsal=rp("isolated-restore-rehearsal",opt["Destination"]+"/prepared-abandonment-rehearsal.json")
pins += [backup,rehearsal,rp("encrypted-backup-payload:state.sqlite.enc",opt["Snapshot"]+"/state.sqlite.enc")]
pins += [rp("fixture-evidence:"+x,hc["OutputDirectory"]+"/"+x) for x in
 ("before.rows.json","fixture.public.json","00-rehearsal/invocation.json","00-rehearsal/stdout.raw","00-rehearsal/stderr.raw")]
g={"schema":"researchos.recovery-migration-grant.v1","purpose":"RESEARCHOS_PREPARED_SCHEMA23_TO24_V1",
 "stage":"APPLY_ORIGINAL","binding":{"plan_id":m.PLAN,"backup":backup,"rehearsal":rehearsal},"options":opt,"pins":pins}
def validate(change):
 q=copy.deepcopy(g);change(q);return m.validate_grant(q,cfg,hc)
check("fixed_source_28_target_29",lambda:ensure(sum(x.startswith("source-") for x in m.inventory_roles())==28 and len(m.inventory_roles())==57))
check("full_producer_inventory",lambda:ensure(len(m.validate_grant(g,cfg,hc)[1])==60))
allpins,allowed=m.validate_grant(g,cfg,hc)
check("explicit_full_selection",lambda:ensure(m.validate_selection(list(allowed.values()),allowed)[1]==[]))
check("partial_explicit_missing",lambda:ensure(len(m.validate_selection([backup],allowed)[1])==59))
check("declared_alias_same_ref",lambda:ensure(m.same(m.plain(allpins[m.ALIAS_ROLE]),m.plain(allpins[m.ALIAS_TARGET]))))
check("uint64_precise",lambda:ensure(m.decode(b'{"n":18446744073709551615}')["n"]==18446744073709551615))
check("reject_bool_bytes",lambda:m.rawpin({**backup,"bytes":True}),True)
check("reject_float_bytes",lambda:m.rawpin({**backup,"bytes":5.0}),True)
check("reject_negative_bytes",lambda:m.rawpin({**backup,"bytes":-1}),True)
check("reject_bare_digest",lambda:m.rawpin({**backup,"sha256":"a"*64}),True)
check("reject_upper_digest",lambda:m.rawpin({**backup,"sha256":"sha256:"+"A"*64}),True)
check("reject_extra_rawpin_field",lambda:m.rawpin({**backup,"private_ref":"x"}),True)
check("reject_duplicate_json",lambda:m.decode(b'{"a":1,"a":2}'),True)
check("reject_nan_json",lambda:m.decode(b'{"a":NaN}'),True)
for name,path in [("unc","//server/share/key"),("ads","D:/temp/a:secret"),("parent","D:/temp/../key"),
 ("reserved","D:/temp/NUL"),("relative","temp/a"),("trailing","D:/temp/a.")]:
 check("reject_path_"+name,lambda p=path:m.canonical(p),True)
check("bool_integer_comparison",lambda:ensure(not m.same({"n":True},{"n":1})))
check("reject_duplicate_selection_role",lambda:m.validate_selection([backup,backup],allowed),True)
check("reject_unselected_alias_role",lambda:m.validate_selection([alias],allowed),True)
check("reject_resident_program_selection",lambda:m.validate_selection([allpins["source-program"]],allowed),True)
check("reject_selection_pin_change",lambda:m.validate_selection([{**backup,"bytes":6}],allowed),True)
check("reject_unknown_role",lambda:validate(lambda q:q["pins"].append(rp("private-key",temp+"/key.dpapi"))),True)
check("reject_private_raw_db_role",lambda:validate(lambda q:q["pins"].append(rp("encrypted-backup-payload:state.sqlite",temp+"/snapshot/state.sqlite"))),True)
check("reject_cipher_path_escape",lambda:validate(lambda q:q["pins"].append(rp("encrypted-backup-payload:key.enc","D:/private/key.enc"))),True)
check("reject_duplicate_grant_role",lambda:validate(lambda q:q["pins"].append(copy.deepcopy(q["pins"][1]))),True)
check("reject_missing_fixed_inventory",lambda:validate(lambda q:q["pins"].__delitem__(3)),True)
check("reject_alias_digest_change",lambda:validate(lambda q:q["pins"][0].update(sha256="sha256:"+"0"*64)),True)
check("reject_release_outside_temp",lambda:validate(lambda q:q["options"].update(SourceRoot="D:/private")),True)
check("reject_wrong_plan",lambda:validate(lambda q:q["options"].update(Plan="schema20-to21")),True)
check("reject_backup_key_path",lambda:validate(lambda q:q["binding"]["backup"].update(path=temp+"/snapshot/key.dpapi")),True)
check("reject_inventory_path_change",lambda:validate(lambda q:q["pins"][3].update(path=temp+"/source/private.json")),True)
check("reject_empty_selection",lambda:m.validate_selection([],allowed),True)
tree=ast.parse(raw)
run=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="run")
check("guard_finally_structure",lambda:ensure(any(isinstance(x,ast.Try) and any(isinstance(z,ast.Call) and isinstance(z.func,ast.Attribute) and z.func.attr=="close" for y in x.finalbody for z in ast.walk(y)) for x in ast.walk(run))))
check("no_key_or_database_reader",lambda:ensure(not any(isinstance(x,ast.Import) and any(a.name in ("sqlite3","subprocess","ctypes") for a in x.names) for x in ast.walk(tree))))
check("raw_copy_uses_guard_buffer",lambda:ensure('data = guard.get_buffer(pin["path"])' in raw.decode() and 'emit_new(target, data)' in raw.decode()))
m.canonical=real_canonical
copy_path=n/"raw-byte-control-copy.json"
sample=b'{"owner_id":18446744073709551615,"nested":{"private_ref":"DO_NOT_FOLLOW"},"spacing":  [1, 2]}\\n'
check("raw_byte_copy_uint64_no_recursive_follow",lambda:ensure(m.emit_new(copy_path,sample)["bytes"]==len(sample) and copy_path.read_bytes()==sample))
check("exclusive_copy_rejects_existing",lambda:m.emit_new(copy_path,sample),True)
(n/"pure-controls.results.json").write_text(json.dumps({"schema":"researchos.source-only-controls.v1","controls":results,"count":len(results),"native":False,"sql":False,"archive_run_called":False},indent=2)+"\n",encoding="utf-8")
print("GPA_PURE_CONTROLS_OK "+str(len(results)))
