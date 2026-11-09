from pathlib import Path
import json, hashlib
O=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/legacy_migration_fixture_independent_review_codex/4ec609adce7346a9b8fe61e898a8a15e')
Q=O.parent.parent/'legacy_migration_fixture_source_codex/edd7ae2789974a469dd2fc3a1bce50a9'
def j(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):
    raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def dump(name,obj): (O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
v=j(O/'static-verification.json')
post=j(Q/'postseal-tool-io.json')
c=next(x for x in post['calls'] if x['key']=='legacy_seal_revision')
result=c['result']; result=result.get('value',result)
emitted=json.loads(result['output'])
postchecks=[]
for name in ('HANDOFF.json','MANIFEST.json'):
    actual=pin(Q/name); exp=emitted['refs'][name]
    postchecks.append(dict(name=name,actual=actual,expected=exp,match=actual['sha256']==exp['sha256'] and actual['bytes']==exp['bytes']))
dump('postseal-independent-check.json',dict(authority='NONE',outer_exit=result['exit_code'],standalone_Python_exit_marker_present=False,standalone_Python_exit_note='Source command invoked fixed Python directly; outer process exit0 observed. No separate product exit inferred.',checks=postchecks))
dump('findings.json',dict(authority='NONE',formal_acceptance=False,verdict='REQUEST_CHANGES',critical=[],important=[dict(id='LEGACY-ROLLBACK-001',file='candidate-root/internal/domain/client_session_bootstrap_test.go',line=119,cause='setup does not create project; useLegacyTranscriptFixture requires at least one matching Project/Profile row',impact='rollback assertions unreachable after helper returns missing Project identity',recommendation='use legacyTranscriptFixtureDatabase directly for schema-only rollback, or explicitly create Project before copy helper',evidence=['inputs/author/candidate-root/internal/domain/client_session_bootstrap_test.go:117','inputs/author/candidate-root/internal/domain/legacy_migration_fixture_test.go:121','inputs/dependencies/domain_test.go:167','inputs/dependencies/domain_test.go:205'],verification='STATIC_CALL_PATH_ONLY')],ordinary='BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE',candidate_execution='NOT_RUN'))
dump('HDF.json',dict(schema='researchos.independent-source-review-handoff.v1',authority='NONE',formal_acceptance=False,status='REQUEST_CHANGES_SOURCE_ONLY',namespace=str(O),subject=pin(Q/'HANDOFF.json'),subject_manifest=pin(Q/'MANIFEST.json'),report=pin(O/'report.md'),findings=pin(O/'findings.json'),verification=pin(O/'static-verification.json'),input_pins=pin(O/'input-pins.json'),postseal_check=pin(O/'postseal-independent-check.json'),author_postseal=pin(Q/'postseal-tool-io.json'),critical_count=0,important_count=1,ordinary_upgrade='BLOCKED',candidate_native_Go_SQL_execution='NOT_RUN',mechanical_failures_this_review=0,prior_833_826_and_FULL_not_reset=True,canonical_writes=False,source_adoption_authority=False,next_actor='Root: arrange new immutable Source revision for LEGACY-ROLLBACK-001; independently review before guarded actual component execution. Ordinary remains blocked.'))
members=[dict(relative_path=p.relative_to(O).as_posix(),**pin(p)) for p in sorted(O.rglob('*')) if p.is_file() and p.relative_to(O).as_posix() not in ('MF.json','postseal-tool-io.json')]
dump('MF.json',dict(schema='researchos.independent-source-review-manifest.v1',authority='NONE',members=members,exclusions={'MF.json':'self fingerprint','postseal-tool-io.json':'seal tool return recorded after sealing and separately pinned'}))
for name in ('w0599_legacy_read.py','w0599_legacy_review.py'):
    temp=Path('C:/Users/yqyyds/AppData/Local/Temp')/name
    archived=O/('read.py' if name.endswith('_read.py') else 'review.py')
    if temp.is_file() and temp.read_bytes()==archived.read_bytes(): temp.unlink()
print(json.dumps(dict(authority='NONE',formal_acceptance=False,status='REQUEST_CHANGES_SOURCE_ONLY',refs={name:pin(O/name) for name in ('HDF.json','MF.json','report.md','findings.json')},member_count=len(members),author_postseal_refs_all_match=all(x['match'] for x in postchecks),native_Go_SQL_execution='NOT_RUN',independent_mechanical_failure=0),ensure_ascii=False))

