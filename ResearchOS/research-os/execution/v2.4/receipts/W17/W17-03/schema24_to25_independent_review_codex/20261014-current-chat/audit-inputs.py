import pathlib,json,hashlib,subprocess,datetime,sys
E=pathlib.Path(__file__).parent;A=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W17/W17-03/schema24_to25_source_codex/20261014-current-chat');S=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/schema24-to25-native-20261014');BASE='60f8c81a7529081eb51d525ab913d63102148a46';HEAD='1b5ec5d049db7811f6e0d8b143659ea5e2f0836b';TREE='3a7d5085a5389ea89ceae8dab637d1fb4f0f9b43'
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));cache={};checks=[]
def pin(x,source):
 p=pathlib.Path(x['path']);assert not any(y in p.name.lower() for y in ['.dpapi','private.key','privatekey']);k=str(p.resolve()).lower()
 if k not in cache:cache[k]={'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
 got=cache[k];assert got['sha256']==x['sha256'].removeprefix('sha256:') and got['bytes']==x['bytes'],(source,str(p),got,x)
 checks.append({'source':source,'path':str(p),'sha256':got['sha256'],'bytes':got['bytes']})
def git(*args):return subprocess.check_output(['git','-C',str(S),*args])
assert sha((A/'SOURCE_REPORT.md').read_bytes())=='91570238b80db2037d15b6b33862ffc7f39d345179ce6443e34ea742f688f4dc';assert sha((A/'manifest.json').read_bytes())=='00ff8811feefb3ef2c515470a4b6ed4a6438dc540594d0a743ebba7e265717ff'
assert git('rev-parse','HEAD').decode().strip()==HEAD;assert git('rev-parse','HEAD^{tree}').decode().strip()==TREE;assert git('status','--porcelain')==b'';assert git('diff','--check',BASE,HEAD)==b''
scope=read(A/'scope.json');changed=git('diff','--name-only',BASE,HEAD).decode().splitlines();assert len(changed)==22 and set(changed)==set(scope['paths'])
m=read(A/'manifest.json');assert len(m['artifacts'])==274
for x in m['artifacts']:pin(x,'author-artifact')
for role,x in m['program_pins'].items():pin(x,'program-or-tool:'+role)
for name in ['source24-build-inputs','target25-r3-build-inputs']:
 d=read(A/name/'compiler-inputs.json');assert len(d['inputs'])==d['file_count']
 for x in d['inputs']:pin(x,name)
for x in read(A/'final-freeze/source-pins.json'):
 pin(x,'frozen-source');b=(S/x['relative']).read_bytes();assert sha(b)==x['live_sha256'].removeprefix('sha256:');assert b==git('show',HEAD+':'+x['relative']);o=E/'source-snapshot'/x['relative'];o.parent.mkdir(parents=True,exist_ok=True);o.write_bytes(b)
for x in read(A/'final-freeze/readonly-guards.json'):
 pin(x,'readonly-dependency');assert (S/x['relative']).read_bytes()==git('show',BASE+':'+x['relative'])
(E/'source.patch').write_bytes(git('diff','--binary',BASE,HEAD));(E/'git-status.before.raw').write_bytes(git('status','--short'))
for n in ['scope.json','SOURCE_REPORT.md','manifest.json','public-handoff03.config.json']:(E/('author-'+n)).write_bytes((A/n).read_bytes())
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':HEAD,'tree':TREE,'base':BASE,'changed':changed,'author_artifacts':len(m['artifacts']),'compiler_inputs':{'source24':2255,'target25r3':2311},'verified_unique_files':len(cache),'verified_pin_occurrences':len(checks),'programs':m['program_pins'],'all_verified':True,'checks':checks}
(E/'input-integrity-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(E/'unique-input-pins.before.json').write_text(json.dumps(list(cache.values()),ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in r.items() if k not in ['checks','programs','changed']}))
