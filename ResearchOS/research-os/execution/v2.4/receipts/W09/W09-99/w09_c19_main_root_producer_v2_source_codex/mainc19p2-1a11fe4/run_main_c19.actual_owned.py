"""Source-only future run entrypoint; exact Root request required."""
import hashlib
from pathlib import Path
import sys
import types
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
def main():
    p=N/'main_c19_runtime.source.py';raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='790ad022d0600e53cedaf06c93661bd76ac00a57d7c8f8e7e18defaf318c533f':raise ValueError('PINNED_RUNTIME_DRIFT')
    m=types.ModuleType('main_c19_run_runtime');m.__file__=str(p)
    exec(compile(raw,str(p),'exec'),m.__dict__)
    m.stage('run',sys.argv[1:])
if __name__=='__main__':main()
