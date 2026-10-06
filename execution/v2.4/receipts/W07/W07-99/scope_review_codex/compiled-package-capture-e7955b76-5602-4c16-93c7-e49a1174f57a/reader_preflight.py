import importlib.util,json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
COL=ROOT/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/run-c495292dee2d4e4fba7bb11a06979907'
def load(name):
    path=ROOT/'execution/v2.4'/name
    spec=importlib.util.spec_from_file_location('independent_'+name.removesuffix('.py'),path)
    module=importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
    return module
def ref(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
API=load('formal_case_index.py');PROFILE=load('formal_profile_w07.py')
proof=API.strict_json((COL/'proof.json').read_bytes())
source=API.strict_json((ROOT/proof['source_before_ref']['path']).read_bytes())
tools=API.strict_json((ROOT/proof['version_vector_ref']['path']).read_bytes())['tool']
context={'compilation_invocation_ref':ref(COL/'go-list.invocation.json')}
result={'mode':'ACTUAL_MAIN_READ_ONLY_COMPILED_INPUTS_PRECHECK','formal_acceptance':False,'network_calls':0,'proof':ref(COL/'proof.json'),'reader':ref(ROOT/'execution/v2.4/formal_profile_w07.py')}
reader=API.Reader(ROOT)
try:
    PROFILE._compiled_inputs(API,reader,context,proof,source,tools,API.interval(proof,'actual proof'))
    raise AssertionError('incomplete actual main vector unexpectedly accepted')
except API.InvalidEvidence as exc:
    result['actual_rejection']={'code':exc.code,'message':str(exc)}
    assert exc.code=='SOURCE_COVERAGE'
reader.finish()
result['files_read']=len(reader.read_hashes)
(OUT/'reader_preflight.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
