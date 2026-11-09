import ast, hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_root_inputs_walk_revision_preparation_codex/1c4ea6999d4d4437a0202c4e81ce581b"
SOURCE=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_root_inputs_source_preparation_codex/5de88f71cba44dd8a43ed83739d6f854/construct_root_inputs.desktop58.v2.py"
def need(ok, why):
    if not ok: raise RuntimeError(why)
def pin(p):
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name, value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    p=BASE/name
    with p.open('xb') as stream: stream.write(raw)
    return pin(p)
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'Pinned flags')
BASE.mkdir(parents=True,exist_ok=True)
old=SOURCE.read_bytes()
need(hashlib.sha256(old).hexdigest()=='2e51ef50c02c190aef23e346a35724fddc8e8fed1360d78e2d6b49b2090b06d8' and len(old)==24100,'Source pin')
needle=b"    found = set()\n    for directory, dirs, files in os.walk(root, topdown=True, followlinks=False):\n"
replacement=b"    found = set()\n    def abort_walk(error):\n        raise error\n    for directory, dirs, files in os.walk(root, topdown=True, onerror=abort_walk, followlinks=False):\n"
need(old.count(needle)==1,'Unique source block')
new=old.replace(needle,replacement,1)
need(new.replace(replacement,needle,1)==old,'Exact whole-file inverse')
old_ast=ast.parse(old)
new_ast=ast.parse(new)
unchanged=[]
for item in old_ast.body:
    if isinstance(item,(ast.FunctionDef,ast.AsyncFunctionDef)) and item.name!='physical_members':
        target=next(x for x in new_ast.body if isinstance(x,type(item)) and x.name==item.name)
        need(ast.dump(item,include_attributes=False)==ast.dump(target,include_attributes=False),'AST drift '+item.name)
        need(ast.get_source_segment(old.decode('utf-8'),item)==ast.get_source_segment(new.decode('utf-8'),target),'Byte drift '+item.name)
        unchanged.append(item.name)
compile(new,str(BASE/'construct_root_inputs.desktop58.v3.py'),'exec')
out=BASE/'construct_root_inputs.desktop58.v3.py'
with out.open('xb') as stream: stream.write(new)
source_ref=pin(out)
inverse=save('source-inverse.v3.json',{'schema':'researchos.desktop58-constructor-source-inverse.v1','old_ref':pin(SOURCE),'new_ref':source_ref,'whole_file_inverse':True,'changed_functions':['physical_members'],'unchanged_function_names':unchanged,'enumeration_error_behavior':'callback raises the original OSError; no retry or catch','candidate_execution':0,'canonical_writes':0,'formal_increment':0})
origin=json.loads("{\"schema\":\"researchos.failure-origin.v1\",\"actor\":\"codex:/root\",\"kind\":\"metadata-read-path-spelling\",\"observed_failure_ordinal\":554,\"registered_failure_count\":532,\"frozen_desktop58_cut\":553,\"after_fixed_cut\":true,\"python_exit_code\":null,\"native_exit_code\":1,\"description\":\"Initial resumed source read used a nonexistent receipt path. No Python, constructor, target or canonical operation occurred. Corrected path read succeeded; immutable cut not amended.\",\"tool_observation\":{\"input\":{\"cmd\":\"$ErrorActionPreference='Stop'\\nGet-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/P13/desktop58_root_inputs_source_preparation_codex/5de88f71cba44dd8a43ed83739d6f854/construct_root_inputs.desktop58.v2.py' -TotalCount 180\",\"max_output_tokens\":6000},\"result\":{\"chunk_id\":\"1743fe\",\"wall_time_seconds\":0.7823743,\"exit_code\":1,\"original_token_count\":110,\"output\":\"Get-Content: \\r\\nLine |\\r\\n   3 |  Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2. …\\r\\n     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\\r\\n     | Cannot find path 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/P13/desktop58_root_inputs_source_preparation_codex/5de88f71cba44dd8a43ed83739d6f854/construct_root_inputs.desktop58.v2.py' because it does not exist.\\r\\n\"}}}")
origin_ref=save('failure-origin.after-cut.metadata-read-path.json',origin)
hdf=save('handoff.json',{'schema':'researchos.desktop58-constructor-source-revision-handoff.v1','actor':'codex:/root','decision':'SOURCE_PREPARATION_ONLY_AWAITING_INDEPENDENT_REVIEW','requested_change':'D58-CONSTRUCTOR-R01','constructor_ref':source_ref,'original_source_ref':pin(SOURCE),'inverse_ref':inverse,'pending_after_cut_origin_ref':origin_ref,'observed_failure_count':554,'fixed_cut_count':553,'constructor_invocations':0,'canonical_writes':0,'formal_increment':0})
entries=[pin(BASE/'revise_source.py'),source_ref,inverse,origin_ref,hdf]
mf=save('manifest.json',{'schema':'researchos.source-preparation-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({'source_ref':source_ref,'handoff_ref':hdf,'manifest_ref':mf,'inverse_ref':inverse,'pending_after_cut_origin_ref':origin_ref,'unchanged_functions':len(unchanged),'canonical_writes':0,'constructor_invocations':0},ensure_ascii=False))

