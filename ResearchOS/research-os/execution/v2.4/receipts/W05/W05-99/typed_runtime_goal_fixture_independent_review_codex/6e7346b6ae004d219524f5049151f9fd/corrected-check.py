from pathlib import Path
import json, hashlib, sys
import re
from collections import Counter
def fingerprint(p):
    raw=p.read_bytes()
    return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def tokens(text):
    rx=r'//[^\n]*|/\*[\s\S]*?\*/|`[^`]*`|"(?:\\.|[^"\\])*"|\x27(?:\\.|[^\x27\\])*\x27|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[^\s]'
    return [m.group() for m in re.finditer(rx,text) if not m.group().startswith(('//','/*'))]
def analysis(text):
    ts=tokens(text)
    stack=[]; pairs={}
    for i,x in enumerate(ts):
        if x in ['(', '[', '{']: stack.append((x,i))
        elif x in [')',']','}']:
            opening,j=stack.pop()
            if (opening,x) not in [('(',')'),('[',']'),('{','}')]: raise ValueError('unbalanced')
            pairs[j]=i
    if stack: raise ValueError('unclosed')
    calls=[]; positions=[]
    for i in range(len(ts)-4):
        if ts[i:i+2]==['t','.'] and ts[i+2] in ['Fatal','Fatalf','Fatalln','Error','Errorf','Errorln','Skip','Skipf','SkipNow'] and ts[i+3]=='(':
            calls.append(tuple(ts[i:pairs[i+3]+1])); positions.append(i)
    nodes=[]
    for i,x in enumerate(ts):
        if x!='if': continue
        j=i+1
        while j<len(ts):
            if ts[j]=='{': break
            if ts[j] in ['(','[']: j=pairs[j]
            j+=1
        if j<len(ts) and any(j<p<pairs[j] for p in positions): nodes.append(tuple(ts[i:pairs[j]+1]))
    names=re.findall(r'func\s+(Test\w+)\s*\(',text)
    return calls,nodes,names
R = Path('D:/作品集/ResearchOS/research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'
V=B / 'typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd'
Q = B / 'typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931'
def show(p):
    print('\nFILE '+str(p))
    print(p.read_text(encoding='utf-8'))
if sys.argv[1] == 'initial':
    print('\n'.join(str(p.relative_to(Q)) for p in Q.rglob('*') if p.is_file()))
    for name in ['HDF.json','MF.json','report.md','scope-map.json','source-refs.json']:
        p=Q/name
        if p.exists(): show(p)
elif sys.argv[1] == 'read':
    for arg in sys.argv[2:]: show(Path(arg))
elif sys.argv[1] == 'code':
    for p in sorted(Q.glob('*.patch')):
        show(p)
    p=Q/'candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go'
    print('\nHELPER')
    print('\n'.join(f'{i}: {line}' for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1)))
elif sys.argv[1] == 'context':
    h=json.loads((Q/'HDF.json').read_text(encoding='utf-8'))
    show(Path(h['contract_review']['path']))
    show(Q/'static-checks.json')
    show(Q/'base-refs.json')
    for p in (B/'typed_runtime_goal_fixture_source_io_codex/814-b6832e-76618678c33e47ffb4e2ad9bd5e9c208').rglob('*'):
        if p.is_file(): print(str(p))
elif sys.argv[1] == 'lines':
    p=Path(sys.argv[2])
    lines=p.read_text(encoding='utf-8').splitlines()
    for i in range(int(sys.argv[3])-1,min(int(sys.argv[4]),len(lines))): print(f'{i+1}: {lines[i]}')
elif sys.argv[1] == 'search':
    h=json.loads((Q/'HDF.json').read_text(encoding='utf-8'))
    for ref in h['read_dependencies']:
        p=Path(ref['path'])
        for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
            if re.search(sys.argv[2],line): print(f'{p.name}:{i}: {line}')
elif sys.argv[1] == 'check':
    if (V/'checks.json').exists(): raise ValueError('check output already exists; do not overwrite')
    refs=[]; mismatches=[]
    def verify(ref):
        p=Path(ref['path']); actual=fingerprint(p); refs.append(actual)
        if actual['sha256']!=ref['sha256'] or actual['bytes']!=ref['bytes']: mismatches.append({'expected':ref,'actual':actual})
    verify({'path':(Q/'HDF.json').as_posix(),'sha256':'21452223845c767f89fb1660b21f751b906a9a6d2a6f9d2adefd0787b4e94f53','bytes':8255})
    verify({'path':(Q/'MF.json').as_posix(),'sha256':'dcb1812c7b5d44a8db70fe0bb98ba93c9013ae016487f952a392565ec7715299','bytes':6789})
    h=json.loads((Q/'HDF.json').read_text(encoding='utf-8'))
    mf=json.loads((Q/'MF.json').read_text(encoding='utf-8'))
    for ref in mf['members']: verify(ref)
    for ref in h['read_dependencies']: verify(ref)
    verify(h['contract_review']); verify(h['original_full_closed'])
    br=json.loads((Q/'base-refs.json').read_text(encoding='utf-8'))
    results=[]
    for ref in br['refs']:
        verify(ref)
        base=Path(ref['path']); new=Q/'candidate-root/internal/domain'/base.name
        bc,bi,bn=analysis(base.read_text(encoding='utf-8'))
        nc,ni,nn=analysis(new.read_text(encoding='utf-8'))
        results.append({'file':new.as_posix(),'base_calls':len(bc),'base_assertion_ifs':len(bi),'calls_preserved':not (Counter(bc)-Counter(nc)),'ifs_preserved':not (Counter(bi)-Counter(ni)),'test_names':bn,'test_names_preserved':bn==nn})
    sm=json.loads((Q/'scope-map.json').read_text(encoding='utf-8')); verify(sm['raw_ref'])
    raw=Path(sm['raw_ref']['path']).read_text(encoding='utf-8').splitlines()
    leaves=[{'test':m['failed_leaf'],'original_event_matches':json.loads(raw[m['original_failure']['raw_line']-1])==m['original_failure']['actual_event']} for m in sm['mapping']]
    totals=Counter()
    for line in raw:
        event=json.loads(line)
        if event.get('Test') and event.get('Action') in ['pass','fail','skip']: totals[event['Action']]+=1
    io=B/'typed_runtime_goal_fixture_source_io_codex/814-b6832e-76618678c33e47ffb4e2ad9bd5e9c208'
    for p in io.rglob('*'):
        if p.is_file(): refs.append(fingerprint(p))
    out={'scope':'SOURCE_COMPONENT_ONLY','hash_mismatches':mismatches,'four_original_files':results,'original_call_total':sum(x['base_calls'] for x in results),'original_assertion_if_total':sum(x['base_assertion_ifs'] for x in results),'original_full_test_totals':dict(totals),'original_10_failures':leaves,'new_helper_skip_calls':[c for c in analysis((Q/'candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go').read_text(encoding='utf-8'))[0] if c[2].startswith('Skip')],'Go_native_SQL_model_execution':False,'formal_acceptance':False}
    (V/'checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (V/'input-refs.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
