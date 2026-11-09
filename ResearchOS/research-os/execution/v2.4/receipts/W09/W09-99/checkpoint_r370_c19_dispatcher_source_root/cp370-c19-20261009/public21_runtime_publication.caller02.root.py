"""Publish a runtime qualification only from actual independent review and hosts."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys, types

N = Path(__file__).resolve().parent
helper = N / 'public21_actual_resources.caller02.host02.root.py'
raw = helper.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '9a7eb7907f6957321539c1bcc683774c1f1ed01a339c651a922ac0046e89c8ff'
text = raw.decode('utf-8')
assert text.count('mode=sys.argv[1]') == 1
pub = types.ModuleType('root_public21_current_publication')
pub.__file__ = str(helper)
sys.modules[pub.__name__] = pub
exec(compile(text.split('mode=sys.argv[1]')[0], str(helper), 'exec'), pub.__dict__)
api, base = pub.api, pub.base

def payload():
    assert len(sys.argv) == 6
    refs = {key:pub.pin(Path(path)) for key,path in zip(('hdf','mf','decision'),sys.argv[2:5])}
    hdf, mf, decision = (api.doc(refs[key]) for key in ('hdf','mf','decision'))
    actor = 'codex:/root/full_w09_source_review'
    assert decision['schema'] == 'researchos.public21-runtime-independent-review-decision.v1'
    assert hdf['schema'] == 'researchos.public21-runtime-independent-review-hdf.v1'
    assert hdf['review_author'] == decision['review_author'] == actor
    assert decision['independent_non_author'] is True and decision['verdict'] == 'RUNTIME_CLOSURE_ACCEPTED'
    assert decision['formal_acceptance'] is False and decision['execution_grant'] is False
    assert hdf['manifest_ref'] == refs['mf'] and hdf['decision_ref'] == refs['decision']
    assert any(ref == refs['decision'] for ref in mf['members'])
    fields = ('source_hdf_ref','source_mf_ref','caller_ref','runner_contract_ref',
              'qualification_scope_ref','python_ref','control_ref','runtime_manifest_ref')
    for field in fields:
        assert hdf[field] == decision[field]
        api.checked(decision[field])
    manifest = api.doc(decision['runtime_manifest_ref'])
    assert manifest['schema'] == 'researchos.root-public21-runtime-manifest.v1'
    assert manifest['issued_by'] == pub.ROOT and manifest['root_thread_id'] == pub.THREAD
    assert decision['source_author'] == hdf['source_author'] == manifest['source_author'] == api.AUTHOR
    assert decision['runner_source_author'] == hdf['runner_source_author'] == manifest['runner_source_author'] == api.AUTHOR
    assert decision['resource_refs'] == manifest['resource_refs']
    for field in ('source_hdf_ref','source_mf_ref','caller_ref','runner_contract_ref','qualification_scope_ref'):
        assert manifest[field] == decision[field]
    assert decision['source_hdf_ref'] == pub.pin(pub.PC/'HDF.json')
    assert decision['source_mf_ref'] == pub.pin(pub.PC/'MF.json')
    assert decision['caller_ref'] == pub.pin(pub.CALLER)
    assert decision['runner_contract_ref'] == api.LEAF_REFS['contract_ref']
    contract = api.doc(decision['runner_contract_ref'])
    assert api.same_ref(decision['python_ref'],contract['locked_python_ref'])
    assert api.same_ref(decision['control_ref'],contract['old21_control'])
    peer = pub.peer_wrap(Path(sys.argv[5]),actor,'RUNTIME_QUALIFICATION_ISSUANCE',refs)
    value = dict(schema='researchos.root-public21-runtime-qualification-payload.v1',issued_by=pub.ROOT,
        root_thread_id=pub.THREAD,status='QUALIFIED_FOR_PUBLIC21_BOOTSTRAP',independent_non_author=True,
        formal_programme_qualification=False,review_author=actor,resource_refs=decision['resource_refs'],
        review_hdf_ref=refs['hdf'],review_mf_ref=refs['mf'],review_decision_ref=refs['decision'],
        review_hostpair_binding_ref=peer,payload_created_utc=datetime.now(timezone.utc).isoformat())
    for field in fields:
        value[field] = decision[field]
    scope = api.doc(value['qualification_scope_ref'])
    api.finite_lease(scope['created_utc'],scope['lease_expires_at'])
    assert api.when(scope['created_utc']) <= api.when(hdf['reviewed_utc']) <= api.when(api.doc(peer)['received_at']) <= api.when(value['payload_created_utc'])
    pref = pub.save('runtime-qualification.payload.actual.root.json',value)
    observer = pub.save('RUNTIME_QUALIFICATION_ISSUANCE.observation-request.root.json',dict(
        operation='RUNTIME_QUALIFICATION_ISSUANCE',
        observed_refs=[pref,value['qualification_scope_ref'],*refs.values(),peer],peer_actor=None))
    print(json.dumps(dict(payload_ref=pref,observation_request_ref=observer,
                         formal_acceptance=False,execution_grant=False),ensure_ascii=False))

def seal():
    pub.bind_root('RUNTIME_QUALIFICATION_ISSUANCE',Path(sys.argv[2]))
    pref = pub.pin(pub.O/'runtime-qualification.payload.actual.root.json')
    value = api.doc(pref)
    binding = pub.pin(pub.O/'RUNTIME_QUALIFICATION_ISSUANCE.actual-root-binding.root.json')
    wrapper = dict(value,schema='researchos.root-public21-qualified-runtime.v1',payload_ref=pref,
                   root_issuance_binding_ref=binding,created_utc=datetime.now(timezone.utc).isoformat())
    qref = pub.save('runtime-qualification.issued.actual.root.json',wrapper)
    refs = api.kernel()['runtime_review_chain'](qref,wrapper,api.doc(wrapper['runner_contract_ref']))
    print(json.dumps(dict(qualification_ref=qref,runtime_review_chain_verified=True,chain_ref_count=len(refs),
                         formal_acceptance=False,execution_grant=False,Canon_written=False),ensure_ascii=False))

if sys.argv[1] == 'payload':
    payload()
elif sys.argv[1] == 'seal':
    seal()
else:
    raise ValueError('ROOT_RUNTIME_PUBLICATION_MODE')
