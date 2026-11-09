"""Future Root metadata draft builder; no canonical writer or native launcher.

scope INPUT_REF_JSON OUTPUT_LEAF
draft SCOPE_REF_JSON REVIEW_REF_JSON CANONICAL_COPIES_REF_JSON OUTPUT_LEAF

All output leaves are new/exclusive. INPUT requires explicit resources/tuples;
NULL preparation templates are refused. Actual CAS/seal/grant are Root OPEN
integration steps, not implemented by this builder and never synthesized here.
"""
import copy
import datetime
import hashlib
import json
import sys
import traceback
import types
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
GATE_PATH=Path(__file__).with_name('authority_adapter.v2.proposed.py')
GATE_SHA='21dd857e41f5cadcc4009a775c09f3103c8e3e35908786a1b656f2cd158aac09'
TEMPLATE_REF={'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\f08_driver18_execution_revision_preparation_codex\\fb328e152ae54da6b4be24cbc3b94ece\\scope.UNBOUND.v3.proposed.json', 'sha256': 'ba4317e79eaf45f8f0cc53990284692f1ae2ed55b2584d77c082a63f87f5a1e2', 'bytes': 2808}

def need(ok,why):
    if not ok:raise ValueError(why)

def write(p,raw):
    with p.open('xb') as f:f.write(raw)
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def save(p,obj):return write(p,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf8'))

def getgate():
    b=GATE_PATH.read_bytes();need(hashlib.sha256(b).hexdigest()==GATE_SHA,'PINNED_ADAPTER')
    m=types.ModuleType('driver18_metadata_authority');m.__file__=str(GATE_PATH)
    exec(compile(b,str(GATE_PATH),'exec'),m.__dict__)
    return m

def newleaf(g,text):
    p=g.safe(text,ROOT/'execution/v2.4/receipts/W05/W05-99')
    need(p.parent.is_dir() and not p.exists(),'EXCLUSIVE_LEAF_PARENT_REQUIRED')
    p.mkdir();return p

def build_scope(g,r,inp):
    x=r.doc(inp);need(x['schema']=='researchos.driver18-root-binding-input.v1' and x['owner']=='codex:/root','ROOT_INPUT')
    s=r.doc(TEMPLATE_REF)
    s['controller_ref']={'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\f08_driver18_root_binding_revision_preparation_codex\\ae14ede5d4d34ea493f9945886997cb2\\driver18_controller.v4.proposed.py', 'sha256': '75d3f1180764c817d828d8765e1dd824f8fc6912fff4675c0cdb78e0fd8ee503', 'bytes': 21592}
    keys=['actual_Root_registration','actual_origin_cut','authority_validator_ref','resource_catalog_ref',
          'public_environment','work_root','prepare_output_root','execute_output_root',
          'prepare_launcher_output_root','execute_launcher_output_root']
    for key in keys:need(x.get(key) is not None,'ROOT_REQUIRED_'+key);s[key]=x[key]
    a=s['actual_Root_registration'];need(a['phase'] in ['prepare','execute'],'PHASE')
    s['prepared_ref']=x['prepared_ref']
    need((a['phase']=='prepare')==(s['prepared_ref'] is None),'SEPARATE_PREPARE_EXECUTE_SCOPE')
    s['actual_non_author_controller_review_ref']=None
    s['preparation_only']=False;s['mode']='PARTIAL_17_EXPLICIT'
    s['ordered_cases']=[f'I{i:02d}' for i in range(1,19) if i!=17]
    need(s['caps']==g.CAPS,'CAPS_UNCHANGED')
    need(g.safe(s['authority_validator_ref']['path'])==GATE_PATH.resolve() and
         s['authority_validator_ref']['sha256']==GATE_SHA,'THIS_ADAPTER_ONLY')
    # Scope writing only prepares review input; actual validation/registration
    # still requires independent full-scope review and sealed Root CAS.
    for key in g.FIXED:r.verify(s[key]);need(s[key]['sha256']==g.FIXED[key],'FIXED_PREFIX')
    r.verify(s['authority_validator_ref']);r.verify(s['actual_origin_cut']);r.verify(s['resource_catalog_ref'])
    for key in ['controller_review_path','registration_review_path']:g.safe(a[key],ROOT/'execution/v2.4/receipts')
    need(s['source_acceptance'] is False,'NO_ACCEPTANCE')
    return s

def draft(g,r,sref,reviewref,copiesref,out):
    s=g.scope(r,sref);a=s['actual_Root_registration'];phase=a['phase'];prefix='f08_driver18_'+phase
    g.safe(str(out),g.safe(a['registration_namespace']))
    cr=r.doc(reviewref)
    need(g.safe(reviewref['path'])==g.safe(a['controller_review_path']) and
         cr['schema']=='researchos.driver18-bound-controller-review.v1' and cr['reviewer'] in g.REVIEWERS and
         cr['decision']=='READY_FOR_ROOT_DRIVER18_'+phase.upper()+'_ONCE' and
         cr['requested_changes']==[] and cr['scope_sha256']==sref['sha256'] and
         cr['mode']=='PARTIAL_17_EXPLICIT','FULL_SCOPE_NONAUTHOR_REVIEW')
    for k in ['controller_ref','launcher_ref','authority_validator_ref','utility_ref','owned_helper_ref','debug_helper_ref']:
        need(cr['code_refs'][k]==s[k],'REVIEW_EXACT_CODE')
    copies=r.doc(copiesref)['entries'];need([x['canonical_path'] for x in copies]==g.CANON,'FOUR_ORDERED_COPIES')
    raws=[r.verify(x['ref']) for x in copies];cp,ow=map(g.parse,raws[:2])
    need([cp['revision'],ow['revision'],len(cp['failure_counters'])]==a['before'],'ACTUAL_BEFORE_TUPLE')
    need(all((ROOT/p).read_bytes()==b for p,b in zip(g.CANON,raws)),'LIVE_FOUR_DRAFT_CAS')
    need(cp['head']==a['source_guard_expected']['head'],'HEAD_BASELINE')
    cut=r.doc(s['actual_origin_cut']);need(cut['before']==a['before'] and cut['after']==a['after'] and cut['counter_reset'] is False,'EXACT_ORIGIN_CUT')
    need(len(cut['origins'])==a['after'][2]-a['before'][2],'ORIGIN_COUNT')
    seen=set()
    for row in cut['origins']:
        ref=row['evidence_ref'];need(row['original_payload']==r.doc(ref) and row['counter_reset'] is False,'RAW_ORIGIN')
        need(ref['sha256'] not in seen and all(x.get('evidence_ref',{}).get('sha256')!=ref['sha256'] for x in cp['failure_counters']),'DUPLICATE_ORIGIN')
        seen.add(ref['sha256'])
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();nc=copy.deepcopy(cp);no=copy.deepcopy(ow)
    nc.update(revision=a['after'][0],expected_previous_revision=a['before'][0],updated_at=stamp,updated_by='codex:/root')
    nc['failure_counters'].extend(cut['origins'])
    nc['work_in_progress'][prefix+'_scope_ref']=sref
    nc['work_in_progress'][prefix+'_controller_review_ref']=reviewref
    no.update(revision=a['after'][1],amended_at=stamp,amended_by='codex:/root')
    need(a['lease_key'] not in no['special_paths'],'EXISTING_LEASE_NOT_REPLACED')
    no['special_paths'][a['lease_key']]=g.lease(s,sref)
    original=[write(out/(Path(p).stem+'.original.json'),b) for p,b in zip(g.CANON,raws)]
    desired=[save(out/'checkpoint.desired.json',nc),save(out/'path_ownership.desired.json',no),
             write(out/'step_state.desired.json',raws[2]),write(out/'commands.desired.json',raws[3])]
    save(out/'registration.draft.json',{'schema':'researchos.driver18-root-registration-draft.v1',
         'scope_ref':sref,'controller_review_ref':reviewref,'before':a['before'],'after':a['after'],
         'canonical_paths':g.CANON,'original_refs':original,'desired_refs':desired,'origin_cut_ref':s['actual_origin_cut'],
         'current_root_lease':g.lease(s,sref),'invocation_contract':{
             'cwd':str(ROOT),'env':s['public_environment'],'timeout':a['registration_timeout_seconds'],
             'output_root':str(g.safe(a['registration_output_root'])),
             'registration_review_path':a['registration_review_path']},
         'registration_metadata_paths':g.CANON[:2],'actual_registration_executed':False,
         'formal_increment':0,'source_acceptance':False,'root_CAS_executor':'OPEN_SEPARATE_ROOT_SOURCE_REVIEW_REQUIRED'})
    r.unchanged()
    need(all((ROOT/p).read_bytes()==b for p,b in zip(g.CANON,raws)),'FINAL_DRAFT_LIVE_FOUR_CAS')

def main():
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'PYTHON_I_S_UTF8')
    sys.dont_write_bytecode=True;out=None;first=None
    try:
        need(len(sys.argv)>=2 and sys.argv[1] in ['scope','draft'],'METADATA_ACTION_ONLY')
        g=getgate();r=g.Reader();action=sys.argv[1]
        if action=='scope':
            need(len(sys.argv)==4,'scope INPUT_REF_JSON OUTPUT_LEAF')
            value=build_scope(g,r,g.parse(sys.argv[2].encode()))
            out=newleaf(g,sys.argv[3]);sref=save(out/'scope.proposed.json',value)
            g.scope(r,sref);r.unchanged()
        else:
            need(len(sys.argv)==6,'draft SCOPE_REF_JSON REVIEW_REF_JSON COPIES_REF_JSON OUTPUT_LEAF')
            sref,reviewref,copiesref=[g.parse(x.encode()) for x in sys.argv[2:5]]
            # Authenticate immutable refs before claiming ownership of output.
            for ref in [sref,reviewref,copiesref]:r.verify(ref)
            out=newleaf(g,sys.argv[5]);draft(g,r,sref,reviewref,copiesref,out)
        save(out/'metadata-inputs.json',{'refs':list(r.refs.values()),'target_calls':0,'actual_CAS':False})
        save(out/'completed.json',{'actor':'codex:/root','action':action,'reported_exit':0,
                                 'actual_CAS':False,'actual_grant':False,'source_acceptance':False})
    except BaseException as e:
        first={'stage':'METADATA_DRAFT','error':repr(e),'traceback':traceback.format_exc(),
               'actual_native_exit':None,'automatic_retry':False,'counter_reset':False}
        if out is not None:
            try:save(out/'failure.origin.json',first)
            except BaseException as second:first['secondary']=repr(second)
        sys.stderr.write(json.dumps(first,ensure_ascii=False)+'\n')
    return 1 if first else 0

if __name__=='__main__':
    try:exit_code=main()
    except BaseException as exc:
        sys.stderr.write(json.dumps({'stage':'ENTRY','error':repr(exc),'actual_native_exit':None})+'\n');exit_code=1
    sys.exit(exit_code)
