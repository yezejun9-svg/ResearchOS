"""Source-only future prepare entrypoint; exact Root request required."""
import hashlib
from pathlib import Path
import sys
import types
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
def main():
    p=N/'full_w09_runtime.source.py';raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08':raise ValueError('PINNED_RUNTIME_DRIFT')
    m=types.ModuleType('full_w09_prepare_runtime');m.__file__=str(p)
    exec(compile(raw,str(p),'exec'),m.__dict__)
    m.stage('prepare',sys.argv[1:])
if __name__=='__main__':main()
