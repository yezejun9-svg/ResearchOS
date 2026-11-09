from review_driver import *
seal=json.loads((E/'FINAL-SEAL.json').read_text())
mismatch=[rel for rel,meta in seal['manifest'].items() if hashlib.sha256((E/rel).read_bytes()).hexdigest()!=meta['sha256']]
assert mismatch==['LEDGER.jsonl'],mismatch
save(E/'SEAL-EMISSION-DIAGNOSTIC.json',dict(initial_manifest_drift=mismatch,cause='Ordinary runner appended its own completion ledger entry after first manifest generation. Separate finalizer now emits after all ordinary writes.',source_or_verdict_changed=False))
ledger('SEAL_EMISSION_ACCOUNTING','RESOLVED','Final seal emitted by separate finalizer after ordinary ledger completes; separate finalizer envelope excluded to avoid recursion.')
target=E/'commands/030-final-seal';target.mkdir(parents=True,exist_ok=False)
argv=[PY,'-B','-X','utf8',str(E/'emit_final_seal.py')]
save(target/'recipe.json',dict(argv=argv,cwd=str(WT),env={},mode='run'))
with (target/'stdout.bin').open('wb') as out,(target/'stderr.bin').open('wb') as err:
 result=subprocess.run(argv,cwd=WT,stdout=out,stderr=err)
save(target/'result.json',dict(native_exit=result.returncode))
assert result.returncode==0
final=json.loads((E/'FINAL-SEAL.json').read_text());assert all(hashlib.sha256((E/p).read_bytes()).hexdigest()==v['sha256'] for p,v in final['manifest'].items())
print((target/'stdout.bin').read_text())
