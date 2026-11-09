from pathlib import Path
import urllib.request,urllib.error,json,hashlib,datetime,concurrent.futures
OUT=Path(__file__).absolute().parent
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,raw):
 with (OUT/name).open('xb') as f:f.write(raw)
 return {'path':str(OUT/name),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def doc(name,d):return save(name,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def fetch(label,url):
 r={'url':url,'started_at':now(),'method':'GET','credentials':False,'retry':False}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'ResearchOS-public-resource-review','Accept':'application/vnd.github+json' if 'api.github.com/' in url else '*/*'})
  with urllib.request.urlopen(req,timeout=25) as response:
   raw=response.read(4*1024*1024+1)
   if len(raw)>4*1024*1024:raise ValueError('public response exceeds 4MiB')
   r.update(status=response.status,final_url=response.url,headers=dict(response.headers),body_ref=save(label+'.raw',raw))
 except Exception as e:
  r.update(error=repr(e),status=getattr(e,'code',None))
  if isinstance(e,urllib.error.HTTPError):r['error_body_ref']=save(label+'.error.raw',e.read())
 r['ended_at']=now();doc(label+'.capture.json',r)
 return r
def repository(repo):
 label=repo.replace('/','__');base='https://api.github.com/repos/'+repo
 meta=fetch(label+'-meta',base);head=fetch(label+'-head',base+'/commits/HEAD')
 result={'repository':repo,'meta':meta,'head':head}
 if head.get('status')!=200:return result
 h=json.loads(Path(head['body_ref']['path']).read_bytes());sha=h['sha'];result['commit']=sha
 listing=fetch(label+'-root',base+'/contents?ref='+sha);result['listing']=listing
 if listing.get('status')==200:
  files=json.loads(Path(listing['body_ref']['path']).read_bytes());result['documents']=[]
  for item in files:
   if item['type']=='file' and (item['name'].lower()=='readme.md' or item['name'].lower().startswith('license')):
    result['documents'].append(fetch(label+'-'+item['name'],item['download_url']))
 if repo=='deepseek-ai/awesome-deepseek-agent':
  result['guides']=[fetch(label+'-'+name,'https://raw.githubusercontent.com/'+repo+'/'+sha+'/docs/'+name+'.md') for name in ('pi_mono','opencode','claude_code')]
 return result
repos=['deepseek-ai/awesome-deepseek-agent','anthropics/claude-agent-sdk-typescript','anthropics/anthropic-sdk-typescript','anthropics/anthropic-sdk-go','modelcontextprotocol/go-sdk']
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(repository,repos))
doc('repositories.json',results)
urls=[('deepseek-tools','https://api-docs.deepseek.com/guides/tool_calls/'),('deepseek-thinking','https://api-docs.deepseek.com/guides/thinking_mode/'),('opencode-go','https://opencode.ai/docs/go/'),('claude-overview','https://code.claude.com/docs/en/agent-sdk/overview'),('claude-checkpoint','https://code.claude.com/docs/en/agent-sdk/file-checkpointing'),('claude-sessions','https://code.claude.com/docs/en/agent-sdk/sessions')]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:docs=list(pool.map(lambda x:fetch(*x),urls))
doc('documentation.json',docs)
print(json.dumps({'repositories':[{'repo':r['repository'],'commit':r.get('commit'),'head_status':r['head'].get('status')} for r in results],'documentation_status':[{'url':r['url'],'status':r.get('status'),'error':r.get('error')} for r in docs]},ensure_ascii=False))
