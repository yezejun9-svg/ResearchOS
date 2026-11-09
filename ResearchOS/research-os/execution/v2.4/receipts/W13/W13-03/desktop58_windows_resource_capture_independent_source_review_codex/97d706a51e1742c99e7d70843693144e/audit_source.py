import ast,hashlib,json,struct,os
from pathlib import Path
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W13/W13-03/desktop58_windows_resource_capture_source_revision_codex/3aff012b57924a41a233cb9e162cfc0d'
checks=[];refs=[]
def check(n,v):checks.append({'check':n,'passed':bool(v)})
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def readref(r):
 p=Path(r['path']);b=p.read_bytes();check('pin '+str(p),hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']);refs.append(r);return b
def j(p):return json.loads(p.read_bytes())
def save(n,d):
 p=O/n
 with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
h=j(S/'handoff.json');m=json.loads(readref(h['manifest_ref']))
check('manifest9actualmembers',len(m['members'])==9)
for r in m['members']:readref(r)
check('handoff fixed',pin(S/'handoff.json')['sha256']=='ca1ea0033c8cab7dd5ce38b1dc035557f41679baad27f20f0cf1a68cbf38ce3f')
inv=j(S/'source-inverse.json');old=readref(inv['base_ref']);new=readref(inv['proposed_ref'])
t=ast.parse((S/'derive_source.py').read_text(encoding='utf-8'))
changes=next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id=='changes' for a in n.targets))
check('exact4anchors',len(changes)==4)
text=new.decode('utf-8')
for a,b in reversed(changes):
 check('new anchor once '+str(changes.index((a,b))),text.count(b)==1)
 text=text.replace(b,a,1)
check('wholebyteinverse',text.encode()==old)
ot,nt=ast.parse(old),ast.parse(new)
of={n.name:ast.dump(n,include_attributes=False) for n in ot.body if isinstance(n,ast.FunctionDef)}
nf={n.name:ast.dump(n,include_attributes=False) for n in nt.body if isinstance(n,ast.FunctionDef)}
check('onlyrunASTchanged',[k for k in of if of[k]!=nf.get(k)]==['run'] and set(of)==set(nf))
check('alloutsideRunASTsame',ast.dump(ast.Module(body=[n for n in ot.body if not isinstance(n,ast.FunctionDef) or n.name!='run'],type_ignores=[]))==ast.dump(ast.Module(body=[n for n in nt.body if not isinstance(n,ast.FunctionDef) or n.name!='run'],type_ignores=[])))
compile(new,'source-static-only','exec')
q=j(S/'root-q.resource-fields.proposed.json');add=q['new_root_q_fields'];wr=add['wldp_static_ref'];rep=json.loads(readref(add['wldp_candidate_report_ref']))
check('twoexplicitRootfields',set(add)=={'wldp_static_ref','wldp_candidate_report_ref'})
check('sourceonlyflags',rep['actual_qualification'] is False and rep['native_target_executed'] is False and q['authorization'] is False and q['actual_loaded_complete'] is False)
check('oneexactcandidate',len(rep['candidate_additions'])==1 and {k:rep['candidate_additions'][0][k] for k in ('path','sha256','bytes')}==wr)
readref(wr)
pe=json.loads(readref(rep['fresh_evidence_refs']['pe_explicit']));names=json.loads(readref(rep['fresh_evidence_refs']['direct_import_name_matches']))
check('peWldpPin',all(pe['targets']['wldp'][k]==wr[k] for k in ('sha256','bytes')))
cmd=pe['targets']['cmd'];cmdraw=readref({k:cmd[k] for k in ('path','sha256','bytes')})
def delay_imports(b):
 off=struct.unpack_from('<I',b,60)[0]
 check('cmdPEsignature',b[off:off+4]==b'PE\0\0')
 ns=struct.unpack_from('<H',b,off+6)[0];optsz=struct.unpack_from('<H',b,off+20)[0];op=off+24;magic=struct.unpack_from('<H',b,op)[0]
 dd=op+(112 if magic==0x20b else 96);imagebase=struct.unpack_from('<Q' if magic==0x20b else '<I',b,op+(24 if magic==0x20b else 28))[0]
 sections=[]
 for i in range(ns):
  p=op+optsz+40*i;vsize,va,size,raw=struct.unpack_from('<IIII',b,p+8);sections.append((va,max(vsize,size),raw))
 def fileoff(rva):
  for va,size,raw in sections:
   if va<=rva<va+size:return raw+rva-va
  raise ValueError('Unmapped RVA')
 rva,size=struct.unpack_from('<II',b,dd+13*8)
 if not rva:return []
 p=fileoff(rva);out=[]
 for pos in range(p,p+size,32):
  values=struct.unpack_from('<8I',b,pos)
  if not any(values):break
  name=values[1] if values[0]&1 else values[1]-imagebase;n=fileoff(name);end=b.index(0,n);out.append(b[n:end].decode('ascii'))
 return out
