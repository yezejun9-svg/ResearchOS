import pathlib,json,sqlite3,hashlib
p=pathlib.Path(__file__).parent
smoke=json.loads((p/'control-cold-session-smoke.json').read_text(encoding='utf-8-sig'))
db=sqlite3.connect('file:'+smoke['data_root']+'/researchos.sqlite?mode=ro',uri=True)
rows=[dict(zip(['principal','roles','root','parent'],r)) for r in db.execute('SELECT a.id,a.roles,o.root,o.parent FROM auth_principals a LEFT JOIN orchestration_identity o ON o.principal=a.id ORDER BY a.id')]
assert len(rows)==3
owner=[r for r in rows if json.loads(r['roles'])==['OWNER']][0]
assert owner['root']==owner['principal'] and owner['parent'] is None
for r in rows:
 assert r['root']==owner['root']
 if r is not owner: assert r['parent']==owner['principal'] and json.loads(r['roles']) in [['SCHEDULER'],['EXECUTOR']]
assert db.execute("SELECT count(*) FROM domain_objects WHERE kind='Run'").fetchone()[0]==0
db.close()
info={'candidate':'a57ca3e33b4e9d7c9351cd4143f8914c936f6bda','phase1_principals':rows,'all_lineage_registered_before_run':True,'independent_verifier_created':False,'same_owner_authority_root':True,'notes':'OS bootstrap creates Owner; first RegisterExecutionIdentity inserts its explicit self root. Both generated SCHEDULER and EXECUTOR are explicit delegated children of that Owner root before token route installation. Phase 2 needs a genuinely independent trusted verifier service root and local trusted administrator registration. Different agent names or same-OS-user delegation do not demonstrate protected holdout. No missing lineage among the three phase-1 principals in the observed successful setup.'}
(p/'phase1-lineage-addendum.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
manifest=json.loads((p/'handoff-manifest.json').read_text())
files=[{'path':f.name,'sha256':sha(f)} for f in sorted(p.iterdir()) if f.is_file() and f.name!='source-bundle-final.json']
bundle={'candidate':info['candidate'],'base':manifest['base'],'source_files':manifest['source_files'],'evidence_files':files,'prior_manifest_sha256':sha(p/'handoff-manifest.json'),'status':'FROZEN_PENDING_INDEPENDENT_REVIEW'}
(p/'source-bundle-final.json').write_text(json.dumps(bundle,indent=2),encoding='utf-8')
print('explicit_lineage_rows='+str(len(rows)))
print('source_bundle_sha256='+sha(p/'source-bundle-final.json'))
