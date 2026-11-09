from read_public import ROOT,OUT,V5,sha,save
import json,re,subprocess,pathlib
checks=[]
manifest=json.loads((V5/'manifest.json').read_text(encoding='utf-8'))
for x in manifest['files']:
 p=(V5/x['path']).resolve()
 if not p.is_relative_to(V5.resolve()): checks.append({'path':x['path'],'error':'escape'}); continue
 b=p.read_bytes(); checks.append({'path':x['path'],'match':sha(b)==x['sha256'] and len(b)==x['bytes']})
save('proposal-manifest.audit.json',checks)
scope=json.loads((V5/'scope_proposal.json').read_text(encoding='utf-8'))['scope']
scope_rows=[]
snap=OUT/'public-source-snapshots';snap.mkdir()
for x in scope:
 p=ROOT/x['path']; row=dict(x);row['actual_exists']=p.exists()
 if p.exists():
  b=p.read_bytes(); dest=snap/x['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
  row.update(sha256=sha(b),bytes=len(b),snapshot=dest.relative_to(OUT).as_posix())
 scope_rows.append(row)
save('scope20.current.json',scope_rows)
git=[]
for rel in ['internal/domain/client_protocol.go','internal/domain/client_command_identity.go','internal/domain/client_protocol_configuration.go','internal/domain/backup_host_configuration.go','internal/domain/client_protocol_control_windows_test.go']:
 argv=['git','show','22752a6a41732c8c158d7d7e1b8932ec958f8cb8:'+rel]
 p=subprocess.run(argv,cwd=ROOT,capture_output=True)
 row={'argv':argv,'cwd':str(ROOT),'exit':p.returncode,'stderr':p.stderr.decode('utf-8','replace')}
 if p.returncode==0:
  dest=OUT/'frozen-handler-22752'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.stdout)
  row.update(path=dest.relative_to(OUT).as_posix(),sha256=sha(p.stdout),bytes=len(p.stdout))
 git.append(row)
save('handler.git-read.invocations.json',git)
extra=[]
for rel in ['internal/store/sqlite.go','internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json','.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/sqlite.go']:
 b=(ROOT/rel).read_bytes();extra.append({'path':rel,'sha256':sha(b),'bytes':len(b),'timing':'supplemental capture after prior static read; not represented as original before'})
save('inputs.supplemental.json',extra)
b=(V5/'candidate.sql.txt').read_text(encoding='utf-8')
summary={'SQL_EXECUTED':False,'tables':re.findall(r'CREATE TABLE (\w+)',b),'views':re.findall(r'CREATE VIEW (\w+)',b),'triggers':re.findall(r'CREATE TRIGGER (\w+)',b),'categories':re.findall(r"(?:SELECT|UNION ALL SELECT) '([^']+)',json_array",b),'proposal_listed':len(checks),'proposal_mismatch':[x for x in checks if x.get('match') is not True],'scope_paths':len(scope),'scope_absent':[x['path'] for x in scope_rows if not x['actual_exists']]}
save('ddl.static-inventory.json',summary)
before=json.loads((OUT/'inputs.before.json').read_text(encoding='utf-8'));after=[];drift=[]
for x in before+extra:
 p=ROOT/x['path'];row={'path':x['path'],'absent':True}
 if p.exists():
  raw=p.read_bytes();row={'path':x['path'],'sha256':sha(raw),'bytes':len(raw)}
 if row.get('sha256')!=x.get('sha256') or row.get('absent',False)!=x.get('absent',False): drift.append({'before':x,'after':row})
 after.append(row)
save('inputs.after.json',after);save('drift.json',drift)
print(json.dumps({'scope':len(scope),'present':sum(x['actual_exists'] for x in scope_rows),'tables':len(summary['tables']),'views':len(summary['views']),'triggers':len(summary['triggers']),'categories':len(summary['categories']),'manifest_entries':len(checks),'mismatch':len(summary['proposal_mismatch']),'git_errors':sum(x['exit']!=0 for x in git),'drift':len(drift),'executed_tests':0,'sql_execution':0},ensure_ascii=False))
