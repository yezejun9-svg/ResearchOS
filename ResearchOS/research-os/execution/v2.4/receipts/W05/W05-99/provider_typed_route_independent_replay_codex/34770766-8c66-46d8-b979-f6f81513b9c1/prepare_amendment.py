import pathlib,json,hashlib,difflib
M=pathlib.Path('D:/作品集/ResearchOS/research-os');H=pathlib.Path(__file__).resolve().parent;OLD=H.parent/'7dcde82f-d47d-4c69-989f-3a1c59f929ab';A=M/'execution/v2.4/receipts/W05/W05-99/integration_codex/context-and-overlay-amendments-r289/attempt3-frozen-inputs/overlay_prepare_scope_amendment.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def write(n,o):(H/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(A)=='d30e8ad95502e3701649c6feafeb3000a107599b2f56683c5c08ef7defa5063e';a=json.loads(A.read_text(encoding='utf-8'));original=OLD/'independent_provider_public_boundary_windows_test.go';assert sha(original)==a['original_overlay_ref']['sha256']
raw=original.read_text(encoding='utf-8-sig');old='delta[n]=Object{"before":Hash(b),"after":Hash(a)}}';assert raw.count(old)==1;fixed=raw.replace(old,old+'}')
old='inv:=independentInventory(t,db);if len(inv)!=int(Num(spec["expected_inventory"])){t.Fatal("nonempty original inventory")}';new='inv:=independentInventory(t,db);expected,numberErr:=Num(spec,"expected_inventory");if numberErr!=nil||expected<1{t.Fatal("invalid expected inventory",numberErr)};if len(inv)!=int(expected){t.Fatal("nonempty original inventory")}';assert fixed.count(old)==1;fixed=fixed.replace(old,new)
(H/original.name).write_text(fixed,encoding='utf-8',newline='\n');(H/'overlay-authorized.diff').write_text(''.join(difflib.unified_diff(raw.splitlines(True),fixed.splitlines(True),fromfile=str(original),tofile=str(H/original.name))),encoding='utf-8')
for n in ['export.json','synthetic_workspace_evidence.txt']:(H/n).write_bytes((OLD/n).read_bytes())
(H/'inputs').mkdir();inputs=json.loads((OLD/'original7.before.json').read_text(encoding='utf-8'))
for e in inputs:
 src=pathlib.Path(e['original']['path']);assert sha(src)==e['original']['sha256'];dst=H/'inputs'/(e['id']+'.sqlite');dst.write_bytes(src.read_bytes());e['copy']=ref(dst)
write('original7.before.json',inputs)
driver=(OLD/'driver.py').read_text(encoding='utf-8-sig').replace("ROOT/'cache/tmp'","ROOT/'cache-r289/tmp'").replace("ROOT/'cache/go'","ROOT/'cache-r289/go'")
driver=driver.replace("str(SCOPE)]","str(SCOPE),str(HERE/'amendment-ref.json'),str(pathlib.Path(json.loads((HERE/'amendment-ref.json').read_text(encoding='utf-8'))['path']))]")
(H/'driver.py').write_text(driver,encoding='utf-8',newline='\n');write('amendment-ref.json',ref(A));write('authorized-repair.json',{'amendment':ref(A),'original_overlay':ref(original),'new_overlay_before_gofmt':ref(H/original.name),'changes':a['exact_changes'],'old_raw_preserved':True,'previous_cases':0})
print(json.dumps({'root':str(H),'overlay':ref(H/original.name)},ensure_ascii=False))