di=delay_imports(cmdraw)
check('actualcmdPEdelayWldp','wldp.dll' in [n.casefold() for n in di])
check('PEserializednamesexact',di==cmd['pe']['delay_imports'])
check('directedgeexact',any(e['from']==cmd['path'] and e['raw_name'].casefold()=='wldp.dll' and e['import_kind']=='delay_imports' and e['system32_filename_matches']==[wr['path']] and e['catalog_matches']==[] for e in names['edges']))
oldruntime=json.loads(readref(rep['input_refs']['selected_runtime_catalog']))
check('old1296',len(oldruntime['files'])==1296)
check('oldabsence',not any(os.path.normcase(x['path'])==os.path.normcase(wr['path']) for x in oldruntime['files']))
check('candidate1297',len({os.path.normcase(x['path']) for x in oldruntime['files']}|{os.path.normcase(wr['path'])})==1297)
check('unchangedaddusesactual','normalized = actual(row)' in new.decode() and of['add']==nf['add'] and of['actual']==nf['actual'])
check('falseloadmarker',"'Windows_Wldp_actual_loaded_proven': False" in new.decode())
check('runtimeappendonly',changes[2][1] in new.decode())
check('unresolveddeclared',any('API-set' in s for s in rep['open']))
failure_review=R/'execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_independent_review_codex/4bcd6b1bf2f941efa63f31e7a6cc7e67/review.final.json'
fr=j(failure_review)
check('rejectmatchescandidate',fr['cause']['fact']['before']=={'sha256':wr['sha256'],'bytes':wr['bytes']} and fr['qualification'] is False)
audit=save('audit.json',{'schema':'researchos.readonly-source-audit.v1','checks':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks),'actual_cmd_delay_imports':di,'input_refs':refs,'candidate_executed':False,'new_failure_origins':[]})
review={'schema':'researchos.desktop58-windows-resource-capture-independent-source-review.v1','reviewer':'codex:/root/w05_merge_review','non_author':True,'decision':'READY_SOURCE_PREPARATION_ONLY' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES','requested_changes':[x for x in checks if not x['passed']],'source_ref':inv['proposed_ref'],'source_sha256':inv['proposed_ref']['sha256'],'author_handoff_ref':pin(S/'handoff.json'),'author_manifest_ref':h['manifest_ref'],'audit_ref':audit,'failed_execution_review_ref':pin(failure_review),'wholebyteinverse_anchors':4,'actual_current_Wldp_pin_verified':wr,'old_runtime_count':1296,'new_runtime_candidate_count':1297,'actual_loaded_proven':False,'same_failed_input_retry_allowed':False,'candidate_executed':False,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'new_failure_count':0,'inherited_author_origins_already_counted':[pin(S/'failure-origin-001.json'),pin(S/'failure-origin-002.json')],'open':['Fresh Root UUID/literal/current canonical/cut required.','Fresh complete capture and actual bound scope review, CAS and unique grant required.','Dynamic actual hFile unknown-load rejection unchanged; API-set/delay/forwarder complete closure not established.','Static PE and a newly hashed DLL do not qualify the failed run or prove future full loaded lifecycle.'],'status':'STOPPED'}
rr=save('review.json',review)
report=save('report.json',{'conclusion':review['decision'],'checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'scope':'Read/hash/AST/PE byte parsing only. No candidate import/execution or complete resource-tree reread.','changes':'Two explicit pinned Root q fields, cmd PE delay provenance check, one runtime addition and false observed-load marker. All other source bytes recovered by exact inverse.','boundaries':review['open']})
hd=save('handoff.json',{'schema':'researchos.independent-source-review-handoff.v1','review_ref':rr,'report_ref':report,'audit_ref':audit,'decision':review['decision'],'new_failure_count':0,'new_failure_origins':[],'status':'STOPPED'})
es=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mf=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':es,'count':len(es),'self_excluded':True,'mutable_after_seal':False})
print(json.dumps({'review':rr,'handoff':hd,'manifest':mf,'passed':sum(x['passed'] for x in checks),'total':len(checks),'findings':review['requested_changes']},ensure_ascii=False))

