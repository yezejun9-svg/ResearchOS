import datetime, hashlib, json, pathlib
E=pathlib.Path(__file__).parent
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):
    return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
ledger=read(E/'ledger.json')
assert len(ledger['attempts'])==29 and ledger['failed_attempt_count']==3
config=read(E/'public-handoff03.config.json')
for role in ['SourceBackupProgram','RootProgram','ControlProgram','BackupProgram','EnrollmentProgram','PythonProgram','BrokerSource','PrivateStdinHelper']:
    actual=pin(pathlib.Path(config[role]['path']))
    assert 'sha256:'+actual['sha256']==config[role]['sha256'] and actual['bytes']==config[role]['bytes']
for rel in ['00-source-backup/invocation.json','00-rehearsal/invocation.json']:
    inv=read(E/'public-cli-handoff03'/rel)
    assert inv['Result']['actual_exit']==0 and inv['ActualLifetimeClosed'] and not inv['NativeAuthorityAcceptance']
    clean=inv['Result']['job_cleanup']
    assert clean['assigned_before_resume'] and clean['job_idle_confirmed'] and clean['handles_closed'] and not clean['errors']
result=read(E/'public-cli-handoff03/05-case.result.json')
assert result['original_unchanged'] and result['before_rows_sha256']==result['after_rows_sha256']
manifest=dict(schema='researchos.schema24-to25-source-freeze.v1',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='SOURCE_IMPLEMENTED_PUBLIC_FIXTURE_PASS_PENDING_INDEPENDENT_REVIEW_AND_NATIVE_SYNTHETIC_GRANT',author='codex:/root/mu_v5_review_resume',identity=read(E/'final-freeze/identity.json'),formal_increment=0,native_execution='NOT_RUN',original_database_execution='NOT_AUTHORIZED_NOT_RUN',independent_review='PENDING',go_attempt_count=len(ledger['attempts']),failed_attempt_count=ledger['failed_attempt_count'],tests=read(E/'final-freeze/verification-summary.json'),program_pins={k:v for k,v in config.items() if isinstance(v,dict)},report=pin(E/'SOURCE_REPORT.md'),artifacts=[dict(relative=p.relative_to(E).as_posix(),**pin(p)) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='manifest.json'])
(E/'manifest.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(report=pin(E/'SOURCE_REPORT.md'),manifest=pin(E/'manifest.json'),artifact_count=len(manifest['artifacts'])),ensure_ascii=True))
