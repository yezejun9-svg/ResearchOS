import ctypes, datetime, hashlib, json, pathlib
from ctypes import wintypes
ROOT=pathlib.Path(r'D:\作品集\ResearchOS\research-os'); OUT=pathlib.Path(__file__).parent
DISPATCH=ROOT/'.local/live/current-chat-normal-desktop-first-use-20261012/data/runtime-dispatches/705b11ec99044fef19e85f57e2d2b712'
p=DISPATCH/'effect-4fb5e02fb7c2d82b268957e0b16aca25ad086fc7d50c684394759f00e0f1d6eb.json'
raw=p.read_bytes(); j=json.loads(raw); payload=j['receipt']['payload']; body=payload.get('body')
meta={'status':payload.get('status'),'receipt_state':j['receipt'].get('state'),'body_type':type(body).__name__,'events':[],'source':{'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}}
if isinstance(body,str):
    for line in body.splitlines():
        if not line.startswith('data:'): continue
        text=line[5:].strip()
        if text=='[DONE]': meta['events'].append({'done':True}); continue
        try: event=json.loads(text)
        except ValueError: continue
        for choice in event.get('choices',[]):
            delta=choice.get('delta',choice.get('message',{}))
            meta['events'].append({'finish_reason':choice.get('finish_reason'),'tool_names':[t.get('function',{}).get('name') for t in delta.get('tool_calls',[])],'has_text':bool(delta.get('content'))})
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]; kernel.CreateFileW.restype=wintypes.HANDLE
kernel.CloseHandle.argtypes=[wintypes.HANDLE]; kernel.CloseHandle.restype=wintypes.BOOL
handle=kernel.CreateFileW(str(DISPATCH/'owner.lock'),0x80000000,0,None,3,0x80,None)
valid=handle!=ctypes.c_void_p(-1).value
meta['native_owner_lock']={'operation':'GENERIC_READ; share=0; OPEN_EXISTING','opened':valid,'last_error':0 if valid else ctypes.get_last_error(),'closed':bool(kernel.CloseHandle(handle)) if valid else None}
meta['at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT/'03-effect-and-native-lock.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sources=['apps/desktop/main/lib/desktop-management.js','internal/host/desktop_management_windows.go','internal/host/runtime_qualification_windows.go','internal/host/runtime_verifier_process_windows.go','internal/domain/runtime_qualification_execution_windows.go','internal/domain/runtime_qualification_confirmation_windows.go','internal/domain/runtime_model_windows.go','internal/domain/runtime_model.go','internal/domain/runtime_model_verification.go','internal/domain/runtime_broker_windows.go','internal/domain/runtime_command_queue_windows.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_recovery_windows.go','internal/domain/runtime.go','adapters/runtime/mu/worker.mjs','adapters/runtime/bridge_windows.go','ops/experiment_sandbox/sandbox_windows.go']
refs=[]
for name in sources:
    p=ROOT/name; b=p.read_bytes(); refs.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
(OUT/'04-source-refs.json').write_text(json.dumps({'main_head':'4f4023c956f84d65743f39ce77d6c8899a21ada1','composition_head_observed':'2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02','refs':refs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(meta,ensure_ascii=True))
