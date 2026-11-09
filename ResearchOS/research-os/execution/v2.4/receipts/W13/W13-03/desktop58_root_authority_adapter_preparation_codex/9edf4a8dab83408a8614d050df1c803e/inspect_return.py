import ast,json
from pathlib import Path
p=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_cli2_controller_revision_preparation_codex/48d76385c123478e90864ebbfc2ad24a/authorization_gate.current58.final.proposed.py')
b=p.read_bytes();s=b.decode();node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='validate_grant')
ret=node.body[-1]
print(json.dumps({'CRLF':b.count(b'\r\n'),'LF':b.count(b'\n'),'return_node':type(ret).__name__,'span':[ret.lineno,ret.end_lineno],'raw_segment':ast.get_source_segment(s,ret)},ensure_ascii=False))
