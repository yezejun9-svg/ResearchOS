"""Complete only the three checks not reached by original1218, then publish metadata."""
from pathlib import Path
import ast, copy, datetime, difflib, hashlib, json, types, uuid
R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;BASE=W/'w09_formal_root_bridge_source_codex/bridge-20261010-06'
PR=W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-06-attach'
ADOPT=W/'main_w09_formal_router_sequence_root/fix-20261010-01'
MR=W/'main_w09_formal_router_sequence_independent_review_codex/review-20261010-01-full'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
origin=s.capture('4dae03',1,1,1218)
s.write('original1218.origin.json',dict(original_ordinal=1218,original_io=origin,
    original_script_ref=s.pin(D/'build_bridge7.source.py'),original_prefix_ref=s.pin(D/'delta-controls.json'),
    original_guard_ref=s.pin(D/'source-guard.closed.json'),outer_exit=1,Python_exit=1,
    Native_exit=None,Go_exit=None,SQL_exit=None,dispatcher_exit=None,TP_exit=None,RootStage_exit=None,model_exit=None,
    reason='Reviewer AST literal extraction omitted known GUARD/TP/OWNED symbol literals; no product call.',
    product_failure=False,successful_prefix_replayed=False))
prefix=json.loads((D/'delta-controls.json').read_bytes())
base=json.loads((BASE/'HDF.json').read_bytes());mf=json.loads((BASE/'MF.json').read_bytes())
review=json.loads((PR/'HDF.json').read_bytes());adoption=json.loads((ADOPT/'Main-adoption.closed.root.json').read_bytes())
refs=[s.pin(__file__),s.pin(HELPER),s.pin(D/'build_bridge7.source.py'),s.pin(D/'delta-controls.json'),prefix['source_guard_ref'],
    s.pin(BASE/'HDF.json'),s.pin(BASE/'MF.json'),base['source_ref'],base['consumer_launcher_ref'],base['root_calling_contract_ref'],
    s.pin(PR/'HDF.json'),review['decision_ref'],s.pin(ADOPT/'Main-adoption.closed.root.json')]
g=s.guard();checks=[];failure=None;created=None
def check(name,value,detail=None):
    checks.append(dict(name=name,passed=bool(value),detail=detail))
    if not value:raise ValueError(name)
