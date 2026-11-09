from review_driver import *
import socket,time
from urllib.request import urlopen
with socket.socket() as s: s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
p=run('019-preview-expanded',[NODE,str(WT/'apps/web/node_modules/vite/bin/vite.js'),'preview','--host','127.0.0.1','--port',str(port),'--strictPort'],WT/'apps/web',start=True)
try:
 for i in range(80):
  try:
   with urlopen(f'http://127.0.0.1:{port}/',timeout=.4) as r:
    if r.status==200: break
  except Exception: time.sleep(.2)
 run('020-expanded-forms',[NODE,str(E/'expanded_forms_probe.cjs'),f'http://127.0.0.1:{port}',str(WT),str(E/'expanded-forms-01')],env={'RESEARCHOS_PLAYWRIGHT_MODULE':PLAY})
finally:
 p.terminate();p.wait(timeout=10);save(E/'commands/019-preview-expanded/stop.json',dict(pid=p.pid,native_exit=p.returncode))
