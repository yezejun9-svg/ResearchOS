import pathlib,json,subprocess,sys,datetime,hashlib
out=pathlib.Path(__file__).resolve().parent
argv=[sys.executable,"-I",str(out/"run_cases.py")]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/"driver.stdout.raw").open("xb") as stdout,(out/"driver.stderr.raw").open("xb") as stderr:
 p=subprocess.run(argv,cwd="D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-session-list-identity-r306",stdout=stdout,stderr=stderr)
r={"argv":argv,"cwd":"D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-session-list-identity-r306","started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"actual_exit":p.returncode,"stdout_sha256":hashlib.sha256((out/"driver.stdout.raw").read_bytes()).hexdigest(),"stderr_sha256":hashlib.sha256((out/"driver.stderr.raw").read_bytes()).hexdigest(),"retry":False}
(out/"driver.invocation.json").write_text(json.dumps(r,indent=2),encoding="utf-8")
print(json.dumps(r));print((out/"driver.stdout.raw").read_text(encoding="utf-8"));print((out/"driver.stderr.raw").read_text(encoding="utf-8"));sys.exit(p.returncode)
