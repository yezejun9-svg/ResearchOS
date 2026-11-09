from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

root = Path(__file__).resolve().parent
old = root.parent / 'product-v1-workbench-author'
repo = Path('D:/作品集/ResearchOS/research-os')
scope_path = repo / 'execution/product-v1/receipts/single-harness-20261104/workbench/scope.json'
scope = json.loads(scope_path.read_text(encoding='utf-8-sig'))
wt = Path(scope['worktree'])
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert not (root / 'FROZEN.json').exists()
assert sha(old / 'FROZEN.json') == '0146759979ed06a19392881eaaf2f031bbeef951ed0cd1befa2f3b9a97e7195f'
old_manifest = json.loads((old / 'EVIDENCE_MANIFEST.json').read_text(encoding='utf-8'))
assert all(sha(old / row['path']) == row['sha256'] for row in old_manifest['files'])
assert all(json.loads((root / 'checks-02/source-readback.json').read_text(encoding='utf-8')).values())
assert all(row['exit_code'] == 0 for row in json.loads((root / 'checks-02/results.json').read_text(encoding='utf-8')))
git = json.loads((root / 'git-final-02/result.json').read_text(encoding='utf-8'))
assert git['exact_scope'] and all(row['exit_code'] == 0 for row in git['commands'])
vite = json.loads((root / 'vite-01/result.json').read_text(encoding='utf-8'))
assert vite['exit_code'] == 0 and vite['all_source_unchanged'] and len(vite['outputs']) == 3
pins = json.loads((root / 'checks-02/source-pins.json').read_text(encoding='utf-8'))
baseline = json.loads((root / 'baseline-review.json').read_text(encoding='utf-8'))['baseline_sha256']
changed = []
for name in scope['production_paths'] + scope['test_paths']:
    assert sha(wt / name) == pins[name] == sha(root / 'candidate' / name)
    if pins[name] != baseline[name]: changed.append(name)
    target = root / 'source-snapshot' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((wt / name).read_bytes())
assert set(changed) == {'apps/web/src/workbench.jsx', 'tests/ui/desktop/harness-workbench.test.mjs'}
build_inputs = json.loads((root / 'vite-01/command.json').read_text(encoding='utf-8'))['inputs']
assert all(sha(Path(row['source_path'])) == row['sha256'] for row in build_inputs)
assert next(row['sha256'] for row in build_inputs if row['path'] == 'apps/web/src/workbench.jsx') == pins['apps/web/src/workbench.jsx']

# Retain the old failed build's actual raw files, without its intermediate tree.
for name in ['command.json', 'stdout', 'stderr', 'result.json']:
    target = root / 'prior-evidence/author-vite-01' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(old / 'vite-01' / name, target)
