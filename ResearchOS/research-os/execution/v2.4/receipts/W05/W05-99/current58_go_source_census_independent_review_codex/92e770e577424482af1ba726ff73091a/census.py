import pathlib,json,hashlib,re,datetime,traceback
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
O=pathlib.Path(__file__).parent
P=R/'execution/v2.4/receipts/W05/W05-99'
A=R/'execution/v2.4/receipts/W13/W13-03/fresh58_public_source_authority_codex/16e288f44f104376898cde4336c705a1'
G=P/'whole58_terminal_evidence_gap_independent_review_codex/669dc830cf8b9f5360d36592c380f044'
READS={}
def read(p):
 p=pathlib.Path(p); b=p.read_bytes(); READS[str(p)]={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def obj(p):return json.loads(read(p))
def write(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def mask(s):
 # Keep offsets/newlines while hiding comments and all Go literal forms.
 pat=r'//[^\n]*|/\*[\s\S]*?\*/|`[^`]*`|"(?:\\[\s\S]|[^"\\])*"|\x27(?:\\[\s\S]|[^\x27\\])*\x27'
 return re.sub(pat,lambda m:''.join('\n' if c=='\n' else ' ' for c in m.group()),s)
def main():
 cat=obj(A/'public-source-catalog.json'); combined=obj(A/'combined58-source-set.json'); sm=obj(G/'suite-map.json');sign=obj(G/'signing-map.json')
 combined_paths={x['path'] for x in combined['files']}; rows=cat['files']; checks=[]; funcs=[]; packages={}; signals=[]
 for row in rows:
  path=row['path']; raw=read(R/path);sha=hashlib.sha256(raw).hexdigest(); blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  checks.append({'path':path,'sha256_equal':sha==row['sha256'],'bytes_equal':len(raw)==row['bytes'],'git_blob_equal':blob==row['git_blob']})
  if not path.endswith('.go'):continue
  s=raw.decode('utf-8-sig');m=mask(s);pm=re.search(r'^\s*package\s+(\w+)',m,re.M);assert pm,path
  pkg=pm.group(1);directory=path.rsplit('/',1)[0] if '/' in path else '.';pk=directory+':'+pkg
  entry=packages.setdefault(pk,{'directory':directory,'package':pkg,'go_files':[],'tests':[]})
  tags=[{'line':i+1,'text':t} for i,t in enumerate(s.splitlines()) if t.startswith('//go:build ') or t.startswith('// +build ')]
  entry['go_files'].append({'path':path,'sha256':sha,'build_constraints':tags,'in_combined58_delta':path in combined_paths})
  depth=0;pos=0
  for fm in re.finditer(r'\bfunc\s+(\w+)\s*\(',m):
   depth+=m[pos:fm.start()].count('{')-m[pos:fm.start()].count('}');pos=fm.start()
   if depth!=0:continue
   name=fm.group(1);opening=m.find('{',fm.end());semi=m.find(';',fm.end())
   if opening<0:continue
   d=1;end=opening+1
   while end<len(m) and d:d+=(m[end]=='{')-(m[end]=='}');end+=1
   sig=m[fm.start():opening].strip();body=s[opening:end];bm=m[opening:end];startline=s.count('\n',0,fm.start())+1
   is_test=path.endswith('_test.go') and re.match(r'^Test(?:[^a-z].*)?$',name) is not None and name!='TestMain' and bool(re.search(r'\(\s*\w+\s+\*\s*\w+\.T\s*\)',sig))
   f={'id':pk+'::'+name,'name':name,'package_key':pk,'path':path,'line':startline,'end_line':s.count('\n',0,end)+1,'signature':sig,'top_level_test':is_test,'test_main':name=='TestMain','in_combined58_delta':path in combined_paths,'calls':sorted(set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',bm))),'signals':[]}
   for i,line in enumerate(body.splitlines()):
    if re.search(r'\b(?:Skip|Skipf|SkipNow|Short|Getenv|LookupEnv|Setenv|NewServer|NewTLSServer|ListenAndServe|exec\.Command|CommandContext|MODEL|SDK|API_KEY|OPENAI|ANTHROPIC|DEEPSEEK)\b',line,re.I):
     signal={'path':path,'line':s.count('\n',0,opening)+1+i,'function':name,'text':line.strip()};f['signals'].append(signal);signals.append(signal)
   funcs.append(f)
   if is_test:entry['tests'].append(name)
 all_testnames={(f['package_key'].split(':')[0],f['name']) for f in funcs if f['top_level_test']}
 batches=[]
 for b in sm.get('old_whole38_selected_batches',[]):
  names=b.get('exact_top_selectors',[]);directory=b.get('package','').removeprefix('./')
  batches.append({'id':b.get('id'),'package':directory,'selectors':names,'present':[n for n in names if (directory,n) in all_testnames],'missing':[n for n in names if (directory,n) not in all_testnames],'execution_qualification_inherited':False})
 # Conservative name-only intrapackage reachability: duplicate names retained, never evidence of network absence.
 bypkg={}
 for f in funcs:bypkg.setdefault(f['package_key'],{}).setdefault(f['name'],[]).append(f)
 tests=[]
 for f in funcs:
  if not f['top_level_test']:continue
  seen=set();pending=[f['name']];reachable=[]
  while pending:
   n=pending.pop()
   if n in seen:continue
   seen.add(n)
   for h in bypkg[f['package_key']].get(n,[]):
    reachable.extend(h['signals']);pending.extend(c for c in h['calls'] if c not in seen)
  x={k:v for k,v in f.items() if k not in ('calls','signals')};x['direct_signals']=f['signals'];x['reachable_local_signals']=reachable;x['configuration_classification']='STATIC_REVIEW_REQUIRED_NOT_RUNTIME_AUTHORIZATION';tests.append(x)
 assert all(all(v for k,v in x.items() if k!='path') for x in checks),'catalog drift'
 census={'schema':'researchos.current58-go-source-census.v1','source_commit':cat['commit'],'catalog_ref':READS[str(A/'public-source-catalog.json')],'counts':{'public_files':len(rows),'go_files':sum(len(x['go_files']) for x in packages.values()),'package_directories':len({x['directory'] for x in packages.values()}),'package_clauses':len(packages),'top_tests':len(tests),'test_main':sum(f['test_main'] for f in funcs)},'parser':'Offset-preserving Go comments/literal masker, top-level declaration and testing.T signature recognition; no Go parser/compiler/build-tag resolution executed. Reachability is conservative name-only local linkage, not complete call graph.','packages':list(packages.values()),'tests':tests,'old_whole38_batches':batches,'source_only':True,'actual_test_execution':False,'formal_acceptance':False}
 write('census.json',census);write('catalog-current-checks.json',checks);write('all-source-functions.json',funcs);write('source-signals.json',signals);write('signing-boundaries.reference.json',sign)
 write('inputs.json',list(READS.values()))
 print(json.dumps({'counts':census['counts'],'batches':[{k:v for k,v in b.items() if k not in ('selectors','present')}|{'present_count':len(b['present'])} for b in batches],'signals':len(signals),'combined_file_count':len(combined_paths),'catalog_keys':list(cat),'suite_keys':list(sm)},ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except BaseException:
  (O/'audit.failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
