"""Driver18 metadata-only reader proposal. No CAS, native calls or grant minting.

Root must separately review/register this adapter and furnish actual registration
and phase evidence. This file is never an authority merely because it exists.
"""
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
CANON = ['execution/v2.4/checkpoint.json', 'execution/v2.4/path_ownership.json',
         'execution/v2.4/step_state.json', 'execution/v2.4/commands.json']
REVIEWERS = {'codex:/root/w05_merge_review', 'codex:/root/f08_whole_scope_review',
             '/root/f08_whole_scope_review'}
CAPS = {'native_calls':32, 'compiler_seconds':600, 'test_seconds':750,
        'inner_seconds':3300, 'outer_seconds':3600, 'cleanup_seconds':5,
        'images':64, 'compiler_processes':2048, 'job_active_processes':16,
        'fixture_HTTP':0, 'SDK_Node_model_external_paid':0}
FIXED = {
    'controller_ref':'75d3f1180764c817d828d8765e1dd824f8fc6912fff4675c0cdb78e0fd8ee503',
    'launcher_ref':'fbf9c52568678e3733a0e50300a53c2044be96afee85672d3d2bf4df78af9086',
    'utility_ref':'333d69e00a421efcbb08e9ddf06e1486e911cd82af4a0d46a8bb60c8203f2bea',
    'owned_helper_ref':'6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad',
    'debug_helper_ref':'8368debd47b8a1df7e4b8c6f11d28abdd7df49d8683ac755134d3877ca818e27',
    'fixed_inputs_ref':'31175d54ca846c47f4a3183f43b50578db7d59b16f783c6ce07adc06d0e59624'}

def need(ok, why):
    if not ok:
        raise ValueError(why)

def parse(raw):
    def pairs(rows):
        out = {}
        for k, v in rows:
            need(k not in out, 'DUPLICATE_JSON_KEY')
            out[k] = v
        return out
    return json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def safe(text, root=None):
    need(isinstance(text, str) and text, 'PATH_REQUIRED')
    p = Path(text)
    need('..' not in p.parts, 'DOTDOT_PATH')
    if not p.is_absolute():
        need(not p.drive, 'DRIVE_RELATIVE_PATH')
        p = ROOT / p
    need(p.resolve() == p, 'NONCANONICAL_PATH')
    for q in [p, *p.parents]:
        if os.path.lexists(q):
            need(not q.is_symlink() and not getattr(q.lstat(), 'st_file_attributes', 0) & 0x400,
                 'REPARSE_ALIAS')
    if root is not None:
        need(p != root and p.is_relative_to(root), 'PATH_BOUNDARY')
    return p

def refshape(ref):
    need(isinstance(ref, dict) and set(ref) == {'path','sha256','bytes'}, 'EXACT_REF')
    need(type(ref['bytes']) is int and ref['bytes'] >= 0 and
         isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'REF_VALUE')

class Reader:
    def __init__(self):
        self.raw = {}
        self.refs = {}

    def verify(self, ref):
        refshape(ref)
        p = safe(ref['path'])
        b = p.read_bytes()
        need(len(b) == ref['bytes'] and hashlib.sha256(b).hexdigest() == ref['sha256'], 'PIN ' + str(p))
        key = str(p)
        need(key not in self.raw or self.raw[key] == b, 'INPUT_CHANGED_DURING_READ')
        self.raw[key] = b
        self.refs[key] = {'path':key, 'sha256':ref['sha256'], 'bytes':ref['bytes']}
        return b

    def doc(self, ref):
        return parse(self.verify(ref))

    def actual(self, path, sha):
        p = safe(path)
        b = p.read_bytes()
        need(hashlib.sha256(b).hexdigest() == sha, 'ACTUAL_INPUT_SHA')
        ref = {'path':str(p), 'sha256':sha, 'bytes':len(b)}
        # Retain and consume this exact buffer; no verify-then-second-read.
        need(str(p) not in self.raw or self.raw[str(p)] == b, 'INPUT_CHANGED')
        self.raw[str(p)] = b
        self.refs[str(p)] = ref
        return ref, parse(b)

    def unchanged(self):
        for p, b in self.raw.items():
            need(safe(p).read_bytes() == b, 'FINAL_INPUT_DRIFT ' + p)

def path_key(p):
    # Windows physical comparison only; original path spelling stays in refs.
    return str(p).casefold()

def zero(value):
    return type(value) is int and value == 0

def exact_location(ref, root, name):
    refshape(ref)
    need(safe(ref['path']) == safe(root) / name, 'EXACT_EVIDENCE_LOCATION_' + name)

def tree_files(root):
    root=safe(root);out={}
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:safe(str(Path(directory)/name),root)
        for name in files:
            p=safe(str(Path(directory)/name),root);key=path_key(p)
            need(key not in out,'PHYSICAL_DUPLICATE_FILE');out[key]=p
    return out

