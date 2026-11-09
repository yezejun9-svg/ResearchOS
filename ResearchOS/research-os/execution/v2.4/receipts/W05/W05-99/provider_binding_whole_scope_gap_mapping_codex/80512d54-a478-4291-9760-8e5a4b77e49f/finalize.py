import pathlib,json,hashlib,datetime
O=pathlib.Path(__file__).parent
def r(p):
 b=p.read_bytes();return {'path':str(p).replace('\\','/'),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def w(n,x):
 p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return r(p)
w('tool_read_invocations.json',{'actual_outer_exit_code':0,'tool_chunks':['0b0971','5659db','aa56e7','a4f590','70947c','792374','f55381','926660','570b4b','587824','a172d3','43c580','56f920','0c2974'],'scope':'read source/rg/Git; write only owned review scripts/snapshots/JSON','note':'No product/native tests or SQL; initial console excerpts may be truncated. Complete byte snapshots and Git subprocess raw are retained. No invented native exit for pipeline components.'})
entries=[r(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
m=w('manifest.json',{'schema':'researchos.public-review-manifest.v1','entry_count':len(entries),'entries':entries,'excludes':['manifest.json','handoff.json']})
h=w('handoff.json',{'decision':'READONLY_GAP_MAPPING_NO_EXECUTION_OR_SOURCE_ACCEPTANCE','mapping_ref':r(O/'mapping.json'),'manifest_ref':m,'audit_ref':r(O/'read_audit.json'),'source_comparison_ref':r(O/'source_comparison.json'),'failure_origins_ref':r(O/'failure_origins.json'),'candidate_commit':'6fb5263681c17f0e50920c354dc07ed440a23714','main_head':'2cdb0d43d5a600eef13c8f1735946a9adf52d079','handler_unfrozen':True,'input_count':70,'cases':0,'source_or_canonical_mutation':0,'formal_increment':0})
print(json.dumps({'mapping':r(O/'mapping.json'),'manifest':m,'handoff':h,'entry_count':len(entries)},ensure_ascii=True))
