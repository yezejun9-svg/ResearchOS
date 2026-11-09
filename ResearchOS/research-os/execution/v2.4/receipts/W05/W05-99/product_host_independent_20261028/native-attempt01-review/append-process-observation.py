import pathlib,json,hashlib,datetime
E=pathlib.Path(__file__).resolve().parent
P=E.parent.parent/'product_host_native_20261028/attempt-01-process-observation.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expected='96150446c61d975f494d77acfc91539d4fc52a63a86b8b0004bdb4ca6612c694'
if sha(P)!=expected:raise RuntimeError('process observation changed')
obs=json.loads(P.read_bytes());report=json.loads((E/'REVIEW.json').read_bytes())
if obs['target_pid']!=37624 or obs['target_present'] or obs['matched_processes'] or obs['termination_mechanism']!='NOT_OBSERVED' or not obs['no_action_performed']:raise RuntimeError('unexpected observation')
with (E/'snapshots/attempt-01-process-observation.json').open('xb') as f:f.write(P.read_bytes())
report['previous_review_ref']={'path':str(E/'REVIEW.json'),'sha256':sha(E/'REVIEW.json')}
report['process_observation_ref']={'path':str(P),'sha256':expected,'bytes':P.stat().st_size}
report['observed']['root_postflight_process_observation']=obs
report['pending_root_observation']=['Post-run bundle/source/input and isolated state observation if Root has not yet captured']
report['process_termination_conclusion']='Target PID37624 and matching build04 processes absent at06:50:43Z; historical termination mechanism remains NOT_OBSERVED. Framework kill callback inferred from frozen source/error path; actual taskkill OS effect remains unproven.'
report['at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (E/'REVIEW-FINAL.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':str(E/'REVIEW-FINAL.json'),'sha256':sha(E/'REVIEW-FINAL.json')}))
