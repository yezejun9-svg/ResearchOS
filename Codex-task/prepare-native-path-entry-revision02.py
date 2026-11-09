from pathlib import Path
import json, hashlib, difflib

cwd=Path(__file__).resolve().parent
old=cwd/'product-v1-native-path-entry-prepare-01'
new=cwd/'product-v1-native-path-entry-prepare-02'
new.mkdir()
copy=['real-electron-flow.mjs','choose-owned-folder.ps1','scope.template.json','README.md','runner.diff','runner-purechecks.mjs','path-entry-purechecks.ps1']
for name in copy:(new/name).write_bytes((old/name).read_bytes())
helper=(new/'choose-owned-folder.ps1').read_text(encoding='utf-8')
marker="try {\n  Require ((Get-FileHash"
predicate="""function Assert-MessageDeadline([DateTime]$Now,[DateTime]$Limit) {
  if ($Now.Kind -ne [DateTimeKind]::Utc -or $Limit.Kind -ne [DateTimeKind]::Utc -or $Now -ge $Limit) {
    throw 'MESSAGE_SEND_DEADLINE_EXPIRED_OR_NON_UTC'
  }
}
"""
assert helper.count(marker)==1
helper=helper.replace(marker,predicate+marker)
needle='    $sent=[OwnedPathWin32]::SetText($edit,0x000C'
assert helper.count(needle)==1
helper=helper.replace(needle,'    Assert-MessageDeadline ([DateTime]::UtcNow) $actionDeadline\n'+needle)
needle='    $script:uncertain=$true\n    if ($Purpose'
assert helper.count(needle)==1
helper=helper.replace(needle,"    $messageDeadline=$actionDeadline\n    if ($ForCleanup) {$messageDeadline=$cleanupDeadline}\n    Assert-MessageDeadline ([DateTime]::UtcNow) $messageDeadline\n"+needle)
# No synchronous query or other blocking work occurs between this final pure
# deadline check and PostMessage; only uncertainty/attempt scalar bookkeeping.
(new/'choose-owned-folder.ps1').write_text(helper,encoding='utf-8',newline='\n')
(new/'helper.diff').write_text(''.join(difflib.unified_diff((old/'choose-owned-folder.ps1').read_text(encoding='utf-8').splitlines(True),helper.splitlines(True),fromfile='freeze01/choose-owned-folder.ps1',tofile='revision02/choose-owned-folder.ps1')),encoding='utf-8')
scope=json.loads((new/'scope.template.json').read_text(encoding='utf-8'))
scope['harness']['folder_helper_sha256']=hashlib.sha256((new/'choose-owned-folder.ps1').read_bytes()).hexdigest()
scope['status']='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_NEW_SCOPE_AND_EXACT_JOB'
(new/'scope.template.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=(new/'README.md').read_text(encoding='utf-8')
readme=readme.replace('# Native path entry candidate 01 — NOT_RUN','# Native path entry candidate 02 — NOT_RUN',1)
readme+='''
Revision 02 preserves frozen 01 and only closes the final message-send deadline
gap. After all synchronous control queries, WM_SETTEXT checks the action UTC
deadline again. BM_CLICK checks the action deadline (or independent cleanup
deadline for IDCANCEL) after all queries; only scalar attempt/uncertainty
bookkeeping intervenes before the queue call. No activation or replay is added.
The 23 prior pure cases are inherited, not rerun. Only the new deadline predicate
and complete helper AST syntax are checked for this revision. Actual runtime is
still NOT_RUN. Root explicitly declined registering/running frozen 01.
'''
(new/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'status':'REVISION02_SOURCE_PREPARED_NOT_RUN','path':str(new),'helper_sha256':scope['harness']['folder_helper_sha256']}))
