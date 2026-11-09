import hashlib,os,subprocess,sys
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
GO=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
WT=ROOT/'.local/worktrees/product-v1-native-preparation-desktop-drain-20261105'
PATTERN='^(TestHarnessPreparationFailureAtomicTerminalAndRestart|TestHarnessPreparationFailureRejectsConflictsAndRollsBack|TestHarnessPreparationProofRejectsUnknownAndIncompleteFacts|TestHarnessStoppedChildPreparationReleasesOnlyLocalZeroHold|TestHarnessPreparationLocalHoldConflictsRollBackSettlement|TestHarnessPreparationExistingReleaseConflictRefusesRepeat|TestHarnessPreparationReleaseAppendFailureRollsBackC5|TestHarnessConcreteQualifiedHandleNoChildPreflight|TestDesktopExitStoppedNativePreparationKeepsConsumedHistory|TestDesktopExitStoppedNativePreparationRejectsCounterevidence|TestDesktopExitCompletedLocalUnknownPreservesReleaseGate|TestDesktopExitUnknownIncompleteRefused|TestCompletedRuntimeLocalLaunchRelease)$'
ARGS=['test','-p=1','-v','-count=1','-run',PATTERN,'./internal/domain']
assert hashlib.sha256(GO.read_bytes()).hexdigest()=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
assert Path.cwd()==WT and sys.argv[1:]==[str(GO),*ARGS]
for name in ['GOENV','GOPROXY','GOSUMDB','GOWORK']:assert os.environ.get(name)=='off'
os.environ['GOMAXPROCS']='1'
raise SystemExit(subprocess.run([str(GO),*ARGS],cwd=WT,check=False).returncode)
