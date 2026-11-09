"""Prepare BR7 by rebasing two fixed constants; no Root/product entry is called."""
from pathlib import Path
import ast, copy, datetime, difflib, hashlib, json, types, uuid
R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
BASE=W/'w09_formal_root_bridge_source_codex/bridge-20261010-06'
PR=W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-06-attach'
ADOPT=W/'main_w09_formal_router_sequence_root/fix-20261010-01'
MR=W/'main_w09_formal_router_sequence_independent_review_codex/review-20261010-01-full'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
base=json.loads((BASE/'HDF.json').read_bytes());mf=json.loads((BASE/'MF.json').read_bytes())
review=json.loads((PR/'HDF.json').read_bytes())
adoption=json.loads((ADOPT/'Main-adoption.closed.root.json').read_bytes())
refs=[s.pin(__file__),s.pin(HELPER),s.pin(BASE/'HDF.json'),s.pin(BASE/'MF.json'),*mf['members'],
    s.pin(PR/'HDF.json'),review['manifest_ref'],review['decision_ref'],
    s.pin(ADOPT/'Main-adoption.closed.root.json'),s.pin(ADOPT/'Main-adoption.source-guard.closed.root.json'),
    adoption['target_after_ref'],s.pin(MR/'HDF.json'),s.pin(MR/'MF.json'),adoption['independent_review_ref'],
    adoption['independent_delivery_audit_ref']]
unique={}
for ref in refs:
    key=str(Path(ref['path']).resolve(strict=True))
    assert key not in unique or unique[key]==ref
    unique[key]=ref
refs=list(unique.values())
g=s.guard();checks=[];failure=None;created=None
def check(name,value,detail=None):
    checks.append(dict(name=name,passed=bool(value),detail=detail))
    if not value:raise ValueError(name)
