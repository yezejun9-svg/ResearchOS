import json
import pathlib

here = pathlib.Path(__file__).resolve().parent
ledger = here / 'diagnostic-ledger.jsonl'
present = {json.loads(line)['id'] for line in ledger.read_text(encoding='utf-8').splitlines() if line.strip()}
rows = [
    ('003-worktree-add', 'RESOURCE_DIAGNOSTIC', 'Full worktree checkout exhausted D: disk space; Git removed incomplete target. Recreated same branch with --no-checkout and sparse paths.', 128),
    ('004-partial-worktree-diagnostic', 'RESOURCE_DIAGNOSTIC', 'Confirmed failed full checkout target absent and disk nearly full.', 1),
    ('011-sparse-target-check', 'COMMAND_DIAGNOSTIC', 'PowerShell variable included whitespace around target path; corrected following recipe.', 1),
    ('012-restore-sparse-worktree', 'COMMAND_DIAGNOSTIC', 'Sparse checkout pathspec . did not match; explicit sparse directories used later.', 1),
    ('018-domain-core', 'COMMAND_DIAGNOSTIC', 'Read-only source slice overshot EOF; corrected bounded read.', 1),
    ('023-service-config-map', 'COMMAND_DIAGNOSTIC', 'Read-only rg included nonexistent service.go; found actual declaration in runtime_qualification_failure_windows.go.', 2),
    ('030-pref-f01-repro', 'EXPECTED_PRE_FIX_FAIL', 'Independent original overlay reproduced F01: original guard accepted replacement directory after rename, distinct native file IDs; replacement only received write and Sync.', 1),
    ('031-pref-f02-repro', 'FIXTURE_SETUP_DIAGNOSTIC', 'Sparse worktree lacked evaluation packages; added required evaluation sparse paths.', 1),
    ('033-pref-f02-repro-retry', 'FIXTURE_SETUP_DIAGNOSTIC', 'Sparse worktree lacked spec/v2.0/contracts/domain.schema.json; added spec/v2.0 sparse path.', 1),
    ('035-pref-f02-repro-final', 'EXPECTED_PRE_FIX_FAIL', 'Independent original overlay reproduced F02: positive full census/replay passed while four original raw fact cuts failed to reject changed stdout, stderr, bridge, rejection.', 1),
    ('036-list-directory-constant', 'COMMAND_DIAGNOSTIC', 'Read-only rg used nonexistent local golang.org/x/sys module path; resolved system constant through installed Go source and Microsoft documentation.', 2),
    ('054-prior-mu-command-map', 'COMMAND_DIAGNOSTIC', 'Read-only rg requested nonexistent test-matrix.json from prior source evidence; located pinned command IDs in command-index.json.', 2),
]
with ledger.open('a', encoding='utf-8') as out:
    for id_, cls, cause, exit_code in rows:
        if id_ in present:
            continue
        out.write(json.dumps({'id': id_, 'at': '2026-10-15', 'class': cls, 'cause': cause, 'native_exit': exit_code, 'raw_location': f'{id_}/stdout.raw and {id_}/stderr.raw', 'disposition': 'Preserved original raw capture; no counter/status rewriting'}, ensure_ascii=False) + '\n')
