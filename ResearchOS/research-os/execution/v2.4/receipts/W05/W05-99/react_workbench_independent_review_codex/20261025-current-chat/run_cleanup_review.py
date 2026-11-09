from review_driver import *
result=run('026-cleanup-owned',['pwsh','-NoProfile','-File',str(E/'cleanup_owned_review.ps1')])
save(E/'CLEANUP.json',dict(owned_disposable_roots=json.loads(result),retained='Review worktree and its built candidate bundle retained for Root inspection; receipts and failed attempts retained.'))
print('owned disposable credentials/data/binary removed')
