from pathlib import Path
import re

p=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-harness-progress-ui-20261105/apps/web/src/workbench.jsx')
s=p.read_text(encoding='utf8')
marker="import { HARNESS_CAPABILITIES, canSubmitHarness, hasHarnessCapability, harnessStatusLabel, createHarnessController } from './harness.js'"
assert s.count(marker)==1
s=s.replace(marker,marker+"\nimport { HarnessRunProgress, HarnessPermissionNotice } from './components/harness-run-progress.jsx'")
start=s.index('function NativeHarnessWorkbench(')
end=s.index('function NativeMuWorkbench(',start)
block=s[start:end]
block,n=re.subn(r'(?=<div className="conversation-transcript" aria-label="Codex [^"]+">)', '<HarnessRunProgress task={task} events={state.events}/>\n        ',block,count=1)
assert n==1
block,n=re.subn(r'\{!capabilities\.can_submit && <p role="status">[^<]*\{capabilities\.reason_codes\.join\([^)]*\)\}</p>\}', '<HarnessPermissionNotice capabilities={capabilities}/>',block,count=1)
assert n==1
s=s[:start]+block+s[end:]
p.write_text(s,encoding='utf8',newline='\n')
print('workbench import, progress component and permission notice inserted')
