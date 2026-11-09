from pathlib import Path
import ast,json,hashlib
o=Path(__file__).parent
old=(o/'audit.py').read_bytes()
new=old.replace(b"c['grant_ref']['sha256'] and set",b"c['grant_ref']['sha256']] and set")
ast.parse(new)
with (o/'audit.v2.py').open('xb') as f:f.write(new)
for tool,outer,native,error in [('d10ed8',1,1,'Own audit SyntaxError missing list closing bracket line53; explicit PythonNativeExit=1'),('54b991',1,None,'PowerShell quoting truncated own Python -c before any file writes; SyntaxError; no explicit native exit bridge')]:
 p=o/('failure-origin.'+tool+'.json')
 v={'tool_id':tool,'actual_outer_exit':outer,'actual_native_exit':native,'error':error,'candidate_executions':0,'original_script':{'path':str(o/'audit.py'),'sha256':hashlib.sha256(old).hexdigest(),'bytes':len(old)},'raw_tool_trace_available_in_conversation':True,'raw_file_capture':False,'outside_registered_cut':516,'count_once':True}
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 b=p.read_bytes();print(json.dumps({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)},ensure_ascii=False))
