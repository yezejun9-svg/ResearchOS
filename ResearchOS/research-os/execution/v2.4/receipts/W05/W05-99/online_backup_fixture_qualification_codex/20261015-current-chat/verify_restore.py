"""Fixture-only read-only restore checks; prints counts/digests and selected public binding facts."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

task = Path('D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp')
case = sys.argv[1]
suffix = '-r2' if case == 'Q01' else ''
root = task / 'fixture' / case
source = root / 'source-data/researchos.sqlite'
restored = root / ('restored-data' + suffix) / 'researchos.sqlite'
def connect(path):
    uri = 'file:' + quote(str(path.resolve()).replace('\\','/'),safe='/:') + '?mode=ro'
    con = sqlite3.connect(uri,uri=True)
    con.execute('PRAGMA query_only=ON')
    return con
src, dst = connect(source), connect(restored)
def rows(con):
    return con.execute("SELECT kind,id,body FROM domain_objects ORDER BY kind,id").fetchall()
src_objects, dst_objects = rows(src), rows(dst)
src_without_binding = [(k,i,b) for k,i,b in src_objects if k != 'WorkspaceBinding']
dst_without_binding = [(k,i,b) for k,i,b in dst_objects if k != 'WorkspaceBinding']
src_binding = [(i,json.loads(b)) for k,i,b in src_objects if k == 'WorkspaceBinding']
dst_binding = [(i,json.loads(b)) for k,i,b in dst_objects if k == 'WorkspaceBinding']
out = {'case':case,'source_domain_objects':len(src_objects),'restored_domain_objects':len(dst_objects),
       'non_workspace_domain_objects_byte_equal':src_without_binding == dst_without_binding,
       'workspace_binding_ids_equal':[x[0] for x in src_binding] == [x[0] for x in dst_binding],
       'source_binding_statuses':[b.get('status') for _,b in src_binding],
       'restored_binding_statuses':[b.get('status') for _,b in dst_binding],
       'source_auth_credentials':src.execute('SELECT count(*) FROM auth_credentials').fetchone()[0],
       'restored_auth_credentials':dst.execute('SELECT count(*) FROM auth_credentials').fetchone()[0]}
src_map = {(k,i):json.loads(b) for k,i,b in src_without_binding}
dst_map = {(k,i):json.loads(b) for k,i,b in dst_without_binding}
out['non_workspace_changed_fields'] = [
    {'kind':key[0],'id':key[1],'fields':[field for field in sorted(set(src_map[key]) | set(dst_map[key])) if src_map[key].get(field) != dst_map[key].get(field)],
     'source_status':src_map[key].get('status'),'restored_status':dst_map[key].get('status')}
    for key in sorted(set(src_map) & set(dst_map)) if src_map[key] != dst_map[key]
]
if case == 'Q02':
    assert len(dst_binding) == 1
    binding = dst_binding[0][1]
    target = Path(binding['real_path'])
    expected = task / 'fixture/Q02/restored-data'
    target_abs = target.resolve()
    out['restored_binding_under_new_root'] = target_abs.is_relative_to(expected.resolve())
    out['restored_binding_project_equal'] = binding.get('project_id') == src_binding[0][1].get('project_id')
    out['restored_binding_ref_equal'] = binding.get('authorized_workspace_ref') == src_binding[0][1].get('authorized_workspace_ref')
    file = target / 'src/main.go'
    out['restored_file_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None
    out['restored_empty_directory'] = (target / 'empty').is_dir()
    out['restored_host_files'] = sorted(p.name for p in (expected / 'host').iterdir()) if (expected / 'host').is_dir() else []
src.close(); dst.close()
print(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(',',':')))
