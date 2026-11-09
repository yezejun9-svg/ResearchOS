from pathlib import Path
import hashlib, json, subprocess, datetime

out = Path(__file__).resolve().parent
author = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/control-business-proof')
channel = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/current-control-channel')
def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, encoding='utf-8').strip()
author_files = [
    'AGENTS.md', 'execution/project_identity.json',
    'evaluation/evolution/control_current.go', 'evaluation/evolution/control_protocol.go',
    'internal/domain/evolution_control_current.go', 'internal/domain/evolution_control_current_execution.go',
    'internal/domain/evolution_control_current_test.go', 'internal/domain/evolution_control_freeze.go',
    'internal/domain/evolution_control_delta.go', 'internal/domain/evolution_control_delta_integrity.go',
    'internal/domain/evolution_control_snapshot.go', 'internal/domain/evolution_control_projection.go',
    'internal/domain/evolution_control_execution.go', 'internal/domain/evolution_control_holdout.go',
    'internal/domain/evolution_control_host.go', 'internal/domain/evolution.go',
    'internal/domain/evolution_execution.go', 'internal/domain/evolution_holdout.go',
    'internal/domain/evolution_release_windows.go', 'internal/domain/orchestration.go',
    'internal/domain/runtime.go', 'ops/supervisor/control_authority_windows.go',
    'ops/supervisor/control_holdout_windows.go', 'ops/supervisor/control_fixture_windows.go',
    'ops/supervisor/release_drain_windows.go', 'ops/experiment_sandbox/sandbox_windows.go',
]
channel_files = ['apps/control/current_control_windows.go', 'apps/control/current_control_windows_test.go',
    'apps/control/drain_windows.go', 'ops/supervisor/release_host/control_windows.go']
sources = []
for owner, root, files in [('author', author, author_files), ('channel', channel, channel_files)]:
    for name in files:
        raw = (root/name).read_bytes()
        sources.append({'owner':owner,'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
freeze = (author/'internal/domain/evolution_control_freeze.go').read_text(encoding='utf-8').splitlines()
needles = ['if err = controlBusinessReadsetUnchanged', 'delta[i].Reason =', 'func controlBusinessReadsetUnchanged', 'selected :=']
locations = [{'line':i+1,'source':s} for i,s in enumerate(freeze) if any(n in s for n in needles)]
audit = {'mode':'READ_ONLY_SOURCE_PRE_REVIEW','verdict':'NEEDS_WORK','final_acceptance':False,
    'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_freeze':False,'author_root':str(author),'author_head':git(author,'rev-parse','HEAD'),
    'author_status':git(author,'status','--short'), 'channel_root':str(channel),
    'channel_commit':'f85cf066888d90042d8c1378a95ed29814be07e9',
    'channel_head':git(channel,'rev-parse','HEAD'),'channel_status':git(channel,'status','--short'),
    'channel_author_files_equal':{name:(author/name).read_bytes()==(channel/name).read_bytes() for name in channel_files},
    'source_files':sources,'findings':[{'id':'P1-01','priority':1,
        'title':'B0 to G0 authority changes lack named allowlist',
        'file':'internal/domain/evolution_control_freeze.go','locations':locations}],
    'tests_executed':False,'build_executed':False,'native_executed':False,'private_live_access':False}
(out/'source-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name != 'manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_files':len(sources),'author_head':audit['author_head'],'findings':len(audit['findings']),'review_sha256':manifest['review.md']},ensure_ascii=False))
