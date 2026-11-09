"""Read-only AST probe of the W13 registered source manifest patterns."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\react-workbench-redesign-20261025')
OUT = Path(__file__).parent
source = (ROOT / 'ops/ci/ui.py').read_text(encoding='utf-8')
tree = ast.parse(source, filename='ops/ci/ui.py')
assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'patterns' for target in node.targets)]
assert len(assignments) == 1
patterns = ast.literal_eval(assignments[0].value)
assert len(patterns) == len(set(patterns))
original = ['apps/control/*.go', 'apps/web/src/*', 'apps/web/package*.json', 'apps/web/index.html',
            'internal/**/*.go', 'adapters/**/*.go', 'migrations/sqlite/*.sql', 'spec/v2.0/contracts/*.json',
            'spec/v2.0/ui/*.json', 'tests/ui/**/*.go', 'tests/ui/*.py', 'tests/ui/expected.json',
            'ops/ci/ui.py', 'execution/commands.json', 'go.mod', 'go.sum', 'execution/toolchains/locked.json']
assert set(original) <= set(patterns)
assert set(patterns) - set(original) == {'apps/web/src/**/*', 'tests/ui/**/*.js', 'tests/ui/**/*.cjs'}
sources = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
           for pattern in patterns for path in ROOT.glob(pattern) if path.is_file()}
required = [
    'apps/web/src/components/app-shell.jsx',
    'apps/web/src/components/ui.jsx',
    'apps/web/src/components/workbench-layout.jsx',
    'tests/ui/frontend-redesign.cjs',
    'tests/ui/frontend-redesign-fixture.cjs',
]
assert all(path in sources for path in required)
expected = json.loads((OUT / 'SOURCE13-final.json').read_text(encoding='utf-8'))['source_sha256']
assert all(sources[path] == expected[path] for path in required)
assert 'tests/ui/desktop/w13-react.test.js' in sources
report = {'schema': 'researchos.source14-ci-pattern-probe.v1', 'status': 'PASS',
          'syntax': 'ast.parse PASS', 'pattern_count': len(patterns), 'original_patterns_preserved': True,
          'new_patterns': sorted(set(patterns) - set(original)), 'required_sha256': {path: sources[path] for path in required},
          'existing_w13_react_test_hashed': sources['tests/ui/desktop/w13-react.test.js'],
          'total_source_manifest_entries': len(sources),
          'boundary': 'AST + glob source binding only; no registered W13 suite or formal acceptance was run'}
(OUT / 'SOURCE14-CI-PROBE.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'status': report['status'], 'required': len(required), 'patterns': len(patterns), 'entries': len(sources)}, ensure_ascii=False))
