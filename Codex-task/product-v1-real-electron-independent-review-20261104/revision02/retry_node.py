from pathlib import Path
from check import run,NODE
R=Path(__file__).resolve().parent
old=(R/'independent-node.mjs').read_text(encoding='utf-8')
needle="assert.doesNotMatch(source,/\\bprocess"
assert old.count(needle)==1
new=old.replace(needle,"assert.doesNotMatch(source.split('\\n').filter(line=>!line.trimStart().startsWith('//')).join('\\n'),/\\bprocess")
p=R/'independent-node02.mjs';assert not p.exists();p.write_text(new,encoding='utf-8')
raise SystemExit(run('independent-node-02',[str(NODE),str(p)]))
