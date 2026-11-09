exec((__import__('pathlib').Path(__file__).parent/'prepare.py').read_text().split("assert git('rev-parse','HEAD')")[0])
paths=['evaluation/holdout/jev','evaluation/evolution','evaluation/skills']
data=subprocess.check_output(['git','-C',str(SRC),'archive','c6f39e84fd0efa046a9651bb5542a4f3c6b4344b',*paths])
with tarfile.open(fileobj=io.BytesIO(data)) as a:
 for m in a.getmembers():assert (m.isfile() or m.isdir()) and (SNAP/m.name).resolve().is_relative_to(SNAP.resolve())
 a.extractall(SNAP,filter='data')
files=[{'path':p.relative_to(SNAP).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for prefix in paths for p in (SNAP/prefix).rglob('*') if p.is_file()]
save('source-supplement.json',{'reason':'First host test setup identified three omitted local evaluation packages; raw failure preserved. No candidate source change.','files':files});print(len(files))