def complete_manifest(r, ref, root, required):
    exact_location(ref,root,'manifest.json')
    member_manifest(r,ref,required)
    m=r.doc(ref);need(m['excluded_only_self'] is True,'FULL_OUTPUT_MANIFEST')
    rows=m['files'];expected=tree_files(root);expected.pop(path_key(safe(ref['path'])))
    need({path_key(safe(x['path'])) for x in rows}==set(expected),'OUTPUT_MANIFEST_MEMBERSHIP')
    for x in rows:safe(x['path'],safe(root))

def same_ref(a, b):
    refshape(a); refshape(b)
    return safe(a['path']) == safe(b['path']) and a['sha256'] == b['sha256'] and a['bytes'] == b['bytes']

def member_manifest(r, ref, required):
    m = r.doc(ref)
    rows = m.get('members', m.get('files'))
    need(isinstance(rows, list) and rows, 'EMPTY_MANIFEST')
    seen = {}
    for row in rows:
        refshape(row)
        key = path_key(safe(row['path']))
        need(key not in seen, 'DUPLICATE_MANIFEST_MEMBER')
        r.verify(row); seen[key] = row
    for item in required:
        key = path_key(safe(item['path']))
        need(key in seen and same_ref(seen[key], item), 'REQUIRED_MANIFEST_MEMBER')

def job(result):
    need(isinstance(result, dict) and type(result.get('actual_exit')) is int and result['actual_exit'] == 0,
         'ACTUAL_NATIVE_ZERO_REQUIRED')
    need(result.get('timed_out') is False and result.get('error') is None and result.get('resumed') is True,
         'JOB_EXECUTION_FACTS')
    need(type(result.get('owned_child_pid')) is int and result['owned_child_pid'] > 0 and
         type(result.get('creation_time_100ns')) is int and result['creation_time_100ns'] > 0, 'PID_CTIME')
    c = result['job_cleanup']
    for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume',
              'job_idle_confirmed','primary_exit_confirmed','handles_closed']:
        need(c.get(k) is True, 'JOB_CLEANUP_' + k)
    need(c.get('active_processes_last_observed') == 0 and c.get('errors') == [] and
         c.get('termination_requested') is False and
         c.get('unassigned_suspended_child_termination_requested') is False, 'JOB_UNCLEAN')

