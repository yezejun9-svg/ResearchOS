import ast,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;old=HERE/'register_product_v1_go_check.py';new=HERE/'register_product_v1_go_check_v2.py';assert not new.exists();raw=old.read_text(encoding='utf8');needle="r'\./[A-Za-z0-9_/]+'";assert raw.count(needle)==1
text=raw.replace(needle,"r'\./[A-Za-z0-9_/-]+'");ast.parse(text);new.write_text(text,encoding='utf8');assert old.read_text(encoding='utf8')==raw
print('Old registrar preserved; v2 allows hyphenated Go package names. SHA256 '+hashlib.sha256(new.read_bytes()).hexdigest())
