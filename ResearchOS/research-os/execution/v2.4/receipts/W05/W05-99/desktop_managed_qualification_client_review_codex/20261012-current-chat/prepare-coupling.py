from pathlib import Path
OUT=Path(__file__).resolve().parent
AUTHOR=OUT.parents[1]/'desktop_managed_qualification_client_codex/20261012-current-chat'
s=(AUTHOR/'candidate-binary-coupling.mjs').read_text(encoding='utf-8')
s=s.replace("path.join(worktree, 'apps/desktop/main/lib/desktop-management.js')","path.join(worktree, '.local/managed-client-bound-final3/apps/desktop/main/lib/desktop-management.js')")
s=s.replace("path.join(worktree, `.local/managed-client-coupling-${runId}`)","path.join(receipt, `real-core-fixture-${runId}`)")
s=s.replace(".local/managed-client-bound-final/apps/web/dist",".local/managed-client-bound-final3/apps/web/dist")
(OUT/'core-coupling.mjs').write_text(s,encoding='utf-8')
