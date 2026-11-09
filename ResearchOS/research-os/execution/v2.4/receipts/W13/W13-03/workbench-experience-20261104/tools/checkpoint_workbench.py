import json
import sys
from datetime import datetime, timezone
from resume_workbench import REPO, RECEIPT, CANDIDATE, digest, write_json

DIAGNOSTICS = [
    ('sandbox-git-read', 2, None, ['999e1a', 'd39742'], 'Restricted Git reads reported work-tree/cwd permission errors. Approved elevated read succeeded. No source change.'),
    ('windowsapps-python-alias', 1, 1, ['7570ed'], 'WindowsApps Python alias could not execute; existing pythoncore-3.14-64 was located and used successfully.'),
    ('skill-resource-user-context', 1, None, [], 'skills.read additional resource returned skill environment unavailable; read the installed same skill file directly.'),
    ('skill-resource-get-context', 1, None, [], 'skills.read additional resource returned skill environment unavailable; read the installed same skill file directly.'),
    ('preflight-script-locator', 1, None, ['29d757'], 'The first read used the wrong skill-relative script path; located and successfully ran skills/user-context/scripts/user_context_preflight.py.'),
    ('baseline-render-dom-assumption', 1, None, ['b45d25'], 'Baseline fixture report FAIL because old preserved dist lacked new layout selector; report retained. Revised baseline capture succeeded. GUI outer tool exit was 0.'),
    ('candidate-render-css-cascade', 1, None, ['dc22af'], 'Candidate r1 reported FAIL: conversation 168px at 1440. Fixed CSS import order; final r3 passes.'),
    ('r2-overflow-method-correction', 1, 0, ['269b46'], 'r2 reported PASS using innerWidth but screenshot showed 320px overflow. Preserve report, supersede overflow conclusions with strict clientWidth r3 checks.'),
    ('builder-test-cwd', 1, 1, ['d79960'], 'Builder initially ran root-relative test from apps/web cwd; retained diagnostic. Correct-root tests subsequently passed.'),
    ('builder-sandbox-git-read', 1, None, ['6aef2b'], 'Builder read-only Git diff failed in restricted environment; outer command continued with exit0. Elevated diff succeeded.'),
    ('builder-line-ending-check', 1, 2, ['7a5288'], 'Git diff check flagged new CRLF lines. Fixed changed lines while preserving unchanged bytes; final diff check passed. Outer shell continued with exit0.'),
    ('git-auto-gc-oom', 1, None, ['54f039'], 'Automatic Git repack ran out of memory after candidate commit. Commit 3cd8e4ce succeeded, was verified and fast-forwarded. No GC retry; subsequent Git commands disable automatic maintenance per invocation.'),
    ('independent-bundle-report-command-length', 1, None, [], 'Windows rejected the initial long independent report-writing command with os206 before CreateProcess; it did not execute or write a report. Completed validation facts were retained and transferred through a workspace JSON file and a short copy command. No product operation or acceptance threshold changed.'),
]

