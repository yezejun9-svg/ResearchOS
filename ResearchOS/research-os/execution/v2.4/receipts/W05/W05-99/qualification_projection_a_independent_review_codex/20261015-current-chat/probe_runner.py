import review_runner as r
import json, os
env=os.environ.copy()
env.update(json.loads((r.E/'candidate-regressions.command.json').read_text(encoding='utf-8'))['env_allowlist'])
r.run('adapter-numeric-positive-control',[r.GO,'run',str(r.E/'adapter_numeric_probe.go')],r.CAND,env)
