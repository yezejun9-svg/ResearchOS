import os,sys,json,subprocess,time,importlib.util,hashlib
from pathlib import Path
E=Path(__file__).resolve().parent
group=sys.argv[1]
module=E/(group+".py")
spec=importlib.util.spec_from_file_location("collection_group",module);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
args=[sys.executable,"-B","-Xutf8",str(module)]
recipe=dict(id=group,group=group.upper(),fullargv=args,cwd=str(m.W),relevantenv={k:os.environ.get(k) for k in ["TMP","TEMP","PYTHONUTF8","PATH"]},
 exact_sql=getattr(m,"SQL",[]),uri_flags="mode=ro&cache=private; PRAGMA query_only=ON; no immutable" if getattr(m,"SQL",[]) else None,
 original_database=str(m.DB) if getattr(m,"SQL",[]) else None,intent=m.INTENT,script_sha256=hashlib.sha256(module.read_bytes()).hexdigest(),
 rawstdout=group+".stdout.raw",rawstderr=group+".stderr.raw",nativeexit=group+".exit.json",prewritten_at=time.time())
rp=E/(group+".recipe.json");assert not rp.exists();rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2),encoding="utf8")
with (E/(group+".stdout.raw")).open("wb") as o,(E/(group+".stderr.raw")).open("wb") as er:
 p=subprocess.run(args,cwd=m.W,stdout=o,stderr=er)
(E/(group+".exit.json")).write_text(json.dumps(dict(native_exit=p.returncode,finished_at=time.time())),encoding="utf8")
print((E/(group+".stdout.raw")).read_text(encoding="utf8",errors="replace"))
print((E/(group+".stderr.raw")).read_text(encoding="utf8",errors="replace"),file=sys.stderr)
sys.exit(p.returncode)

