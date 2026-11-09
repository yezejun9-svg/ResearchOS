from pathlib import Path
import re,json,hashlib
N=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=B/'provider_whole9_g1_root_executor_codex/788ce69c409b472799ee1389b778f9da';A=B/'integration_codex/provider-g1-readonly-adjudication-r301'
def put(p,o):
 with (N/p).open('x',encoding='utf-8') as f:f.write(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)
def directive(line):
 s=line.lstrip();m=re.match(r'(?:not ok|ok)\s+[0-9]+\b',s)
 if not m:return False
 return re.search(r'\s+#\s*(skip|todo)\b',s[m.end():],re.I)!=None
def tap(raw):
 need(raw.endswith(b'\n'),'terminal newline');lines=raw.decode('utf-8').splitlines();need(lines[0]=='TAP version 13','TAP version')
 points=[];plans=[];summaries={}
 for line in lines:
  need(not re.match(r'\s*(?:Bail out!|not ok\b)',line),'failure or bailout')
  need(not directive(line),'test point directive')
  m=re.fullmatch(r'ok (\d+) - (.+)',line)
  if m:points.append((int(m[1]),m[2]))
  m=re.fullmatch(r'1\.\.(\d+)',line)
  if m:plans.append(int(m[1]))
  m=re.fullmatch(r'# (tests|pass|fail|cancelled|skipped|todo) (\d+)',line)
  if m:
   need(m[1] not in summaries,'duplicate summary');summaries[m[1]]=int(m[2])
 need(plans==[26] and [x[0] for x in points]==list(range(1,27)),'plan / points')
 need(len(set(x[1] for x in points))==26,'duplicate title')
 need(summaries==dict(tests=26,pass=26,fail=0,cancelled=0,skipped=0,todo=0),'counts')
 return {'points':points,'summaries':summaries,'plan':plans}
raw=(O/'js3.stdout.raw').read_bytes();p=tap(raw);bad=re.compile(rb'#\s*(SKIP|TODO)\b',re.I)
mis=[{'line_number':i+1,'line':l.decode('utf-8')} for i,l in enumerate(raw.splitlines()) if bad.search(l)]
strings=json.loads((A/'tap-string-controls.actual.json').read_text(encoding='utf-8'))['controls'];sr=[]
for c in strings:
 actual=directive(c['line']);need(actual==c['directive'],'directive differs')
 if type(c.get('acceptable')) is bool:need((not actual and re.match(r'\s*not ok\b',c['line']) is None)==c['acceptable'],'point decision differs')
 if type(c.get('summary_acceptable')) is bool:need((int(c['line'].split()[-1])==0)==c['summary_acceptable'],'summary differs')
 sr.append({'line':c['line'],'expected_directive':c['directive'],'independent_actual_directive':actual,'matches':True})
changes={'nonzero-todo':raw.replace(b'# todo 0\n',b'# todo 1\n'),'nonzero-skipped':raw.replace(b'# skipped 0\n',b'# skipped 1\n'),'duplicate-summary':raw+b'# tests 26\n','missing-summary':raw.replace(b'# todo 0\n',b''),'missing-point':re.sub(rb'^ok 26 - .*\n',b'',raw,flags=re.M),'duplicate-point-id':re.sub(rb'^ok 26 - ',b'ok 25 - ',raw,flags=re.M),'actual-not-ok':re.sub(rb'^ok 26 - ',b'not ok 26 - ',raw,flags=re.M),'actual-skip-directive':re.sub(rb'(^ok 26 - .*?)(\n)',rb'\1 # SKIP unavailable\2',raw,flags=re.M),'actual-todo-directive':re.sub(rb'(^ok 26 - .*?)(\n)',rb'\1 # TODO later\2',raw,flags=re.M),'truncated-final-line':raw[:-1],'duplicate-plan':raw+b'1..26\n'}
cr=[]
for k,b in changes.items():
 need(b!=raw,'unchanged mutation')
 try:tap(b)
 except ValueError as e:cr.append({'name':k,'bytes_sha256':sha(b),'rejected':True,'reason':str(e)})
 else:raise ValueError('corrupted raw accepted '+k)
