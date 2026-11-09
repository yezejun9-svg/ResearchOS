import pathlib,json,hashlib,subprocess
O=pathlib.Path(r'C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-v2-review-20261012');S=pathlib.Path(r'C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012')
d=json.loads((S/'.local/qualification-build-output-v2-02/apps/desktop/resources/client-wire/descriptor.json').read_text());go=d['go_tool_ref'];assert hashlib.sha256(pathlib.Path(go['path']).read_bytes()).hexdigest()==go['sha256']
args=[go['path'],'version','-m',str(S/'.local/qualification-build-output-v2-02/apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')];p=subprocess.run(args,cwd=O,capture_output=True)
(O/'validator-build-metadata.stdout.raw').write_bytes(p.stdout);(O/'validator-build-metadata.stderr.raw').write_bytes(p.stderr);(O/'validator-build-metadata.invocation.json').write_text(json.dumps({'argv':args,'cwd':str(O),'exit':p.returncode},ensure_ascii=False,indent=2)+'\n');assert p.returncode==0
print(p.stdout.decode())
