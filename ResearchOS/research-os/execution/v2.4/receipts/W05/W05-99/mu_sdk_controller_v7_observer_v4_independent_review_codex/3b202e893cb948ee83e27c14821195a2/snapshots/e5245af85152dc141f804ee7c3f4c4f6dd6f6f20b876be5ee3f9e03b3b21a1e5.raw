"""AST-only C7 delta contract; no candidate launch, OS call, or provider."""
from pathlib import Path
import ast
import hashlib
import json
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
C6=HERE.parents[1]/"mu_sdk_controller_revision_v6_codex/c309fe6cec1c400ea212065fbd484e73"
DELTA_KEYS=("canonical_transactions_source","job_watchdog_source",
            "source_guard_source","base_owned_process_source")

def controller_tree(path):
    return ast.parse(path.read_bytes(),filename=str(path))

def actual_context_assignment(tree):
    assignments=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="context"
                                                for t in node.targets):
            if isinstance(node.value,ast.Dict):
                keys=[k.value for k in node.value.keys if isinstance(k,ast.Constant)]
                if "independent_source_review" in keys and "outer_job_contract" in keys:
                    assignments.append(node)
    assert len(assignments)==1
    return assignments[0]

old_tree=controller_tree(C6/"controller.py")
new_tree=controller_tree(HERE/"controller.py")
old_text=(C6/"controller.py").read_text(encoding="utf-8")
new_text=(HERE/"controller.py").read_text(encoding="utf-8")
old_fragment='''                 "cleanup_producer_source":CLEANUP_PRODUCER_REF}'''
new_fragment='''                 "cleanup_producer_source":CLEANUP_PRODUCER_REF,
                 "canonical_transactions_source":CANONICAL_TRANSACTION_REF,
                 "job_watchdog_source":JOB_WATCHDOG_REF,
                 "source_guard_source":SOURCE_READ_GUARD_REF,
                 "base_owned_process_source":BASE_OWNED_PROCESS_REF}'''
assert old_text.count(old_fragment)==1 and new_text.count(new_fragment)==1
assert new_text.replace(new_fragment,old_fragment)==old_text
old_context=actual_context_assignment(old_tree)
new_context=actual_context_assignment(new_tree)
old_keys=[k.value for k in old_context.value.keys]
new_keys=[k.value for k in new_context.value.keys]
assert len(new_keys)==len(old_keys)+4
assert set(new_keys)-set(old_keys)==set(DELTA_KEYS)
assert len(new_keys)==len(set(new_keys))
assert all(key not in old_keys for key in DELTA_KEYS)

# Remove just the four new dict entries, then compare the entire Source AST.
new_context.value.keys=[k for k in new_context.value.keys if k.value not in DELTA_KEYS]
new_context.value.values=[v for k,v in zip(
    actual_context_assignment(controller_tree(HERE/"controller.py")).value.keys,
    new_context.value.values) if k.value not in DELTA_KEYS]
assert ast.dump(old_tree,include_attributes=False)==ast.dump(new_tree,include_attributes=False)

for name in ("canonical_transactions.py","owned_job_hooks.py","phase_worker.py",
             "job_deadline_watchdog.py","job_probe_worker.py",
             "held_job_cleanup_producer.py"):
    assert (HERE/name).read_bytes()==(C6/name).read_bytes(),name

# Execute only the inert C7 controller definitions and the exact context Dict
# expression extracted above. No launch function or callback is invoked.
scope={"__file__":str(HERE/"controller.py"),"__name__":"c7_delta_extract"}
exec(compile((HERE/"controller.py").read_bytes(),str(HERE/"controller.py"),"exec"),scope)
assert scope["HERE"]==HERE
for name in ("CANONICAL_TRANSACTION_REF","JOB_WATCHDOG_REF","CLEANUP_PRODUCER_REF"):
    ref=scope[name]
    assert Path(ref["path"]).parent==HERE and scope["pin"](ref["path"])==ref
doc={"outer_job_contract":{"path":"outer","sha256":"0"*64,"bytes":1}}
seed={"observer_source":scope["OBSERVER_SOURCE_REF"],
      "controller_source_review":{"path":"review","sha256":"1"*64,"bytes":1},
      "python_binary":scope["PINNED_PYTHON_REF"]}
values={"doc":doc,"controller_ref":scope["pin"](HERE/"controller.py"),
        "phase_dir":HERE,"public_env":{},
        "seed":seed,"HERE":HERE,
        "pin":scope["pin"],
        **{key:scope[key] for key in
           ("CLEANUP_PRODUCER_REF","CANONICAL_TRANSACTION_REF","JOB_WATCHDOG_REF",
            "SOURCE_READ_GUARD_REF","BASE_OWNED_PROCESS_REF")}}
context_expr=actual_context_assignment(controller_tree(HERE/"controller.py")).value
actual_context=eval(compile(ast.Expression(context_expr),str(HERE/"controller.py")+"::context","eval"),values)
assert actual_context["canonical_transactions_source"]==scope["CANONICAL_TRANSACTION_REF"]
assert actual_context["job_watchdog_source"]==scope["JOB_WATCHDOG_REF"]
assert actual_context["source_guard_source"]==scope["SOURCE_READ_GUARD_REF"]
assert actual_context["base_owned_process_source"]==scope["BASE_OWNED_PROCESS_REF"]

# O4 function is extracted as pure AST instead of importing the candidate.
o4=Path(scope["OBSERVER_SOURCE_REF"]["path"])
o4_tree=ast.parse(o4.read_bytes(),filename=str(o4))
names={"SOURCE_PROVENANCE_SCHEMA","SOURCE_AUTHOR_POLICY","RUNNER_REF"}
funcs={"require","source_author_provenance"}
nodes=[]
for node in o4_tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names
                                           for t in node.targets):nodes.append(node)
    if isinstance(node,ast.FunctionDef) and node.name in funcs:nodes.append(node)
assert len(nodes)==5
o4_scope={}
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
             str(o4)+"::pure-functions","exec"),o4_scope)
assert len(actual_context)>=11
provenance_context={**actual_context,"runner_source":o4_scope["RUNNER_REF"]}
actual=o4_scope["source_author_provenance"](provenance_context)
expected=scope["expected_source_provenance"](provenance_context)
assert actual==expected and len(actual["sources"])==11
print(json.dumps({"status":"PASS",
    "checks":["exact four fields in actual before_resume context AST",
              "exact four-field inverse restores C6 controller text and AST",
              "six helper Source bytes copied unchanged",
              "HERE-local hard pins relocate to C7 namespace",
              "actual context passes O4 eleven-role provenance helper"],
    "real_winapi_calls":0,"native_process_starts":0,
    "threads_started":0,"provider_calls":0,"canonical_writes":0},indent=2))
