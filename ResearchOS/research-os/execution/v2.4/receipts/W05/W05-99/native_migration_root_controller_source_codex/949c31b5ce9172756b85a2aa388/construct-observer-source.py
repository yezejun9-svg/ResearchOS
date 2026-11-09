"""Static construction of the minimal observed owned-process helper."""
import ast,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
B=P.parent.parent
base=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
raw=base.read_bytes()
assert hashlib.sha256(raw).hexdigest()=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
text=raw.decode("utf-8")
original=text
changes=[
("import ctypes\n","import ctypes\nimport copy\n"),
("def run_owned(argv, cwd, env, stdout, stderr, timeout, stdin=None, creation_flags=0):",
 "def run_owned_observed(argv, cwd, env, stdout, stderr, timeout, stdin=None, creation_flags=0, on_observation=None, cancel_requested=None):"),
("    def record_error(exc):\n",
 """    def emit_observation(event):
        if on_observation is not None:
            snapshot = copy.deepcopy(result)
            snapshot['stage'] = stage
            on_observation(event, snapshot)

    def check_cancel():
        if cancel_requested is not None and cancel_requested():
            raise RuntimeError('Root requested owned case cancellation')

    def record_error(exc):
"""),
("        import msvcrt\n\n        stage = 'RESOLVE_WINDOWS_API'",
 """        if on_observation is not None and not callable(on_observation):
            raise ValueError('on_observation must be callable')
        if cancel_requested is not None and not callable(cancel_requested):
            raise ValueError('cancel_requested must be callable')
        check_cancel()
        import msvcrt

        stage = 'RESOLVE_WINDOWS_API'"""),
("        stage = 'CREATE_SUSPENDED'\n",
 "        check_cancel()\n        stage = 'CREATE_SUSPENDED'\n"),
("        cleanup['assigned_before_resume'] = True\n",
 "        cleanup['assigned_before_resume'] = True\n        emit_observation('assigned-before-resume')\n        check_cancel()\n"),
("            result['resumed'] = True\n",
 "            result['resumed'] = True\n            emit_observation('resumed')\n"),
("            while not observe():\n",
 "            while not observe():\n                check_cancel()\n                emit_observation('live')\n"),
]
# Preserve the original raw newline convention; only matched spans change.
for before,after in changes:
    assert text.count(before)==1,(before,text.count(before))
    text=text.replace(before,after,1)
inverse=text
for before,after in reversed(changes):
    assert inverse.count(after)==1
    inverse=inverse.replace(after,before,1)
assert inverse==original
path=P/"windows_owned_observed.py"
with path.open("xb") as f:f.write(text.encode("utf-8"))
ast.parse(text,filename=str(path))
controller=P/"root_native_migration_controller.py"
ast.parse(controller.read_text(encoding="utf-8"),filename=str(controller))
patch="".join(difflib.unified_diff(original.splitlines(keepends=True),text.splitlines(keepends=True),
                                 fromfile=str(base),tofile=str(path)))
with (P/"owned-observer.patch").open("x",encoding="utf-8",newline="\n") as f:f.write(patch)
def ref(x):
 b=x.read_bytes();return {"path":str(x),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
with (P/"observer-static.json").open("x",encoding="utf-8",newline="\n") as f:
 json.dump({"original_ref":ref(base),"new_ref":ref(path),"inverse_raw_bytes_equal":inverse.encode("utf-8")==raw,
            "observer_receives_no_handles":True,"native_execution":False,"go_execution":False,
            "controller_and_observer_ast_parse":True},f,ensure_ascii=True,indent=2)
print(json.dumps({"controller_ref":ref(controller),"observer_ref":ref(path),
                  "source_only":True,"inverse_bytes_equal":True},ensure_ascii=True))

