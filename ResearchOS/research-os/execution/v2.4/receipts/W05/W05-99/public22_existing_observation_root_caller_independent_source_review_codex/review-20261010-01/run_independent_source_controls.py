import sys
sys.dont_write_bytecode=True
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import ntpath
from pathlib import Path
import traceback
Q=Path(__file__).resolve().parent
SOURCE=Q.parents[1]/'public22_existing_observation_root_caller_source_codex/recheckroot-20261009-01'
def pin(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8');path=Q/name
    with path.open('xb') as stream:assert stream.write(raw)==len(raw)
    return pin(path)
def reviewer_save(_source_root,name,value):
    assert name in ('source-controls.json','identity-and-scope-controls.json','real-Source-peer.mapping-control.binding.json')
    return save('replayed-'+name,value)
class RedirectOnlyOutput(ast.NodeTransformer):
    def __init__(self):self.names=[]
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='m' and node.func.attr=='save' and len(node.args)>=2 and isinstance(node.args[0],ast.Name) and node.args[0].id=='N' and isinstance(node.args[1],ast.Constant):
            name=node.args[1].value
            if name in ('source-controls.json','identity-and-scope-controls.json','real-Source-peer.mapping-control.binding.json'):
                self.names.append(name);node.func=ast.Name(id='_reviewer_save',ctx=ast.Load())
        return node
def main():
    basis=json.loads((Q/'verified-source-basis.index.json').read_text(encoding='utf-8'))
    mf={Path(x['path']).name:x for x in basis['members']}
    inputs=json.loads(Path(mf['source-inputs.json']['path']).read_text(encoding='utf-8'))
    resources=json.loads(Path(mf['runtime-resources.complete.json']['path']).read_text(encoding='utf-8'))
    runtime=json.loads(Path(mf['runtime-closure-control.json']['path']).read_text(encoding='utf-8'))
    assert len(resources['resource_refs'])==149 and len(runtime['verified_resource_refs'])==153
    spec=importlib.util.spec_from_file_location('task54_review_guard',Q/'read_source_basis.py');lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
    guard=lib.Guard();closed=False;refs={}
    for ref in [basis['source_hdf_ref'],basis['source_mf_ref'],*basis['members'],*inputs['source_resource_refs'],*resources['resource_refs'],*runtime['verified_resource_refs']]:
        key=ntpath.normcase(ntpath.normpath(ref['path']))
        assert key not in refs or (refs[key]['sha256'],refs[key]['bytes'])==(ref['sha256'],ref['bytes'])
        refs.setdefault(key,ref)
    try:
        for ref in refs.values():guard.read(ref['path'],ref)
        routed=[]
        for name in ('source-controls.py','identity-and-scope-controls.py'):
            path=Path(mf[name]['path']);raw=path.read_bytes();assert pin(path)==mf[name]
            tree=ast.parse(raw);redirect=RedirectOnlyOutput();tree=redirect.visit(tree);ast.fix_missing_locations(tree)
            expected=['source-controls.json'] if name=='source-controls.py' else ['real-Source-peer.mapping-control.binding.json','identity-and-scope-controls.json']
            assert redirect.names==expected
            globs={'__file__':str(path),'__name__':'task54_source_replay_only','_reviewer_save':reviewer_save}
            sink=io.StringIO()
            with contextlib.redirect_stdout(sink):
                exec(compile(tree,str(path),'exec'),globs);globs['main']()
            routed.append({'source_ref':mf[name],'redirected_save_calls_only':redirect.names,
                'stdout':sink.getvalue(),'production_Source_AST_not_modified':True})
        old=json.loads((Q/'replayed-source-controls.json').read_text(encoding='utf-8'))
        peer=json.loads((Q/'replayed-identity-and-scope-controls.json').read_text(encoding='utf-8'))
        assert len(old['controls'])==53 and all(x['status']=='PASS' for x in old['controls'])
        assert len(peer['controls'])==11 and all(x['status']=='PASS' for x in peer['controls'])
        assert old['SQL_queries']==peer['SQL_queries']==0
        assert all(ntpath.normcase(ntpath.normpath(x['path'])) in refs for x in resources['resource_refs'])
        assert {Path(x['path']).name for x in resources['explicit_added_resource_refs']}=={'source_read_guard.py','canonical_transactions.py'}
        closure=guard.close();closed=True;cref=save('independent-controls.guard.closed.json',closure)
        result=save('independent-controls.json',{'schema':'researchos.public22-existing-root-independent-source-controls.v1',
            'actor_id':'codex:/root/backup_regression_resources','source_author':basis['source_author'],
            'status':'PASS_SOURCE_ONLY','source_controls53_passed':53,'identity_scope11_passed':11,
            'runtime149_and_published153_complete_pin_hold_passed':True,'total_Source_checks':65,
            'guarded_unique_ref_count':len(refs),'guard_ref':cref,'output_redirects':routed,
            'held149_resource_refs':resources['resource_refs'],'original1043_failed_input_not_retried':True,
            'Source_resource149_complete':'SourceGuard and TP explicit additions retained; every149 and published153 actual pin held and closure checked',
            'root_runtime_qualification_executed':False,
            'original1025_result':'FAILED_RETAINED','original1043_result':'FAILED_RETAINED',
            'SQL_queries':0,'new_native_children':0,'Go_dispatcher_model_calls':None,
            'Source_Main_Canon_old_case_writes':0,'actual_registration':False,'execution_grant':False,'formal_acceptance':False})
        print(json.dumps({'result_ref':result,'guard_ref':cref,'Source_checks':65,'unique_pins':len(refs),
            'runtime_manifest_pins':149,'published_runtime_closure_pins':153,'retained_handles':0,
            'SQL_queries':0,'new_native_children':0},ensure_ascii=False))
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
