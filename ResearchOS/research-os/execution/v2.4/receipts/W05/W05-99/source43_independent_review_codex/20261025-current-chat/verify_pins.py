import pathlib,json,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8')
repo=pathlib.Path('D:/作品集/ResearchOS/research-os')
out=pathlib.Path(__file__).parent
scopepath=repo/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp531/Source43-independent-review-scope.json'
scope=json.loads(scopepath.read_text(encoding='utf-8'))
assert hashlib.sha256(scopepath.read_bytes()).hexdigest()=='4c06080c42b92443f9d1d000c61ca2cd73e1ce0235b2e6918e1a41fd73ac9d97'
wt=pathlib.Path(scope['review_worktree'])
rows=[]
for name in scope['source_allowlist']:
    data=(wt/name).read_bytes(); actual={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
    expected=scope['accepted_mechanical41_pins'].get(name)
    if expected: assert all(actual[k]==expected[k] for k in actual),(name,actual,expected)
    rows.append({'path':name,**actual,'mechanical_pin_equal':bool(expected)})
author=repo/'execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261025-current-chat'
final=json.loads((author/'FINAL-manifest.json').read_text(encoding='utf-8'))
for name,expected in final['evidence'].items():
    data=(author/name).read_bytes(); assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],name
result={'scope_hash_verified':True,'mechanical41_exact':sum(x['mechanical_pin_equal'] for x in rows),'files':rows,'author_final_hash':hashlib.sha256((author/'FINAL-manifest.json').read_bytes()).hexdigest(),'author_final_references_verified':list(final['evidence'])}
(out/'pins-verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(result,indent=2,ensure_ascii=False))
