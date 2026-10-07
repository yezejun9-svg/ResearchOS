import contextlib,hashlib,io,json,pathlib,subprocess,types
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(__file__).resolve().parent;B=O.parent
commit='f327ee10844810d8ada7a7b83aae05412d757c4a';prefix='execution/v2.4/receipts/W02/W02-99/'
blob=lambda path:subprocess.check_output(['git','show',commit+':'+prefix+path],cwd=R)
helper=blob('evidence_reuse.py');assert hashlib.sha256(helper).hexdigest()=='3e9e060609e34b190807f06d14e5cf984ddcef855454caafa94c93a7eede78b5'
m=types.ModuleType('frozen_reuse');m.__file__=str(B/'evidence_reuse.py');exec(compile(helper,m.__file__,'exec'),m.__dict__)
original=B/'run-20261005T204515Z-b2910479b670/driver-sources/parent_driver.py'
current=blob('parent_driver.py').decode();changed=current.replace('def g02(g):','def g02(g, _review_import_effect=print("W02_REVIEW_IMPORT_EFFECT")):',1)
assert changed!=current
probe=O/'g02_default_expression_mutant.txt'
with probe.open('x',encoding='utf-8') as f:f.write(changed)
try:result=m.verify_driver_ast(original,probe);accepted=True;reason=None
except Exception as e:result=None;accepted=False;reason=type(e).__name__+':'+str(e)
# Prove the Python semantic using only a two-line standalone harmless fragment.
# Never import or execute the mutated parent driver.
output=io.StringIO()
with contextlib.redirect_stdout(output):exec('def example(arg=print("W02_REVIEW_IMPORT_EFFECT")):\n    pass\n',{})
report={'finding':'g02 default/decorator import-time expressions are unbounded by AST exemption','helper_commit':commit,'helper_sha256':hashlib.sha256(helper).hexdigest(),'mutant_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'mutated_parent_executed':False,'ast_validator_accepted_mutant':accepted,'standalone_python_definition_output':output.getvalue(),'validator_result':result,'exception':reason,'new_Go_GUI_provider_service_calls':0}
with (O/'ast_boundary_probe.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False))