def scope(r, sref):
    s = r.doc(sref)
    need(s['schema'] == 'researchos.driver18-root-finite-scope.proposed.v1' and
         s['preparation_only'] is False and s['source_acceptance'] is False and s['caps'] == CAPS, 'SCOPE_BOUNDARY')
    for k, sha in FIXED.items():
        need(s[k]['sha256'] == sha, 'FROZEN_CODE_' + k); r.verify(s[k])
    r.verify(s['authority_validator_ref'])
    a = s['actual_Root_registration']
    need(a['schema'] == 'researchos.driver18-root-registration-binding.v1' and
         a['owner'] == 'codex:/root' and a['phase'] in ['prepare','execute'], 'ROOT_PHASE_BINDING')
    need(re.fullmatch('[0-9a-f]{32}', a['run_uuid']) is not None, 'EXPLICIT_UUID')
    need(a['lease_key']=='f08_driver18_'+a['phase']+'_'+a['run_uuid'], 'DEDICATED_DRIVER_LEASE_KEY')
    before, after = a['before'], a['after']
    need(all(isinstance(v,list) and len(v)==3 and all(type(x)is int and x>=0 for x in v)
             for v in [before,after]), 'EXPLICIT_TUPLES')
    need(after[:2] == [before[0]+1,before[1]+1] and after[2]>=before[2], 'FORWARD_TUPLE')
    need(s['actual_non_author_controller_review_ref'] is None, 'NO_SCOPE_REVIEW_HASH_CYCLE')
    for k in ['controller_review_path','registration_review_path']:
        safe(a[k], ROOT/'execution/v2.4/receipts')
    ns = safe(a['registration_namespace'], ROOT/'execution/v2.4/receipts/W05/W05-99')
    need(a['run_uuid'] in ns.name, 'ROOT_REGISTRATION_UUID')
    safe(a['registration_output_root'],ns)
    need(type(a['registration_timeout_seconds']) is int and a['registration_timeout_seconds']>0,
         'ROOT_EXPLICIT_METADATA_TIMEOUT')
    roots = []
    for k in ['work_root','prepare_output_root','execute_output_root',
              'prepare_launcher_output_root','execute_launcher_output_root']:
        p = safe(s[k], ROOT/'.local' if k=='work_root' else ROOT/'execution/v2.4/receipts/W05/W05-99')
        need(a['run_uuid'] in p.name, 'UNIQUE_PHASE_ROOT'); roots.append(p)
    need(all(x!=y and not x.is_relative_to(y) and not y.is_relative_to(x)
             for i,x in enumerate(roots) for y in roots[i+1:]), 'OVERLAPPING_ROOTS')
    need(set(s['public_environment']) <= {'SystemRoot','WINDIR','ComSpec','PATH','PATHEXT'}, 'PUBLIC_ENV')
    need(s['mode']=='PARTIAL_17_EXPLICIT' and s['ordered_cases']==[f'I{i:02d}' for i in range(1,19) if i!=17],
         'I17_NOT_AUTHORIZED')
    need((a['phase']=='prepare') == (s['prepared_ref'] is None), 'PHASE_PREPARED_BINDING')
    res = r.doc(s['resource_catalog_ref'])
    need(isinstance(res['files'],list) and res['files'] and 0<len(res['compiler_images'])<=61, 'FINITE_RESOURCES')
    allowed={}
    for item in res['files']:
        r.verify(item); key=path_key(safe(item['path']))
        need(key not in allowed, 'DUPLICATE_RESOURCE_PATH'); allowed[key]=item
    for item in [res['python'],res['go'],*res['compiler_images']]:
        need(path_key(safe(item['path'])) in allowed and same_ref(allowed[path_key(safe(item['path']))],item), 'TOOL_NOT_CATALOGUED')
    need(res['go']['sha256']=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490', 'LOCKED_GO')
    need(res['python']['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b', 'LOCKED_PYTHON')
    safe(res['GOROOT']); destinations=set()
    for row in res['offline_modcache_copies']:
        p=Path(row['relative_path'])
        need(not p.is_absolute() and not p.drive and '..' not in p.parts and p.parts, 'OFFLINE_RELATIVE_PATH')
        need(p.parts[0].casefold()!='modernc.org' or len(p.parts)<2 or p.parts[1].casefold()!='sqlite@v1.60.1', 'PRISTINE_SOURCE_OVERWRITE')
        key=str(p).casefold(); need(key not in destinations, 'OFFLINE_DUPLICATE'); destinations.add(key)
        ref=row['ref']; need(path_key(safe(ref['path'])) in allowed and same_ref(allowed[path_key(safe(ref['path']))],ref), 'OFFLINE_SOURCE_PIN')
    r.doc(s['actual_origin_cut'])
    for ref in a['evidence_refs']:
        r.verify(ref)
    return s

def lease(s, sref):
    a=s['actual_Root_registration']
    return {'owner':'codex:/root','run_uuid':a['run_uuid'],'phase':a['phase'],
            'scope_ref':sref,'mode':'EXCLUSIVE_ROOT_FINITE_DRIVER_VALIDATION',
            'paths':[s[k] for k in ['work_root','prepare_output_root','execute_output_root',
                                  'prepare_launcher_output_root','execute_launcher_output_root']],
            'source_writes':False,'SQL24_adoption':False}

def registration(r, s, sref, bundle):
    """Root-sealed adapter bundle wraps original Root receipts, never substitutes them."""
    a=s['actual_Root_registration']; phase=a['phase']; prefix='f08_driver18_'+phase
    need(bundle['schema']=='researchos.driver18-root-registration-evidence.v1', 'REGISTRATION_BUNDLE')
    ns=safe(a['registration_namespace']);regout=safe(a['registration_output_root'],ns)
    for key in ['draft_ref','draft_manifest_ref','audit_ref','intent_ref','invocation_ref','requested_ref',
                'wrapper_invocation_ref','verified_ref','stdout_ref','stderr_ref','manifest_ref']:
        safe(bundle[key]['path'],ns)
    for ref in bundle['registration_code_and_draft_refs'].values():safe(ref['path'],ns)
    draft=r.doc(bundle['draft_ref']); audit=r.doc(bundle['audit_ref']); intent=r.doc(bundle['intent_ref'])
    inv=r.doc(bundle['invocation_ref']); verified=r.doc(bundle['verified_ref'])
    need(draft['scope_ref']==sref and draft['before']==a['before'] and draft['after']==a['after'], 'DRAFT_SCOPE_TUPLE')
    need(draft['schema']=='researchos.driver18-root-registration-draft.v1' and
         draft['canonical_paths']==CANON and draft['registration_metadata_paths']==CANON[:2] and
         draft['actual_registration_executed'] is False and draft['source_acceptance'] is False and
         draft['current_root_lease']==lease(s,sref) and draft['invocation_contract']=={
             'cwd':str(ROOT),'env':s['public_environment'],'timeout':a['registration_timeout_seconds'],
             'output_root':str(regout),'registration_review_path':a['registration_review_path']},
         'CURRENT_DRAFT_LEASE_AND_INVOCATION')
    for ref in draft['original_refs']+draft['desired_refs']:safe(ref['path'],ns)
    originals=[r.verify(x) for x in draft['original_refs']]; desired=[r.verify(x) for x in draft['desired_refs']]
    need(len(originals)==len(desired)==4 and originals[2:]==desired[2:], 'FOUR_CANONICAL_TWO_WRITES')
    oldcp,oldow=map(parse,originals[:2]); cp,ow=map(parse,desired[:2])
    need(a['lease_key'] not in oldow['special_paths'], 'PREEXISTING_LEASE_NOT_OVERWRITTEN')
    need([oldcp['revision'],oldow['revision'],len(oldcp['failure_counters'])]==a['before'] and
         [cp['revision'],ow['revision'],len(cp['failure_counters'])]==a['after'], 'ACTUAL_SNAPSHOT_TUPLES')
    cut=r.doc(s['actual_origin_cut']); need(cut['before']==a['before'] and cut['after']==a['after'] and cut['counter_reset'] is False,'ORIGIN_CUT')
    need(cp['failure_counters']==oldcp['failure_counters']+cut['origins'], 'ENTIRE_OLD_FAILURE_PREFIX')
    seen=set()
    for item in cut['origins']:
        ref=item['evidence_ref']; payload=r.doc(ref)
        need(item['original_payload']==payload and item['counter_reset'] is False and ref['sha256'] not in seen,
             'ORIGIN_FACT_PRESERVATION')
        need(all(x.get('evidence_ref',{}).get('sha256')!=ref['sha256'] for x in oldcp['failure_counters']), 'ORIGIN_RECOUNT')
        seen.add(ref['sha256'])
    need(len(cut['origins'])==a['after'][2]-a['before'][2], 'ORIGIN_COUNT')
    cref=cp['work_in_progress'][prefix+'_controller_review_ref']; cr=r.doc(cref)
    need(safe(cref['path'])==safe(a['controller_review_path']) and
         cr['schema']=='researchos.driver18-bound-controller-review.v1' and cr['reviewer'] in REVIEWERS and
         cr['decision']=='READY_FOR_ROOT_DRIVER18_'+phase.upper()+'_ONCE' and cr['requested_changes']==[], 'ACTUAL_CONTROLLER_REVIEW')
    need(cr['scope_sha256']==sref['sha256'] and cr['mode']=='PARTIAL_17_EXPLICIT', 'FULL_SCOPE_REVIEW')
    for k in ['controller_ref','launcher_ref','authority_validator_ref','utility_ref','owned_helper_ref','debug_helper_ref']:
        need(cr['code_refs'][k]==s[k], 'REVIEW_CODE_PIN')
    need(cp['work_in_progress'][prefix+'_scope_ref']==sref and
         ow['special_paths'][a['lease_key']]==lease(s,sref), 'CANONICAL_SCOPE_AND_LEASE')
    # Exact inverse protects all other tasks/status/head/formal/failure chain fields.
    pc=parse(desired[0]); po=parse(desired[1])
    for obj,old,keys in [(pc,oldcp,['revision','expected_previous_revision','updated_at','updated_by','failure_counters']),
                         (po,oldow,['revision','amended_at','amended_by'])]:
        for k in keys:
            if k in old: obj[k]=old[k]
            else: obj.pop(k,None)
    for k in [prefix+'_scope_ref',prefix+'_controller_review_ref']:
        if k in oldcp['work_in_progress']:pc['work_in_progress'][k]=oldcp['work_in_progress'][k]
        else:pc['work_in_progress'].pop(k,None)
    if a['lease_key'] in oldow['special_paths']:po['special_paths'][a['lease_key']]=oldow['special_paths'][a['lease_key']]
    else:po['special_paths'].pop(a['lease_key'],None)
    need(pc==oldcp and po==oldow, 'UNRELATED_CANONICAL_CHANGE')
    need(intent['actor']=='codex:/root' and intent['automatic_retry'] is False and
         intent['transition']=={k:[a['before'][i],a['after'][i]] for i,k in enumerate(['checkpoint','ownership','failures'])}, 'ACTUAL_INTENT')
    for i,row in enumerate(intent['metadata']):
        need(i<2 and row['path']==CANON[i] and same_ref(row['original_ref'],draft['original_refs'][i]) and
             same_ref(row['desired_ref'],draft['desired_refs'][i]), 'INTENT_RAW_BYTES')
    need(len(intent['metadata'])==2 and intent['unchanged']==[
        {'path':CANON[i],'sha256':draft['original_refs'][i]['sha256']} for i in [2,3]], 'UNCHANGED_ST_CM')
    regref=intent['review_ref']; reg=r.doc(regref)
    need(safe(regref['path'])==safe(a['registration_review_path']) and reg['reviewer'] in REVIEWERS and
         reg['schema']=='researchos.root-registration-source-review.v1' and
         reg['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and reg['requested_changes']==[] and
         reg['actual_registration_executed'] is False and reg['expected_before']==a['before'] and
         reg['expected_after']==a['after'], 'ROOT_REGISTRATION_NONAUTHOR_REVIEW')
    need(same_ref(reg['current_scope_ref'],sref) and
         same_ref(reg['registration_draft_ref'],bundle['draft_ref']) and
         same_ref(reg['registration_draft_manifest_ref'],bundle['draft_manifest_ref']) and
         reg['canonical_paths']==CANON and reg['original_refs']==draft['original_refs'] and
         reg['desired_refs']==draft['desired_refs'] and reg['current_root_lease']==lease(s,sref),
         'REGISTRATION_REVIEW_CURRENT_DRAFT')
    prepared_refs=r.doc(bundle['registration_code_and_draft_refs']['prepared_refs'])
    need(prepared_refs=={'schema':'researchos.driver18-registration-prepared-refs.v1',
         'current_scope_ref':sref,'registration_draft_ref':bundle['draft_ref'],'canonical_paths':CANON,
         'original_refs':draft['original_refs'],'desired_refs':draft['desired_refs'],
         'current_root_lease':lease(s,sref)},'REGISTRATION_PREPARED_REFS_CURRENT_DRAFT')
    preaudit=r.doc(bundle['registration_code_and_draft_refs']['audit'])
    need(preaudit['schema']=='researchos.driver18-registration-preexecution-audit.v1' and
         preaudit['actual_registration_executed'] is False and
         same_ref(preaudit['current_scope_ref'],sref) and same_ref(preaudit['registration_draft_ref'],bundle['draft_ref']) and
         preaudit['original_refs']==draft['original_refs'] and preaudit['desired_refs']==draft['desired_refs'],
         'PREEXECUTION_AUDIT_CURRENT_DRAFT')
    need(not same_ref(bundle['audit_ref'],bundle['registration_code_and_draft_refs']['audit']),
         'POSTAUDIT_CANNOT_REPLACE_PREAUDIT')
    member_manifest(r,bundle['draft_manifest_ref'],[sref,bundle['draft_ref'],
        *bundle['registration_code_and_draft_refs'].values(),*draft['original_refs'],*draft['desired_refs']])
    for key in ['register','wrapper','prepared_refs','audit']:
        ref=bundle['registration_code_and_draft_refs'][key]; r.verify(ref)
        need(reg[key+'_sha256']==ref['sha256'], 'REGISTRATION_REVIEW_FULL_PINS')
    need(reg['copied_canonical_before_refs'] and len(reg['copied_canonical_before_refs'])==4, 'REVIEW_FOUR_ORIGINALS')
    for ref,b in zip(reg['copied_canonical_before_refs'],originals):
        need(safe(ref['path']).parent==safe(regref['path']).parent and r.verify(ref)==b, 'INDEPENDENT_ORIGINAL_COPY')
    need(audit['actor']=='codex:/root' and audit['status']=='ACTUAL_CANONICAL_REGISTRATION_CLOSED_NO_CASE_ACCEPTANCE' and
         audit['before']==a['before'] and audit['after']==a['after'] and audit['actual_registration_exit']==0 and
         same_ref(audit['intent_ref'],bundle['intent_ref']) and same_ref(audit['invocation_ref'],bundle['invocation_ref']) and
         same_ref(audit['verified_ref'],bundle['verified_ref']) and same_ref(audit['review_ref'],regref), 'SEALED_REGISTRATION_AUDIT')
    need(inv['actor']=='codex:/root' and inv['actual_exit']==0 and inv['wrapper_error'] is None and
         inv['automatic_retry'] is False and inv['counter_reset'] is False and same_ref(inv['review_ref'],regref), 'ACTUAL_REGISTRATION_INVOCATION')
    job(inv['result'])
    need(inv['runner_sha256']==reg['register_sha256'] and inv['wrapper_sha256']==reg['wrapper_sha256'],
         'ACTUAL_REGISTRATION_PROGRAM_PINS')
    resources=r.doc(s['resource_catalog_ref']);codes=bundle['registration_code_and_draft_refs']
    expected_argv=[resources['python']['path'],'-I','-S','-X','utf8',codes['register']['path'],
         '--registration-draft',bundle['draft_ref']['path'],'--draft-sha256',bundle['draft_ref']['sha256'],
         '--registration-review',regref['path'],'--review-sha256',regref['sha256'],
         '--output-root',str(regout)]
    request=r.doc(bundle['requested_ref'])
    need(request=={'schema':'researchos.driver18-registration-request.v1','actor':'codex:/root',
         'argv':expected_argv,'cwd':str(ROOT),'env':s['public_environment'],
         'timeout':a['registration_timeout_seconds'],'current_scope_ref':sref,
         'registration_draft_ref':bundle['draft_ref'],'review_ref':regref,
         'stdout_ref_path':bundle['stdout_ref']['path'],'stderr_ref_path':bundle['stderr_ref']['path'],
         'automatic_retry':False,'counter_reset':False},'FULL_REGISTRATION_REQUEST')
    need(inv['argv']==expected_argv and inv['cwd']==str(ROOT) and
         same_ref(inv['requested_ref'],bundle['requested_ref']) and
         same_ref(inv['registration_draft_ref'],bundle['draft_ref']) and same_ref(inv['current_scope_ref'],sref) and
         inv['env']==request['env'] and inv['timeout']==request['timeout'], 'ACTUAL_REGISTRATION_ARGV')
    wrapper=r.doc(bundle['wrapper_invocation_ref'])
    need(wrapper['actor']=='codex:/root' and wrapper['argv']==[
         resources['python']['path'],'-I','-S','-X','utf8',codes['wrapper']['path'],
         '--request',bundle['requested_ref']['path'],'--request-sha256',bundle['requested_ref']['sha256']] and
         wrapper['cwd']==str(ROOT) and wrapper['env']==s['public_environment'] and
         same_ref(wrapper['requested_ref'],bundle['requested_ref']) and
         same_ref(wrapper['inner_invocation_ref'],bundle['invocation_ref']) and
         wrapper['automatic_retry'] is False and wrapper['counter_reset'] is False,
         'ACTUAL_WRAPPER_FULL_REQUEST_PAIR')
    job(wrapper['result'])
    for obj in [intent,audit,verified]:
        need(same_ref(obj['current_scope_ref'],sref) and same_ref(obj['registration_draft_ref'],bundle['draft_ref']) and
             same_ref(obj['requested_ref'],bundle['requested_ref']), 'CAS_ENVELOPE_CURRENT_PAIR')
    need(same_ref(audit['wrapper_invocation_ref'],bundle['wrapper_invocation_ref']) and
         same_ref(audit['draft_manifest_ref'],bundle['draft_manifest_ref']), 'AUDIT_WRAPPER_AND_DRAFT')
    for key in ['stdout_ref','stderr_ref','invocation_ref','requested_ref','wrapper_invocation_ref',
                'audit_ref','intent_ref','verified_ref','manifest_ref']:
        safe(bundle[key]['path'],regout)
    for key in ['stdout','stderr']:
        raw=r.verify(bundle[key+'_ref']);need(hashlib.sha256(raw).hexdigest()==inv[key+'_sha256'],'REGISTRATION_RAW')
    need([verified['checkpoint'],verified['ownership'],verified['failure_origins']]==a['after'] and
         verified['step_state_commands_unchanged'] is True and same_ref(verified['intent_ref'],bundle['intent_ref']), 'POST_CAS_VERIFIED')
    copies=bundle['canonical_after_copies']; need([x['canonical_path'] for x in copies]==CANON,'ORDERED_CANONICAL_COPIES')
    for item,b in zip(copies,desired):need(r.verify(item['ref'])==b,'ACTUAL_DESIRED_COPY')
    member_manifest(r,bundle['manifest_ref'],[bundle[k] for k in ['draft_ref','draft_manifest_ref','audit_ref','intent_ref','invocation_ref','requested_ref','wrapper_invocation_ref','verified_ref','stdout_ref','stderr_ref']]+list(bundle['registration_code_and_draft_refs'].values())+[regref]+draft['original_refs']+draft['desired_refs']+[x['ref'] for x in copies])
    return desired

def outer_completion(r, ref, s, sref, gref, phase):
    d=r.doc(ref); raw=r.doc(d['tool_result_ref'])
    original=r.doc(d['outer_invocation_ref']);initial=r.doc(original['tool_initial_result_ref'])
    need(original['schema']=='researchos.driver18-root-outer-invocation.v1' and
         original['actor']=='codex:/root' and original['cwd']==str(ROOT) and
         original['argv']==d['argv'] and original['run_uuid']==s['actual_Root_registration']['run_uuid'] and
         same_ref(original['scope_ref'],sref) and same_ref(original['grant_ref'],gref) and
         original['launcher_output_root']==s[phase+'_launcher_output_root'] and
         original['inner_output_root']==s[phase+'_output_root'] and
         type(initial['session_id']) is int and initial['session_id']==original['session_id']==d['session_id'] and
         initial.get('exit_code') is None and d['tool_completion_session_id']==d['session_id'],
         'ORIGINAL_OUTER_INVOCATION_COMPLETION_PAIR')
    need(d['actual_native_launcher_exit'] is None,'UNSAMPLED_OUTER_NATIVE_REMAINS_NULL')
    need(d['schema']=='researchos.driver18-root-outer-completion.v1' and d['actor']=='codex:/root' and
         d['phase']==phase and zero(d['actual_outer_exit']) and zero(raw['exit_code']) and
         d['automatic_retry'] is False and d['counter_reset'] is False, 'FINAL_OUTER_TOOL_RESULT')
    need(d['actual_native_launcher_exit'] is None or d['actual_native_launcher_exit']==0,'NO_NATIVE_FAILURE')
    need(d['run_uuid']==s['actual_Root_registration']['run_uuid'] and d['launcher_ref']==s['launcher_ref'], 'OUTER_BINDING')
    res=r.doc(s['resource_catalog_ref']);argv=d['argv']
    need(len(argv)==11 and safe(argv[0])==safe(res['python']['path']) and argv[1:5]==['-I','-S','-X','utf8'] and
         safe(argv[5])==safe(s['launcher_ref']['path']) and argv[6]==phase and
         safe(argv[7])==safe(sref['path']) and argv[8]==sref['sha256'] and
         safe(argv[9])==safe(gref['path']) and argv[10]==gref['sha256'] and
         same_ref(d['scope_ref'],sref), 'ACTUAL_OUTER_ARGV')

def prepared_evidence(r, s, proof):
    psref=proof['prepare_scope_ref']; ps=scope(r,psref)
    need(ps['actual_Root_registration']['phase']=='prepare', 'ACTUAL_PREPARE_SCOPE')
    pgref=proof['prepare_grant_ref']; pg=r.doc(pgref)
    verify_authority(r,ps,psref,pg,allow_execute=False)
    for k in ['work_root','prepare_output_root','prepare_launcher_output_root','fixed_inputs_ref','resource_catalog_ref']:
        need(ps[k]==s[k], 'PREPARE_EXECUTE_SAME_INPUTS')
    prepared=r.doc(s['prepared_ref']);need(same_ref(proof['prepared_ref'],s['prepared_ref']),'EXACT_PREPARED_OUTPUT')
    work=safe(s['work_root']);inner=safe(ps['prepare_output_root']);outer=safe(ps['prepare_launcher_output_root'])
    locations={'prepared_ref':(inner,'prepared.json'),'inner_result_ref':(inner,'result.json'),
        'inner_manifest_ref':(inner,'manifest.json'),'launcher_invocation_ref':(outer,'inner.invocation.json'),
        'launcher_requested_ref':(outer,'requested.json'),'launcher_completed_ref':(outer,'completed.json'),
        'launcher_manifest_ref':(outer,'manifest.json'),'launcher_stdout_ref':(outer,'stdout.raw'),
        'launcher_stderr_ref':(outer,'stderr.raw')}
    for key,(root,name) in locations.items():exact_location(proof[key],root,name)
    need(prepared['work_root']==s['work_root'] and prepared['fixed_inputs_ref']==s['fixed_inputs_ref'] and
         prepared['resource_catalog_ref']==s['resource_catalog_ref'] and zero(prepared['actual_Go_calls']) and
         prepared['I17']=='FATAL_OPEN' and prepared['all18']=='NOT_RUN' and
         same_ref(prepared['root_preparation_grant_ref'],pgref), 'PREPARED_RESULT')
    fixed=r.doc(s['fixed_inputs_ref']);resources=r.doc(s['resource_catalog_ref']);expected={}
    def add(relative,source):
        p=safe(str(work/relative),work);key=path_key(p)
        need(key not in expected,'PREPARED_DESTINATION_COLLISION');r.verify(source)
        expected[key]={'path':str(p),'sha256':source['sha256'],'bytes':source['bytes']}
    for key,base in [('fork_lock_ref',Path('fork')),('original_lock_ref',Path('modcache/modernc.org/sqlite@v1.60.1'))]:
        rows=r.doc(fixed[key])['files'];need(len(rows)==1899,'EXPECTED_COMPLETE_MODULES')
        for row in rows:add(base/row['relative_path'],{k:row[k] for k in ['path','sha256','bytes']})
    for row in resources['offline_modcache_copies']:add(Path('modcache')/row['relative_path'],row['ref'])
    mappings=[('test_source_ref','fork/driver18_innocuous_test.go'),('surface_ref','consumer/surface.go'),
              ('producer_ref','consumer/cmd/i16fixture/main.go'),('probe_ref','old-probe/main.go'),
              ('consumer_mod_ref','consumer/go.mod'),('sum_ref','consumer/go.sum'),
              ('old_mod_ref','old-probe/go.mod'),('sum_ref','old-probe/go.sum')]
    need(prepared['source_overlays']==[list(x) for x in mappings],'EXACT_PREPARED_OVERLAYS')
    for key,destination in mappings:add(Path(destination),fixed[key])
    rows=prepared['files'];need(isinstance(rows,list) and rows and len(rows)==len(expected),'NONEMPTY_FULL_PREPARED_FILES')
    seen=set()
    for ref in rows:
        p=safe(ref['path'],work);key=path_key(p)
        need(key not in seen and key in expected and same_ref(ref,expected[key]),'PREPARED_EXACT_MEMBER');seen.add(key);r.verify(ref)
    need(seen==set(expected)==set(tree_files(work)),'ACTUAL_PREPARED_COMPLETE_MEMBERSHIP')
    result=r.doc(proof['inner_result_ref'])
    need(result['phase']=='prepare' and result['first_cause'] is None and result['secondary']==[] and
         zero(result['native_calls']) and result['all18_pass'] is False and result['source_acceptance'] is False and
         result['counter_reset'] is False and result['roster']==[
             {'id':f'I{i:02d}','status':'NOT_STARTED','actual_exit':None,'qualified':False} for i in range(1,19)],
         'EXACT_PREPARE_18_ROSTER_NOT_PASS')
    need(all(x['qualified'] is False and x['actual_exit'] is None for x in result['roster']), 'STRICT_ROSTER_TYPES')
    inv=r.doc(proof['launcher_invocation_ref']);job(inv['result']);need(zero(inv['actual_native_exit']),'ACTUAL_PREPARE_NATIVE')
    req=r.doc(proof['launcher_requested_ref']);res=r.doc(ps['resource_catalog_ref'])
    need(req=={'argv':[res['python']['path'],'-I','-S','-X','utf8',ps['controller_ref']['path'],
         'prepare',psref['path'],psref['sha256'],pgref['path'],pgref['sha256']],
         'cwd':str(ROOT),'timeout':3600,'automatic_retry':False,'env':ps['public_environment']},
         'ORIGINAL_PREPARE_CHILD_REQUEST')
    for key in ['launcher_stdout_ref','launcher_stderr_ref']:r.verify(proof[key])
    done=r.doc(proof['launcher_completed_ref']);need(zero(done['reported_exit']) and done['error'] is None and
         done['secondary']==[] and done['source_acceptance'] is False,'PREPARE_COMPLETION')
    pair=r.doc(proof['launcher_pairing_ref'])
    need(pair=={'schema':'researchos.driver18-root-sealed-launcher-pair.v1','actor':'codex:/root',
         'scope_ref':psref,'grant_ref':pgref,'launcher_ref':ps['launcher_ref'],
         'controller_ref':ps['controller_ref'],'launcher_output_root':str(outer),'inner_output_root':str(inner),
         'requested_ref':proof['launcher_requested_ref'],'invocation_ref':proof['launcher_invocation_ref'],
         'stdout_ref':proof['launcher_stdout_ref'],'stderr_ref':proof['launcher_stderr_ref'],
         'completed_ref':proof['launcher_completed_ref'],'outer_completion_ref':proof['outer_completion_ref'],
         'launcher_manifest_ref':proof['launcher_manifest_ref'],'inner_manifest_ref':proof['inner_manifest_ref'],
         'prepared_ref':s['prepared_ref'],'inner_result_ref':proof['inner_result_ref'],
         'actual_child_pid':inv['result']['owned_child_pid'],'creation_time_100ns':inv['result']['creation_time_100ns'],
         'actual_native_exit':inv['actual_native_exit'],'automatic_retry':False,'counter_reset':False},
         'ROOT_ORIGINAL_LAUNCHER_PAIR')
    outer_completion(r,proof['outer_completion_ref'],ps,psref,pgref,'prepare')
    complete_manifest(r,proof['inner_manifest_ref'],inner,[s['prepared_ref'],proof['inner_result_ref']])
    complete_manifest(r,proof['launcher_manifest_ref'],outer,[proof[k] for k in
        ['launcher_invocation_ref','launcher_completed_ref','launcher_requested_ref','launcher_stdout_ref','launcher_stderr_ref']])

def verify_authority(r,s,sref,g,allow_execute=True):
    a=s['actual_Root_registration'];need(g['schema']=='researchos.driver18-root-phase-grant.v1' and
         g['actor']=='codex:/root' and g['actual_registration_completed'] is True and
         g['phase']==a['phase'] and g['run_uuid']==a['run_uuid'] and same_ref(g['scope_ref'],sref) and
         g['automatic_retry'] is False and g['counter_reset'] is False, 'ACTUAL_ROOT_PHASE_GRANT')
    safe(g['registration_evidence_ref']['path'],safe(a['registration_namespace']))
    desired=registration(r,s,sref,r.doc(g['registration_evidence_ref']))
    need([x['canonical_path'] for x in g['canonical_snapshot_refs']]==CANON,'GRANT_FOUR_ORDER')
    for item,raw in zip(g['canonical_snapshot_refs'],desired):need(r.verify(item['ref'])==raw,'GRANT_SNAPSHOT_BYTES')
    need(g['authority_code_refs']=={k:s[k] for k in FIXED}|{'authority_validator_ref':s['authority_validator_ref']},'EXACT_AUTHORITY_CODE')
    # These are Root-produced actual read-only source-guard receipts. Reader
    # validates their strict schema, original raw refs and explicit head/status.
    facts=r.doc(g['root_source_guard_ref']);want=a['source_guard_expected']
    need(facts['schema']=='researchos.driver18-root-source-guard.v1' and facts['actor']=='codex:/root' and
         facts['run_uuid']==a['run_uuid'] and facts['main_git']==want and facts['canonical_refs']==g['canonical_snapshot_refs'], 'SOURCE_GUARD_BINDING')
    for name in ['head','status','index']:
        f=facts['git'][name];job(f['result']);raw=r.verify(f['stdout_ref']);r.verify(f['stderr_ref'])
        gitref=a['source_guard_git_ref'];r.verify(gitref)
        suffix={'head':['rev-parse','HEAD'],'status':['status','--porcelain=v1','--untracked-files=no'],
                'index':['diff','--cached','--name-only']}[name]
        need(f['argv']==[gitref['path'],'-C',str(ROOT),*suffix], 'EXACT_READONLY_GIT_ARGV')
        if name=='head':need(raw.decode('ascii').strip()==want['head'],'ACTUAL_HEAD')
        if name=='status':need(hashlib.sha256(raw).hexdigest()==want['status_sha256'] and len(raw)==want['status_bytes'],'ACTUAL_STATUS')
        if name=='index':need(raw==b'' and want['index_empty'] is True,'ACTUAL_EMPTY_INDEX')
    if a['phase']=='execute':
        need(allow_execute and g['prepared_evidence'] is not None,'EXECUTE_PHASE_EVIDENCE')
        prepared_evidence(r,s,g['prepared_evidence'])
    else:need(g['prepared_evidence'] is None and s['prepared_ref'] is None,'PREPARE_NO_FUTURE_FACTS')

def validate_grant(scope_path,scope_sha256,grant_path,grant_sha256):
    r=Reader();sref,s=r.actual(scope_path,scope_sha256);s=scope(r,sref)
    gref,g=r.actual(grant_path,grant_sha256)
    verify_authority(r,s,sref,g)
    # All reads above are immutable copies/receipts, never live canonical reads.
    r.unchanged()
    return {'scope':s,'phase':g['phase'],'actor':'codex:/root',
            'actual_registration_completed':True,'authorization_input_refs':list(r.refs.values()),
            'source_acceptance':False,'I17':'OPEN_NOT_AUTHORIZED'}
