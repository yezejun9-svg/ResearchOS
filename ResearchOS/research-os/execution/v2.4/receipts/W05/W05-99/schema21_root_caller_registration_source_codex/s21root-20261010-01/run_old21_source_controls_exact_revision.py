from pathlib import Path
Q=Path(__file__).resolve().parent
source=(Q/'run_old21_source_controls.py').read_text(encoding='utf-8')
source=source.replace("(Q/'exact-inverse.json')", "(Q/'numbered-SQL-exact-revision.inverse.json')")
source=source.replace('guard=guard_module.Guard()',"guard=guard_module.Guard();globals()['_active_guard']=guard")
source=source.replace("    closure=save('finite-delta-controls.guard.closed.json',guard.close())\n",'')
source=source.replace("    report=save('finite-delta-controls.json'", "    closure=save('finite-delta-controls.guard.closed.json',guard.close())\n    report=save('finite-delta-controls.json'")
namespace=dict(__name__='__main__',__file__=__file__)
try:exec(compile(source,str(Path(__file__)),'exec'),namespace)
finally:
    guard=namespace.get('_active_guard')
    if guard is not None and any(not stream.closed for stream,_,_ in guard.held):
        namespace['save']('finite-delta-controls.exact-attempt-failure.guard.closed.json',guard.close())
