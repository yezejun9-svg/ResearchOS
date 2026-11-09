from pathlib import Path
import types,json,hashlib,difflib,re
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
F=m.S/'legacy-fixture-repair-20261010-01';proposal_ref={'path':str(F/'proposal.json'),'sha256':'256496494e0b792ad37cebdabdd2fa87a845f9ddbd5108a66140255cb6dca29c','bytes':5094}
proposal=json.loads(Path(proposal_ref['path']).read_bytes());refs=[m.GREF,proposal_ref,proposal['original_copy_ref'],proposal['candidate_ref'],proposal['patch_ref'],*proposal['input_refs']]
checks=[];g=m.guard()
def add(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),'detail':detail})
try:
    g.acquire(refs);before=g.get_buffer(proposal['original_copy_ref']['path']);candidate=g.get_buffer(proposal['candidate_ref']['path']);production=g.get_buffer(proposal['original_Main_ref']['path'])
    target=b'func TestW09LegacyRootMigrationRevokesUnidentifiedRoot(t *testing.T) {'
    ib=before.index(target);ic=candidate.index(target);before_prefix=before[:ib];candidate_prefix=candidate[:ic];old_func=before[ib:];new_func=candidate[ic:]
    add('original_Main_exact_retained',production==before)
    add('only_last_LegacyRoot_test_changed_bytes',before_prefix==candidate_prefix and before.count(target)==candidate.count(target)==1)
    footer=b'\tvar identity string';old_footer=old_func[old_func.index(footer):];new_footer=new_func[new_func.index(footer):]
    add('entire_SQL_observation_assertion_footer_preserved',old_footer==new_footer and b'W09-G02-LEGACY-ROOT' in new_footer and b'identity != "" || revoked != 1 || revision != 2' in new_footer)
    prefix_end=old_func.index(b'\tlegacy, err :=');new_prefix_end=new_func.index(b'\t// Build the actual contiguous')
    add('real_Bootstrap1_and_isolated_DB_unchanged',old_func[:prefix_end]==new_func[:new_prefix_end] and b'store.Open(filepath.Join(t.TempDir(), "legacy.sqlite"))' in new_func and b'defer db.Close()' in new_func)
    body=new_func.decode('utf-8');loop=body[body.index('for version := 2;'):body.index("INSERT INTO retrieval_roots")]
    add('contiguous_2_through_8_actual_SQL_before_ledger',all(t in loop for t in ('version := 2; version <= 8; version++','len(files) != 1','db.Exec(string(raw))','INSERT INTO schema_migrations(version) VALUES(?)')) and loop.index('db.Exec(string(raw))')<loop.index('INSERT INTO schema_migrations(version) VALUES(?)') and loop.count('t.Fatal')>=2)
    refusal=body[body.index('// A populated old database'):body.index('identityMigration, err :=')]
    add('actual_New_prebackup_refusal_required',all(t in refusal for t in ('New(db,','err == nil || !strings.Contains(err.Error(), "MIGRATION_PREBACKUP_REQUIRED")','t.Fatalf(')))
    sql9=body[body.index('identityMigration, err :='):body.index('\tvar identity string')]
    add('fixed_SQL9_exec_then_ledger_before_revocation_observation',all(t in sql9 for t in ('os.ReadFile("../../migrations/sqlite/0009_retrieval_root_identity.sql")','db.Exec(string(identityMigration))','INSERT INTO schema_migrations(version) VALUES(9)')) and sql9.index('db.Exec(string(identityMigration))')<sql9.index('INSERT INTO schema_migrations(version) VALUES(9)'))
    gate=g.get_buffer(str(m.R/'internal/domain/backup_migration.go')).decode();ctor=g.get_buffer(str(m.R/'internal/domain/store.go')).decode();bootstrap=g.get_buffer(str(m.R/'internal/store/sqlite.go')).decode();migration=g.get_buffer(str(m.R/'migrations/sqlite/0009_retrieval_root_identity.sql')).decode()
    add('production_gapped_future_and_prebackup_gates_retained',all(t in gate for t in ('kind != "integer" || v != n || v > len(files)','MIGRATION_UNSUPPORTED_OR_GAPPED_VERSION','if applied != len(files)','MIGRATION_PREBACKUP_REQUIRED')) and ctor.index('checkMigrationInventory(db, files)')<ctor.index('CheckMigrationSafety(db, files)')<ctor.index('db.Begin()'))
    add('real_SQL9_revokes_unknown_identity_and_increments_revision',"root_identity TEXT NOT NULL DEFAULT ''" in migration and "SET revoked=1, revision=revision+1 WHERE root_identity=''" in migration)
    add('fmt_filepath_strings_imports_already_present',all(('"'+name+'"').encode() in before_prefix.split(b')',1)[0] for name in ('fmt','path/filepath','strings')))
    generated=''.join(difflib.unified_diff(before.decode().splitlines(True),candidate.decode().splitlines(True),fromfile='a/internal/domain/retrieval_test.go',tofile='b/internal/domain/retrieval_test.go'))
    add('published_patch_equals_actual_candidate_diff',generated.encode()==g.get_buffer(proposal['patch_ref']['path']))
    add('no_product_or_formal_claim_in_proposal',proposal['source_only'] is True and proposal['Main_written'] is False and proposal['actual_Go_test']=='NOT_RUN' and proposal['public_upgrade']=='NOT_RUN' and proposal['formal_acceptance'] is False)
    verdict='SOURCE_ACCEPTED_CANDIDATE_ONLY' if all(x['passed'] for x in checks) else 'CHANGES_REQUIRED'
    result={'schema':'researchos.w09-legacy-fixture-independent-source-review.v1','review_author':'/root/full_w09_source_review','source_author':'codex:/root','independent_non_author':True,'proposal_ref':proposal_ref,'candidate_ref':proposal['candidate_ref'],'verdict':verdict,'checks':checks,'scope':'SQL9 isolated unit fixture revocation; production prebackup refusal remains required','actual_Go_test':'NOT_RUN','public_upgrade':'NOT_RUN','formal_acceptance':False,'execution_grant':False,'Source21_revalidation_required_after_Main_change':True,'unchanged_production_input_refs':proposal['input_refs'][1:-1]}
    out=m.write('legacy-fixture-candidate.independent-review.json',result);print(json.dumps({'review_ref':out,'verdict':verdict,'checks':checks},ensure_ascii=False),flush=True)
finally:
    closed=g.close();ref=m.write('legacy-fixture-candidate.guard.closed.json',closed);print(json.dumps({'guard_ref':ref,'closed':closed['closed'],'retained_handles_count':closed['retained_handles_count']},ensure_ascii=False),flush=True)
