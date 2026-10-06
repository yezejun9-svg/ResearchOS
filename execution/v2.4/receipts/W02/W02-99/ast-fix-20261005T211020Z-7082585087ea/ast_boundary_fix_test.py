"""Parse-only tests for the independently reported g02 AST exemption defect."""
import ast
import datetime as dt
from pathlib import Path
import sys
import uuid

import evidence_reuse as subject

HERE=Path(__file__).resolve().parent


def main():
    original=HERE/'run-20261005T204515Z-b2910479b670/driver-sources/parent_driver.py'
    current=HERE/'parent_driver.py';source=current.read_text(encoding='utf-8')
    out=HERE/('ast-fix-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:12]);out.mkdir()
    cases=[
      ('g02_default_expression',source.replace('def g02(g):','def g02(g, _boundary=print("AST_BOUNDARY_MUST_NOT_EXECUTE")):',1),'G02_DEFINITION_CHANGED'),
      ('g02_decorator_expression',source.replace('def g02(g):','@print("AST_BOUNDARY_MUST_NOT_EXECUTE")\ndef g02(g):',1),'G02_DEFINITION_CHANGED'),
      ('duplicate_definition',source+'\ndef g02(g):\n    pass\n','DRIVER_MODULE_STRUCTURE_CHANGED'),
      ('async_definition',source.replace('def g02(g):','async def g02(g):',1),'DRIVER_MODULE_STRUCTURE_CHANGED'),
    ]
    module=ast.parse(source)
    indices=[i for i,node in enumerate(module.body) if isinstance(node,ast.FunctionDef) and node.name in ('read','sha')]
    subject.require(len(indices)==2,'TEST_TOP_LEVEL_TARGETS')
    module.body[indices[0]],module.body[indices[1]]=module.body[indices[1]],module.body[indices[0]]
    cases.append(('top_level_order',ast.unparse(module)+'\n','DRIVER_MODULE_STRUCTURE_CHANGED'))
    rows=[]
    # This control is the actual existing g02 body delta, not an invented body.
    control=subject.verify_driver_ast(original,current)
    accepted=any(item['function']=='g02' for item in control)
    rows.append({'case':'existing_g02_body_allowed','expected':'ACCEPT','actual':'ACCEPT' if accepted else 'FAIL',
                 'ok':accepted,'source_sha256':subject.sha(current),'allowed_differences':control})
    for name,text,expected in cases:
        path=out/(name+'.mutant.txt');path.write_text(text,encoding='utf-8',newline='\n')
        try:
            subject.verify_driver_ast(original,path)
            reason='ACCEPTED_MUTANT'
        except subject.Refused as exc:reason=str(exc)
        rows.append({'case':name,'expected':expected,'actual':reason,'ok':reason==expected,
                     'mutant':path.name,'mutant_sha256':subject.sha(path),'mutant_executed':False})
    report={'schema':'researchos.w02-ast-boundary-fix-tests.v1','status':'PASS' if all(r['ok'] for r in rows) else 'FAIL',
            'checks':rows,'check_count':len(rows),'negative_count':len(cases),'new_product_tests_executed':0,
            'new_dispatcher_fixture_children':0,'old_14_negative_cases_rerun':False,'mutants_imported_or_executed':False,
            'helper_sha256':subject.sha(HERE/'evidence_reuse.py'),'original_parent_driver_sha256':subject.sha(original),
            'current_parent_driver_sha256':subject.sha(current),'test_source_sha256':subject.sha(Path(__file__)),
            'argv':[sys.executable,*sys.orig_argv[1:]],'cwd':str(Path.cwd())}
    subject.save(out/'receipt.json',report)
    (out/'evidence_reuse.py').write_bytes((HERE/'evidence_reuse.py').read_bytes())
    (out/'ast_boundary_fix_test.py').write_bytes(Path(__file__).read_bytes())
    subject.save(out/'manifest.json',{p.name:subject.sha(p) for p in out.iterdir() if p.is_file()})
    print(__import__('json').dumps({'status':report['status'],'checks':len(rows),'receipt':str(out/'receipt.json')}))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':sys.exit(main())
