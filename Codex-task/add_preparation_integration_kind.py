import ast
from pathlib import Path
p=Path(__file__).resolve().parent/'prepare_product_v1_integration.py';s=p.read_text(encoding='utf8');a="'native-rpc-wiring','native-qualification-producer']";assert s.count(a)==1;s=s.replace(a,"'native-rpc-wiring','native-qualification-producer','native-preparation-wiring']")
a="'native-qualification-producer':'feat(runtime): add bounded native qualification for synthetic tasks'}";assert s.count(a)==1;s=s.replace(a,"'native-qualification-producer':'feat(runtime): add bounded native qualification for synthetic tasks','native-preparation-wiring':'fix(runtime): settle stopped native preparation without model evidence'}")
a="('native-rpc-runtime','native-rpc-wiring','native-qualification-producer')";assert s.count(a)==1;s=s.replace(a,"('native-rpc-runtime','native-rpc-wiring','native-qualification-producer','native-preparation-wiring')");ast.parse(s);p.write_text(s,encoding='utf8');print('Added reviewed preparation integration kind; not executed')