try:
    g.acquire(refs)
    closed=json.loads(g.get_buffer(prefix['source_guard_ref']['path']))
    assert prefix['count']==prefix['passed']==2 and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
    before=g.get_buffer(base['source_ref']['path']);launcher=g.get_buffer(base['consumer_launcher_ref']['path'])
    base_contract=json.loads(g.get_buffer(base['root_calling_contract_ref']['path']))
    after=before.replace(b'BRIDGE_GENERATION = "bridge-20261010-06"',b'BRIDGE_GENERATION = "bridge-20261010-07"').replace(
        b'"execution/v2.4/formal_profile_w09.py": ("d44500a9fceb9633109884f3860390e5d10bc877b4f3a66986ffd6e2038dc35f", 71397)',
        b'"execution/v2.4/formal_profile_w09.py": ("1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087", 71403)')
    old_tree=ast.parse(before);new_tree=ast.parse(after)
    def literals(tree):
        nodes={node.targets[0].id:node.value for node in tree.body if isinstance(node,ast.Assign)
            and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)}
        symbols={key:ast.literal_eval(nodes[key]) for key in ('GUARD','TP','OWNED')}
        result={key:ast.literal_eval(nodes[key]) for key in ('BRIDGE_GENERATION','AUTHOR','AUTHOR_BACKEND','VERIFIER','ROUTES')}
        result['TRUSTED']={ast.literal_eval(key) if not isinstance(key,ast.Name) else symbols[key.id]:ast.literal_eval(value)
            for key,value in zip(nodes['TRUSTED'].keys,nodes['TRUSTED'].values)}
        return result
    old_c=literals(old_tree);new_c=literals(new_tree)
    fixed=dict(new_c['TRUSTED']);fixed['execution/v2.4/formal_profile_w09.py']=old_c['TRUSTED']['execution/v2.4/formal_profile_w09.py']
    def functions(tree):return {node.name:ast.dump(node,include_attributes=False) for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    check('all_function_class_AST_roles_routes_and_other_TRUSTED_entries_unchanged',functions(old_tree)==functions(new_tree)
        and fixed==old_c['TRUSTED'] and all(old_c[key]==new_c[key] for key in ('AUTHOR','AUTHOR_BACKEND','VERIFIER','ROUTES')))
    check('sealed_consumer_launcher_byte_identical_and_no_generation_pin',
        hashlib.sha256(launcher).hexdigest()=='c64deb904e746fd2d5df6775e0b96375ce36741315109d47ab86408360de5011'
        and len(launcher)==1493 and b'bridge-20261010-06' not in launcher)
    check('protected_BR6_package_and_accepted_review_reused_without_controls_replay',
        review['decision']=='ACCEPTED_SOURCE_ONLY' and review['source_hdf_ref']==s.pin(BASE/'HDF.json')
        and review['source_mf_ref']==s.pin(BASE/'MF.json') and review['source_ref']==base['source_ref']
        and review['guards_closed_zero'] is True and review['retained_handles_count']==0,
        dict(protected_original_package_members=len(mf['members']),original_guard_verified_members_replayed=False,
            all_old_successful_Source_Main_Native_Mode_controls_replayed=False))
    with (D/'w09_root_bridge.source.py').open('xb') as f:f.write(after)
    with (D/'consumer_launch.source.py').open('xb') as f:f.write(launcher)
    patch=''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),
        fromfile=str(BASE/'w09_root_bridge.source.py'),tofile=str(D/'w09_root_bridge.source.py')))
    with (D/'bridge07.patch').open('xb') as f:f.write(patch.encode())
    created=dict(source_ref=s.pin(D/'w09_root_bridge.source.py'),consumer_launcher_ref=s.pin(D/'consumer_launch.source.py'))
    s.write('exact-inverse.json',dict(base_source_ref=base['source_ref'],new_source_ref=created['source_ref'],
        complete_byte_inverse_verified_in_retained_prefix=True,retained_prefix_ref=s.pin(D/'delta-controls.json'),
        changed_bindings=['BRIDGE_GENERATION','TRUSTED.formal_profile_w09.py'],changed_business_functions=[],
        all_functions_classes_AST_unchanged=True,other_TRUSTED_entries_unchanged=True,consumer_launcher_unchanged=True,
        Source_only=True,original1218_preserved=True))
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc));raise
finally:
    guard_ref=s.write('tail-source-guard.closed.json',g.close())
    controls_ref=s.write('tail-delta-controls.json',dict(checks=checks,count=len(checks),passed=sum(x['passed'] for x in checks),
        failure=failure,source_guard_ref=guard_ref,held_count=len(refs),created=created,
        retained_prefix_ref=s.pin(D/'delta-controls.json'),retained_prefix_checks=prefix['passed'],
        original1218_io=origin,Source_only=True,self_acceptance=False,execution_grant=False,formal_acceptance=False,
        product_calls=dict(Native=0,Go=0,SQL=0,dispatcher=0,TP=0,RootStage=0,model=0)))

# Reuse only the unexecuted publication suffix of the original frozen preparation script.
# The failed prefix and its successful two checks are not executed again.
script=ast.parse((D/'build_bridge7.source.py').read_bytes())
start=next(index for index,node in enumerate(script.body) if isinstance(node,ast.Assign)
    and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='created_utc')
suffix=ast.Module(body=script.body[start:],type_ignores=[])
for node in ast.walk(suffix):
    if isinstance(node,ast.keyword) and node.arg=='new_original_failures':
        node.value=ast.List(elts=[ast.Constant(value=1218)],ctx=ast.Load())
ast.fix_missing_locations(suffix)
exec(compile(suffix,'<retained-BR7-publication-only>','exec'),globals())
