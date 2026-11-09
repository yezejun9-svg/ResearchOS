import sys
sys.dont_write_bytecode = True
import json, hashlib, types, collections, re
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'
A = B / 'integration_codex/current-attach-q5-leg2-targeted-root-1791510290800'
C = R / '.local/current-attach-q5-leg2-run-env-1791510290800/typed-child-evidence'
O = Path(__file__).resolve().parent
issues, checks, references, copied = [], [], {}, []

def raw(p): return Path(p).read_bytes()
def read(p): return json.loads(raw(p))
def pin(p):
    p = Path(p).resolve(); data = raw(p)
    return {'path': str(p), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
def save(name, obj):
    p = O / name; p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f: f.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(p)
def check(name, condition, detail=None):
    checks.append({'check': name, 'passed': bool(condition), 'detail': detail})
    if not condition: issues.append(checks[-1])
def verify(ref, origin):
    p = ref.get('path', ref.get('resolved_path'))
    if not p: return
    expected = {'path': str(Path(p).resolve()), 'sha256': ref['sha256'].removeprefix('sha256:'), 'bytes': ref['bytes']}
    try: actual = pin(p)
    except Exception as e:
        check('reference-readable', False, {'origin': origin, 'expected': expected, 'error': repr(e)}); return
    check('exact-reference', actual == expected, {'origin': origin, 'expected': expected, 'actual': actual} if actual != expected else None)
    key = expected['path'].casefold()
    if key in references: check('consistent-reference', references[key] == expected, origin)
    else: references[key] = expected
def walk(obj, origin, skip_canonical=True):
    if isinstance(obj, dict):
        if 'sha256' in obj and 'bytes' in obj and ('path' in obj or 'resolved_path' in obj):
            p = Path(obj.get('path', obj.get('resolved_path'))).resolve()
            if skip_canonical and p.parent == R / 'execution/v2.4' and p.name in ('checkpoint.json', 'commands.json', 'step_state.json', 'path_ownership.json'): return
            verify(obj, origin)
        else:
            for k, v in obj.items(): walk(v, origin + '/' + k, skip_canonical)
    elif isinstance(obj, list):
        for i, v in enumerate(obj): walk(v, origin + '/' + str(i), skip_canonical)
def copy(p, category, base):
    dest = O / 'originals' / category / Path(p).relative_to(base)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('xb') as f: f.write(raw(p))
    copied.append({'source': pin(p), 'copy': pin(dest)})
def events(data, label, expected_parents, expected_leaves=None):
    ev = [json.loads(line) for line in data.decode('utf-8').splitlines()]
    runs, terms = collections.Counter(), collections.defaultdict(list)
    for x in ev:
        check(label + ':package', x.get('Package') == 'researchos.local/research-os/internal/domain')
        t, a = x.get('Test'), x.get('Action')
        if t and a == 'run': runs[t] += 1
        if t and a in ('pass', 'fail', 'skip'): terms[t].append(a)
    check(label + ':exact-start-terminal-set', set(runs) == set(terms))
    check(label + ':single-runs-terminals', all(v == 1 for v in runs.values()) and all(len(v) == 1 for v in terms.values()))
    check(label + ':exact-parents', {n for n in runs if '/' not in n} == set(expected_parents))
    check(label + ':no-orphan-child', all(n.split('/')[0] in expected_parents for n in runs))
    if expected_leaves is not None:
        expected = set(expected_parents) | set(expected_leaves)
        check(label + ':exact-child-cardinality', set(runs) == expected, {'expected': sorted(expected), 'observed': sorted(runs)})
    pkgterm = [x for x in ev if not x.get('Test') and x['Action'] in ('pass', 'fail', 'skip')]
    check(label + ':package-start-terminal', sum(x['Action'] == 'start' and not x.get('Test') for x in ev) == 1 and len(pkgterm) == 1 and ev[-1] == pkgterm[0])
    action = {n: v[0] for n, v in terms.items()}
    for n, a in action.items():
        if a == 'fail' and '/' in n: check(label + ':failure-rollup', action[n.rsplit('/', 1)[0]] == 'fail')
    return {'line_count': len(ev), 'runs': dict(runs), 'actions': action, 'counts': dict(collections.Counter(action.values())), 'package_terminal': pkgterm, 'outputs': [x for x in ev if x.get('Action') == 'output']}

choice, closed = read(A/'source.integration.choice.json'), read(A/'validation.closed.json')
check('choice-pin', pin(A/'source.integration.choice.json')['sha256'] == '8fee24f844dbb06581ea15b7f8665844ce4335fc93a0532d096433a810cea343' and pin(A/'source.integration.choice.json')['bytes'] == 5610)
check('closed-pin', pin(A/'validation.closed.json')['sha256'] == '1f5bbf0fd7ac125875059c4e6e516dfd7419548283ab330cc965b21af58f0593' and pin(A/'validation.closed.json')['bytes'] == 39787)
for p in sorted(A.iterdir()):
    if p.is_file():
        verify(pin(p), 'A9-original'); copy(p, 'A9', A)
        if p.suffix == '.json': walk(read(p), p.name)
for p in sorted(C.rglob('*')):
    if p.is_file():
        verify(pin(p), 'nested-original'); copy(p, 'children', C)
        if p.suffix == '.json': walk(read(p), str(p.relative_to(C)))
source_manifests = []
for comp in choice['source_components']:
    for key in ('source_handoff','source_manifest','independent_handoff','independent_manifest'):
        ref=comp[key]; walk(ref, comp['component']+'/'+key)
        p=Path(ref['path']); copy(p, comp['component']+'-'+key, p.parent)
        if key.endswith('manifest'):
            mf=read(p); walk(mf['members'], comp['component']+'/'+key+'/members')
            source_manifests.append({'component':comp['component'],'kind':key,'type':type(mf['members']).__name__,'members':len(mf['members'])})
oldp = Path(choice['base_current49']); old=read(oldp); verify(pin(oldp), 'old-actual'); copy(oldp,'old-actual',oldp.parent)
check('base-current49-pin', pin(oldp)['sha256']=='d2fd6c15fcdb727fff91aa7bd3c53275230ebc42bd2017a544ff8f17becfb113')
canonical = read(A/'canonical.pre-run.exact.json')
canonical_observed=[]
for ref in canonical['refs']:
    observed=pin(ref['path']); canonical_observed.append({'expected_run':ref,'observed_short_read':observed})
save('canonical.short-read.json', {'revision_at_run':361,'observations':canonical_observed,'not_held_for_review':True})

gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gpraw=raw(gp)
check('guard-code-pin',hashlib.sha256(gpraw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85')
verify(pin(gp),'guard-code')
mod=types.ModuleType('independent_actual_source_guard'); mod.__file__=str(gp);sys.modules[mod.__name__]=mod
exec(compile(gpraw,str(gp),'exec'),mod.__dict__)
guard=mod.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
guard.acquire(list(references.values()))
try:
    parsed=events(guard.get_buffer(str(A/'current-attach-q5-leg2-parent-jsonl.stdout.raw')),'root',closed['exact_parent_names'])
    check('root-actions-exact',parsed['actions']==closed['actions'])
    check('root-starts-exact',set(parsed['runs'])==set(closed['started_names']))
    check('root-counts',parsed['counts']=={'pass':152,'fail':5} and len(closed['exact_parent_names'])==54)
    check('root-package-fail',parsed['package_terminal'][0]['Action']=='fail')
    base25=old['exact_25_parent_names']
    check('old25-all-pass',len(base25)==25 and all(parsed['actions'].get(n)=='pass' for n in base25))
    oldfailed=[n for n,a in old['actions'].items() if a=='fail']
    check('old-six-failures-now-pass',len(oldfailed)==6 and all(parsed['actions'].get(n)=='pass' for n in oldfailed))
    failnames=[n for n,a in parsed['actions'].items() if a=='fail']
    failoutput=[x for x in parsed['outputs'] if x.get('Test') in failnames]
    children=[]
    for d in sorted(p for p in C.iterdir() if p.is_dir()):
        inv,res,ver,par=[read(d/n) for n in ('child-invocation.json','child-result.json','child-event-verdict.json','parent-result.json')]
        data=raw(d/'child.stdout.jsonl'); cp=events(data,d.name,[d.name],inv['leaf_cases'])
        check(d.name+':stdout-raw-equality',data==raw(d/'child.stdout.raw'))
        check(d.name+':stdout-pin',hashlib.sha256(data).hexdigest()==res['stdout_hash'].removeprefix('sha256:')==ver['stdout_hash'].removeprefix('sha256:') and len(data)==res['stdout_bytes'])
        check(d.name+':stderr-pin',hashlib.sha256(raw(d/'child.stderr.raw')).hexdigest()==res['stderr_hash'].removeprefix('sha256:') and len(raw(d/'child.stderr.raw'))==res['stderr_bytes']==0)
        check(d.name+':all-pass',all(a=='pass' for a in cp['actions'].values()) and cp['package_terminal'][0]['Action']=='pass')
        vt=ver['events']['tests']
        check(d.name+':verdict-exact',set(vt)==set(cp['actions']) and all(v['run_count']==v['terminal_count']==1 and v['terminal_action']==cp['actions'][n] for n,v in vt.items()) and ver['events']['line_count']==cp['line_count'])
        check(d.name+':producer-result',res['actual_runner_exit']==0 and res['child_jsonl_verified'] and res['resources_stable'] and par['child_assertions_passed'])
        check(d.name+':producer-pin',inv['tool_resources']['compiled_child']['sha256'].removeprefix('sha256:')==closed['compiled_test_ref']['sha256'])
        check(d.name+':parent-binding',parsed['actions'][d.name]=='pass' and all(obj['case']==d.name for obj in (inv,res,par)))
        check(d.name+':no-extra-authority',all(obj['formal_acceptance'] is False for obj in (inv,res,ver,par)) and inv['provider_kind']=='SYNTHETIC_LOOPBACK_TLS')
        children.append({'case':d.name,'line_count':cp['line_count'],'actions':cp['actions'],'runner_exit':res['actual_runner_exit'],'actual_native_child_exit':res['actual_native_child_exit'],'actual_native_child_pid':res['actual_native_child_pid'],'native_reconciliation':res['native_child_reconciliation'],'parent_exit':par['actual_parent_exit'],'producer':inv['tool_resources']})
    check('six-nested-producers',len(children)==6)
    jobs=[]
    for ref in closed['invocation_refs']:
        j=read(ref['path']);r=j['result'];cl=r['job_cleanup']
        ok=all(cl[k] for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')) and cl['active_processes_last_observed']==0 and not cl['errors'] and not r['timed_out'] and r['error'] is None
        check(Path(ref['path']).name+':owned-job-closure',ok)
        check('FILETIME-is-exact-int',type(r['creation_time_100ns']) is int)
        jobs.append({'receipt':ref,'exit':r['actual_exit'],'creation_time_100ns':str(r['creation_time_100ns']),'closure':cl})
    check('four-owned-jobs',len(jobs)==4 and [j['exit'] for j in jobs]==[0,0,0,1])
    guards=[]
    for p in sorted(A.glob('*-source-guard.cleanup.actual.json')):
        g=read(p);ok=g['closed'] and not g['errors'] and g['retained_handles_count']==0 and g['verification']=='PASSED' and all(x['verified'] and x['closed'] and x['final_path_match'] for x in g['entries'])
        check(p.name+':guard-closure',ok);guards.append({'name':p.name,'entries':len(g['entries']),'closed_verified':ok})
    check('five-guards',len(guards)==5)
    fo=read(A/'failure-origin.871.json')
    check('root-exits-one',fo['actual_outer_exit']==fo['actual_python_exit']==fo['actual_native_exit']==1)
    check('original-python-exit-not-masked',any(e['result'].get('exit_code')==1 and 'ROOT_PYTHON_EXIT=1' in e['result'].get('output','') for e in fo['entries']))
    source=read(A/'source-overlay.json');formatted=read(A/'formatted.source-members.json');inventory=read(A/'actual-tagged-compiler-input-inventory.json')
    check('source-58-exact',source['Source_count']==len(source['sources'])==len(formatted)==closed['source_count']==58)
    producerpaths={r['path'].casefold() for r in inventory['build_inputs']+inventory['product_inventory']}
    check('formatted-in-compiler-inventory',all(r['path'].casefold() in producerpaths for r in formatted))
    inv=read(A/'current-attach-q5-leg2-parent-jsonl.invocation.json')
    check('invocation-54-exact-selector',inv['argv'][6]=='-test.run=^('+'|'.join(closed['exact_parent_names'])+')$')
    bindings={}
    for k in ('RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE','RESEARCHOS_TEST2JSON','RESEARCHOS_GO'):
        p=inv['public_environment'][k];bindings[k]=references.get(str(Path(p).resolve()).casefold());check('environment-resource-bound:'+k,bindings[k] is not None)
    summary={'status':'INDEPENDENT_ACTUAL_EVIDENCE_ACCEPTED_WITH_REAL_FAILURES' if not issues else 'INDEPENDENT_EVIDENCE_REVIEW_FINDINGS','accepted_scope':'A9 exact actual passed/failed originals and execution closure only','Root_product_acceptance':False,'formal_acceptance':False,'full_domain_accepted':False,'formal42_accepted':False,'parent22_accepted':False,'native_migration_accepted':False,'original_paid_business_accepted':False,'root_counts':parsed['counts'],'root_unique_test_count':len(parsed['actions']),'root_parent_count':54,'root_failed_parents':[n for n in failnames if '/' not in n],'failed_terminals':failnames,'failure_outputs':failoutput,'base25_all_pass':base25,'old_six_now_pass':oldfailed,'children':children,'jobs':jobs,'guards':guards,'source_manifests':source_manifests,'resource_bindings':bindings,'canonical_short_read_only':True,'ordinary_historical_program_authority':'BLOCKED','child_native_identity_limit':'Individual child native PID/exit are null; six official test2json runner exits and exact child JSONL pass are observed, descendant closure comes only from Root exclusive Job receipt.','new_test_execution':False,'external_model_requests':0,'native_execution':False,'issue_count':len(issues),'issues':issues,'checks':checks,'verified_reference_count':len(references)}
    save('report.json',summary)
    save('verified-inputs.json',list(references.values()))
    save('originals.index.json',copied)
finally:
    cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
print(json.dumps({'status':summary['status'],'issue_count':len(issues),'reference_count':len(references),'checks':len(checks),'children':[{'case':x['case'],'actions':x['actions'],'lines':x['line_count']} for x in children],'failures':summary['failed_terminals'],'guard_closed':cleanup['closed']},ensure_ascii=False))
