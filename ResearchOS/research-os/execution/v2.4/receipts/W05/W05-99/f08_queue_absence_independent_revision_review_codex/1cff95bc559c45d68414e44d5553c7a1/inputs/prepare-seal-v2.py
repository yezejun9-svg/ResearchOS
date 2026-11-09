from pathlib import Path
import ast,json,hashlib
p=Path(__file__).resolve().parent
def put(name,body):
    with (p/name).open('xb') as f:f.write(body)
    return {'path':(p/name).as_posix(),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
for chunk,cause in [
    ('3d077c','seal.py line20 expected six declarations; scanner required literal func-space and missed actual func(v *f08ProofValidator) evaluate at line1515. No handoff/manifest written before assertion.'),
    ('86f70b','One-line read-only Python metadata inspection had unmatched closing parenthesis; Python parser refused before file read. No product or candidate execution.')]:
    data={'tool_chunk':chunk,'actual_outer_exit':1,'actual_native_python_exit':1,'exit_bridge':'PowerShell command explicitly ended exit $LASTEXITCODE','cause':cause,'product_calls':0,'canonical_writes':0,'source_writes':0,'same_input_retried':False,'counter_reset':False,'raw_tool_result':'Visible conversation tool result; no separately captured native streams'}
    put('failure-origin.'+chunk+'.json',(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
old=(p/'seal.py').read_text(encoding='utf-8')
needle="if line.startswith('func ') and (' '+name+'(' in line):"
replacement="if line.startswith('func') and re.search(r'\\b'+re.escape(name)+r'\\s*\\(',line):"
assert old.count(needle)==1
new=old.replace(needle,replacement,1)
needle="origins=[ref(HERE/'failure-origin.5b7ca2.json'),ref(HERE/'failure-origin.a1e3bf.json')]"
replacement="origins=[ref(HERE/('failure-origin.'+chunk+'.json')) for chunk in ['5b7ca2','a1e3bf','3d077c','86f70b']]"
assert new.count(needle)==1
new=new.replace(needle,replacement,1)
new=new.replace("[HERE/'assemble.py',HERE/'seal.py']","[HERE/'assemble.py',HERE/'seal.py',HERE/'seal.v2.py',HERE/'prepare-seal-v2.py']",1)
needle="'new_failure_origin_refs':origins,'prior_failure_and_erratum_refs':inherit,'counter_mutations':0,"
replacement="'new_failure_origin_refs':origins,'prior_failure_and_erratum_refs':inherit,'counter_mutations':0,'supplemental_failures':['3d077c Python1/outer1','86f70b Python1/outer1'],'locator_cause_verified_by':'062f8f outer0/nativeNULL actual declaration func(v ... evaluate',"
assert new.count(needle)==1
new=new.replace(needle,replacement,1)
ast.parse(new)
out=put('seal.v2.py',new.encode('utf-8'))
put('sealer-v2-diff.json',(json.dumps({'base':{'path':(p/'seal.py').as_posix(),'sha256':hashlib.sha256((p/'seal.py').read_bytes()).hexdigest()},'new':out,'changes':['Accept actual Go func(v receiver) lexical spelling for line locator only','Preserve two additional original metadata errors','AST-check metadata scripts only'],'Go_source_changed':False,'candidate_target_execution':False},indent=2)+'\n').encode('utf-8'))
print(json.dumps(out))
