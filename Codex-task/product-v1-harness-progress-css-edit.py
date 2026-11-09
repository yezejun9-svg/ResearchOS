from pathlib import Path

p=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-harness-progress-ui-20261105/apps/web/src/workbench.css')
s=p.read_text(encoding='utf8')
assert '.harness-run-progress{' not in s
s+='''\n/* Read-only Host Task/Run projection inside the Native Codex conversation. */
.harness-run-progress{margin:12px 0 4px;padding:14px 16px;border:1px solid var(--border);border-radius:12px;background:var(--surface)}
.harness-progress-heading{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin-bottom:12px}
.harness-progress-heading strong{font-size:13px}.harness-progress-heading small,.harness-progress-empty{color:var(--muted);font-size:12px;line-height:1.6}
.harness-progress-empty{margin:0}.harness-progress-stages{list-style:none;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:0;padding:0}
.harness-progress-stages li{display:flex;gap:8px;min-width:0}.harness-progress-dot{flex:none;width:8px;height:8px;margin-top:6px;border:1px solid var(--muted);border-radius:50%;background:var(--surface)}
.harness-progress-stages li[data-state="done"] .harness-progress-dot,.harness-progress-stages li[data-state="observed"] .harness-progress-dot{border-color:var(--success);background:var(--success)}
.harness-progress-stages li[data-state="active"] .harness-progress-dot{border-color:var(--accent);background:var(--accent)}
.harness-progress-stages li[data-state="unresolved"] .harness-progress-dot{border-color:var(--warning);background:var(--warning)}
.harness-progress-stages li>div{min-width:0}.harness-progress-stages strong{display:block;font-size:12px;font-weight:600}.harness-progress-stages li span:last-child{display:block;color:var(--muted);font-size:11px;line-height:1.55;overflow-wrap:anywhere}
.harness-permission-notice{margin:12px 0;padding:12px;border:1px solid var(--border);border-radius:10px;background:var(--subtle);font-size:12px;line-height:1.6}
.harness-permission-notice strong{display:block}.harness-permission-notice ul{margin:7px 0;padding-left:18px}.harness-permission-notice p{margin:7px 0;color:var(--muted)}
.harness-permission-notice details{margin-top:8px}.harness-permission-notice summary{cursor:pointer}.harness-permission-notice code{display:block;overflow-wrap:anywhere;margin-top:5px}
@media(max-width:767px){.harness-progress-heading{display:block}.harness-progress-heading small{display:block;margin-top:3px}.harness-progress-stages{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 10px}}
@media(max-width:390px){.harness-run-progress{padding:12px}.harness-progress-stages{grid-template-columns:minmax(0,1fr);gap:10px}}
'''
p.write_text(s,encoding='utf8',newline='\n')
print('scoped progress CSS appended')
