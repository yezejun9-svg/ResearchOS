import os,pathlib,subprocess,sys
E=pathlib.Path(__file__).resolve().parent
os.environ['RESEARCHOS_R4_UNTRUSTED_IMAGE']='D:/作品集/ResearchOS/research-os/.local/owned-core-stop-r4-independent-review-20261015-tmp/fixture-r4.exe'
argv=[sys.executable,'-B','-X','utf8',str(E/'reviewer_logger.py'),'C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-r4-independent-review-20261015/supervisor-review-v2.exe','-test.v=true','-test.run=TestOwnedImageOwnerAndACEAuthorization|TestOwnedImageRejectsUnsafeInstallationAndCopiedProcessACL|TestOwnedCoreAndParentImageAncestorsRetained|TestReview','-test.timeout=60s']
if len(sys.argv)>1:argv[-2]='-test.run='+sys.argv[1]
raise SystemExit(subprocess.run(argv).returncode)
