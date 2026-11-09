import sys
sys.dont_write_bytecode=True
import json,hashlib,collections,types
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
T=B/'integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2'
A=B/'integration_codex/current-attach-q5-leg2-targeted-root-1791510290800'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,o):
 with (O/n).open('xb') as f:f.write((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
files=[p for p in T.iterdir() if p.is_file() and (p.name.startswith('typed-q3-epoch-parent-jsonl.') or p.name in ('validation.closed.json','original-tool-io.json','failure-origin.823.json'))]
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
code=gp.read_bytes();assert hashlib.sha256(code).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
m=types.ModuleType('supplement_guard');m.__file__=str(gp);exec(compile(code,str(gp),'exec'),m.__dict__)
g=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire([pin(p) for p in files])
try:
 copyrefs=[]
 for p in files:
  dest=O/'originals'/'old-T6-IO'/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(g.get_buffer(str(p)))
  copyrefs.append({'original':pin(p),'copy':pin(dest)})
 old=read(T/'validation.closed.json');inv=read(T/'typed-q3-epoch-parent-jsonl.invocation.json')
 assert pin(inv['stdout_ref']['path'])==inv['stdout_ref'] and pin(inv['stderr_ref']['path'])==inv['stderr_ref']
 ev=[json.loads(l) for l in g.get_buffer(str(T/'typed-q3-epoch-parent-jsonl.stdout.raw')).decode().splitlines()]
 runs=collections.Counter(x['Test'] for x in ev if x['Action']=='run' and x.get('Test'))
 terms=collections.defaultdict(list)
 for x in ev:
  if x.get('Test') and x['Action'] in ('pass','fail','skip'):terms[x['Test']].append(x['Action'])
 assert set(runs)==set(terms) and all(v==1 for v in runs.values()) and all(len(v)==1 for v in terms.values())
 actions={k:v[0] for k,v in terms.items()}
 assert actions==old['actions'] and {n for n in runs if '/' not in n}==set(old['exact_25_parent_names']) and len(old['exact_25_parent_names'])==25
 assert dict(collections.Counter(actions.values()))=={'pass':61,'fail':6} and ev[-1]['Action']=='fail' and 'Test' not in ev[-1]
 current=read(O/'report.json')
 assert set(old['exact_25_parent_names'])==set(current['base25_all_pass'])
 text=(O/'originals/A9/tagged-compiler-input-list.stdout.raw').read_text(encoding='utf-8');decoder=json.JSONDecoder();pos=0;packages=[];paths=set();embeds=[]
 fields=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')
 while pos<len(text):
  while pos<len(text) and text[pos].isspace():pos+=1
  if pos==len(text):break
  pkg,pos=decoder.raw_decode(text,pos);assert not pkg.get('Error') and not pkg.get('DepsErrors');packages.append(pkg['ImportPath'])
  if not pkg.get('Dir'):continue
  for f in fields:
   for n in pkg.get(f,[]):
    p=Path(n);p=p if p.is_absolute() else Path(pkg['Dir'])/p;paths.add(str(p.resolve()).casefold())
    if f.endswith('EmbedFiles'):embeds.append((pkg['ImportPath'],f,str(p.resolve()).casefold()))
 inventory=read(O/'originals/A9/actual-tagged-compiler-input-inventory.json')
 assert packages==inventory['packages'] and len(packages)==inventory['package_count']
 assert paths=={str(Path(x['path']).resolve()).casefold() for x in inventory['build_inputs']}
 assert sorted(embeds)==sorted((x['package'],x['field'],str(Path(x['ref']['path']).resolve()).casefold()) for x in inventory['actual_embed_files'])
 root_events=[json.loads(l) for l in (O/'originals/A9/current-attach-q5-leg2-parent-jsonl.stdout.raw').read_text(encoding='utf-8').splitlines()]
 embedded=[]
 for c in current['children']:
  case=c['case'];pieces=[]
  for x in root_events:
   if x.get('Test')==case and x['Action']=='output':
    line=x['Output'].strip()
    if line.startswith('{'):
     try:parsed=json.loads(line)
     except json.JSONDecodeError:continue
     if isinstance(parsed,dict) and 'Action' in parsed:pieces.append(parsed)
  child=[json.loads(l) for l in (O/'originals/children'/case/'child.stdout.jsonl').read_text(encoding='utf-8').splitlines()]
  assert pieces==child,(case,len(pieces),len(child))
  embedded.append({'case':case,'child_jsonl_lines':len(child),'parent_embedded_lines':len(pieces),'exact_event_equality':True})
 result={'status':'SUPPLEMENT_PASSED','old_T6_counts':dict(collections.Counter(actions.values())),'old_T6_unique_tests':len(actions),'old_T6_parent_count':25,'old_T6_package_exit':'fail','old_T6_originals':copyrefs,'compiler_package_count':len(packages),'compiler_input_count':len(paths),'compiler_embed_count':len(embeds),'compiler_inventory_exactly_reconstructed':True,'nested_parent_embedded_jsonl':embedded,'new_execution':False}
 save('supplement.report.json',result)
finally:save('supplement.source-guard.cleanup.actual.json',g.close())
print(json.dumps(result,ensure_ascii=False))
