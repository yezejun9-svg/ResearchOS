import ast, difflib,hashlib,json
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,obj):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def main():
    p=Q/'old21_root.source.py';raw=p.read_bytes();old=b'    need(sorted(int(Path(k).name[:4]) for k in sql if k.startswith("migrations/sqlite/")) == list(range(1, 22)), "EXACT_SCHEMA21_NUMBERED_SQL")'
    new=b'    numbered = [k for k in sql if k.startswith("migrations/sqlite/") and k.endswith(".sql")]\n    need(all(re.fullmatch(r"migrations/sqlite/[0-9]{4}_[^/]+\\.sql", k) for k in numbered) and sorted(int(Path(k).name[:4]) for k in numbered) == list(range(1, 22)), "EXACT_SCHEMA21_NUMBERED_SQL")'
    assert raw.count(old)==1
    initial=Q/'old21_root.source.initial.py'
    with initial.open('xb') as f:f.write(raw)
    revised=raw.replace(old,new);compile(revised,str(p),'exec')
    p.write_bytes(revised)
    inv=save('numbered-SQL-revision.inverse.json',dict(schema='researchos.exact-byte-revision.v1',initial_ref=pin(initial),candidate_ref=pin(p),old_hex=old.hex(),new_hex=new.hex(),candidate_inverse_SHA=hashlib.sha256(revised.replace(new,old)).hexdigest(),full_inverse_verified=revised.replace(new,old)==raw))
    baseline=json.loads((Q/'source-inputs.basis.json').read_text(encoding='utf-8'))
    # Composite inverse retains the original complete M4 byte-span proof and this single exact byte revision.
    save('composite-exact-inverse.json',dict(schema='researchos.old21-composite-inverse.v1',base_ref=baseline['M4_caller_ref'],initial_inverse_ref=pin(Q/'exact-inverse.json'),revision_inverse_ref=inv,initial_source_ref=pin(initial),candidate_ref=pin(p),full_inverse_chain=True))
    d=Q/'candidate.final.diff'
    with d.open('xb') as f:f.write(''.join(difflib.unified_diff(Path(baseline['M4_caller_ref']['path']).read_text(encoding='utf-8').splitlines(keepends=True),revised.decode().splitlines(keepends=True),fromfile='accepted-M4/main23_root.source.py',tofile='old21_root.source.py')).encode())
    print(json.dumps(dict(candidate_ref=pin(p),inverse_ref=inv,final_diff_ref=pin(d),AST_valid=True)))
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
