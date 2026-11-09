"""Single-use post-close COPY inspector. Never called by the read-only sealer.
NOT AUTHORIZED OR EXECUTED during preparation. SQL exists only in this future child.
"""
import argparse, base64, hashlib, json, os, sqlite3, struct, sys
from pathlib import Path
# -I ignores script directory; this exact private path is the only explicit addition.
sys.path.insert(0,str(Path(__file__).resolve().parent))
from controller_common import file_ref,no_alias,write_json,raw_json,Stop

def encoded(kind,value):
 if kind=='null':return {'typeof':kind,'value':None}
 if kind=='integer':return {'typeof':kind,'decimal':str(value)}
 if kind=='real':return {'typeof':kind,'ieee754_le_hex':struct.pack('<d',value).hex()}
 if kind in ('text','blob') and isinstance(value,bytes):return {'typeof':kind,'base64':base64.b64encode(value).decode('ascii')}
 raise Stop('Unexpected SQLite storage class/value')
def q(name):return '"'+name.replace('"','""')+'"'
def sidecars(path):
 facts=[]
 for suffix in ['-wal','-shm','-journal']:
  p=Path(str(path)+suffix)
  try:s=p.lstat()
  except FileNotFoundError:facts.append({'path':str(p),'absent':True});continue
  raise Stop('Sidecar exists: '+str(p))
 return facts

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);ap.add_argument('--sha256',required=True);a=ap.parse_args()
 if not sys.flags.isolated or not sys.flags.no_site or sys._xoptions.get('utf8') is not True:raise Stop('Isolation flags')
 reqref=file_ref(a.request)
 if reqref['sha256']!=a.sha256:raise Stop('Inspector request digest')
 req=raw_json(Path(a.request).read_bytes())
 if req.get('authorized_by_controller') is not True or req.get('schema')!='researchos.w09.closed-copy-inspection.v1':raise Stop('Controller request required')
 p=no_alias(req['copy_ref']['path']);root=no_alias(req['case_root'])
 if not p.is_relative_to(root) or p.name!='closed.sqlite':raise Stop('Only exact own closed copy')
 proof=raw_json(Path(req['closed_proof_ref']['path']).read_bytes())
 if file_ref(req['closed_proof_ref']['path'])!=req['closed_proof_ref']:raise Stop('Closed proof changed')
 before=file_ref(p)
 if before!=req['copy_ref'] or 'sha256:'+before['sha256']!=proof['sha256'] or before['bytes']!=proof['bytes'] or proof['original_close_observed'] is not True or proof['original_and_copy_sidecars_absent'] is not True or proof['copy_not_opened_as_database'] is not True or proof['checkpoint_busy']!=0 or proof['case_failed'] is not False:raise Stop('Close proof incomplete')
 pre=sidecars(p);out=no_alias(req['inspection_output'],False)
 if not out.is_relative_to(root) or out.exists():raise Stop('Output reuse/escape')
 connection=None;err=None;tables=[];schema=[];total_rows=0;total_bytes=0
 try:
  connection=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True,timeout=0)
  connection.text_factory=bytes
  connection.execute('PRAGMA query_only=ON')
  connection.enable_load_extension(False)
  connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH,16*1024*1024)
  connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH,1024*1024)
  integrity=connection.execute('PRAGMA integrity_check').fetchall()
  if integrity!=[(b'ok',)]:raise Stop('Closed copy integrity check failed')
  foreign=connection.execute('PRAGMA foreign_key_check').fetchall()
  if foreign:raise Stop('Closed copy foreign keys invalid')
  schema=connection.execute('SELECT type,name,tbl_name,rootpage,sql FROM sqlite_schema ORDER BY type,name').fetchall()
  for entry in schema:
   if entry[0]!=b'table':continue
   name=entry[1].decode('utf-8','strict')
   columns=connection.execute('PRAGMA table_xinfo('+q(name)+')').fetchall()
   names=[c[1].decode('utf-8','strict') for c in columns]
   if len(names)>256 or not names:raise Stop('Finite column inventory')
   sql='SELECT '+','.join('typeof('+q(c)+'),'+q(c) for c in names)+' FROM '+q(name)
   rows=[]
   for result in connection.execute(sql):
    row=[encoded(result[i].decode('ascii'),result[i+1]) for i in range(0,len(result),2)]
    text=json.dumps(row,ensure_ascii=False,separators=(',',':'))
    rows.append(text);total_rows+=1;total_bytes+=len(text.encode())
    if total_rows>200000 or total_bytes>128*1024*1024:raise Stop('Typed export resource bound')
   rows.sort()
   tables.append({'name':name,'columns':names,'table_xinfo':[[base64.b64encode(v).decode() if isinstance(v,bytes) else v for v in c] for c in columns],'row_count':len(rows),'ordered_multiset_rows':rows})
 finally:
  if connection is not None:connection.close()
 after=file_ref(p);post=sidecars(p)
 if before!=after:raise Stop('Immutable copy changed')
 encoded_schema=[[{'base64':base64.b64encode(v).decode()} if isinstance(v,bytes) else v for v in row] for row in schema]
 write_json(out,{'schema':'researchos.w09.closed-copy-typed-rows.v1','request_ref':reqref,'copy_before':before,'copy_after':after,'sidecars_before':pre,'sidecars_after':post,'mode':'ro&immutable=1','query_only':True,'connection_closed':True,'sqlite_schema':encoded_schema,'tables':tables,'total_rows':total_rows,'encoded_bytes':total_bytes,'implicit_rowid_separately_exported':False,'limits':'Public fresh fixture COPY only. Text/blob encoded by storage class; row multiplicity preserved. This does not authenticate maliciously rewritten input databases.'})
if __name__=='__main__':main()
