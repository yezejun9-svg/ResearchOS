"""Source-only future prepare entrypoint; exact Root request required."""
import hashlib
from pathlib import Path
import sys
import types
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
def main():
    p=N/'full_w09_runtime.source.py';raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='d1724ec0fa4e3de4000724c262c8f0103c82895ba610059bf5df08482f803528':raise ValueError('PINNED_RUNTIME_DRIFT')
    m=types.ModuleType('full_w09_prepare_runtime');m.__file__=str(p)
    exec(compile(raw,str(p),'exec'),m.__dict__)
    m.stage('prepare',sys.argv[1:])
if __name__=='__main__':main()
