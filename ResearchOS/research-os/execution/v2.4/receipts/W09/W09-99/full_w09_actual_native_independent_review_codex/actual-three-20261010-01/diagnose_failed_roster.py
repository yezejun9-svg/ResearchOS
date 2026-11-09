from pathlib import Path
import types,json
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
runs={'W09-G02':'28aa266121d24ad2988d578df02d23a4','A06':'ba9a185f551c4d4caf123da7eafb4245'}
refs=[]
for selector,run in runs.items():
    v=json.loads((m.N/('actual-'+selector+'-'+run)/'producer/validation.closed.json').read_bytes());packet=json.loads(Path(v['native_packet_ref']['path']).read_bytes());report=json.loads(Path(packet['original_report_ref']['path']).read_bytes());refs.append(packet['original_report_ref']);refs.extend(m.pin(m.R/p) for p in report['raw_evidence_references'])
g=m.guard();out={}
try:
    g.acquire(refs)
    for selector,run in runs.items():
        base=m.R/'execution/receipts/W09/retrieval'/('run-'+run);r=json.loads(g.get_buffer(str(base/'report.json')));events=[json.loads(line) for line in g.get_buffer(str(base/'go-test.stdout.jsonl')).decode().splitlines()]
        out[selector]={'report_passed_tests':r['passed_tests'],'Go_passed_order':[e.get('Test') for e in events if e.get('Action')=='pass' and e.get('Test')],'Go_failed_tests':[e.get('Test') for e in events if e.get('Action')=='fail' and e.get('Test')],'Legacy_outputs':[e.get('Output','') for e in events if e.get('Test')=='TestW09LegacyRootMigrationRevokesUnidentifiedRoot'],'report_missing_assertion_ids':r['missing_assertion_ids'],'report_status':r['status'],'Go_exit':r['exit_code'],'stderr_bytes':len(g.get_buffer(str(base/'go-test.stderr.txt')))}
    ref=m.write('failed-roster.actual-diagnostic.json',out);print(json.dumps({'diagnostic_ref':ref,'actual':out},ensure_ascii=False),flush=True)
finally:
    c=g.close();ref=m.write('failed-roster.diagnostic.guard.closed.json',c);print(json.dumps({'guard_ref':ref,'closed':c['closed'],'retained_handles_count':c['retained_handles_count']},ensure_ascii=False),flush=True)
