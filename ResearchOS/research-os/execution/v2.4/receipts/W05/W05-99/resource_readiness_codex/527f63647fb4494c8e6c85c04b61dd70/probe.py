"""Desktop resource metadata only: no GUI/provider launch, private DB or configuration read."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,ctypes,importlib.util

ROOT=Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assets=[ROOT/'.local/nvda-w1303/nvda_2026.2.exe',ROOT/'.local/nvda-w1303/portable/nvda.exe',
 ROOT/'apps/desktop/node_modules/electron/dist/electron.exe',ROOT/'apps/web/node_modules/vite/bin/vite.js',
 ROOT/'.local/w1401-mu-worker/mu-worker.mjs',ROOT/'third_party/mu/packages/coding-agent/dist/core/sdk.js']
rows=[{'path':str(p),'exists':p.is_file(),'sha256':sha(p) if p.is_file() else None,'size':p.stat().st_size if p.is_file() else None} for p in assets]
modules={name:importlib.util.find_spec(name) is not None for name in ['psutil','win32api','win32con','win32gui','win32process']}
processes=[]
if modules['psutil']:
 import psutil
 for p in psutil.process_iter(['pid','name']):
  name=(p.info['name'] or '').lower()
  if name in ('nvda.exe','electron.exe','researchos.exe','researchos-control.exe','workspace-fixture.exe'):processes.append(p.info)
user32=ctypes.windll.user32
user32.GetForegroundWindow.restype=ctypes.c_void_p
hwnd=user32.GetForegroundWindow();pid=ctypes.c_ulong()
user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd),ctypes.byref(pid))
credentials=[]
for name in ['DEEPSEEK_API_KEY','MOONSHOT_API_KEY']:
 value=os.environ.get(name)
 credentials.append({'variable_name':name,'present':bool(value),'sha256':hashlib.sha256(value.encode()).hexdigest() if value else None})
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'assets':rows,'python_modules':modules,'filtered_processes':processes,
 'foreground_observation':{'hwnd':hwnd,'pid':pid.value,'titles_read':False,'keyboard_sent':False,'focus_requested':False,'target_accessibility_verified':False},
 'process_env_credentials':credentials,'credential_note':'Only process env names and irreversible SHA; no values/private config/DPAPI read. Presence is not usable qualification or proof of a changed credential.',
 'new_gui_processes':0,'provider_calls':0},ensure_ascii=False))
