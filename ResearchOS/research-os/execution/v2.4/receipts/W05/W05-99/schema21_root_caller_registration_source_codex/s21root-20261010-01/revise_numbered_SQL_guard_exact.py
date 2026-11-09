import hashlib,json
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def main():
    p=Q/'old21_root.source.py';raw=p.read_bytes()
    old=b'    numbered = [k for k in sql if k.startswith("migrations/sqlite/") and k.endswith(".sql")]'
    new=b'    numbered = [k for k in sql if re.fullmatch(r"migrations/sqlite/[0-9]{4}_[^/]+\\.sql", k)]'
    assert raw.count(old)==1
    original=Q/'old21_root.source.numbered0.py'
    with original.open('xb') as f:f.write(raw)
    revised=raw.replace(old,new);compile(revised,str(p),'exec');p.write_bytes(revised)
    value=dict(schema='researchos.exact-byte-revision.v1',initial_ref=pin(original),candidate_ref=pin(p),old_hex=old.hex(),new_hex=new.hex(),full_inverse_verified=revised.replace(new,old)==raw,previous_inverse_ref=pin(Q/'numbered-SQL-revision.inverse.json'),Source_next_v24_sessions_pin_preserved=True,nonnumbered_pending_DDL_applied=False)
    receipt=Q/'numbered-SQL-exact-revision.inverse.json'
    with receipt.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(candidate_ref=pin(p),inverse_ref=pin(receipt)),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
