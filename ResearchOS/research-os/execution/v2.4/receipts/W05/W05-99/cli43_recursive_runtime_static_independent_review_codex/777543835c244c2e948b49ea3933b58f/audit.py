import ast,hashlib,json,struct,collections
from pathlib import Path
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';N=P/'cli43_windows_recursive_resource_catalog_codex/ca31885a78a74dff8ac108e20542331e'
inputs={};checks=[];pe_bytes={}
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 if not v:raise RuntimeError(n)
def rd(p):
 p=Path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if str(p) in inputs:ck('stable '+str(p),inputs[str(p)]==r)
 inputs[str(p)]=r;return b
def ref(p):rd(p);return inputs[str(p)]
def vr(r):
 b=rd(r['path']);ck('pin '+r['path'],len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']);return b
def doc(p):return json.loads(rd(p))
def save(n,x):
 with (O/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
for n,h in [('handoff.json','76a863187d325f9725fff812910b67560f7e2f9e1eb934519e9922fbd670146d'),('manifest.json','0dffae3457fb2812fd949b67441f0758a7961c98793aea5aafe5e7713bd274a3')]:ck('Root pin '+n,ref(N/n)['sha256']==h)
h=doc(N/'handoff.json');mf=doc(N/'manifest.json');ck('14 manifest members',mf['count']==len(mf['entries'])==14)
for r in mf['entries']:vr(r)
runtime=json.loads(vr(h['runtime_v3_ref']));old=json.loads(vr(runtime['old_basis_ref']));union=json.loads(vr(h['system32_union_ref']))['files'];parsed=json.loads(vr(h['parsed_ref']))['files'];edoc=json.loads(vr(h['edge_ref']));find=json.loads(vr(h['findings_ref']));inventory=doc(N/'system32-inventory.json')['files'];unknownindex=json.loads(vr(h['unknown_index_ref']))
bef=json.loads(vr(h['before_ref']))['files'];aft=json.loads(vr(h['after_ref']));ck('author57 input rows and no drift',len(bef)==57 and bef==aft['files'] and aft['drift']==[])
oldmap={r['path'].casefold():r for r in old['files']};newmap={r['path'].casefold():r for r in runtime['files']};umap={r['path'].casefold():r for r in union}
ck('counts 1221/1242/54',len(oldmap)==len(old['files'])==1221 and len(newmap)==len(runtime['files'])==1242 and len(umap)==len(union)==54)
ck('old dictionary refs retained exact',all(newmap.get(k)==v for k,v in oldmap.items()))
added={k:v for k,v in newmap.items() if k not in oldmap};ck('new21 exact read-only evidence',len(added)==21 and added=={r['path'].casefold():r for r in runtime['added_static_candidate_files']} and all(umap.get(k)==v for k,v in added.items()))
ck('union all current runtime refs',all(newmap.get(k)==v for k,v in umap.items()))
ck('only54 publicPE+3 metadata inputs',sum(Path(r['path']).parent==Path('C:/Windows/System32') for r in bef)==54)
for r in bef:
 b=vr(r)
 if Path(r['path']).parent==Path('C:/Windows/System32'):
  p=Path(r['path']);s=p.lstat();ck('ordinary public System32 file '+p.name,p.is_file() and not p.is_symlink() and not(getattr(s,'st_file_attributes',0)&0x400));pe_bytes[r['path'].casefold()]=b
ck('exact union observed',set(pe_bytes)==set(umap))
source=rd(Path(runtime['old_basis_ref']['path']).parent/'observe.py').decode();tree=ast.parse(source);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='pe_imports');segment=ast.get_source_segment(source,fn).encode();ck('parser exact old AST segment',segment==vr(runtime['parser_ref']))
ast.parse(rd(N/'recursive.py'));ast.parse(rd(N/'pe-parser.exact.py'))
# Independently check recorded PE evidence against physical file byte offsets; no target parser import/call.
recorded_imports={};total_imports=0
for row in parsed:
 r=row['image_ref'];key=r['path'].casefold();b=pe_bytes[key];pe=row['pe'];ck('parsed ref/status '+key,row['parse_status']=='PARSED' and r==umap[key]==pe['image_ref'])
 u16=lambda o:struct.unpack_from('<H',b,o)[0]
 u32=lambda o:struct.unpack_from('<I',b,o)[0]
 off=u32(0x3c);opt=off+24;magic=u16(opt);count=u16(off+6);optsize=u16(off+20)
 ck('physical PE header '+key,b[:2]==b'MZ' and b[off:off+4]==b'PE\0\0' and off==pe['pe_header_file_offset'] and hex(magic)==pe['optional_magic'])
 sections=[]
 for i in range(count):
  q=opt+optsize+40*i;sections.append({'name':b[q:q+8].rstrip(b'\0').decode('ascii'),'virtual_size':u32(q+8),'rva':u32(q+12),'raw_size':u32(q+16),'raw_offset':u32(q+20)})
 ck('physical section table '+key,sections==pe['sections'])
 headers=u32(opt+60)
 def fileoff(rva):
  if rva<headers:return rva
  matches=[s for s in sections if s['rva']<=rva<s['rva']+s['raw_size']]
  ck('unique RVA '+key+':'+str(rva),len(matches)==1)
  return matches[0]['raw_offset']+rva-matches[0]['rva']
 base=opt+(112 if magic==0x20b else 96);dirs={}
 for d in pe['directories']:
  if d.get('status')=='DIRECTORY_NOT_PRESENT':continue
  q=base+8*d['index'];ck('physical import directory '+key+':'+str(d['index']),q==d['entry_file_offset'] and u32(q)==d['rva'] and u32(q+4)==d['size']);dirs[d['index']]=d
 imports=[]
 for item in pe['imports']:
  delay=item['basis']=='STATIC_PE_DELAY_IMPORT_DIRECTORY';idx=13 if delay else 1;width=32 if delay else 20;q=item['descriptor_file_offset'];d=dirs[idx]
  name_rva=u32(q+(4 if delay else 12));name_offset=fileoff(name_rva);end=b.find(b'\0',name_offset,name_offset+512)
  ck('physical descriptor and name '+key+':'+str(q),end>=name_offset and name_rva==item['name_rva'] and name_offset==item['name_file_offset'] and b[name_offset:end].decode('ascii')==item['dll_name'] and item['image_ref']==r and (not delay or u32(q)==1))
  candidates=[fileoff(d['rva']+i*width) for i in range(d['size']//width)]
  ck('descriptor in actual directory '+key+':'+str(q),q in candidates)
  imports.append(item)
 recorded_imports[key]=imports;total_imports+=len(imports)
ck('54 parsed rows',len(parsed)==54 and set(recorded_imports)==set(umap))
edgekeys=['dll_name','basis','image_ref','descriptor_file_offset','name_rva','name_file_offset']
resolution=collections.Counter()
for edge in edoc['edges']:
 key=edge['parent_pe_ref']['path'].casefold();orig={k:edge[k] for k in edgekeys};ck('edge exact parsed descriptor',edge['parent_pe_ref']==umap[key] and orig in recorded_imports[key]);resolution[edge['resolution']]+=1
 child=edge.get('existing_file_ref')
 if child is not None:ck('resolved child read exact ref',umap.get(child['path'].casefold())==child and Path(child['path']).name.casefold()==edge['dll_name'].casefold())
 else:ck('unread/unknown no invented ref',edge['resolution'] in ['UNKNOWN','NOT_COLLECTED_CAP_128','DISCOVERED_NOT_READ_BEFORE_COLLECTION_STOP'])
ck('exact2148 edges',len(edoc['edges'])==h['edges']==2148)
reasons=collections.Counter(x.get('reason',x.get('resolution')) for x in edoc['unknown']);ck('unknown counts',dict(reasons)==h['unknown_reason_counts'])
unread=find['unread_discovered'];ck('cap128 and74 unread',len(unread)==74 and find['discovered_count']==128 and find['files_read_count']==54 and find['cap_reached'] is True)
ck('unread never catalogued',all(x['path'].casefold() not in newmap and x['path'].casefold() not in umap for x in unread))
ck('capped candidate not catalogued',h['boundary']['inventory_path'].casefold() not in newmap and h['boundary']['existing_file_ref'] is None)
for entry in unknownindex['names']:
 for loc in entry['edge_locators']:
  prefix,index=loc['json_pointer'].rsplit('/',1);ck('unknown locator',prefix=='/unknown' and edoc['unknown'][int(index)]['dll_name'].casefold()==entry['name'].casefold())
ck('honest incomplete policy',runtime['future_actual_loaded_complete'] is None and runtime['execution_authorized'] is False and runtime['unknown_loaded_module_policy']=='REFUSE_UNRECOGNIZED_RESOURCE' and h['static_dependency_graph_complete'] is False)
for r in bef:vr(r)
summary={'checks':len(checks),'failed':sum(not c['passed'] for c in checks),'PEfiles_current_hash_checked':54,'author_input_rows_checked':57,'inherited_dictionary_refs':1221,'new_candidate_refs':21,'runtime_total':1242,'actual_inherited_all1242_rehash':False,'parsed_import_descriptors_checked':total_imports,'edge_records_checked':2148,'unread_nodes_not_opened':74,'cap':128,'target_parser_import_or_execution':0,'DLL_load_or_native_calls':0}
save('audit.json',{'checks':checks,'input_refs':list(inputs.values()),'summary':summary,'resolution_counts':dict(resolution),'unknown_counts':dict(reasons)})
save('review.json',{'schema':'researchos.cli43-recursive-runtime-resource-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'STATIC_PARTIAL_RUNTIME_CATALOG_REVIEWED_FOR_FUTURE_EXACT_SCOPE_BINDING','requested_changes':[],'execution_authorized':False,'source_acceptance':False,'formal_increment':0,'input_handoff_ref':ref(N/'handoff.json'),'input_manifest_ref':ref(N/'manifest.json'),'runtime_ref':h['runtime_v3_ref'],'OS_union_ref':h['system32_union_ref'],'audit_ref':ref(O/'audit.json'),'verified_facts':['All1221 inherited path/hash/length dictionaries remain exact;21 additions are among54 physically read/hashed System32 PE files; catalog total1242. No inherited nonPE file is claimed freshly rehashed.','Author57 before/after rows agree; this review independently read those54 PE files+3 metadata inputs and checked recorded header/section/import descriptor/name bytes, plus2148 edge provenance without importing or invoking target parser/collector.','74 discovered unread nodes and the129th capped candidate have no fabricated catalog refs. API-set virtual mappings1803, one inventory miss and one cap edge remain unknown. Export forwarders are not resolved.','The old parser source AST segment is byte-identical to the sealed parser. This establishes bounded static descriptor evidence, not actual Windows loader behavior.'],'conditions':['Bind exact runtime98b5ef... descriptor and its full SHA/bytes into future actualscope, with independent boundscope review and actual registration/grant. Reserved review path is not populated by this artifact.','Before execution hash every selected actual1242 resource; this review did not reopen1188 inherited noncurrent-PE resources. Future dynamic debug hFile/path/hash observation must reject unknown resource and stop without automatic resource expansion or retry.','54 files are a supported partial preapproval set, not proof they are sufficient for future CLI/network/Go/Windows execution. API sets, forwarders, conditional runtime loads and74 pending nodes stay OPEN.','Keep currentcompiler actualgraph/newWORK/exe provenance and runtime observations separate; no grant, live tuple confirmation, source acceptance or formal increment follows from this catalog.'],'checks_summary':summary,'new_failure_origins':[],'status':'STOPPED'})
print(json.dumps({'output':str(O),'review':ref(O/'review.json'),'summary':summary},ensure_ascii=False))