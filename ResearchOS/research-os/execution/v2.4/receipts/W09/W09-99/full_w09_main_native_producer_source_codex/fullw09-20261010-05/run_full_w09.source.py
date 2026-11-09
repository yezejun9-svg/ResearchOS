"""Source-only future run entrypoint; exact Root request required."""
import hashlib
from pathlib import Path
import sys
import types
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
def main():
    p=N/'full_w09_runtime.source.py';raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='3fa9468a620366860ed1ba0d55c9f8079351e20426eb01ea6642d36ec4b6ec87':raise ValueError('PINNED_RUNTIME_DRIFT')
    m=types.ModuleType('full_w09_run_runtime');m.__file__=str(p)
    exec(compile(raw,str(p),'exec'),m.__dict__)
    m.stage('run',sys.argv[1:])
if __name__=='__main__':main()
