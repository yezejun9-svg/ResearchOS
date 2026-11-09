import pathlib,json,hashlib,subprocess,shutil
E=pathlib.Path(__file__).parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os');commit='7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e'
scope=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp551/Desktop-development-build-scope.json';sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(scope.read_bytes())=='6872af4a2aa0f2268394a8e0867e328f6a443dca531f9d2215715485e6bcbc42'
(E/'Desktop-development-build-scope.json').write_bytes(scope.read_bytes())
git=shutil.which('git');argv=[git,'-C',str(R)]
tree=subprocess.check_output(argv+['rev-parse',commit+'^{tree}']).decode().strip();assert tree=='de59625ee5c1d360c741c95ec3f84b6f2764bb0e'
files=['apps/desktop/build-validator.py','apps/desktop/main/main.js','apps/desktop/main/lib/desktop-management.js','apps/desktop/main/lib/native.js']
refs=[]
for name in files:
 raw=subprocess.check_output(argv+['show',commit+':'+name]);p=E/'snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 refs.append({'path':name,'sha256':sha(raw),'bytes':len(raw),'lines':len(raw.splitlines())})
(E/'SOURCE4-snapshot-manifest.json').write_text(json.dumps({'commit':commit,'tree':tree,'files':refs},indent=2),encoding='utf-8')
print(json.dumps(refs,indent=2))
