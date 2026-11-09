import pathlib,json,hashlib
P=pathlib.Path
O=P(__file__).resolve().parent
R=P('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-broker4-positive-serve-root-1791513411000/original-root-terminal-tool-io.json')
def put(n,b):
 with (O/n).open('xb') as f:f.write(b)
def save(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
b=R.read_bytes()
assert len(b)==860 and hashlib.sha256(b).hexdigest()=='42600e84cbebe3619dc120dd51de487acdf8e0813a25f8a1a53e6d04f24a5096'
put('original-root-terminal-tool-io.json',b)
v=json.loads((O/'review.json').read_bytes())
assert all(x['passed'] for x in v['checks']) and len(v['checks'])==41 and v['authority']=='NONE' and not v['formal_acceptance']
save('handoff.json',{'schema':'researchos.independent-T10-failed-closure-handoff.v1','decision':v['decision'],'review_ref':ref(O/'review.json'),'report_ref':ref(O/'report.md'),'Root_terminal_original_ref':ref(O/'original-root-terminal-tool-io.json'),'execution_IO_ref':ref(O/'original-tool-io.json'),'native_failure_ordinal':892,'new_execution_failures':0,'further_action':'STOP','authority':'NONE','formal_acceptance':False})
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file()]
save('manifest.json',{'schema':'researchos.independent-T10-failed-closure-manifest.v1','members':members,'scope':'All files present before manifest creation; manifest excluded from its own members. full-io.json and post-seal.json are terminal descendants and explicitly excluded.','authority':'NONE','stop':True})
for r in members:assert ref(P(r['path']))==r
print(json.dumps({'handoff_ref':ref(O/'handoff.json'),'manifest_ref':ref(O/'manifest.json'),'report_ref':ref(O/'report.md'),'members_verified':len(members),'decision':v['decision'],'ROOT_PYTHON_EXIT':0},ensure_ascii=False))

