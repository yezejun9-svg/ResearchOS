import sys
sys.dont_write_bytecode=True
import importlib.util
import json
from pathlib import Path
import re
import traceback

Q=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('trial_capture_guard',Q/'guard-library.py')
lib=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

def main():
    links=json.loads((Q/'final-public-links.json').read_text(encoding='utf-8'))
    source=next(v['ref'] for v in links['runner_v9_linked_public_refs'] if v['pointer']=='/source_ref')
    guard=lib.Guard()
    finished=False
    try:
        raw,actual=guard.read(lib.normalize(source['path']),source)
        lines=raw.decode('utf-8').splitlines()
        excerpts=[{'line':i+1,'text':line.strip()[:900]} for i,line in enumerate(lines) if re.search(r'host.?capt|request.?ledger|provider_requests|billing|provider_request|run_root|output_dir|trial-output|capture_dir',line,re.I)]
        doc={'schema':'researchos.original-trial-capture-contract.v1','authority':'NONE','source_ref':actual,'source_excerpts':excerpts,'interpretation':'Source-only capture contract; this Source was not executed by this reconciliation and is not actual upstream request evidence.'}
        result_ref=lib.save('capture-contract.json',doc)
        closed=guard.close();finished=True
        guard_ref=lib.save('capture-contract-source-guard.closed.json',closed)
        print(json.dumps({'result_ref':result_ref,'guard_ref':guard_ref,'excerpts':excerpts},ensure_ascii=False))
    finally:
        if not finished:
            for stream in guard.held:
                stream.close()

code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)