rootcr=json.loads((A/'tap-complete-raw-controls.actual.json').read_text(encoding='utf-8'));need({x['name'] for x in cr}=={x['control'] for x in rootcr['negative_controls']},'control set drift')
go=[json.loads(l) for l in (O/'go3.stdout.raw').read_bytes().splitlines() if l];need(not any(x.get('Action') in ['skip','fail'] for x in go),'go fail/skip');passes=[x['Test'] for x in go if x.get('Action')=='pass' and 'Test' in x];need(len(passes)==13,'go pass count');need(go[-1].get('Action')=='pass' and 'Test' not in go[-1],'package final pass');expected=['TestProviderBindingConfigAndBody','TestProviderBindingReasoningExactHistory','TestProviderBindingWireSignatureWhitespaceAndBlocks'];need(sorted(x for x in passes if '/' not in x)==expected,'go top exact3')
inv=[]
for name in ['go3','js3','node-resolve-alias','go-list','go-compile','go-buildinfo','bundle']:
 j=json.loads((O/(name+'.invocation.json')).read_text(encoding='utf-8'))
 for kind in ['stdout','stderr']:need(sha((O/(name+'.'+kind+'.raw')).read_bytes())==j[kind+'_sha256'],'raw invocation mismatch '+name)
 need(j['actual_exit']==0,'child nonzero '+name);inv.append({'name':name,'actual_exit':j['actual_exit'],'forced_stop':j.get('forced_stop'),'raw_hashes_verified':True})
put('independent_raw_parse.json',{'kind':'OFFLINE_READONLY_PARSING_NOT_PRODUCT_EXECUTION','tap_sha256':sha(raw),'tap':p,'old_false_positive_exact_lines':mis,'string_controls':sr,'whole_tap_mutations':cr,'counts':{'string':len(sr),'whole_raw_negative':len(cr)},'go_actual_top_pass':expected,'go_actual_pass_events':passes,'go_package_final_pass':True,'invocations':inv})
# Actual recorded compilation closure, without invoking Go.
vec=json.loads((O/'compiled-dependencies.before.json').read_text(encoding='utf-8'));norm=lambda p:str(Path(p).resolve()).lower();keys={norm(p) for p in vec};text=(O/'go-list.stdout.raw').read_text(encoding='utf-8-sig');decoder=json.JSONDecoder();pos=0;packages=[]
while pos<len(text):
 while pos<len(text) and text[pos].isspace():pos+=1
 if pos==len(text):break
 obj,pos=decoder.raw_decode(text,pos);packages.append(obj)
fields=['GoFiles','CgoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles'];missing=[];generated=[];count=0
for pkg in packages:
 need(not pkg.get('Error') and not pkg.get('DepsErrors'),'recorded package error')
 for field in fields:
  for name in pkg.get(field,[]):
   p=Path(name) if Path(name).is_absolute() else Path(pkg['Dir'])/name;count+=1
   if norm(p) not in keys:
    if pkg.get('ImportPath','').endswith('.test') and p.name=='_testmain.go':generated.append(str(p))
    else:missing.append({'path':str(p),'package':pkg['ImportPath'],'field':field})
 if pkg.get('Module',{}).get('GoMod') and norm(pkg['Module']['GoMod']) not in keys:missing.append({'gomod':pkg['Module']['GoMod']})
need(not missing,'recorded Go compilation inputs missing')
build=(O/'go-compile.stderr.raw').read_text(encoding='utf-8');artifact=json.loads((O/'artifacts.before-case.json').read_text(encoding='utf-8'));testm=[x for x in artifact if Path(x).name=='_testmain.go'];need(len(testm)==1,'testmain ambiguous');need(testm[0] in build or testm[0].replace('\\','/') in build,'testmain not in compile log');need('domain.g1.test.exe' in build,'exe output absent compile log')
put('independent_build_chain.json',{'recorded_go_list_packages':len(packages),'recorded_compiler_entries':count,'missing':missing,'go_list_generated_placeholders':generated,'actual_generated_testmain':testm,'compile_stderr_testmain_path_found':True,'compile_stderr_exe_output_found':True,'actual_invocation_chain':['bundle child0','go-list child0','go-compile child0','go-buildinfo child0','artifacts.before-case','inputs.pre-case','go3 child0','js3 child0 with harness forced_stop label','taskkill128','outer1'],'new_build_or_test':False})
print(json.dumps({'offline_strings':len(sr),'offline_raw_negatives':len(cr),'go_pass':len(passes),'tap_pass':26,'packages':len(packages),'compiler_entries':count,'missing':missing}))
