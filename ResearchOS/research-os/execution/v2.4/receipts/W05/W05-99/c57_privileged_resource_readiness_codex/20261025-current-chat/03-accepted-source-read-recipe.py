import pathlib,subprocess,hashlib,json
r=pathlib.Path('D:/作品集/ResearchOS/research-os');out=pathlib.Path(__file__).resolve().parent
commit='03aa4d687dfaa541d9b18d4c766805307a537d1d'
path='internal/recoveryboundary/boot_windows.go'
argv=['git','-C',str(r),'show',commit+':'+path]
p=subprocess.run(argv,capture_output=True)
(out/'03-source.stdout.raw').write_bytes(p.stdout);(out/'03-source.stderr.raw').write_bytes(p.stderr);(out/'03-source.exit.txt').write_text(str(p.returncode))
print(json.dumps({'argv':argv,'exit':p.returncode,'source_sha256':hashlib.sha256(p.stdout).hexdigest()}))
assert p.returncode==0
assert hashlib.sha256(p.stdout).hexdigest()=='8cb1639c9e8643dcc3520a699bf6dc1090028e7f7d5347c35ea56171a0c56afe'
lines=p.stdout.decode('utf-8').splitlines()
for low,high in [(876,903),(1268,1322),(1734,1746)]:
    for i in range(low,high+1):print(f'{i}: {lines[i-1]}')