import difflib,hashlib,json,re
from pathlib import Path
N=Path(__file__).resolve().parent;W=N.parents[1];S=W/'restored21_session_profile_source_codex/r21s-1a11f5e';Q=W/'restored21_session_profile_independent_review_codex/r21r-01a11f6b'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(v):
 x=pin(v['path']);assert (x['sha256'],x['bytes'])==(v['sha256'].removeprefix('sha256:'),v['bytes']);return x
def save(n,v):
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True)
 assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
 with p.open('wb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
for p,h,b in [(Q/'HDF.json','b2e36b4a0e841934990501ebc30fe5bd18ca202f7f7cc6bf48e07cbe61c7e919',4387),(Q/'MF.json','e8099b31627cc6b9cec6dbc8d58588765e7a3f08f64121d8051f045e517bf7a3',5916),(S/'HDF.json','e4fafc6053105cc776d344f8d618b14c3514ecfb44913b80effbb1499d459d91',3641),(S/'MF.json','c91eb027dc761b3b12589a084d17526645d68f11e39e0ba50f511d378ac46c5d',8463)]:assert (pin(p)['sha256'],pin(p)['bytes'])==(h,b)
review=json.loads((Q/'HDF.json').read_bytes());assert review['P1_findings']==0 and review['P2_findings']==1
inputs=[pin(z/n) for z in (S,Q) for n in ('HDF.json','MF.json')]
inputs += [verify(v) for v in json.loads((Q/'MF.json').read_bytes())['members']]
overlay=json.loads((S/'source-overlay.json').read_bytes());inputs += [verify(v) for v in overlay['files'].values()]
inputs += [pin(S/n) for n in ('source-overlay.json','profile-contract.json','test-roster.json','failure-origin.936.original-tool-io.json')]
inputs=list({v['path']:v for v in inputs}.values());save('input-pins.before.json',inputs)
changes=[]
for rel,ref in overlay['files'].items():
 raw=Path(ref['path']).read_bytes();old=raw.decode();new=old;substitutions=[]
 def sub(a,b):
  global new
  assert new.count(a)==1,a;new=new.replace(a,b);substitutions.append(dict(old=a,new=b))
 if rel=='internal/domain/backup_restored21_upgrade.go':
  sub('\tpolicy.afterRecovery = func(restored *sql.DB) error {','\tvar sessionEvidence Object\n\tpolicy.afterRecovery = func(restored *sql.DB) error {')
  sub('\t\treturn ctx.Err()\n\t}\n\tvar sessionEvidence Object','\t\tif e := ctx.Err(); e != nil { return e }\n        policy.restored21SessionEvidence = sessionEvidence\n        return nil\n\t}')
  sub('    if result.Recovery != nil { result.Recovery["restored21_session_initialization"] = sessionEvidence }\n','')
  new += (N/'report-hook.go.txt').read_text(encoding='utf8')
 elif rel=='internal/domain/backup.go':
  newline='\r\n' if '\r\n' in old else '\n'
  sub('\tpreserveRestored21UpgradeWorkspaces func(*sql.DB) error'+newline,'\tpreserveRestored21UpgradeWorkspaces func(*sql.DB) error'+newline+'\trestored21SessionEvidence Object'+newline)
  needle='\t\tr.Recovery["local_upgrade"] = policy.purpose'
  hook='''        if policy.restored21SessionEvidence != nil {
            if e = upgradeRestored21PublishEvidence(policy, r.Recovery); e != nil { return r, e }
        }
'''.replace('\n',newline)
  sub(needle,hook+needle)
 elif rel=='internal/domain/backup_restored21_upgrade_test.go':
  needle=' if !ok || evidence["old_typed_rows_unchanged"]!=true || evidence["restored_barriers_refreshed"]!=false{t.Fatal("missing distinct session phase receipt")}\n'
  sub(needle,needle+' persistedRaw,err:=os.ReadFile(filepath.Join(opt.Destination,"restore-report.json"));if err!=nil{t.Fatal(err)}\n var persisted RestoreReport;if err=json.Unmarshal(persistedRaw,&persisted);err!=nil{t.Fatal(err)}\n if !bytes.Equal(Bytes(report.Recovery),Bytes(persisted.Recovery)){t.Fatal("returned and persisted Recovery differ")}\n')
  needle=' if !reflect.DeepEqual(before,history20Rows(t,opt.Source)){t.Fatal("source typed rows changed")}\n'
  sub(needle,' for _,p:=range []string{filepath.Join(opt.Destination,"restore-report.json"),filepath.Join(opt.Snapshot,"restore-report.json")}{if _,err:=os.Stat(p);!os.IsNotExist(err){t.Fatalf("rejected source published restore report %s: %v",p,err)}}\n'+needle)
  sub('func TestRestored21PublicUpgradeFromH20PreservesSource(t *testing.T){','func TestRestored21PublicUpgradeFromH20PreservesSource(t *testing.T){\n restored21ReportHookControls(t)')
  new += (N/'report-hook-test.go.txt').read_text(encoding='utf8')
 p=N/'source-root'/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
 with p.open('wb') as f:f.write(new.encode())
 back=new
 for v in reversed(substitutions):
  # Deletion is inverted from exact full-file diff below, not empty-string replace.
  if v['new']:back=back.replace(v['new'],v['old'])
 a=old.splitlines(keepends=True);b=new.splitlines(keepends=True);ops=[]
 for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():ops.append(dict(op=op,old_lines=a[i:j],new_lines=b[k:l]))
 assert ''.join(z for v in ops for z in v['old_lines']).encode()==raw
 assert ''.join(z for v in ops for z in v['new_lines']).encode()==new.encode()
 changes.append(dict(target=rel,original_ref=ref,candidate_ref=pin(p),substitutions=substitutions,whole_original_byte_inverse=True,whole_candidate_byte_forward=True,opcodes=ops))
save('whole-file-inverse.json',dict(files=changes,Go_AST_parser_executed=False,AST_claim='Complete original bytes reconstruct exactly; identical reconstructed bytes imply identical AST under the same parser; no Go AST execution claimed'))
save('source-overlay.json',dict(files={v['target']:v['candidate_ref'] for v in changes},changed_paths=[v['target'] for v in changes if v['substitutions']],unchanged_paths=[v['target'] for v in changes if not v['substitutions']],base_source_handoff_ref=pin(S/'HDF.json'),independent_source_review_ref=pin(Q/'HDF.json'),actual_adoption=False))
for v in inputs:assert pin(v['path'])==v
print(json.dumps(dict(status='P2_RECEIPT_SOURCE_REVISION_PREPARED',inputs=len(inputs),files=[v['candidate_ref'] for v in changes])))
