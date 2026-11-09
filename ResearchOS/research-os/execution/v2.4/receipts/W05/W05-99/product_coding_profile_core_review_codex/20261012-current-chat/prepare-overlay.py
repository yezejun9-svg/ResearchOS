from pathlib import Path
import json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-product-coding-profile-core-20261012'
(OUT/'overlay.json').write_text(json.dumps({'Replace':{str(WT/'internal/domain/reviewer_coding_windows_test.go'):str(OUT/'reviewer_coding_windows_test.go')}},indent=2)+'\n',encoding='utf-8')
