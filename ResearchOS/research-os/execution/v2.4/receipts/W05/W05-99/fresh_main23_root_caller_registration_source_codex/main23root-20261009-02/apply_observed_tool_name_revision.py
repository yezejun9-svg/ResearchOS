import sys
sys.dont_write_bytecode=True
import ast
import difflib
import hashlib
import json
from pathlib import Path
import traceback
Q=Path(__file__).resolve().parent
def ref(path,raw):return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value,raw=False):
    path=Q/name;data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as s:assert s.write(data)==len(data)
    return ref(path,data)
def main():
    path=Q/'main23_root.source.py';before=path.read_bytes()
    assert hashlib.sha256(before).hexdigest()=='3051b93871f9028bdfcecce11be5fe0b0cc4be843de344844ffc18791aca5619'
    old=b'and call.get("name") in {"functions.exec", "functions.exec_command"}'
    new=b'and call.get("name") in {"exec", "functions.exec", "exec_command", "functions.exec_command"}\r\n         and (call.get("name") in {"exec_command", "functions.exec_command"} or (type(call.get("input", call.get("arguments"))) is str and "tools.exec_command" in call.get("input", call.get("arguments"))))'
    assert before.count(old)==1
    offset=before.index(old);after=before[:offset]+new+before[offset+len(old):]
    assert after[:offset]+old+after[offset+len(new):]==before
    compile(after,str(path),'exec');ast.parse(after)
    snapshot=save('pre-observed-tool-name.caller.py',before,True)
    with path.open('wb') as s:assert s.write(after)==len(after)
    save('observed-tool-name.exact-inverse.json',{'schema':'researchos.main23-observed-tool-name-byte-inverse.v1',
        'previous_candidate_ref':snapshot,'previous_candidate_original_ref':ref(path,before),'candidate_ref':ref(path,after),
        'offset':offset,'old_utf8':old.decode(),'new_utf8':new.decode(),'full_byte_inverse_equal':True,
        'base_inverse_chain_ref':ref(Q/'exact-inverse.json',(Q/'exact-inverse.json').read_bytes()),
        'reason':'Actual owned audit has custom_tool_call.name=exec. Bare/qualified exec are explicit aliases; no unknown tool is admitted. exec wrapper must actually request tools.exec_command.',
        'Main_Canon_writes':0,'authority':'NONE'})
    save('observed-tool-name.diff',''.join(difflib.unified_diff(before.decode('utf-8').splitlines(True),after.decode('utf-8').splitlines(True),fromfile='candidate-before-actual-audit',tofile='candidate-final')).encode('utf-8'),True)
    base=(Q/'inputs/base-main23_root.source.py').read_bytes()
    save('caller.final.diff',''.join(difflib.unified_diff(base.decode('utf-8').splitlines(True),after.decode('utf-8').splitlines(True),fromfile='immutable-v1',tofile='candidate-final')).encode('utf-8'),True)
    binding=json.loads((Q/'actual-source-hostpairs/input-read.binding.json').read_text(encoding='utf-8'))
    identity=binding['header_public_identity']
    assert identity['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084'
    print(json.dumps({'candidate_ref':ref(path,after),'actual_source_header_identity':identity,'authority':'NONE'},ensure_ascii=False))
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
