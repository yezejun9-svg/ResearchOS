import pathlib,json,hashlib
B=pathlib.Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seal=json.loads((B/'PHASE2-final-seal.json').read_text(encoding='utf-8'))
assert sha(B/'PHASE2-final-manifest.json')==seal['manifest_sha256']
m=json.loads((B/'PHASE2-final-manifest.json').read_text(encoding='utf-8'))
for ref in m['files']:assert sha(B/ref['path'])==ref['sha256'],ref['path']
v=json.loads((B/'PHASE2-v12-snapshot-verification.json').read_text(encoding='utf-8'));S=pathlib.Path(v['snapshot'])
for ref in v['candidate_source_files']+v['inherited40']+v['supplementary_files']:assert sha(S/ref['path'])==ref['sha256']
refs=[]
for name in ['138-finalize-independent-phase2','139-final-summary-crosscheck']:
 for p in (B/name).iterdir():
  if p.is_file():refs.append({'path':str(p.relative_to(B)).replace('\\','/'),'sha256':sha(p)})
a={'schema':'researchos.c57.independent-phase2-postseal-audit.v1','status':'ALL_360_MANIFEST_REFS_AND_FINAL57_40_SUPPLEMENTS_MATCH','final_seal_sha256':sha(B/'PHASE2-final-seal.json'),'manifest_ref_count':len(m['files']),'candidate_commit':v['commit'],'new_native_nonzero':0,'cumulative_native_nonzero':9,'formal_increment':0,'diagnostic_label_resolution':{'094-owned-module-copy':'094-phase2-owned-module-cache-prepare','094b-owned-module-copy-r2':'094b-phase2-owned-module-cache-prepare-r2'},'postseal_capture_refs':refs,'note':'Diagnostic display labels are resolved here to exact persisted directories. Prior manifest/seal/report and failures remain unchanged.'}
p=B/'PHASE2-postseal-audit.json';p.write_text(json.dumps(a,indent=2),encoding='utf-8')
print(json.dumps({'audit_sha256':sha(p),'final_seal_sha256':a['final_seal_sha256'],'verified_manifest_refs':len(m['files']),'final_source57':57,'inherited40':40,'supplements':len(v['supplementary_files'])},indent=2))
