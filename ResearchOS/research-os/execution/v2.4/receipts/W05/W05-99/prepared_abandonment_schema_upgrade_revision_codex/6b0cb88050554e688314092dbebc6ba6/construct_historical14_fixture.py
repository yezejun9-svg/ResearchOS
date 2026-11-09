from pathlib import Path
import json,hashlib,re
own=Path("D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\prepared_abandonment_schema_upgrade_revision_codex\\6b0cb88050554e688314092dbebc6ba6")
root=own.parents[7]
# The repository root is explicit; do not derive a writable target from parent counts.
root=Path(r'D:/作品集/ResearchOS/research-os')
old=root/'.local/releases/schema14-09a6a5e/internal/domain/durability.go'
main=root/'internal/domain/backup_upgrade_test.go'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
s=old.read_bytes().decode('utf-8');a=s.index('func (s *Service) ResumeCheckpoint(');next_func=re.search(r'(?m)^func ',s[a+5:]);b=a+5+next_func.start() if next_func else len(s)
body=s[a:b].rstrip()
assert 'runtimeDispatch' not in body
assert body.endswith('}')
renamed=body.replace('func (s *Service) ResumeCheckpoint(', 'func (s *Service) upgradeHistorical14ResumeCheckpoint(',1)
header='''package domain

import (
    "context"
    "database/sql"
)

// Test-only schema14 behavior, copied from the pinned historical durability.go.
// The caller validates the exact restored schema14 before every invocation.
// Current production ResumeCheckpoint retains its native dispatch checks.
'''
p=own/'candidate-root/internal/domain/backup_historical14_resume_test.go'
p.write_bytes((header+renamed+'\n').encode('utf-8'))
s=main.read_bytes().decode('utf-8')
a=s.index('\tsvc := upgradeHistoricalFixtureService(t, db, opt.TargetRoot, version, true)')
extra='''\r
\tresume := svc.ResumeCheckpoint\r
\tif version == 14 {\r
\t\tresume = func(ctx context.Context, token, project, runID, key string, expectedRevision int64) (Object, error) {\r
\t\t\tupgradeHistoricalFixtureService(t, db, opt.TargetRoot, 14, true)\r
\t\t\treturn svc.upgradeHistorical14ResumeCheckpoint(ctx, token, project, runID, key, expectedRevision)\r
\t\t}\r
\t}'''
needle='\tsvc := upgradeHistoricalFixtureService(t, db, opt.TargetRoot, version, true)'
s=s[:a]+s[a:].replace(needle,needle+extra,1)
assert s.count('svc.ResumeCheckpoint(ctx, token, f.project')==3
s=s.replace('svc.ResumeCheckpoint(ctx, token, f.project','resume(ctx, token, f.project')
q=own/'candidate-root/internal/domain/backup_upgrade_test.go';q.write_bytes(s.encode('utf-8'))
pins=json.loads((own/'base-refs.json').read_text(encoding='utf-8'));pins.extend([ref(old),ref(main)])
(own/'base-refs.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
e={'historical_source':ref(old),'copied_method_sha256':hashlib.sha256(body.encode()).hexdigest(),'renamed_method_sha256':hashlib.sha256(renamed.encode()).hexdigest(),'method_body_exact_after_name_inverse':renamed.replace('upgradeHistorical14ResumeCheckpoint','ResumeCheckpoint',1)==body,'not_a_complete_frozen_release_attestation':True,'source_files':[ref(p),ref(q)]}
(own/'historical14-method-provenance.json').write_text(json.dumps(e,indent=2),encoding='utf-8');print(json.dumps(e))

