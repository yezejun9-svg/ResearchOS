import pathlib,json,hashlib,datetime,subprocess,sys,concurrent.futures
sys.stdout.reconfigure(encoding='utf-8')
H=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def fetch(item):
 name,url=item;d=H/'raw'/name;d.mkdir(parents=True,exist_ok=False)
 argv=['C:/Windows/System32/curl.exe','--disable','--proto','=https','--tlsv1.2','--location','--max-redirs','4','--connect-timeout','15','--max-time','45','--silent','--show-error','--user-agent','ResearchOS-Public-Source-Review/1.0','--dump-header',str(d/'headers.raw'),'--output',str(d/'response.raw'),'--write-out','%{http_code}',url]
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(argv,cwd=H,capture_output=True)
 (d/'stdout.raw').write_bytes(p.stdout);(d/'stderr.raw').write_bytes(p.stderr)
 o={'started_at':started,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'cwd':str(H),'exit':p.returncode,'status_stdout':p.stdout.decode(errors='replace'),'source_url':url,'mode':'PUBLIC_READ_NO_AUTH_NO_MODEL','files':{}}
 for n in ['headers.raw','response.raw','stdout.raw','stderr.raw']:
  f=d/n
  if f.exists():b=f.read_bytes();o['files'][n]={'bytes':len(b),'sha256':sha(b)}
 (d/'invocation.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'name':name,'exit':p.returncode,'status':o['status_stdout'],'response':o['files'].get('response.raw')}
if __name__=='__main__':
 entries=json.loads(sys.argv[1])
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for result in pool.map(fetch,entries):print(json.dumps(result))
