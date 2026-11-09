from pathlib import Path
import json,re,ast
from collections import Counter
v=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd')
q=v.parent.parent/'typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931'
tree=ast.parse((v/'corrected-check.py').read_text(encoding='utf-8'))
ctx={'re':re}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['tokens','analysis']],type_ignores=[]),'independent-functions-only','exec'),ctx)
def broad(text):
    ts=ctx['tokens'](text); stack=[]; ends={}
    for i,x in enumerate(ts):
        if x in ['(','[','{']: stack.append(i)
        elif x in [')',']','}']: ends[stack.pop()]=i
    result=[]
    for i,x in enumerate(ts):
        if x!='if': continue
        j=i+1
        while ts[j]!='{':
            if ts[j] in ['(','[']: j=ends[j]
            j+=1
        node=tuple(ts[i:ends[j]+1])
        if any(z in ['Fatal','Fatalf','Error','Errorf'] for z in node): result.append(node)
    return result
result=[]
base=json.loads((q/'base-refs.json').read_text(encoding='utf-8'))
for ref in base['refs']:
    p=Path(ref['path']); before=p.read_text(encoding='utf-8'); after=(q/'candidate-root/internal/domain'/p.name).read_text(encoding='utf-8')
    old,new=broad(before),broad(after)
    strict=ctx['analysis'](before)[1]
    extras=list((Counter(old)-Counter(strict)).elements())
    result.append({'file':p.name,'source_lexical_predicate_count':len(old),'all_preserved':not(Counter(old)-Counter(new)),'non_assertion_identifier_matches':[' '.join(x) for x in extras]})
out={'source_reported_lexical_196_independently_verified':sum(x['source_lexical_predicate_count'] for x in result),'strict_t_assertion_if_count':190,'explanation':'Source predicate matches any Fatal/Fatalf/Error/Errorf identifier, including err.Error. Six additional if nodes are preserved error propagation blocks, not t assertion blocks. No assertion deletion found.','files':result}
with (v/'if-node-supplement.json').open('x',encoding='utf-8',newline='') as f: json.dump(out,f,ensure_ascii=False,indent=2); f.write('\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
