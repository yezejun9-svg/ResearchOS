import hashlib,json,pathlib,sqlite3,struct,subprocess
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT=pathlib.Path(__file__).resolve().parent
WT=ROOT/'.local/worktrees/w05-main24-public-20261012'
DATA=WT/'execution/v2.4/receipts/W05/W05-99/public23_to24_candidate_integration_codex/candidate-20261012-01'
def digest(b): return hashlib.sha256(b).hexdigest()
def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':digest(b),'bytes':len(b)}
def write(n,o): (OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
recipe=ROOT/'execution/v2.4/receipts/W05/W05-99/public23_to24_root_integration_preparation_codex/prepare-20261010-01/composition-map.json'
m=json.loads(recipe.read_text(encoding='utf-8-sig'))
checks=[]
for rel,x in m['proposed_final_files'].items():
    expected=x['source_ref'];source=ref(pathlib.Path(expected['path']));actual=ref(WT/rel)
    checks.append({'relative_path':rel,'tier':x['tier'],'expected':expected,'source':source,'actual':actual,'match':source['sha256']==actual['sha256']==expected['sha256'] and source['bytes']==actual['bytes']==expected['bytes']})
git=lambda *a: subprocess.check_output(['git','-C',str(WT),*a],text=True,encoding='utf-8').strip()
changed=git('diff','--name-only','adc460c2138528f163f7fdab5e8d81dde157b7fb','HEAD').splitlines()
write('source-checks.json',{'schema':'researchos.independent-main24-source-checks.v1','actor':'codex:/root/w05_migration_review','recipe':ref(recipe),'head':git('rev-parse','HEAD'),'parent':git('rev-parse','HEAD^'),'files':checks,'all_match':all(c['match'] for c in checks),'changed_files':changed,'extra_changes':sorted(set(changed)-set(m['proposed_final_files']))})
def rowhash(row):
    b=bytearray()
    for v in row:
        if v is None: t,r=b'N',b''
        elif isinstance(v,int):t,r=b'I',str(v).encode()
        elif isinstance(v,float):t,r=b'F',struct.pack('>d',v)
        elif isinstance(v,str):t,r=b'T',v.encode()
        elif isinstance(v,bytes):t,r=b'B',v
        else:raise TypeError(type(v))
        b+=t+struct.pack('>Q',len(r))+r
    return 'sha256:'+digest(b)
def inspect(label):
    p=DATA/label/'researchos.sqlite';wal=pathlib.Path(str(p)+'-wal')
    assert not wal.exists() or wal.stat().st_size==0,'Nonempty WAL requires isolated family snapshot'
    before=ref(p)
    db=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
    db.execute('PRAGMA query_only=ON')
    schema=list(db.execute("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name"))
    tables={}
    for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        cur=db.execute('SELECT * FROM "'+name.replace('"','""')+'"')
        rows=sorted(rowhash(r) for r in cur)
        tables[name]={'columns':[c[0] for c in cur.description],'rows':rows,'count':len(rows)}
    versions=[r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
    integrity=[r[0] for r in db.execute('PRAGMA integrity_check')]
    foreign_key_violations=list(db.execute('PRAGMA foreign_key_check'))
    db.close()
    after=ref(p);assert before==after
    return {'input':before,'unchanged_after_read':True,'open_mode':'mode=ro&immutable=1; query_only=ON; WAL absent or empty','versions':versions,'integrity':integrity,'foreign_key_violations':foreign_key_violations,'schema':schema,'tables':tables}
states={n:inspect(n) for n in ['source23-copy','candidate24','restored24']}
diffs={}
for a,b in [('source23-copy','candidate24'),('candidate24','restored24')]:
    x,y=states[a]['tables'],states[b]['tables']
    diffs[a+'->'+b]={'new_tables':sorted(set(y)-set(x)),'deleted_tables':sorted(set(x)-set(y)),'changed_tables':[n for n in x.keys()&y.keys() if x[n]!=y[n]]}
receipt= json.loads((DATA/'candidate24/prepared-abandonment-public-backup-handoff.json').read_text(encoding='utf-8-sig'))
checks_sql={'source23_exact':states['source23-copy']['versions']==list(range(1,24)), 'candidate24_exact':states['candidate24']['versions']==list(range(1,25)), 'restored24_exact':states['restored24']['versions']==list(range(1,25)), 'all_integrity_ok':all(v['integrity']==['ok'] and not v['foreign_key_violations'] for v in states.values()),'candidate_proof_empty':states['candidate24']['tables']['runtime_prepared_abandonments']['count']==0,'restored_proof_empty':states['restored24']['tables']['runtime_prepared_abandonments']['count']==0,'original_migrations_preserved':set(states['source23-copy']['tables']['schema_migrations']['rows']).issubset(states['candidate24']['tables']['schema_migrations']['rows']),'candidate_restored_schema_equal':states['candidate24']['schema']==states['restored24']['schema']}
write('sqlite-oracle.json',{'schema':'researchos.independent-main24-sqlite-oracle.v1','actor':'codex:/root/w05_migration_review','states':states,'diffs':diffs,'checks':checks_sql,'receipt_reference':ref(DATA/'candidate24/prepared-abandonment-public-backup-handoff.json')})
print(json.dumps({'source_matches':sum(c['match'] for c in checks),'source_count':len(checks),'extra_changes':sorted(set(changed)-set(m['proposed_final_files'])),'diffs':diffs,'sql_checks':checks_sql},ensure_ascii=False,indent=2))
