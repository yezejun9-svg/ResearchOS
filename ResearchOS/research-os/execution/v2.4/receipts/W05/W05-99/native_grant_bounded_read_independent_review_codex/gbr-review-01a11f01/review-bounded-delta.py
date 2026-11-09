from pathlib import Path
import ast, copy, hashlib, json, re
O=Path(__file__).resolve().parent
checks=[]
def check(name,value,details=None):checks.append(dict(name=name,passed=bool(value),details=details))
def save(name,obj):
 with (O/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
new=(O/'packet/011/native_grant_public_pin_archive.py').read_bytes();old=(O/'packet/018/native_grant_public_pin_archive.py').read_bytes();d=json.loads((O/'packet/008/exact-inverse.json').read_bytes())
check('exact helper pin',hashlib.sha256(new).hexdigest()=='96a7195080dc99a6b669336c7563a51cc1ba60b4f3584b6f4b7a6330a05d0771' and len(new)==23941)
check('old independently reviewed helper pin',hashlib.sha256(old).hexdigest()=='baad4ec59c1ed4451ad8d054f6800f7f8c3e8a4836d004adf367f0d667782ef4' and len(old)==23856)
a=d['old'].encode();b=d['new'].encode();check('exact forward',old.count(a)==1 and old.replace(a,b)==new);check('whole byte inverse',new.count(b)==1 and new.replace(b,a)==old)
nt=ast.parse(new);ot=ast.parse(old)
check('all other top-level AST identical',[ast.dump(n) for n in nt.body if not isinstance(n,ast.FunctionDef) or n.name!='read_ref']==[ast.dump(n) for n in ot.body if not isinstance(n,ast.FunctionDef) or n.name!='read_ref'])
readnode=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='read_ref')
check('with-managed binary read and length before SHA',[type(n).__name__ for n in readnode.body]==['Expr','With','Expr','Expr','Return'] and ast.unparse(readnode.body[1].body[0].value)=='stream.read(value[\'bytes\'] + 1)' and 'len(raw)' in ast.unparse(readnode.body[2]) and 'digest(raw)' in ast.unparse(readnode.body[3]))
safe_names={'require','exact','ref','digest','read_ref'}
module=ast.Module(body=[copy.deepcopy(n) for n in nt.body if isinstance(n,ast.FunctionDef) and n.name in safe_names],type_ignores=[])
check('extract exactly five functions, no entrypoint',len(module.body)==5 and all(n.name in safe_names for n in module.body))
cap=128*1024*1024
cases=[('empty',0,0,None,False,True),('exact',4,4,None,False,True),('short',4,3,None,False,False),('one_extra',4,5,None,False,False),('zero_extra',0,1,None,False,False),('huge_actual_tiny_declared',4,10**12,None,False,False),('cap_request_bounded',cap,0,None,False,False),('bad_sha',4,4,None,True,False),('read_error',4,4,'read',False,False),('negative',-1,0,None,False,False),('bool',True,1,None,False,False),('float',4.0,4,None,False,False),('over_cap',cap+1,0,None,False,False),('string','4',4,None,False,False),('none',None,0,None,False,False)]
observations=[]
for name,declared,actual,err,badsha,want_ok in cases:
 trace=dict(opens=[],reads=[],closed=False,digest_calls=0)
 class Stream:
  def __enter__(self):return self
  def __exit__(self,*args):trace['closed']=True
  def read(self,n):
   trace['reads'].append(n)
   if err=='read':raise OSError('synthetic read error')
   return b'x'*min(actual,n)
 class FakePath:
  def __init__(self,value):self.value=value
  def open(self,mode):trace['opens'].append(mode);return Stream()
 ns={'Path':FakePath,'re':re,'hashlib':hashlib,'canonical':lambda value:value}
 exec(compile(ast.fix_missing_locations(copy.deepcopy(module)),'<independent-read-ref-AST>','exec'),ns)
 actual_digest=ns['digest']
 def observe_digest(raw):trace['digest_calls']+=1;return actual_digest(raw)
 ns['digest']=observe_digest
 valid_declared=type(declared) is int and 0<=declared<=cap
 wanted_raw=b'x'*declared if valid_declared and declared<100 else b''
 value=dict(path='D:/public-source-only/synthetic.dat',sha256='sha256:'+('0'*64 if badsha else hashlib.sha256(wanted_raw).hexdigest()),bytes=declared)
 result=None;error=None
 try:result=ns['read_ref'](value)
 except (ValueError,OSError) as e:error=type(e).__name__
 ok=error is None
 correct=ok==want_ok
 if valid_declared:
  correct=correct and trace['reads']==[declared+1] and trace['opens']==['rb'] and trace['closed']
  if actual!=declared or err:correct=correct and trace['digest_calls']==0
 else:correct=correct and not trace['opens'] and not trace['reads'] and trace['digest_calls']==0
 if want_ok:correct=correct and result==wanted_raw and trace['digest_calls']==1
 check('boundary:'+name,correct,dict(declared=declared,actual_virtual_length=actual,trace=trace,result_ok=ok,error=error))
 observations.append(dict(name=name,pass_expected=want_ok,passed=correct,trace=trace,error=error))
save('bounded-delta-checks.json',checks);save('boundary-observations.json',dict(extracted_functions=sorted(safe_names),canonical_path_predicate='stubbed only for read-boundary controls; unchanged path semantics reused from prior independent review',real_file_IO=False,helper_imported_or_main_executed=False,builder_imported_or_compose_executed=False,cases=observations))
print(json.dumps(dict(checks=len(checks),failed=[x['name'] for x in checks if not x['passed']],boundary_cases=len(cases),source_inverse=True,helper_actual=False,product_native_exit=None)))
