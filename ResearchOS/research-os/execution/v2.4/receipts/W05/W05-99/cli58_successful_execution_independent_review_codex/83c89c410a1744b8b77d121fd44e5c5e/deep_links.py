import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';U='0e298790cd484ec9ba319a379e7e34ed';E=P/'cli58_fresh_compiler_executor_codex'/U;O=Path(__file__).parent;N=P/('integration_codex/cli58-fresh-held2-r334-v2-'+U)
C=[];REF={}
def ck(k,v):C.append({'check':k,'passed':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);raw=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};REF[str(p)]=r;return r
def doc(p):ref(p);return json.loads(path(p).read_bytes())
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
s=doc(N/'scope_registration.json');X=path(s['new_export_root']);result=doc(E/'result.json');cl=doc(E/'compiled-closure.json');a=doc(O/'audit.json');actual={str(path(r['path'])):(r['sha256'],r['bytes']) for r in a['input_refs']};ar={str(path(r['path'])):r for r in cl['archives']};union=set();links=0
for r in cl['importcfg']:
 f=path(r['path']);raw=f.read_bytes();ck('importcfg actualcurrent '+str(f),hashlib.sha256(raw).hexdigest()==r['sha256'] and len(raw)==r['bytes'])
 for line in raw.decode('utf-8',errors='strict').splitlines():
  if line.startswith('packagefile '):
   q=path(line.split('=',1)[1]);union.add(str(q));links+=1;rr=ar.get(str(q));ck('archive exact edge '+str(f)+' '+str(q),rr is not None and actual.get(str(q))==(rr['sha256'],rr['bytes']))
ck('all698 archives exactly importcfg reachable',len(ar)==698 and union==set(ar))
mains=[r for r in cl['WORK'] if path(r['path']).name=='_testmain.go'];ck('generated testmain captured',len(mains)>0)
ck('generated testmain includes actual parent',any('TestCLIProtocolInteractiveAuthority' in path(r['path']).read_text(encoding='utf-8') for r in mains))
for k in ['WORK','cache']:
 ck('fresh namespace '+k,all(path(r['path']).is_relative_to(X) for r in cl[k]))
stages=[]
for stage in result['stages']:
 inv=doc(stage['result_ref']['path']);req=inv['request'];d=inv['result'].get('debug_capture')
 if d is None:continue
 gens=d['process_generations'];ids={(x['pid'],x['creation_time_100ns']) for x in gens};ck('exact generation identity '+stage['label'],len(ids)==len(gens) and all(type(x['pid']) is int and type(x['creation_time_100ns']) is int and x['creation_time_100ns']>2**53 and x['job_membership_observed'] is True for x in gens))
 active=set();peak=0;created=0;exited=0
 for i,event in enumerate(d['events']):
  if event['code']==3:
   ck('CREATE precedes reuse '+stage['label']+str(i),event['pid'] not in active);active.add(event['pid']);created+=1;peak=max(peak,len(active))
  elif event['code']==5:
   ck('EXIT belongs active '+stage['label']+str(i),event['pid'] in active);active.discard(event['pid']);exited+=1
 ck('full event tree '+stage['label'],not active and created==exited==d['create_process_count']==d['exit_process_count']==len(gens) and peak<=req['process_cap'] and created<=2048)
 for mod in d['modules']:
  ck('module belongs exact generation '+stage['label'],(mod['pid'],mod['creation_time_100ns']) in ids and mod['before']==mod['after'])
 jc=inv['result']['job_cleanup'];ck('all explicit handles closed '+stage['label'],jc['explicit_owned_handles_remaining']==0 and jc['explicit_owned_handle_close_successes']==jc['explicit_owned_handle_count'])
 stages.append({'label':stage['label'],'created':created,'exited':exited,'peak_active':peak,'scope_process_cap':req['process_cap'],'generations':len(gens),'actual_module_records':len(d['modules'])})
source=doc(path(s['catalog_ref']['path']));raw=(E/'git-public-blobs.stdout.raw').read_bytes();pos=0;blobs=[]
for row in source['files']:
 end=raw.index(b'\n',pos);header=raw[pos:end].decode('ascii').split(' ');pos=end+1;size=int(header[2]);body=raw[pos:pos+size];pos+=size
 ck('actual Git public blob framing '+row['path'],header[0]==row['git_blob'] and header[1]=='blob' and size==row['bytes'] and raw[pos:pos+1]==b'\n');pos+=1
 ck('actual Git blob SHA current source '+row['path'],hashlib.sha256(body).hexdigest()==row['sha256'] and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+body).hexdigest()==row['git_blob']);blobs.append(row['path'])
ck('Git batch exactly639 no extra',len(blobs)==639 and pos==len(raw))
save('deep-links.json',{'checks':C,'failed_checks':[x for x in C if not x['passed']],'input_refs':list(REF.values()),'importcfg_packagefile_edges':links,'unique_archives':len(ar),'generated_testmain_refs':mains,'debug_event_facts':stages,'actual_Git_blob_count':len(blobs),'qualification':'PENDING_ROOT_CLOSURE','candidate_calls':0,'new_failure_origins':[]})
print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']],'ref':ref(O/'deep-links.json')},ensure_ascii=False))