def main():
    expected = int(sys.argv[1])
    phase = sys.argv[2]
    assert phase in ('BUILDING', 'CHECKPOINTED')
    checkpoint_path = REPO / 'execution/v2.4/checkpoint.json'
    raw = checkpoint_path.read_bytes()
    checkpoint = json.loads(raw)
    assert checkpoint['revision'] == expected, 'Concurrent checkpoint change; reconcile first'
    baseline = json.loads((RECEIPT / 'scope-and-baseline.json').read_bytes())
    before_count = baseline['failure_counter_count_before']
    assert digest(json.dumps(checkpoint['failure_counters'][:before_count], sort_keys=True, ensure_ascii=False).encode()) == baseline['failure_counter_sha256_before']
    assert digest((REPO / 'execution/v2.4/step_state.json').read_bytes()) == baseline['step_state_sha256_before']
    for relative, original in baseline['protected_tracked_before'].items():
        if relative in {'execution/v2.4/checkpoint.json','execution/v2.4/HANDOFF_RESUME_PACK.md'}:
            continue
        target=REPO / relative
        assert (digest(target.read_bytes()) if target.exists() else 'ABSENT_BEFORE') == original
    for relative, original in baseline['source_and_dist_before'].items():
        if relative.startswith('apps/web/dist/'):
            assert digest((REPO / relative).read_bytes()) == original
    existing = {item.get('origin_key') for item in checkpoint['failure_counters']}
    now = datetime.now(timezone.utc).isoformat()
    for key, attempts, exit_code, chunks, detail in DIAGNOSTICS:
        origin = '20261104|workbench-experience|' + key
        if origin not in existing:
            checkpoint['failure_counters'].append({'at':now,'origin_key':origin,'attempts':attempts,'exit':exit_code,
                'tool_chunks':chunks,'status':'DEVELOPMENT_TOOL_OR_REVIEW_DIAGNOSTIC_PRESERVED', 'detail':detail,'counter_reset':False})
    failed_builds=[]
    for failed in sorted((RECEIPT/'desktop-build').glob('build-*/failed.json')):
        failed_builds.append({'path':failed.relative_to(REPO).as_posix(),'sha256':digest(failed.read_bytes())})
    if failed_builds:
        origin='20261104|workbench-experience|desktop-build'
        entry=next((item for item in checkpoint['failure_counters'] if item.get('origin_key')==origin),None)
        if entry is None:
            entry={'at':now,'origin_key':origin,'counter_reset':False}
            checkpoint['failure_counters'].append(entry)
        entry.update({'attempts':len(failed_builds),'actual_failed_build_invocations':len(failed_builds),
            'status':'FAILED_BUILD_EVIDENCE_PRESERVED','evidence':failed_builds,
            'detail':'Build attempts and original scratch remain preserved. The first attempt lacked same-repository Go source in sparse checkout. Immutable new output for the one permitted repair does not reset this origin.'})
    write_json(RECEIPT / 'tool-diagnostics.json', {'original_counter_count':before_count, 'new_record_count':len(checkpoint['failure_counters'])-before_count,
        'current_counter_count':len(checkpoint['failure_counters']), 'records':[item for item in checkpoint['failure_counters'] if item.get('origin_key','').startswith('20261104|workbench-experience|')]})
    integration=json.loads((RECEIPT / 'integration.json').read_bytes())
    resume={
        'schema':'researchos.workbench-resume.v2','at':now,'checkpoint_revision':expected+1,
        'status':phase,'step_id':'W13-03','official_next_step_id':'W05-99',
        'repository':str(REPO),'candidate':str(CANDIDATE),'head':integration['head'],
        'source_status':'INTEGRATED_ON_MAIN_AFTER_INDEPENDENT_REVIEW',
        'scope':'W13-03 DEVELOPMENT_ONLY; real Core/provider and full formal gates not asserted',
        'independent_review_ref':'independent-review.json','independent_review_sha256':digest((RECEIPT / 'independent-review.json').read_bytes()),
        'render_ref':'candidate-render-r3/report.json','render_sha256':digest((RECEIPT / 'candidate-render-r3/report.json').read_bytes()),
        'render_kind':'ELECTRON_RENDER_FIXTURE_ONLY','render_checks':54,'screenshots':14,
        'formal_accepted':0,'formal_required':42,'required_parent_tasks':22,'formal_increment':0,
        'original_tracked_status_preserved':20,'original_dist_files_preserved':33,
        'original_failure_records_preserved':before_count,'failure_records_current':len(checkpoint['failure_counters']),
        'step_state_unchanged':True,'counter_reset':False,'installed_product_changed':False,
        'preserved_blockers':['W13-03 physical NVDA/foreground and existing formal acceptance restrictions',
            'CP575 native helper/installer continuation and original data/host conditions',
            'Current Windows installer, real shared-session/provider, phone, overnight/recovery and 22-parent/42-case acceptance remain unfinished'],
        'next': 'Finish source-bound Desktop development build only; no installation or original-data native actions.' if phase=='BUILDING' else 'Read HANDOFF.md and desktop-build status; next official card remains W05-99, preserve its original retry/resource restrictions.',
    }
    build_status=RECEIPT / 'desktop-build' / 'summary.json'
    if build_status.exists():
        resume['desktop_build_ref']='desktop-build/summary.json'
        resume['desktop_build_sha256']=digest(build_status.read_bytes())
        built=json.loads(build_status.read_bytes())
        resume['desktop_build_status']=built['status']
        resume['desktop_output']=built['output']
    build_review=RECEIPT/'desktop-build/independent-review.json'
    if build_review.exists():
        resume['desktop_independent_review_ref']='desktop-build/independent-review.json'
        resume['desktop_independent_review_sha256']=digest(build_review.read_bytes())
    write_json(RECEIPT / 'RESUME.json',resume)
    (RECEIPT / f'checkpoint.before-cp{expected+1}.json').write_bytes(raw)
    checkpoint['expected_previous_revision']=expected
    checkpoint['revision']=expected+1
    checkpoint['current_Main_HEAD']=integration['head']
    checkpoint['current_Main_tree']=integration['tree']
    checkpoint['user_workbench_iteration']={'status':phase,'step_id':'W13-03','at':now,
        'resume_ref':(RECEIPT / 'RESUME.json').relative_to(REPO).as_posix(),
        'main_head':integration['head'],'formal_increment':0,'failure_records_current':len(checkpoint['failure_counters'])}
    assert checkpoint_path.read_bytes()==raw
    write_json(checkpoint_path,checkpoint)
    handoff=REPO / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
    prefix=f'# Current user workbench continuation CP{expected+1}\n\nRead execution/v2.4/receipts/W13/W13-03/workbench-experience-20261104/RESUME.json first. UI source integrated Main 3cd8e4ce; independent source review and 54 fixture-render checks passed. Desktop development build {phase}. Original 2305 failure records and old CP575 branches preserved; new diagnostics appended without reset. Formal 0/42 and all 22 parent gates remain unfinished.\n\n'
    temporary=handoff.with_name(handoff.name+'.workbench-new')
    temporary.write_bytes(prefix.encode()+handoff.read_bytes())
    temporary.replace(handoff)
    print(json.dumps({'checkpoint':expected+1,'phase':phase,'failure_records':len(checkpoint['failure_counters']),'formal_increment':0}))

if __name__=='__main__':
    main()