(root / 'prior-evidence/author-vite-02-platform-reference.json').write_text(json.dumps({
    'origin': ['e29a92','55fa05'], 'classification': 'historical_build_harness_early_failure',
    'message': 'FileNotFoundError while copying the worktree spec/v2.0/ui/design-tokens.json before Vite invocation.',
    'evidence_kind': 'platform-tool reference, not a fabricated raw log file',
    'original_c_directory_retained': str(old / 'vite-02'),
}, indent=2) + '\n', encoding='utf-8')
events = [
    {'unique_origin':'WB-Q20-LATE_ACK-DRAFT','classification':'PRODUCT_P2','status':'fixed_for_independent_recheck',
     'source_tool_origins':['QA checks01/independent-ui.stdout.raw','QA review01/review.json'],
     'detail':'One product defect with two confirmed counterexamples: new text and edits back to original were cleared by late success. Original raw SHA85a2418dcb3514db1214126afd9462d391e652586b02609b2af874cfb125cfea retained.'},
    {'unique_origin':'AUTHOR-R2-CLEANUP-VM-VISIBLE','classification':'AUTHOR_TEST_HARNESS','status':'corrected_without_lowering_assertions',
     'source_tool_origins':['976e28','35f2c3','03b699','77fa97'],
     'detail':'Attempt01 had45PASS/1FAIL. Exact cleanup code reached a visible callback absent from the synthetic VM context; ReferenceError occurred before assertions. Only that callback fake was added; failed source/raw retained.'},
    {'unique_origin':'QA-Q02-PROJECTION-INPUT','classification':'INDEPENDENT_QA_TEST_HARNESS','status':'reported_and_corrected_by_independent_qa',
     'source_tool_origins':['QA review01/review.json'],
     'detail':'Independent QA initially supplied a Task instead of TaskRef to activity projection. This is separate from the two genuine Q20 product failures.'},
    {'unique_origin':'VITE-EXTERNAL-OUTDIR-NOTICE','classification':'NONBLOCKING_BUILD_NOTICE','status':'retained',
     'source_tool_origins':['149ae2'], 'detail':'Fresh C-owned outDir is outside snapshot root and is intentionally not automatically emptied.'},
]
(root / 'DIAGNOSTICS.json').write_text(json.dumps({'diagnostic_events':events,'old_diagnostics_inherited_without_recount':True,'old_diagnostics':'prior-evidence/author.freeze01.diagnostics.json'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
frozen = {
    'state':'SOURCE_FROZEN_FOR_INDEPENDENT_REVIEW','revision':'freeze02','decision':'SOURCE_FIX_READY_FOR_INDEPENDENT_QA',
    'construction_frozen':True,'source_modification_permitted':False,'at':datetime.now(timezone.utc).isoformat(),
    'worktree':str(wt),'base_head':scope['base_head'],'scope_path':str(scope_path),'scope_sha256':sha(scope_path),
    'previous_freeze':{'path':str(old/'FROZEN.json'),'sha256':sha(old/'FROZEN.json'),'manifest_sha256':sha(old/'EVIDENCE_MANIFEST.json'),'all276_pins_unchanged':True},
    'independent_previous_review':{'path':str(root/'prior-evidence/review.json'),'sha256':sha(root/'prior-evidence/review.json')},
    'interface_sha256':'046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c',
    'source_sha256':{name:pins[name] for name in scope['production_paths']},
    'test_sha256':{name:pins[name] for name in scope['test_paths']},
    'changed_since_freeze01':changed,'unchanged_since_freeze01':sorted(set(baseline)-set(changed)),
    'tests':{'node_syntax_exit':0,'node_syntax_commands':4,'pure_tests_exit':0,'tests':46,'pass':46,'fail':0,'skip':0,'raw_directory':'checks-02','tool_origin':'87ad82'},
    'build':{'vite_exit':0,'output_files':3,'all_final_production_inputs_unchanged':True,'raw_directory':'vite-01','tool_origin':'149ae2'},
    'git':{'diff_check_exit':0,'status_exit':0,'stat_exit':0,'exact10':True,'raw_directory':'git-final-02','tool_origin':'78da17'},
    'pending_blockers':[],'independent_source_approval':False,'native_execution_authorized':False,
    'formal_increment':0,'product_acceptance_increment':0,'commit_created':False,
    'real_gui_runs':0,'real_http_requests':0,'native_or_harness_runs':0,'model_runs':0,'old_probe_replays':0,'pending_processes':[],
    'diagnostic_events':events,
}
(root/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

directories = ['source-snapshot','baseline','checks-01','checks-02','git-final-01','git-final-02','attempt-01','prior-evidence']
top = ['FROZEN.json','README.md','DIAGNOSTICS.json','baseline-review.json','install-01.json','install-02.json',
       'prepare_revision.py','finish_fix.py','install_fix.py','repair_fixture.py','install_fixture_repair.py',
       'run_pure_checks.py','run_vite_build.py','run_git_checks.py','freeze02.py']
select = ['vite-01/command.json','vite-01/stdout','vite-01/stderr','vite-01/result.json']
archive = {'root':str(root),'root_files':top+['ARCHIVE_FILES.json','EVIDENCE_MANIFEST.json'],'include_directories':directories,
           'selected_files':select,'excluded':['node_modules','cache','candidate','vite-01/source','vite-01/dist'],
           'note':'Selected portable evidence only. Original C freeze01 and this complete C root remain retained.'}
(root/'ARCHIVE_FILES.json').write_text(json.dumps(archive,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selected = {root/name for name in top+['ARCHIVE_FILES.json']+select}
for name in directories:
    selected.update(path for path in (root/name).rglob('*') if path.is_file())
entries = [{'path':path.relative_to(root).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size} for path in sorted(selected)]
(root/'EVIDENCE_MANIFEST.json').write_text(json.dumps({'semantics':'selected portable archive evidence','file_count':len(entries),'files':entries,'source_frozen_sha256':sha(root/'FROZEN.json')},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'FROZEN_sha256':sha(root/'FROZEN.json'),'MANIFEST_sha256':sha(root/'EVIDENCE_MANIFEST.json'),'ARCHIVE_FILES_sha256':sha(root/'ARCHIVE_FILES.json'),'files':len(entries),'old276_unchanged':True}))