try:
    g.acquire(refs)
    base_contract=json.loads(g.get_buffer(str(BASE/'root-calling-contract.source.json')))
    before=g.get_buffer(base['source_ref']['path']);launcher=g.get_buffer(base['consumer_launcher_ref']['path'])
    actual_main=g.get_buffer(adoption['target_after_ref']['path'])
    main_guard=json.loads(g.get_buffer(str(ADOPT/'Main-adoption.source-guard.closed.root.json')))
    main_review=json.loads(g.get_buffer(adoption['independent_review_ref']['path']))
    check('exact_given_BR6_Main_and_actual_adoption_chain',
        s.pin(BASE/'HDF.json')['sha256']=='0fda15ff927c164aca24e27a1ef92691f5a81e20838ac263a25fbcb0c9be265d'
        and s.pin(BASE/'MF.json')['sha256']=='26c766cfe71628f12f95efcbe13b9bd28a3c14c8adcab7fc28d911d2ae373962'
        and hashlib.sha256(before).hexdigest()=='59943073eb7c2e745d68acbe8b46e0031617de6d87fbe675584cb172de6ccd55'
        and len(before)==54832 and hashlib.sha256(actual_main).hexdigest()=='1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087'
        and len(actual_main)==71403 and s.pin(ADOPT/'Main-adoption.closed.root.json')['sha256']=='6d2389c04f99f6a4f691d6a059a38f277cd26b2db7c04efa8e6a9f25f03b5e31'
        and adoption['Main_integrated'] is True and main_review['decision']=='ACCEPTED_SOURCE_ONLY'
        and main_guard['closed'] is True and main_guard['retained_handles_count']==0 and main_guard['errors']==[])
    changes=[
        (b'BRIDGE_GENERATION = "bridge-20261010-06"',b'BRIDGE_GENERATION = "bridge-20261010-07"'),
        (b'"execution/v2.4/formal_profile_w09.py": ("d44500a9fceb9633109884f3860390e5d10bc877b4f3a66986ffd6e2038dc35f", 71397)',
         b'"execution/v2.4/formal_profile_w09.py": ("1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087", 71403)')]
    after=before
    for old,new in changes:
        assert after.count(old)==1
        after=after.replace(old,new)
    restored=after
    for old,new in reversed(changes):
        assert restored.count(new)==1
        restored=restored.replace(new,old)
    check('exact_two_constant_delta_complete_byte_inverse',restored==before,
        dict(changed_bindings=['BRIDGE_GENERATION','TRUSTED.formal_profile_w09'],source_bytes_unchanged=len(after)==len(before)))
    old_tree=ast.parse(before);new_tree=ast.parse(after)
    def literal_constants(tree):
        return {node.targets[0].id:ast.literal_eval(node.value) for node in tree.body
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
            and node.targets[0].id in ('TRUSTED','BRIDGE_GENERATION','AUTHOR','AUTHOR_BACKEND','VERIFIER','ROUTES')}
    old_c=literal_constants(old_tree);new_c=literal_constants(new_tree)
    fixed=dict(new_c['TRUSTED']);fixed['execution/v2.4/formal_profile_w09.py']=old_c['TRUSTED']['execution/v2.4/formal_profile_w09.py']
    def functions(tree):return {node.name:ast.dump(node,include_attributes=False) for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    check('all_function_class_AST_roles_routes_and_other_TRUSTED_entries_unchanged',
        functions(old_tree)==functions(new_tree) and fixed==old_c['TRUSTED']
        and all(old_c[key]==new_c[key] for key in ('AUTHOR','AUTHOR_BACKEND','VERIFIER','ROUTES'))
        and ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(old_tree,include_attributes=False))
    check('sealed_consumer_launcher_byte_identical_and_no_generation_pin',
        hashlib.sha256(launcher).hexdigest()=='c64deb904e746fd2d5df6775e0b96375ce36741315109d47ab86408360de5011'
        and len(launcher)==1493 and b'bridge-20261010-06' not in launcher)
    check('protected_BR6_package_and_accepted_review_reused_without_controls_replay',
        review['decision']=='ACCEPTED_SOURCE_ONLY' and review['source_hdf_ref']==s.pin(BASE/'HDF.json')
        and review['source_mf_ref']==s.pin(BASE/'MF.json') and review['source_ref']==base['source_ref']
        and review['guards_closed_zero'] is True and review['retained_handles_count']==0,
        dict(protected_BR6_members=len(mf['members']),old_author22_replayed=False,old_BR5_36_replayed=False,
            old_independent24_and_tail2_replayed=False,Main47_replayed=False,Native4_and_Mode6_replayed=False))
    with (D/'w09_root_bridge.source.py').open('xb') as f:f.write(after)
    with (D/'consumer_launch.source.py').open('xb') as f:f.write(launcher)
    patch=''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),
        fromfile=str(BASE/'w09_root_bridge.source.py'),tofile=str(D/'w09_root_bridge.source.py')))
    with (D/'bridge07.patch').open('xb') as f:f.write(patch.encode())
    created=dict(source_ref=s.pin(D/'w09_root_bridge.source.py'),consumer_launcher_ref=s.pin(D/'consumer_launch.source.py'))
    s.write('exact-inverse.json',dict(base_source_ref=base['source_ref'],new_source_ref=created['source_ref'],
        inverse_sha256=hashlib.sha256(restored).hexdigest(),complete_byte_inverse=True,
        changed_business_functions=[],changed_bindings=['BRIDGE_GENERATION','TRUSTED.formal_profile_w09.py'],
        all_functions_classes_AST_unchanged=True,other_TRUSTED_entries_unchanged=True,
        consumer_launcher_unchanged=True,Source_only=True))
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc));raise
finally:
    guard_ref=s.write('source-guard.closed.json',g.close())
    controls_ref=s.write('delta-controls.json',dict(checks=checks,count=len(checks),passed=sum(x['passed'] for x in checks),
        failure=failure,source_guard_ref=guard_ref,held_count=len(refs),created=created,
        Source_only=True,self_acceptance=False,execution_grant=False,formal_acceptance=False,
        product_calls=dict(Native=0,Go=0,SQL=0,dispatcher=0,TP=0,RootStage=0,model=0)))

created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
revision=uuid.uuid4().hex
notes='''# Bridge07 Root calling contract

Actual Source author: codex:/root/full_w09_source_review, backend /root/full_w09_source_review. Formal verifier remains /root/backup_regression_resources. This prepared Source requires a new independent Source review and actual Root authority. It issues no execution grant, Mode qualification or formal acceptance.

The only code changes from sealed BR6 are BRIDGE_GENERATION=bridge-20261010-07 and TRUSTED formal_profile_w09.py SHA/bytes=1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087/71403. Root has actually adopted the independently reviewed tuple-to-list boundary correction; original1208 remains failed. The consumer launcher is byte-identical and discovers the sealed Caller in its own directory. All ten stages, actual peer offsets, six routes, five roles, Main Native/Mode gates, exact resource/TEMP contracts, SourceReadGuard, current4 and owner/worker/lease conditions remain unchanged.

BR6's original four-archive proof, normalized Canon classification, fresh request authority, separate persistent/authority snapshots and unchanged TP exclusive CAS remain mandatory. Canon aliases never substitute a different exact ref object. Root must use a fresh BR7 Source review, request and finite Scope.source_actor=/root/full_w09_source_review, with generation and current Source refs bound; no old proposal or Scope is relabeled.

After adoption, rebuild the actual context seed and formal vector with the new Main pin. Native Source21 excludes formal_profile_w09.py; four existing NF6 Native reports and six Mode decisions are preserved subject to every unchanged Main gate. This Source author does not reissue or independently accept them. No Native, Go, SQL, dispatcher, TP, Root stage, Scope or Main/Canon write is performed by this preparation. Successful prior Source controls, the 47 Main candidate checks and existing Native/Mode checks are referenced without replay.
'''
with (D/'ROOT_CALL_CONTRACT.md').open('xb') as f:f.write(notes.encode())
contract_ref=s.pin(D/'ROOT_CALL_CONTRACT.md')
contract=copy.deepcopy(base_contract)
contract.update(generation='bridge-20261010-07',source_revision_uuid=revision,
    source_ref=created['source_ref'],consumer_launcher_ref=created['consumer_launcher_ref'],contract_ref=contract_ref,
    base_hdf_ref=s.pin(BASE/'HDF.json'),base_mf_ref=s.pin(BASE/'MF.json'),base_source_ref=base['source_ref'])
