import json,os,pathlib,subprocess,sys
E=pathlib.Path(__file__).resolve().parent
W=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/owned-core-stop-authority-r4-20261015')
GO='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe'
extra=E/'independent_store_review_windows_test.go'
overlay=E/'store-overlay.json'
overlay.write_text(json.dumps({'Replace':{str(W/'internal/store/independent_store_review_windows_test.go'):str(extra)}},indent=2),encoding='utf-8')
args=[GO,'test','-count=1','-v','-overlay',str(overlay),'-run','TestReviewMalformedModelEffectMustNotBeSafe|TestNativeExitProofRequiresExplicitNumericCapturePerClass|TestCommitSignalBoundaryHonorsCallerCancellationAndEarlierDeadline|TestOwnedCoreStopInspectJournalCrashBoundaries|TestOwnedStopOnlineBackupWALAndLogicalCAS|TestOwnedStopBarrierNativeQueryOnlyAndReservedWriter|TestOwnedCoreStopPublicIdentitySameSIDOwnerAndSchema','./internal/ownedcorestop','./internal/store','./internal/host']
raise SystemExit(subprocess.run([sys.executable,'-B','-X','utf8',str(E/'reviewer_logger.py'),*args],cwd=W).returncode)
