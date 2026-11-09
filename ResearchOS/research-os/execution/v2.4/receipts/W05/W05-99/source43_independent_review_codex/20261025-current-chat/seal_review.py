import pathlib,json,hashlib,datetime,sys
sys.stdout.reconfigure(encoding='utf-8')
base=pathlib.Path(__file__).parent
def pin(p):
    data=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
assert json.loads((base/'commands/047-freeze/result.json').read_text(encoding='utf-8'))['native_exit']==0
manifest=json.loads((base/'FINAL-manifest.json').read_text(encoding='utf-8'))
for entry in manifest['files']+manifest['retained_rebuildable_binaries']+manifest['author_final_and_supplement']:
    p=pathlib.Path(entry['path']);actual=pin(p);assert actual==entry,str(p)
seal={'schema':'researchos.source43-independent-final-seal.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest':pin(base/'FINAL-manifest.json'),'finalizer':[pin(p) for p in sorted((base/'commands/047-freeze').iterdir()) if p.is_file()],'seal_recipe':pin(base/'commands/048-seal/recipe.json'),'verified_manifest_references':len(manifest['files'])+len(manifest['retained_rebuildable_binaries'])+len(manifest['author_final_and_supplement']),'boundary':'This seal intentionally does not recursively hash itself or its own completed 048-seal stdout/stderr/result. Their native receipts remain adjacent; all reviewed product commands are closed.'}
target=base/'FINAL-seal.json';assert not target.exists();target.write_text(json.dumps(seal,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'seal':pin(target),'manifest':pin(base/'FINAL-manifest.json'),'verdict':'LIMITED_SOURCE_ACCEPTED'},ensure_ascii=False,indent=2))
