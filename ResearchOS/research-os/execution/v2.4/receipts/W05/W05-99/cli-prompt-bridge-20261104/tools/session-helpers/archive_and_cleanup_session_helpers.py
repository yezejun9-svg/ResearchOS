import hashlib,json
from pathlib import Path
cwd=Path(__file__).resolve().parent
assert cwd==Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task')
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
names='''archive_build_retry_tools.py archive_cli_tools.py build_cli_development_r2.py build_cli_development.py builder-stdout-author-controller.py checkpoint_cli_cp583.py cli-prompt-author.py cli-prompt-baseline-controller.py cli-prompt-finalize.py cli-prompt-int64-fix.py cli-prompt-metadata.py cli-prompt-pretest.py cli-prompt-retry-prepare.py cli-prompt-test-controller-r2.py cli-prompt-test-controller.py cli-prompt-tests-author.py compatibility-development-build-r2.py compatibility-development-build.py finish_artifacts_cp586.py fix_cli_scope_metadata.py integrate_builder_stdout_fix.py integrate_cli_prompt_bridge.py materialize_cli_prompt_closure_r2.py materialize_cli_prompt_closure.py prepare_compatibility_build_controller.py prepare_compatibility_build_retry.py start_builder_stdout_fix.py w05-routing-author.py w05-routing-finalize.py w05-routing-fix-01.py w05-routing-refine.py w05-routing-test-controller-r2.py w05-routing-test-controller.py workbench-builder-edit.py workbench-builder-finalize.py workbench-builder-review-fixes.py workbench-desktop-build-controller-r2.py workbench-desktop-build-controller.py workbench-desktop-build-retry-prepare.py workbench-desktop-build-summary.py archive_and_cleanup_session_helpers.py'''.split()
assert set(names)=={p.name for p in cwd.iterdir() if p.is_file() and p.suffix=='.py'},'Inspect unexpected new script before cleanup'
archive=out/'tools/session-helpers';archive.mkdir(exist_ok=False)
rows=[]
for name in names:
    source=cwd/name;assert source.parent==cwd and not source.is_symlink()
    raw=source.read_bytes();target=archive/name;target.write_bytes(raw)
    assert target.read_bytes()==raw
    rows.append({'temporary':str(source),'archive':str(target.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest()})
for row in rows:
    source=Path(row['temporary']);assert source.parent==cwd
    assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256']
    source.unlink()
(out/'temporary-helper-cleanup.json').write_text(json.dumps({'status':'EXACT_OWNED_TEMP_SCRIPTS_ARCHIVED_VERIFIED_AND_REMOVED','files':rows,'old_user_files_or_evidence_removed':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'temporary_scripts_archived_and_removed':len(rows),'final_checkpoint_controller':str(archive/'finish_artifacts_cp586.py')}))
