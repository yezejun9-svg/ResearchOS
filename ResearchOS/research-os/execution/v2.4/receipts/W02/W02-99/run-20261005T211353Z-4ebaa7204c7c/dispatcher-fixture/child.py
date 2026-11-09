import json,os,sys,time
mode=sys.argv[1]
if mode=='timeout': time.sleep(30)
if mode=='badexit': sys.exit(17)
if mode=='malformed': print('not json'); sys.exit(0)
if mode=='null': print('null'); sys.exit(0)
if mode=='array': print('[]'); sys.exit(0)
if mode=='duplicate-key': print('{"status":"FAIL","status":"PASS","assertion_ids":["X"]}'); sys.exit(0)
if mode=='nonfinite': print('{"status":"PASS","assertion_ids":["X"],"cost":NaN}'); sys.exit(0)
ids=[] if mode=='zero' else ['REAL-CHILD']
if mode=='duplicate': ids=['X','X']
if mode=='secret':
    value=os.environ['RESEARCHOS_W0299_API_KEY']
    print(value,file=sys.stderr)
    ids=[value]
if mode=='no-inheritance': assert 'RESEARCHOS_W0299_API_KEY' not in os.environ
print(json.dumps({'status':'PASS','assertions':len(ids),'assertion_ids':ids,'scope':'FIXTURE'}))
