"""Invoke one Root-decided concrete operation; does not create approvals."""
import hashlib,json,os,sys
from pathlib import Path
E=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
C=R/'execution/v2.4/receipts/W17/W17-03/native25_controller_adaptation_codex/20261014-current-chat/root_native_pause_migration_controller.py'
assert hashlib.sha256(C.read_bytes()).hexdigest()=='c95ed27b644368fd846bd5ddbd4fc8268cbfea65eb2a8165691456e707a221fa'
m=type(sys)('root_concrete_controller');m.__file__=str(C);sys.modules[m.__name__]=m
exec(compile(C.read_bytes(),str(C),'exec'),m.__dict__)
assert len(sys.argv)==3 and sys.argv[1] in ('sign','publish','release-fixture')
approval_path=Path(sys.argv[2]).resolve();assert approval_path.parent==E
approval=m.public_ref(approval_path);a=m.decode(m.read_ref(approval));snapshot=m.decode(m.read_ref(a['Snapshot']));config=snapshot['config_ref']
try:
 if sys.argv[1]=='sign':
  runtime_private=os.environ.pop('RESEARCHOS_ROOT_RUNTIME_ISSUER_PATH')
  result=m.sign_reviewed(config,approval,runtime_private)
  runtime_private=''
 elif sys.argv[1]=='publish':result=m.publish_signed(config,approval)
 else:result=m.release_fixture(config,approval)
 print(json.dumps({'public_ref':result},ensure_ascii=True))
except BaseException as exc:
 print(json.dumps({'operation_failed':True,'error_type':type(exc).__name__}),file=sys.stderr)
 raise SystemExit(1)
