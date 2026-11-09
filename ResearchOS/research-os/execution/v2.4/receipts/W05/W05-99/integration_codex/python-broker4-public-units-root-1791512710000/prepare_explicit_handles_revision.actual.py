import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;Q=P/"revision-explicit-binary-handles";Q.mkdir()
old=P/"validate_python_broker4_public_units.actual_owned.py";raw=old.read_bytes()
a=b'result=helper.run_owned(argv,str(R),env,str(O/"units.stdout.raw"),str(O/"units.stderr.raw"),60,creation_flags=0x08000000)'
b=b'''with (O/"units.stdout.raw").open("xb") as out, (O/"units.stderr.raw").open("xb") as err:
  result=helper.run_owned(argv,str(R),env,out,err,60,creation_flags=0x08000000)'''
assert raw.count(a)==1;raw=raw.replace(a,b)
raw=raw.replace(b"python-broker4-public-units-env-1791512710000",b"python-broker4-public-units-env-1791512710000-revision1")
compile(raw,str(Q/"validate_python_broker4_public_units_revision.actual_owned.py"),"exec")
with (Q/"validate_python_broker4_public_units_revision.actual_owned.py").open("xb") as f:f.write(raw)
def pin(p):
 r=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
receipt=json.loads((P/"units.invocation.json").read_bytes())
assert receipt["owned_process"]["actual_exit"] is None and receipt["owned_process"]["owned_child_pid"] is None
assert receipt["owned_process"]["stage"]=="PREPARE_EXPLICIT_STD_HANDLES" and receipt["owned_process"]["job_cleanup"]["handles_closed"]
with (P/"failure879.exit-qualification.json").open("xb") as f:f.write((json.dumps(dict(ordinal=879,immutable_origin_ref=pin(P/"failure-origin.879.json"),invocation_ref=pin(P/"units.invocation.json"),actual_outer_exit=1,actual_python_driver_exit=1,actual_unit_child_exit=None,actual_native_exit=None,unit_tests_executed=0,guard_finally_closed=True,error="Root supplied str paths where helper requires binary streams; no child created.",automatic_retry=False),indent=2)+"\n").encode())
print("ROOT_PYTHON_EXIT=0")


