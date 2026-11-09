"""Read/hash/AST checks only; never import or execute the publisher or gate."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')


def pin(p):
    raw = p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


def put(name, value):
    with (HERE/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())


fixed = json.loads((HERE/'fixed-inputs.json').read_bytes())
selection = json.loads((HERE/'selection.static.json').read_bytes())
checks = []
after = []
for name, ref in fixed.items():
    got = pin(Path(ref['path']))
    checks.append({'name':'fixed:'+name,'passed':got==ref})
    after.append(got)
for row in selection['files']:
    p = ROOT/row['path']; raw = p.read_bytes()
    got = pin(p); after.append(got)
    checks.append({'name':'source:'+row['path'],'passed':got['bytes']==row['bytes'] and
                   got['sha256']==row['sha256'] and
                   hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob']})
tree = Path(fixed['tree']['path']).read_bytes()
names = [r.split(b'\t',1)[1].decode('utf-8') for r in tree[:-1].split(b'\0')]
checks.append({'name':'full-sealed-tree-no-casefold-alias','passed':len(names)==len(set(x.casefold() for x in names))})
raw = (HERE/'publish.proposed.py').read_bytes(); syntax = ast.parse(raw)
imports = [ast.unparse(n) for n in ast.walk(syntax) if isinstance(n,(ast.Import,ast.ImportFrom))]
checks.append({'name':'no-native/network/SQL-import','passed':not any(x in '\n'.join(imports) for x in ['subprocess','ctypes','sqlite3','urllib','socket'])})
checks.append({'name':'gate-only-source-predicate','passed':b'module.validate_current58_source(' in raw and b'module.load_scope(' not in raw and b'module.validate_grant(' not in raw})
checks.append({'name':'request-before-output-exclusive','passed':raw.index(b'module.validate_current58_source(')<raw.index(b'    out.mkdir()')})
checks.append({'name':'root-source-no-Git-API','passed':b'git.exe' not in raw and b'subprocess' not in raw and b'.unlink(' not in raw})
checks.append({'name':'catalogue-new-source-union','passed':selection['selected_file_count']==len(selection['files']) and len(selection['combined58_paths'])==58 and len(selection['added_paths'])==42 and not selection['changed_old_paths']})
checks.append({'name':'single-read-verify-buffer','passed':b'raw = read(ref[\'path\'])' in raw and b'    return raw\n\n\ndef doc' in raw})
checks.append({'name':'actual-forward-review-required','passed':b'f14dcdf6cfa2676db6022e7a852abd38e2095bc45a0529566b10997001a03624' in raw})
for name in ['publish.proposed.py','static_audit.py']:
    ast.parse((HERE/name).read_bytes())
put('inputs.after.static.json',{'files':after,'drift':[x['name'] for x in checks if not x['passed']]})
put('static-audit.json',{'schema':'researchos.fresh58-public-source-producer-static-audit.v1',
    'checks':checks,'failed':sum(not c['passed'] for c in checks),'candidate_imported':False,'candidate_executed':False,
    'gate_imported_or_executed':False,'actual_compiler_graph':None,'source_count':len(selection['files']),
    'Go_count':selection['all_platform_Go_count'],'native_target_calls':0,'AST_files':2,
    'source_publisher_ref':pin(HERE/'publish.proposed.py'),'source_acceptance':False})
print(json.dumps({'checks':len(checks),'failed':sum(not c['passed'] for c in checks),
                  'audit_ref':pin(HERE/'static-audit.json')},ensure_ascii=False))
if any(not c['passed'] for c in checks):
    raise SystemExit(1)
