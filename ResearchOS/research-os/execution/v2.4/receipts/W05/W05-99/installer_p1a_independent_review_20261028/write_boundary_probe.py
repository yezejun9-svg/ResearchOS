import json, os, pathlib, subprocess
R=pathlib.Path(__file__).resolve().parent
W=pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\installer-p1a-20261028')
locked=json.loads((W/'execution/toolchains/locked.json').read_bytes())['tools']
existing=R/'scratch/preexisting-receipts';existing.mkdir(exist_ok=False)
(existing/'sentinel.txt').write_text('preserve original receipts',encoding='utf-8')
before=sorted(p.name for p in existing.iterdir())
argv=[locked['python']['path'],'-B',str(W/'ops/release/product_installer/build.py'),'--candidate',str(R/'scratch/not-used-candidate'),'--output',str(R/'scratch/not-used-output'),'--receipts',str(existing),'--go',locked['go']['path']]
p=subprocess.run(argv,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
(R/'preexisting-receipts.stdout.raw').write_bytes(p.stdout);(R/'preexisting-receipts.stderr.raw').write_bytes(p.stderr)
after=sorted(p.name for p in existing.iterdir())
result={'argv':argv,'exit':p.returncode,'before':before,'after':after,'existing_directory_modified':before!=after,'failure_receipt':json.loads((existing/'failed.json').read_bytes())}
(R/'preexisting-receipts-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert p.returncode==1 and result['existing_directory_modified']
print('Confirmed existing receipts changed after create-new refusal')