contract['CLI_prefix'][-1]=created['source_ref']['path']
contract['Main_adoption_closed_ref']=s.pin(ADOPT/'Main-adoption.closed.root.json')
contract['Main_independent_review_ref']=adoption['independent_review_ref']
contract['Main_required_ref']=adoption['target_after_ref']
contract['BR6_accepted_review_ref']=review['decision_ref']
contract['business_delta_from_BR6']='Two constants only: generation and TRUSTED profile SHA/bytes; no function AST changes.'
contract['fresh_after_Main_adoption_vector_required']=True
contract['old_22_and_24_controls_rerun']=False
calling_ref=s.write('root-calling-contract.source.json',contract)
source_inputs_ref=s.write('source-inputs.json',dict(schema='researchos.w09-bridge07-source-inputs.v1',
    base_hdf_ref=s.pin(BASE/'HDF.json'),base_mf_ref=s.pin(BASE/'MF.json'),base_source_ref=base['source_ref'],
    base_source_inputs_ref=base['source_inputs_ref'],base_accepted_review_hdf_ref=s.pin(PR/'HDF.json'),
    base_accepted_review_mf_ref=review['manifest_ref'],base_accepted_review_decision_ref=review['decision_ref'],
    current_Main_ref=adoption['target_after_ref'],Main_adoption_closed_ref=s.pin(ADOPT/'Main-adoption.closed.root.json'),
    Main_adoption_guard_ref=s.pin(ADOPT/'Main-adoption.source-guard.closed.root.json'),
    Main_independent_review_hdf_ref=s.pin(MR/'HDF.json'),Main_independent_review_mf_ref=s.pin(MR/'MF.json'),
    Main_independent_review_decision_ref=adoption['independent_review_ref'],
    Main_independent_review_actual_peer_audit_ref=adoption['independent_delivery_audit_ref'],
    current_source_ref=created['source_ref'],current_consumer_launcher_ref=created['consumer_launcher_ref'],
    existing_TRUSTED_metadata={key:list(value) for key,value in new_c['TRUSTED'].items()},
    retained_Base_author_contribution=base['base_source_contribution'],
    original1208='FAILED_RETAINED_MAIN_TUPLE_TYPE_ARRAY_BOUNDARY',
    Root_adoption_actual_host_chunk='05d5fe',Root_adoption_actual_outer_exit=0,Root_adoption_actual_Python_exit=0,
    protected_BR6_member_refs=mf['members'],historical_original1190_io=base['original1190_io'],
    historical_original1185_io=base['original1185_io_preserved'],old_controls_replayed=False,
    current_CP_OW_SS_not_read=True,execution_grant=False,formal_acceptance=False))
s.write('preparation-metadata.json',dict(created_utc=created_utc,source_revision_uuid=revision,
    source_ref=created['source_ref'],consumer_launcher_ref=created['consumer_launcher_ref'],contract_ref=contract_ref,
    root_calling_contract_ref=calling_ref,source_inputs_ref=source_inputs_ref,delta_controls_ref=controls_ref,
    source_guard_ref=guard_ref,generation='bridge-20261010-07',base_hdf_ref=s.pin(BASE/'HDF.json'),
    base_mf_ref=s.pin(BASE/'MF.json'),base_source_ref=base['source_ref'],
    base_source_contribution=base['base_source_contribution'],base_accepted_review=review,
    Main_adoption_closed_ref=s.pin(ADOPT/'Main-adoption.closed.root.json'),
    Main_independent_review_ref=adoption['independent_review_ref'],Main_required_ref=adoption['target_after_ref'],
    inherited_BR6_historical_diagnostics=base['prior_Attach_review_original_diagnostics_preserved'],
    original1190_io=base['original1190_io'],original1185_io_preserved=base['original1185_io_preserved'],
    new_original_failures=[],independent_source_review_required=True,Source_author_self_acceptance=False))
print(json.dumps(dict(Source_status='SOURCE_PREPARED_UNSEALED',checks=len(checks),passed=sum(x['passed'] for x in checks),
    source_ref=created['source_ref'],consumer_launcher_ref=created['consumer_launcher_ref'],
    root_calling_contract_ref=calling_ref,source_guard_ref=guard_ref,product_calls=0,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
