import sys,json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
p=O/"prepare_checkpoint_execution_facts.actual.py";raw=p.read_bytes()
replacements=[
(b"86852319669c0b34a31fff88c3c3ed5c7517d11b4b91d042cafa82fb2e0b05",b"86852319669c0b34a31fff88c3c3c3ed5c7517d11b4b91d042cafa82fb2e0b05"),
(b"pending.sort(key=lambda v:v[\"ordinal\"])",b'''for n,a,p,g,description in [(874,1,1,None,"Root CP362 facts preparation hardpin transcription failed before guards or canonical mutation."),(875,1,None,None,"Root PowerShell diagnostic pipeline syntax rejected before body/process execution.")]:
 ref=pin(O/f"failure-origin.{n}.json")
 pending.append(dict(ordinal=n,origin_ref=ref,actual_outer_exit=a,actual_python_exit=p,actual_native_exit=g,description=description))
pending.sort(key=lambda v:v["ordinal"])'''),
(b"list(range(848,874))",b"list(range(848,876))"),
(b"registered_after=871,highest=873,next=874",b"registered_after=873,highest=875,next=876"),
(b"Appends26 distinct original848..873",b"Appends28 distinct original848..875"),
(b'("native_temp_actual_failure_independent_review_codex/c13a1cf32d414d74b350883ebd8e4d09"',b'("native_python_broker_temp_env_independent_review_codex/9e4f389d093d4ea58eb5ec06e102876d","7c0ad0872da573a5a6948b2c6e7d55a438e57e3cc2ba65b70329e9cea6dd2518",4535,"8edd94cc087bf2f042fcec9a892f04687eb0898dc67c683e2fe710f85cbf58bb",5044),\n("native_temp_actual_failure_independent_review_codex/c13a1cf32d414d74b350883ebd8e4d09"'),
(b"broker4_source=\"SEALED_PENDING_INDEPENDENT_REVIEW\"",b"broker4_source=\"SOURCE_ACCEPTED_PENDING_ROOT_BOUNDARY_ACTUAL\"")
]
for old,new in replacements:
 assert raw.count(old)==1,(old,raw.count(old));raw=raw.replace(old,new)
compile(raw,str(O/"prepare_checkpoint_execution_facts_revision.actual.py"),"exec")
with (O/"prepare_checkpoint_execution_facts_revision.actual.py").open("xb") as f:f.write(raw)
print("ROOT_PYTHON_EXIT=0")


