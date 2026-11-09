import json,socket
from pathlib import Path
from datetime import datetime,timezone
out=Path(__file__).resolve().parent/'loopback-capability.json'
assert not out.exists(),'Do not repeat a failed capability probe without new evidence'
report={'at':datetime.now(timezone.utc).isoformat(),'purpose':'One self-owned ephemeral numeric-loopback capability check before any model-server startup','existing_endpoints_contacted':0,'ollama_requests':0,'model_inference_calls':0,'process_starts':0,'D_writes':0,'port_scanning':False}
listener=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client=None;accepted=None
try:
    listener.settimeout(2)
    listener.bind(('127.0.0.1',0))
    listener.listen(1)
    report['owned_port']=listener.getsockname()[1]
    client=socket.socket(socket.AF_INET,socket.SOCK_STREAM);client.settimeout(2)
    client.connect(listener.getsockname())
    accepted,_=listener.accept();accepted.settimeout(2)
    client.sendall(b'owned-scope-probe')
    assert accepted.recv(64)==b'owned-scope-probe'
    report['status']='SELF_OWNED_LOOPBACK_AVAILABLE'
except OSError as error:
    report.update(status='SELF_OWNED_LOOPBACK_BLOCKED',error_type=type(error).__name__,errno=error.errno,winerror=getattr(error,'winerror',None))
finally:
    for handle in [accepted,client,listener]:
        if handle is not None:handle.close()
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
