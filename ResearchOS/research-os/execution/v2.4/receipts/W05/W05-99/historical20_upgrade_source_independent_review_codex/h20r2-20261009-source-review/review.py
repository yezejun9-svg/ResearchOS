import pathlib,json,hashlib,re,difflib
P=pathlib.Path;N=P(__file__).resolve().parent;B=N.parent.parent
C=B/'historical20_upgrade_test_revision_codex/h20r2-1a11ee4f162766098eda3028b0679f2'
R1=B/'historical20_upgrade_source_codex/h20-r1-root-1791519270000-scoped-check'
BASE=B/'historical20_upgrade_source_codex/h20-1a11ebe661670a1a49d0ea22092604a'
AR=B/'history20_failed_actual_independent_review_codex/h20a914-20261009-review'
checks=[];inputs={}
def ck(n,v):checks.append(dict(name=n,passed=bool(v)))
def pin(p):
 p=P(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(v):
 x=dict(path=str(P(v['path']).resolve()),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes']);a=pin(x['path'])
 ck('pin:'+x['path'],a==x);ck('pin-consistency:'+x['path'],x['path'] not in inputs or inputs[x['path']]==x);inputs[x['path']]=x
 return x
def add(p):return verify(pin(p))
def fixed(p,h,z):return verify(dict(path=str(p),sha256=h,bytes=z))
def read(p):return json.loads(P(p).read_bytes())
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(N/n)
fixed(C/'HDF.json','7e6b01bb9bf1adaa6d92cfb3e0b9e558da4d300abe76be4258c1d6984abafb19',6217)
fixed(C/'MF.json','c80d8a5c51bdc4a32eae36510f95af0ee0d9ed09705abb56988713002e55b396',7132)
fixed(AR/'HDF.json','b130d4fd90f39391b6ef353990fab38cbcc7c4f5dd4a991caa9b8c6f395150e6',3321)
fixed(AR/'MF.json','2c8f71f482c1d936f887bcbc2a864518a2470b55a4f85452adaf473c2fee6fa8',3774)
for d in (C,AR):
 for v in read(d/'MF.json')['members']:verify(v)
h=read(C/'HDF.json')
for v in h['candidate_files']:verify(v)
for k in ('old_handoff_ref','old_manifest_ref','report_ref','contract_ref','inverse_ref','patch_ref','checks_ref','guard_ref','origin_counter_ref','actual914_provenance_ref'):verify(h[k])
for v in read(R1/'MF.json')['members']:verify(v)
baseline=read(BASE/'input-pins.json');add(BASE/'input-pins.json')
ck('exact-baseline66',len(baseline)==66)
for v in baseline:verify(v)
g=read(C/'guard.final.json')
for v in g['before']:verify(v)
ck('author-source-pin-observation',g['before']==g['after'] and g['unchanged'] and g['source_hash_recheck_only'] and not g['native_win32_guard_executed'])
p=read(C/'actual914-provenance.json')
for k in ('validation_closed_ref','jsonl_ref'):verify(p[k])
ck('original914-still-failed',read(p['validation_closed_ref']['path'])['pass_count']==8 and read(p['validation_closed_ref']['path'])['fail_count']==1)
ck('reuse914-independent-failed-closure',read(AR/'HDF.json')['status']=='FAILED_ACTUAL_CLOSURE_VERIFIED_FIXTURE_ROOT_CAUSE_CONFIRMED')
iv=read(C/'exact-inverse.json');verify(iv['old_test_ref']);verify(iv['new_test_ref'])
old=P(iv['old_test_ref']['path']).read_bytes();new=P(iv['new_test_ref']['path']).read_bytes()
ck('nine-replacements',len(iv['edits'])==9)
inv=new
for i,e in enumerate(reversed(iv['edits'])):
 a=e['old'].encode();b=e['new'].encode();ck('inverse-unique:'+str(i),inv.count(b)==1);inv=inv.replace(b,a,1)
ck('full-test-byte-inverse',inv==old)
for rel in ('internal/domain/backup.go','internal/domain/backup_history20_upgrade.go','internal/domain/backup_upgrade.go','ops/backup/main.go'):
 ck('production-unchanged:'+rel,(C/'candidate-root'/rel).read_bytes()==(R1/'candidate-root'/rel).read_bytes())
text=new.decode();oldtext=old.decode()
def fn(s,name):
 block=s.split('func '+name+'(',1)[1]
 return block.split('\nfunc ',1)[0]
for name in ('TestHistory20PublicUpgradePreservesSourceAndRevokesRestoredCredentials','TestHistory20MigrationRollsBackDDLWhenLedgerInsertFails','TestHistory20ImplicitStartupStillRejectsPopulatedSource','history20Rows'):
 ck('whole-function-byte-unchanged:'+name,fn(text,name)==fn(oldtext,name))
fixture=fn(text,'history20Fixture')
ck('source-separate-parent','Source: filepath.Join(base,"source","source.sqlite")' in fixture)
ck('key-separate-parent','KeyFile: filepath.Join(base,"key","recovery.key")' in fixture)
ck('snapshot-destination-siblings','Snapshot: filepath.Join(base,"backup")' in fixture and 'Destination: filepath.Join(base,"candidate")' in fixture)
ck('parents-created-before-resource-writes',fixture.index('os.MkdirAll(dir,0700)')<fixture.index('os.WriteFile(path,data,0600)'))
dirs=[P('source'),P('key'),P('backup'),P('candidate')]
ck('four-layout-directories-nonoverlapping',all(not a.is_relative_to(b) and not b.is_relative_to(a) for i,a in enumerate(dirs) for b in dirs[i+1:]))
drift=fn(text,'TestHistory20RejectsReleaseAndSourceDrift')
expected={'migration-hash':'UPGRADE_RELEASE_HASH: 0021_research_pending_windows.sql','extra-numbered-migration':'UPGRADE_RELEASE_MIGRATIONS: require exact 1..20','foreign-table':'UPGRADE_SOURCE_SCHEMA','session-addon':'UPGRADE_SOURCE_SCHEMA'}
for k,v in expected.items():ck('negative-exact-error:'+k,'"'+k+'":"'+v+'"' in drift)
ck('negative-specific-not-any-error','err==nil || err.Error()!=expectedError' in drift)
ck('negative-output-and-whole-source-checks','[]string{opt.Destination,opt.Snapshot}' in drift and 'Hash(history20Rows(t,opt.Source))!=Hash(before)' in drift)
prod=(C/'candidate-root/internal/domain/backup_history20_upgrade.go').read_text()
ck('release-count-exact-error','fmt.Errorf("UPGRADE_RELEASE_MIGRATIONS: require exact 1..%d", count)' in prod)
ck('release-hash-exact-error','fmt.Errorf("UPGRADE_RELEASE_HASH: %s", name)' in prod)
ck('schema-exact-error','fmt.Errorf("UPGRADE_SOURCE_SCHEMA")' in prod)
ck('source20-before-target21-before-schema',prod.index('sourceRelease, _, e := upgradeHistory20Release(opt.SourceRoot, 20)')<prod.index('targetRelease, sqls, e := upgradeHistory20Release(opt.TargetRoot, 21)')<prod.index('return report, fmt.Errorf("UPGRADE_SOURCE_SCHEMA")'))
generic=fn(text,'TestHistory20RestoreFailureRetainsEncryptedBackupAndSource')
ck('errors-import-used',' "errors"\n' in text and 'errors.Is(err,context.Canceled)' in generic)
ck('callback-reached-required','callbackCalled:=false' in generic and 'callbackCalled=true' in generic and 'if !callbackCalled || !errors.Is(err,context.Canceled)' in generic)
ck('callback-DDL-before-return-cancel',generic.index('callbackCalled=true')<generic.index('target.ExecContext(ctx,"CREATE TABLE fixture_unpublished(value TEXT)")')<generic.index('return context.Canceled'))
ck('uncancelled-background-outer','RestoreBackup(context.Background()' in generic)
ck('manifest-exact-retention','backupManifestBefore,err:=os.ReadFile' in generic and 'backupManifestAfter,err:=os.ReadFile' in generic and '!bytes.Equal(backupManifestBefore,backupManifestAfter)' in generic)
ck('destination-not-published-backup-retained-source-equal','os.Stat(opt.Destination);!os.IsNotExist(err)' in generic and 'os.Stat(opt.Snapshot);err!=nil' in generic and 'Hash(now)!=Hash(before)' in generic)
ck('generic-component-scope-explicit','generic RestoreBackup component failure, not the public UpgradeLocal failure path' in generic)
backup=(C/'candidate-root/internal/domain/backup.go').read_text()
ck('production-callback-wrap-supports-Is','MIGRATION_FAILED: isolated copy discarded; stable backup retained: %w' in backup)
parents=re.findall(r'^func (TestHistory20[A-Za-z0-9_]+)\(',text,re.M)
oldparents=re.findall(r'^func (TestHistory20[A-Za-z0-9_]+)\(',oldtext,re.M)
leaftext=re.search(r'for _, tc := range \[\]string\{([^}]+)\}',drift).group(1)
leaves=re.findall(r'"([^"]+)"',leaftext)
ck('five-parents-unchanged',parents==oldparents and len(parents)==5)
ck('four-leaves-nine-terminals',leaves==['migration-hash','extra-numbered-migration','foreign-table','session-addon'] and len(parents)+len(leaves)==9)
save('independent-diff.json',dict(diff=''.join(difflib.unified_diff(oldtext.splitlines(True),text.splitlines(True),fromfile='R1',tofile='R2')),expected_errors=expected,selected_parents=parents,expected_terminals=sorted(parents+['TestHistory20RejectsReleaseAndSourceDrift/'+x for x in leaves])))
for v in inputs.values():ck('final-unchanged:'+v['path'],pin(v['path'])==v)
save('guard.final.json',dict(schema='researchos.independent-source-pin-observation.v1',state='RELEASED',all_input_pins_unchanged=True,input_count=len(inputs),os_read_handles_acquired=False,canonical_handles_acquired=False,retained_handles_count=0,only_own_review_namespace_written=True))
save('input-pins.json',list(inputs.values()))
save('checks.json',dict(checks=checks,passed=sum(v['passed'] for v in checks),failed=sum(not v['passed'] for v in checks),input_count=len(inputs)))
print(json.dumps(dict(checks=len(checks),input_count=len(inputs),failed=[v for v in checks if not v['passed']],source_only=True,Go_SQL_native_API_private_model=False),ensure_ascii=True))

