from pathlib import Path
import types,json,hashlib,datetime,tempfile,re,ast
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
P=m.N/'actual-W09-G01-4fd62ca511684dc39d62c5571d8ddaf5/producer'
v=json.loads((P/'validation.closed.json').read_bytes());ready=json.loads((P.parent/'prepare.ready.json').read_bytes());choice=json.loads((m.N/'source.choice.json').read_bytes());c={**choice['common'],**choice['selectors']['W09-G01']}
report=json.loads(Path(v['summary']['report_ref']['path']).read_bytes());inventory=json.loads(Path(v['summary']['compiler_inventory_ref']['path']).read_bytes());bp=json.loads(Path(c['compiler_blueprint_ref']['path']).read_bytes())
authority=json.loads((m.D/'G01.authority-observation.json').read_bytes());scope=authority['scope.W09-G01.json'];vector=authority['native.canonical-vector.json'];audit=json.loads((m.S/'w09.G01-native-run-final.actual-audit.root.json').read_bytes())
prior=json.loads((m.D/'G01.review-result.json').read_bytes());assert len(prior['checks'])==9 and all(x['passed'] for x in prior['checks']) and prior['all_closed'] is True
lead=[m.GREF,*bp['stable_input_refs'],*inventory['private_generated_input_refs'],*inventory['private_export_refs'],*c['source21'],*report['owned_export']['members'],audit['original_capture_ref'],m.pin(m.S/'w09.G01-native-run-final.actual-audit.root.json'),*ready['guard_cleanup_refs'],*v['invocation_refs']]
lead.extend(m.refs(v['summary']));lead.extend(c['tool_refs'].values());lead.append(c['toolchain_ref'])
for ref in v['invocation_refs']:lead.extend(m.refs(json.loads(Path(ref['path']).read_bytes())))
for ref in v['guard_cleanups']:lead.append(ref['ref'])
for relative in report['raw_evidence_references']:lead.append(m.pin(m.R/relative))
unique={}
for ref in lead:
    ref=m.absolute(ref);assert unique.get(ref['path'],ref)==ref;unique[ref['path']]=ref
g=m.guard();checks=[];mode_refs=None
def check(label,condition,detail=None):
    item={'check':label,'passed':bool(condition),'detail':detail};checks.append(item)
    with (m.D/'G01.tail-checks-progress.jsonl').open('ab') as f:f.write((json.dumps(item,ensure_ascii=False)+'\n').encode())
    if not condition:raise ValueError(label)
def doc(ref):return json.loads(g.get_buffer(m.absolute(ref)['path']))
def source_doc(path):return json.loads(g.get_buffer(str(path)))
try:
    g.acquire(list(unique.values()))
    check('all_actual_Source_guards_closed',v['all_guards_closed'] is True and v['all_owned_jobs_closed'] is True and v['all_cleanup_receipts_saved'] is True and not v['cleanup_errors'] and all(doc(x['ref'])['closed'] is True and doc(x['ref'])['retained_handles_count']==0 and not doc(x['ref'])['errors'] for x in v['guard_cleanups']) and all(doc(x['ref'])['closed'] is True and doc(x['ref'])['retained_handles_count']==0 and not doc(x['ref'])['errors'] for x in ready['guard_cleanups']))
    original=(m.D/'review_g01.py').read_text(encoding='utf-8');start=original.index('    decoder=json.JSONDecoder()');end=original.index('\nfinally:',start);tail=original[start:end]
    exec(compile('if True:\n'+tail,str(m.D/'review_g01.py')+'#unfinished_tail','exec'),globals())
finally:
    closed=g.close();ref=m.write('G01.tail.guard.closed.json',closed)
    result=m.write('G01.completed-review-result.json',{'selector':'W09-G01','prior_9_checks_reused_ref':m.pin(m.D/'G01.review-result.json'),'prior_checks_repeated':False,'new_checks':checks,'mode_refs':mode_refs,'guard_ref':ref,'all_closed':closed['closed'],'retained_handles_count':closed['retained_handles_count'],'Source_controls_repeated':False,'product_calls':0,'formal_acceptance':False,'execution_grant':False})
    print(json.dumps({'review_result_ref':result,'guard_ref':ref,'closed':closed['closed'],'retained_handles_count':closed['retained_handles_count']},ensure_ascii=False),flush=True)
