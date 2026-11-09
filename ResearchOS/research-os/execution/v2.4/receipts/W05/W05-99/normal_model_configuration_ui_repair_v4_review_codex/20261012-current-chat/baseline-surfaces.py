from pathlib import Path
import subprocess,json,datetime
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v4-20261012'
BASE=OUT/'baseline-source'
for name in ['tests/ui/continuity/surfaces_driver.js','apps/desktop/main/lib/v2.js','apps/web/src/v2client.js','internal/api/contracts/client.protocol.schema.json']:
    raw=subprocess.check_output(['git','show','292ad860f9e76cf2795d5a3010da1d114d01ff56:'+name],cwd=WT)
    p=BASE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
argv=['C:/nvm4w/nodejs/node.exe',str(BASE/'tests/ui/continuity/surfaces_driver.js'),str(BASE)]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
run=subprocess.run(argv,cwd=OUT,capture_output=True,timeout=30)
(OUT/'baseline-surfaces.stdout').write_bytes(run.stdout);(OUT/'baseline-surfaces.stderr').write_bytes(run.stderr)
(OUT/'baseline-surfaces.invocation.json').write_text(json.dumps(dict(argv=argv,cwd=str(OUT),exit_code=run.returncode,started_at=started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n',encoding='utf-8')
before=json.loads(run.stdout);after=json.loads((OUT/'cumulative-surfaces.stdout').read_text(encoding='utf-8'))
def facts(value):
    c=value['checks']
    return dict(legal_count=c['legal_envelopes']['count'],legal_agree=c['legal_envelopes']['agree'],legal_mismatches=[dict(probe=r['probe'],method=r['method']) for r in c['legal_envelopes']['rows']],refusals_count=c['refusals']['count'],refusals_agree=c['refusals']['agree'],refusal_mismatches=[r for r in c['refusals']['rows'] if not r['agree']])
result=dict(base=facts(before),candidate=facts(after),driver_exit_zero_is_not_all_assertions_pass=True)
(OUT/'surface-comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
