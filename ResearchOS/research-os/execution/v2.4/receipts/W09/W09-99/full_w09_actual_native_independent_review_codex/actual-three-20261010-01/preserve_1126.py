from pathlib import Path
import types,json
D=Path(__file__).resolve().parent
p=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/w09_formal_consumer_readiness_readonly_codex/readiness-20261010-01/preserve_queries.py')
m=types.ModuleType('preserve');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);m.D=D
print(json.dumps(m.capture('38ad19',1126,'SOURCE_REVIEWER_PREPARE_GUARD_NOT_INCLUDED_IN_READSET',1),ensure_ascii=False),flush=True)
