from pathlib import Path
import types,json
D=Path(__file__).resolve().parent
old=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/w09_formal_consumer_readiness_readonly_codex/readiness-20261010-01/preserve_queries.py')
m=types.ModuleType('original_io_preserver');m.__file__=str(old)
exec(compile(old.read_bytes(),str(old),'exec'),m.__dict__)
m.D=D
refs=m.capture('ba56b6',1122,'SOURCE_REVIEWER_ONE_SHOT_GUARD_REACQUIRE',1)
print(json.dumps(refs,ensure_ascii=False),flush=True)
