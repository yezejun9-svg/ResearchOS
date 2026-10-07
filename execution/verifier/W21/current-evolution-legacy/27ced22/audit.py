"""W21 R04 read-only source/public-receipt audit. Never executes a test/helper."""
from pathlib import Path
import hashlib, json, subprocess, re, datetime

out=Path(__file__).resolve().parent
root=out.parents[4]
target='27ced22e73da7631d65bdd6e1844de24dd198065'
control='36956330065ef7dc9e91005850ee19e1dea69a48'
inputs={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def bytes_read(p):
    p=Path(p);b=p.read_bytes();inputs[p.relative_to(root).as_posix()]={'sha256':sha(b),'bytes':len(b)};return b
def read(p):return json.loads(bytes_read(p).decode('utf-8'))
def text_read(p):return bytes_read(p).decode('utf-8')
def write(name,d): (out/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def gitblob(revision,path):
    r=subprocess.run(['git','show',revision+':'+path],cwd=root,capture_output=True)
    return r.stdout if r.returncode==0 else None
def local_public(s):
    # Archived Windows strings sometimes contain doubled separators. Never follow private locators.
    s=s.replace('\\','/');s=re.sub('/+','/',s)
    marker='/execution/'
    if marker in s:s='execution/'+s.split(marker,1)[1]
    assert s.startswith('execution/') and '..' not in Path(s).parts,s
    p=(root/s).resolve();assert p.is_relative_to(root)
    return p

matrix=read(root/'execution/verifier/W21/final-index-version-audit/f510491/reuse-matrix.json')
cases={c['case']:c for c in matrix['cases'] if c['case'] in ['C10','C12','C20']}
frozen={c['id']:c for c in read(root/'spec/v2.0/contracts/acceptance.json')['cases']}
old_cases={};old_reports={};commands=[]
for cid,rid in [('C10','163c0536-0805-4932-81df-d765a88fe57d'),('C12','163c0536-0805-4932-81df-d765a88fe57d'),('C20','5402da3d-e835-42d6-8b5f-168b941158dc')]:
    p=root/f'execution/receipts/W16/{rid}/{cid}.json';case=read(p);old_cases[cid]=case
    verifier=read(root/f'execution/verifier/W16/{rid}.json')
    assert case['version_manifest']['git_head']==cases[cid]['accepted_revision']
    for a in case['assertion_results']:
        assert a['status']=='PASS'
        assert a['expected']==next(x['expected'] for x in frozen[cid]['assertions'] if x['id']==a['assertion_id'])
    for cmd in case['command_receipt']:
        invpath=root/cmd['reference'];assert sha(bytes_read(invpath))==cmd['sha256'].removeprefix('sha256:')
        inv=read(invpath);assert inv['exit_code']==0 and inv['command_key']==cmd['command_key']
        for k in ['stdout','stderr']:
            assert sha(bytes_read(root/cmd[k]['path']))==cmd[k]['sha256'].removeprefix('sha256:')
        entry=json.loads(text_read(root/cmd['stdout']['path']))
        reportpath=local_public(entry['receipt']);report=read(reportpath)
        # Only public report + adjacent stdout/stderr/before metadata. No private locator is opened.
        rawpath=reportpath.parent/'stdout.txt'
        raw=text_read(rawpath) if rawpath.exists() else None
        if raw is not None:
            listed=report.get('hashes',{}).get('stdout.txt')
            if listed:assert sha(rawpath.read_bytes())==listed.removeprefix('sha256:')
        beforepath=reportpath.parent/'before.json'
        before=read(beforepath) if beforepath.exists() else {}
        old_reports[cmd['reference']]={'report':report,'path':reportpath,'raw':raw,'before':before}
        commands.append({'case':cid,'command_key':cmd['command_key'],'invocation':cmd['reference'],
            'historical_revision':cmd['code_revision'],'historical_exit_code':inv['exit_code'],
            'public_report':reportpath.relative_to(root).as_posix(),
            'historical_assertion_ids':entry['assertion_ids'],
            'native_command':before.get('command_receipt',{}).get('argv'),
            'execution_in_this_review':False})

controlbase=root/'execution/verifier/W16/current-control-admission/3695633'
manifest=read(controlbase/'manifest.json')
# Hash only explicitly public review artifacts; do not walk a protected store.
for name in ['review.md','readonly-result.json','readonly-test-04.log','public-binding-audit.json']:
    b=bytes_read(controlbase/name);assert sha(b)==manifest[name].removeprefix('sha256:')
control_result=read(controlbase/'readonly-result.json')
assert control_result['private_proof_recomputed']['gain'] is False
assert control_result['public_proof_recomputed']['gain'] is False
assert control_result['normal_gate']=='REJECTED' and control_result['experiment_outcome']=='NO_IMPROVEMENT'
assert control_result['current_owner_now']=='UNVERIFIED_STOPPED'
control_raw=text_read(controlbase/'readonly-test-04.log')
assert '--- PASS: TestIndependentCurrentPersistedReview' in control_raw
integrationpath=root/'execution/receipts/W16/current-control-admission/root-integration-4528561/report.json'
integration=read(integrationpath)
assert integration['source_commit']==control and integration['normal_release_authorized'] is False
integration_comparison=[]
for p,h in integration['source_files'].items():
    current=bytes_read(root/p)
    integration_comparison.append({'path':p,'integration_sha256':h,'current_sha256':sha(current),'unchanged':h==sha(current)})
targetedpath=root/'execution/receipts/W16/current-control-admission/final-targeted-tests.log'
targeted=text_read(targetedpath)
targeted_passes=re.findall(r'^--- PASS: (\S+)',targeted,re.M)
assert 'TestControlCurrentPreparationRejectsAuthorityDrift' in targeted_passes
assert 'TestControlCurrentGoTestCannotOwnAuthority' in targeted_passes
# The existing current R08 evidence is a generic independence subset, not C10 native tamper coverage.
r08path=root/'execution/receipts/W21/current-domain-delta/27ced22/report.json'
r08report=read(r08path);r08=r08report['groups']['R08']
r08raw=root/'execution/receipts/W21/current-domain-delta/27ced22/R08/stdout.jsonl'
assert sha(bytes_read(r08raw))==r08['stdout_sha256']
r08_ids=[a['assertion_id'] for a in r08['assertions'] if a['assertion_id'].startswith('W06-G01-INDEPENDENCE') and a['status']=='PASS']
assert len(r08_ids)==3

# Bounded direct/source-call inventory: explicit paths, never represented as a transitive closure.
paths=set()
for c in cases.values():paths.update(c['direct_production_changed_paths']);paths.update(c['shared_scope_changed_paths'])
for pattern in ['internal/domain/evolution*.go','evaluation/evolution/*.go','ops/supervisor/*holdout*.go',
    'ops/supervisor/fixture_windows.go','ops/supervisor/control_authority_windows.go','internal/domain/backup*.go']:
    paths.update(p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file())
paths.update(integration['source_files'])
paths.update(['ops/ci/evolution.py','ops/ci/orchestration.py','ops/ci/jev.py','ops/ci/acceptance_audit.py',
    'internal/domain/decision_c20_test.go','internal/domain/decision.go','adapters/decision/jev.go',
    'internal/domain/auth.go','internal/domain/remote_auth.go','internal/domain/context.go',
    'internal/domain/changes.go','internal/domain/conflicts.go','internal/domain/orchestration.go',
    'internal/domain/runtime.go','internal/domain/budget.go','internal/domain/budget_scopes.go',
    'internal/domain/budget_usage.go','internal/domain/experiments.go',
    'ops/supervisor/holdout_windows_test.go','go.mod','go.sum'])
paths={p for p in paths if (root/p).is_file()}
source_current={p:{'sha256':sha(bytes_read(root/p)),'bytes':(root/p).stat().st_size} for p in sorted(paths)}
for p,m in source_current.items():assert sha(gitblob(target,p))==m['sha256'],p
deltas=[]
for cid in ['C10','C12','C20']:
    rev=cases[cid]['accepted_revision'];rows=[];inventory=old_cases[cid]['version_manifest']['source_sha256']
    for p,current in source_current.items():
        old=gitblob(rev,p)
        if p in inventory and old is not None:assert sha(old)==inventory[p].removeprefix('sha256:')
        rows.append({'path':p,'accepted_sha256':sha(old) if old is not None else None,
            'current_sha256':current['sha256'],'state':'ADDED_SINCE_ACCEPTANCE' if old is None else ('UNCHANGED' if sha(old)==current['sha256'] else 'CHANGED'),
            'in_original_inventory':p in inventory})
    deltas.append({'case':cid,'accepted_revision':rev,'target_revision':target,'files':rows,
        'counts':{s:sum(x['state']==s for x in rows) for s in ['CHANGED','UNCHANGED','ADDED_SINCE_ACCEPTANCE']},
        'transitive_dependency_closure_proven':False})

def function_info(path,name):
    text=(root/path).read_text(encoding='utf-8');pattern=r'^func (?:\([^\n]*?\) )?'+re.escape(name)+r'\('
    m=re.search(pattern,text,re.M);assert m,(path,name)
    end=re.search(r'^func ',text[m.end():],re.M);stop=m.end()+end.start() if end else len(text)
    body=text[m.start():stop]
    return {'file':path,'function':name,'line':text[:m.start()].count('\n')+1,
        'body_sha256':sha(body.encode()),'body_ends_before_next_function':True}
locations=[function_info('internal/domain/evolution_test.go',n) for n in ['evoSetupMode','run','TestW16C10','TestW16C12','TestW16C20']]
locations += [function_info('internal/domain/evolution_holdout_test.go','prepareC20PrivateOperation'),
    function_info('internal/domain/decision_c20_test.go','TestW11C20RubricOnly'),
    function_info('internal/domain/evolution.go','actSystemCandidate'),
    function_info('internal/domain/evolution_acceptance.go','evolutionRecordValid'),
    function_info('internal/domain/evolution_execution.go','ExecuteEvolutionFixture'),
    function_info('internal/domain/evolution_execution.go','runEvolutionCanary')]

negative=['TestW16C20PrivateProofMissing','TestW16C20PrivateProofTampered','TestW16C20PrivateVerifierRevoked','TestW16C20PrivateVerifierGrantRemoved','TestW16C20PrivateRemoteVerifier']
selectors=[
    {'case':'C10','package':'./internal/domain','selector':'^(TestW16C10)$','registered_commands':['test.evolution','test.orchestration'],
        'assertions':['C10-01','C10-02','C10-03'],'prerequisites':['Windows native build via RESEARCHOS_GO','AppContainer candidate/stable invocation','public SQLite/HTTP fixture'],
        'note':'W16/C10 test.orchestration delegates to evolution_main and executes the same selector; it is not an independent extra selector.'},
    {'case':'C12','package':'./internal/domain','selector':'^(TestW16C12)$','registered_commands':['test.evolution'],
        'assertions':['C12-ADMITTED','C12-01','C12-02','C12-03','C12-STABLE'],
        'prerequisites':['Windows native build/AppContainer','degradation canary invocation','encrypted backup isolated restore','exact stable native health']},
    {'case':'C20','package':'./internal/domain','selector':'^('+'|'.join(['TestW16C20']+negative)+')$',
        'registered_commands':['test.evolution'],'assertions':['C20-01','C20-02','C20-03','C20-PRIVATE-MISSING','C20-PRIVATE-TAMPER','C20-PRIVATE-REVOKED','C20-PRIVATE-GRANT-REMOVED','C20-PRIVATE-REMOTE-DENIED'],
        'prerequisites':['Windows native build/AppContainer','new protected Canary input/labels/proof','private proof reopen and recomputation','negative mutation/revocation fixtures']},
    {'case':'C20','package':'./internal/domain','selector':'^(TestW11C20RubricOnly)$','registered_commands':['test.jev.fixture'],
        'assertions':['C20-JEV-SAME-OBJECTIVE','C20-JEV-RUBRIC-SCORE-UP','C20-JEV-NO-AUTO'],
        'prerequisites':['public synthetic SQLite and loopback Jev HTTP fixture'],'note':'No external provider; only the Jev rubric interface subset, never full C20.'},
    {'case':'C20','package':'./ops/supervisor','selector':'^TestObjectiveHoldoutGain$',
        'registered_commands':['test.evolution secondary helper'],'assertions':[],
        'prerequisites':['pure objective-verdict unit check'],'note':'Runner executes this after C20; passing zero W16 assertions is supplementary, not case acceptance.'},
    {'case':'C20','package':None,'selector':None,'registered_commands':['acceptance.audit'],
        'script':'ops/ci/acceptance_audit.py','assertions':['C20-AUDIT-INTEGRITY','C20-AUDIT-VERSIONS','C20-AUDIT-NO-GAIN','C20-AUDIT-PROTECTED-RAW'],
        'prerequisites':['existing exact evolution/Jev invocation paths','external protected blob integrity access'],
        'note':'Historical Python audit, not a Go selector. Not executed or reopened in this review.'}]
for s in selectors:s['executed_in_this_review']=False

scope_by_assertion={
 'C10-01':('Current-control preparation rejects selected authority table drift; no four-class legacy native tamper replay.', ['current-control authority-drift public log'], 'Four native writes, immutable baseline/labels/permissions/stable image remain historical only.'),
 'C10-02':('R08 current generic self/child/alias independence and current-control owner authority checks support a subset.', ['R08 '+','.join(r08_ids),'current-control GoTestCannotOwnAuthority'], 'Legacy forged evolution receipt and candidate-author self release matrix not revalidated.'),
 'C10-03':('No latest complete independent rule-proposal result found in the explicitly reviewed evidence.', [], 'Old-suite retention plus new independent samples and no same-transaction self approval remain historical.'),
 'C12-01':('Current-control rejection has gain=false and no degradation-triggered canary rollback.', [], 'No current native degradation, threshold trigger, exact stable hash restore and health chain.'),
 'C12-02':('No-gain candidate REJECTED is distinct from degradation FROZEN and retry refusal.', ['current-control normal_gate=REJECTED'], 'No current full FROZEN/PROMOTE/repeated START_CANARY matrix.'),
 'C12-03':('Persisted current-control identity/delta binding does not supply legacy rollback-trigger metrics or rollback receipt.', [], 'Legacy actual/threshold/old-new hash/restore-health/requalification record remains historical.'),
 'C20-01':('Persisted current-control public/private gain=false and REJECTED support no-gain refusal for that profile.', ['current-control readonly-result.json'], 'Different control profile; no complete current legacy rubric-only/private-proof negative matrix.'),
 'C20-02':('Control snapshot/owner/plan/version bindings exist, but this is not an old/new rubric comparison on identical samples.', ['current-control readonly-result.json'], 'Dual rubric raw scores, identical sample/input/objective results and model/version scope require the legacy C20 plus Jev evidence; no current rerun exists here.'),
 'C20-03':('Persisted current-control recomputation retains NO_IMPROVEMENT and gain=false.', ['current-control readonly-result.json'], 'Supports only its own synthetic control conclusion; does not establish complete current legacy C20 or real-world gain.')}
mapping=[]
for cid,case in old_cases.items():
    for a in case['assertion_results']:
        aid=a['assertion_id'];summary,refs,gap=scope_by_assertion[aid]
        actuals=a['actual'] if isinstance(a['actual'],list) else [a['actual']]
        historical=[]
        for actual in actuals:
            inv=actual['invocation_reference'];report=old_reports[inv]
            matches=[v for v in report['report']['assertions'] if v['assertion_id']==actual['assertion_id']]
            assert matches and matches[0]['status']=='PASS'
            match=matches[0]
            for key in ['expected','actual']:
                if key in actual:assert match[key]==actual[key]
            raw=match.get('raw',match.get('raw_evidence'))
            if raw and report['raw'] is not None:
                line=report['raw'].splitlines()[raw['line']-1]
                assert match['assertion_id'] in line
            historical.append({'assertion_id':actual['assertion_id'],'invocation':inv,
                'public_report':report['path'].relative_to(root).as_posix(),'raw':raw,'status':'PASS_HISTORICAL'})
        mapping.append({'case':cid,'assertion_id':aid,'frozen_expected':a['expected'],
            'historical_evidence':historical,'current_status':'PARTIAL','latest_scope':summary,
            'latest_refs':refs,'remaining_gap':gap,'new_execution':False})

write('selectors.json',selectors)
write('assertion-map.json',mapping)
write('source-deltas.json',deltas)
write('source-current.json',{'target':target,'files':source_current,'scope':'bounded selected direct/call-related inventory; not a transitive dependency closure'})
write('source-locations.json',locations)
write('historical-commands.json',commands)
write('control-reuse.json',{'source_commit':control,'review_ref':(controlbase/'review.md').relative_to(root).as_posix(),
    'raw_ref':(controlbase/'readonly-test-04.log').relative_to(root).as_posix(),'result':control_result,
    'integration_source_comparison':integration_comparison,'targeted_public_passes':targeted_passes,
    'reused_as':'historical persisted synthetic recomputation; no private bytes reopened',
    'limits':['gain=false is not dual-rubric coverage','historical currentAtSEAL is not now-current',
        'owner UNVERIFIED_STOPPED and native event authenticity UNVERIFIED remain unchanged',
        'current-control drain was refused; targeted stop was cleanup, not C12 rollback or release proof']})
review={'schema':'W21_R04_LEGACY_EVOLUTION_READONLY_AUDIT_V1','reviewer':'codex:/root/control_drain',
    'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'target_revision':target,
    'verdict':'PARTIAL','task_completed':'Read-only requested inventory and evidence mapping completed',
    'cases':{c:{'status':'PARTIAL','historical_status':'PASS','accepted_revision':cases[c]['accepted_revision'],
        'frozen_assertions':len(frozen[c]['assertions']),'current_full_case_acceptance':False} for c in cases},
    'new_test_executions':0,'native_child_executions':0,'provider_calls':0,'private_payload_reads':0,
    'source_files_checked':len(source_current),'source_matches_target_git':True,
    'formal_case_status_modified':False,'canonical_status_modified':False,'dependencies_complete':False,
    'finding':'No fresh product failure inferred. Shared evolution/control/backup source drift leaves legacy full-case applicability unresolved.',
    'limits':['Only public receipts, public aggregate review outputs and repository source were read.',
        'Historical case PASS is retained at its accepted revision, not lifted automatically to current source.',
        'C20 current-control gain=false cannot substitute for complete old/new rubric, same sample/input, private objective proof and Jev matrix.',
        'No private recomputation helper, protected raw, legacy native tests, provider or blocked flow was run.',
        'No LIVE, SCM, normal release, full A16/W18 or current-control production activation acceptance.']}
for p,m in source_current.items():assert sha((root/p).read_bytes())==m['sha256'],p
write('review.json',review)
write('input-hashes.json',inputs)
print(json.dumps({'verdict':'PARTIAL','source_files':len(source_current),'assertions_mapped':len(mapping),
    'delta_counts':{d['case']:d['counts'] for d in deltas},'integration_changed':[x['path'] for x in integration_comparison if not x['unchanged']]}))
