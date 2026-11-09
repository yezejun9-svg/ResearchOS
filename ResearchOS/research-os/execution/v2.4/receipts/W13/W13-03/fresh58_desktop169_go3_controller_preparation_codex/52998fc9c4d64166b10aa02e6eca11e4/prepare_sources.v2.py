"""Pure IO/AST preparation; does not import any candidate."""
import ast,hashlib,json,difflib,re
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');OUT=Path(__file__).resolve().parent
MAP=ROOT/'execution/v2.4/receipts/W13/W13-03/fresh58_validation_reference_mapping_codex/c745e294c1304498a6094777a42ed6e2/mapping.json'
inputs=[]
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def pin(p):
    b=Path(p).read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(ref):
    p=Path(ref['path']);p=p if p.is_absolute() else ROOT/p;b=p.read_bytes()
    need(hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes'],'Pin mismatch')
    inputs.append(pin(p));return b
def put(n,b):
    if not isinstance(b,bytes):b=(json.dumps(b,ensure_ascii=False,indent=2)+'\n').encode()
    with (OUT/n).open('xb') as f:f.write(b)
    return pin(OUT/n)
mapping=json.loads(read({'path':str(MAP),'sha256':'bc3abc71c485fa48c53a576e476ae5606d0dd02a4197ec89c68b7d7950691e0d','bytes':15097}));refs=mapping['references']
old=read(refs['debug_tree_helper_ref']);new=old;edits=[]
def change(a,b):
    global new
    a=a.replace('\n','\r\n').encode();b=b.replace('\n','\r\n').encode();need(new.count(a)==1,'Exact helper anchor '+repr(a[:60]));new=new.replace(a,b,1);edits.append({'old':a.decode(),'new':b.decode()})
change('process_cap, stdin=None, creation_flags=0):','process_cap, stdin=None, creation_flags=0, future_images=None, future_context=None):')
change("    loaded_files = []\n","    loaded_files = []\n    future_pins = {}\n    debug['future_image_admissions'] = []\n    debug['future_images_declared'] = []\n")
change("        module_pins.update(image_pins)\n",'''        module_pins.update(image_pins)
        if future_images is not None:
            if not isinstance(future_images,list) or len(future_images)>20 or len(future_images)+len(image_pins)>64:
                raise ValueError('Finite future image list bound')
            if not isinstance(future_context,dict) or set(future_context)!={'root','run_uuid','case_name','scope_sha256'}:
                raise ValueError('Exact future image context required')
            future_root=Path(future_context['root'])
            if not future_root.is_absolute() or str(future_root.absolute())!=str(future_root) or str(future_root.resolve(strict=False))!=str(future_root):
                raise ValueError('Future root canonical spelling')
            if len(future_context['run_uuid'])!=32 or any(c not in '0123456789abcdef' for c in future_context['run_uuid']):
                raise ValueError('Future run UUID')
            if len(future_context['scope_sha256'])!=64 or any(c not in '0123456789abcdef' for c in future_context['scope_sha256']):
                raise ValueError('Future scope hash')
            for row in future_images:
                if set(row)!={'path','sha256','bytes','origin_ref','case_name','scope_sha256','run_uuid','allocation_ordinal','max_creates'}:
                    raise ValueError('Exact future row fields')
                p=Path(row['path'])
                if not p.is_absolute() or str(p)!=str(p.absolute()) or str(p.resolve(strict=False))!=str(p) or not p.is_relative_to(future_root):
                    raise ValueError('Future image outside exact root or alias')
                if os.path.lexists(p):raise ValueError('Future image must initially be absent')
                if any(row[k]!=future_context[k] for k in ['case_name','scope_sha256','run_uuid']):raise ValueError('Future case/scope mismatch')
                if type(row['allocation_ordinal']) is not int or not 0<=row['allocation_ordinal']<20 or row['max_creates'] not in [1,2]:raise ValueError('Future finite ordinal/create bound')
                expected=future_root/(row['run_uuid']+'-'+str(row['allocation_ordinal']).zfill(2))/'resources/client-wire/researchos-client-wire-validator.exe'
                if str(p)!=str(expected):raise ValueError('Future exact alias not frozen ordinal')
                cur=p
                while cur!=cur.parent:
                    if os.path.lexists(cur):
                        st=os.lstat(cur)
                        if cur.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:raise ValueError('Future path reparse')
                    cur=cur.parent
                origin=row['origin_ref']
                if set(origin)!={'path','sha256','bytes'} or image_pins.get(image_key(origin['path']))!={'sha256':row['sha256'],'bytes':row['bytes']} or origin['sha256']!=row['sha256'] or origin['bytes']!=row['bytes']:
                    raise ValueError('Future origin must be an actual pinned fresh negative child')
                raw=Path(origin['path']).read_bytes()
                if len(raw)!=origin['bytes'] or hashlib.sha256(raw).hexdigest()!=origin['sha256']:raise ValueError('Future origin changed')
                key=image_key(p)
                if key in image_pins or key in future_pins:raise ValueError('Duplicate future image')
                future_pins[key]={'row':row,'used':0}
                debug['future_images_declared'].append({'path':str(p),'case_name':row['case_name'],'allocation_ordinal':row['allocation_ordinal'],'uses':0})
''')
change("        def reject_load(fact, expected_pin, reason):\n",'''        class FILE_INFORMATION(ctypes.Structure):
            _fields_=[('attributes',DWORD),('creation',wintypes.FILETIME),('access',wintypes.FILETIME),('write',wintypes.FILETIME),
                      ('volume',DWORD),('sizeHigh',DWORD),('sizeLow',DWORD),('links',DWORD),('indexHigh',DWORD),('indexLow',DWORD)]
        file_info=bind('GetFileInformationByHandle',[HANDLE,ctypes.POINTER(FILE_INFORMATION)],wintypes.BOOL)
        open_exact=bind('CreateFileW',[wintypes.LPCWSTR,DWORD,DWORD,ctypes.c_void_p,DWORD,DWORD,HANDLE],HANDLE)
        def info(handle):
            value=FILE_INFORMATION();require(file_info(handle,ctypes.byref(value)))
            if value.attributes & (0x400|0x10):raise RuntimeError('Future executable reparse/directory')
            return {'volume':int(value.volume),'index':(int(value.indexHigh)<<32)|int(value.indexLow),
                    'bytes':(int(value.sizeHigh)<<32)|int(value.sizeLow)}
        def admit_future(fact, retained, key):
            declaration=future_pins[key];row=declaration['row'];p=Path(row['path'])
            if declaration['used']>=row['max_creates']:raise RuntimeError('Future executable generation cap')
            # The debug event still suspends this child. Read the same current path by a held handle;
            # no write/delete sharing, no directory or reparse resolution is accepted.
            cur=p
            while cur!=cur.parent:
                if os.path.lexists(cur):
                    st=os.lstat(cur)
                    if cur.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:raise RuntimeError('Future executable ancestor replaced')
                cur=cur.parent
            held=open_exact(str(p),0x80000000,1,None,3,0x00200000,None)
            if not held or held==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
            handles.append(held)
            buffer=ctypes.create_unicode_buffer(32768);length=file_name(held,buffer,len(buffer),0)
            if not length or length>=len(buffer):raise ctypes.WinError(ctypes.get_last_error())
            actual=buffer.value[4:] if buffer.value.startswith('\\\\\\\\?\\\\') else buffer.value
            event_path=fact['path_from_actual_file_handle'];event_path=event_path[4:] if event_path.startswith('\\\\\\\\?\\\\') else event_path
            expected={'sha256':row['sha256'],'bytes':row['bytes']}
            if str(Path(actual).resolve())!=str(p) or str(Path(event_path).resolve())!=str(p):raise RuntimeError('Future final path mismatch')
            event_identity,current_identity=info(retained),info(held)
            if event_identity!=current_identity or event_identity['bytes']!=row['bytes'] or fact['before']!=expected or hash_loaded_file(held,capture_deadline)!=expected:
                raise RuntimeError('Future path and event file identity/digest mismatch')
            declaration['used']+=1
            item={'path':str(p),'scope_sha256':row['scope_sha256'],'case_name':row['case_name'],'allocation_ordinal':row['allocation_ordinal'],
                  'pid':fact['pid'],'creation_time_100ns':fact['creation_time_100ns'],'event_file_identity':event_identity,
                  'current_path_file_identity':current_identity,'pin':expected,'checked_before_debug_continue':True}
            debug['future_image_admissions'].append(item)
            for declared in debug['future_images_declared']:
                if declared['path']==str(p):declared['uses']=declaration['used']
            image_pins[key]=expected;module_pins[key]=expected

        def reject_load(fact, expected_pin, reason):
''')
change("                if module_pins.get(image_key(path_buffer.value)) != fact['before']:\n",'''                future_key=image_key(path_buffer.value)
                if event_code==3 and future_key in future_pins:
                    try:admit_future(fact,retained,future_key)
                    except BaseException as exc:reject_load(fact,{'sha256':future_pins[future_key]['row']['sha256'],'bytes':future_pins[future_key]['row']['bytes']},'Future image admission failed: '+error_text(exc))
                if module_pins.get(image_key(path_buffer.value)) != fact['before']:
''')
change("            event_fact = {'code':int(event.code), 'pid':int(event.pid), 'tid':int(event.tid)}\n", "            event_fact = {'code':int(event.code), 'pid':int(event.pid), 'tid':int(event.tid)}\n            may_continue = True\n")
change("            except BaseException as exc:\n                record_error(exc)\n            finally:\n",'''            except BaseException as exc:
                record_error(exc)
                if future_images is not None and not cleanup_mode:
                    # In this new opt-in mode a failed event is never released to execute.
                    may_continue=False
                    cleanup['termination_requested']=True
                    cleanup['termination_code_requested']=0xE0000008
                    stopped=bool(terminate_job(job,0xE0000008))
                    cleanup['termination_succeeded']=stopped
                    event_fact['termination_before_continue']=stopped
                    if stopped:may_continue=True
                    else:record_error(ctypes.WinError(ctypes.get_last_error()))
            finally:
''')
change("                    require(continue_debug(event.pid, event.tid, status))\n", "                    if may_continue:require(continue_debug(event.pid, event.tid, status))\n                    event_fact['debug_event_continued']=may_continue\n")
need(new!=old,'No helper change');ast.parse(new.decode())
back=new
for e in reversed(edits):need(back.count(e['new'].encode())==1,'Inverse anchor');back=back.replace(e['new'].encode(),e['old'].encode(),1)
need(back==old,'Whole helper inverse')
put('windows_debug_job_tree.future_images.proposed.py',new);put('helper.edits.json',edits)
put('helper.diff',''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='9c77',tofile='future-images-proposal')).encode())
source=ROOT/'tests/ui/desktop/http-wire-boundary.test.mjs';original=source.read_bytes();inputs.append(pin(source))
text=original.decode();pat=re.compile(r"^\s*'([^']+)'\s*:\s*\(\)\s*=>\s*negativeChild\('([^']+)'",re.M)
rows=[{'name':'desktop-http/'+m[1],'mode':m[2],'source_line':text[:m.start()].count('\n')+1} for m in pat.finditer(text)]
needle="test('desktop-http/revision/private-json-whitespace'"
need(text.count(needle)==1,'Whitespace case unique')
rows.append({'name':'desktop-http/revision/private-json-whitespace','mode':'nbsp','source_line':text[:text.index(needle)].count('\n')+1})
need(len(rows)==20 and len({x['name'] for x in rows})==20,'Exact20 allocator routes')
blocked={'missing','digest','alias','descriptor','module-drift'}
for i,row in enumerate(rows):row.update(allocation_ordinal=i,allocations_per_case=1,expected_image_creates=0 if row['mode'] in blocked else (2 if row['mode']=='unreaped' else 1),actual_usage=None,status='NOT_RUN')
roster=json.loads(read(refs['desktop_frozen_roster']));names={x['name'] for x in roster['leaves']};need(all(x['name'] in names for x in rows),'All aliases in frozen169')
patch="""  const aliasPath=process.env.RESEARCHOS_DESKTOP_NEGATIVE_ALIAS_PLAN;assert(aliasPath);
  const aliasRaw=fs.readFileSync(aliasPath);assert.equal(crypto.createHash('sha256').update(aliasRaw).digest('hex'),process.env.RESEARCHOS_DESKTOP_NEGATIVE_ALIAS_SHA256);
  const aliases=JSON.parse(aliasRaw);assert.equal(aliases.schema,'researchos.desktop-negative-alias-plan/1');
  assert.equal(aliases.case_name,process.env.RESEARCHOS_DESKTOP_CASE_NAME);assert.equal(aliases.mode,mode);assert.equal(aliases.rows.length,1);
  const allocated=aliases.rows[0];assert.match(allocated.run_uuid,/^[0-9a-f]{32}$/);assert(Number.isInteger(allocated.ordinal)&&allocated.ordinal>=0&&allocated.ordinal<20);
  const root=path.join(fixtureParent,allocated.run_uuid+'-'+String(allocated.ordinal).padStart(2,'0'));
  assert.equal(root,allocated.root);assert.equal(fs.existsSync(root),false);fs.mkdirSync(root);
  fs.writeFileSync(path.join(parent,'negative-alias.used.json'),JSON.stringify({plan_sha256:process.env.RESEARCHOS_DESKTOP_NEGATIVE_ALIAS_SHA256,case_name:aliases.case_name,mode,root,ordinal:allocated.ordinal}),{flag:'wx'});
"""
oldline="  const root=path.join(fixtureParent,crypto.randomUUID());fs.mkdirSync(root);\n"
need(text.count(oldline)==1,'Negative allocation anchor')
instrumented=text.replace(oldline,patch,1)
need(instrumented.replace(patch,oldline,1).encode()==original,'Whole instrumentation inverse')
put('http-wire-boundary.alias.instrumented.mjs.proposed.txt',instrumented.encode())
put('alias.edits.json',[{'old':oldline,'new':patch}]);put('negative-alias-roster.json',{'rows':rows,'count':20,'executable_aliases':15,'original_setup_copy_mkdir_wx_preserved':True,'prebuild_clones':False,'mechanism':'exact future path at suspended CREATE event','all_NOT_RUN':True})
put('inputs.before.json',inputs)
put('static-audit.initial.json',{'helper_AST_parse':True,'helper_whole_inverse':True,'alias_whole_inverse':True,'original_assertion_bytes_untouched':True,
 'JavaScript_parser_executed':False,'Go_Node_SQL_helper_DLL_target_calls':0,'source_acceptance':False,'new_failure_origins':[]})
print(json.dumps({'helper':pin(OUT/'windows_debug_job_tree.future_images.proposed.py'),'alias':pin(OUT/'http-wire-boundary.alias.instrumented.mjs.proposed.txt'),'rows':20},ensure_ascii=False))
