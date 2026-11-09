import pathlib,subprocess,sys
E=pathlib.Path(__file__).resolve().parent
W='D:/作品集/ResearchOS/research-os/.local/worktrees/owned-core-stop-authority-r4-20261015'
GO='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe'
args=[GO,'test','-count=1','-v','-overlay',str(E/'store-overlay.json'),'-run','TestReviewFiniteEffectStateSemantics','./internal/store']
raise SystemExit(subprocess.run([sys.executable,'-B','-X','utf8',str(E/'reviewer_logger.py'),*args],cwd=W).returncode)
