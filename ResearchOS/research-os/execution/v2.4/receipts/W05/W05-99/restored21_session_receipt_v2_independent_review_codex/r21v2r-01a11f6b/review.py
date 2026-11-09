import sys
sys.dont_write_bytecode=True
import hashlib,json,re,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os");W=R/"execution/v2.4/receipts/W05/W05-99"
C=W/"restored21_session_receipt_v2_source_codex/r21receipt2-1a11f5e"
S=W/"restored21_session_profile_source_codex/r21s-1a11f5e"
Q=W/"restored21_session_profile_independent_review_codex/r21r-01a11f6b"
GP=W/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
forbidden={str((R/"execution/v2.4"/(n+".json")).resolve()).casefold() for n in ("checkpoint","path_ownership","step_state","commands")}
def pin(p):
 p=Path(p).resolve();assert str(p).casefold() not in forbidden
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(v):
 p=pin(v["path"]);assert (p["sha256"],p["bytes"])==(v["sha256"].removeprefix("sha256:"),v["bytes"]),v["path"];return p
def save(n,v):
 with (N/n).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
checks=[]
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
h=verify(dict(path=str(C/"HDF.json"),sha256="c82ce472df31f2634565a29374da101898044755517364f731b317c72837c11a",bytes=5047))
m=verify(dict(path=str(C/"MF.json"),sha256="b8f6399f0e071d7a29407351251173551892c242c347173133d06f8d3febceb6",bytes=10025))
H=json.loads((C/"HDF.json").read_bytes());M=json.loads((C/"MF.json").read_bytes());inputs=json.loads((C/"input-pins.before.json").read_bytes())
refs=[h,m]+[verify(v) for v in M["members"]]+[verify(v) for v in inputs]+[pin(GP),pin(__file__),pin(sys.executable)]
refs=list({v["path"].casefold():v for v in refs}.values())
ck("guard_exact",pin(GP)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
gm=types.ModuleType("r21v2_source_guard");gm.__file__=str(GP);sys.modules[gm.__name__]=gm
exec(compile(GP.read_bytes(),str(GP),"exec"),gm.__dict__)
g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 g.acquire(refs)
 def raw(p):return g.get_buffer(str(Path(p).resolve()))
 def text(p):return raw(p).decode()
 def norm(p):return text(p).replace("\r\n","\n")
 def obj(p):return json.loads(raw(p))
 base=S/"source-root";candidate=C/"source-root"
 handler=text(candidate/"internal/domain/backup_restored21_upgrade.go");oldhandler=text(base/"internal/domain/backup_restored21_upgrade.go")
 backup=text(candidate/"internal/domain/backup.go");oldbackup=text(base/"internal/domain/backup.go")
 test=text(candidate/"internal/domain/backup_restored21_upgrade_test.go");oldtest=text(base/"internal/domain/backup_restored21_upgrade_test.go")
 hook=text(C/"report-hook.go.txt");hooktest=text(C/"report-hook-test.go.txt")
 ck("source_manifest_exact",H["manifest_ref"]==m)
 ck("base_source_exact",pin(S/"HDF.json")["sha256"]=="e4fafc6053105cc776d344f8d618b14c3514ecfb44913b80effbb1499d459d91")
 ck("original_independent_review_exact",pin(Q/"HDF.json")["sha256"]=="b2e36b4a0e841934990501ebc30fe5bd18ca202f7f7cc6bf48e07cbe61c7e919" and obj(Q/"HDF.json")["independent_static_controls"]==85)
 ck("review_has_original_receipt_finding",obj(Q/"findings.json")[0]["id"]=="R21-RECEIPT-01")
 ck("author77static32inputs0actual",H["source_checks"]==77 and len(inputs)==32 and H["actual_test_count"]==0 and all(v["passed"] for v in obj(C/"source-controls.json")["checks"]))
 inv=obj(C/"whole-file-inverse.json")
 ck("five_exact_overlay_files",len(inv["files"])==5)
 for item in inv["files"]:
  rel=item["target"]
  ck("entire_old_opcode_inverse_"+rel,"".join(z for op in item["opcodes"] for z in op["old_lines"]).encode()==raw(item["original_ref"]["path"]))
  ck("entire_new_opcode_forward_"+rel,"".join(z for op in item["opcodes"] for z in op["new_lines"]).encode()==raw(item["candidate_ref"]["path"]))
  ck("exact_original_ref_"+rel,pin(base/rel)==item["original_ref"])
  ck("exact_new_ref_"+rel,pin(candidate/rel)==item["candidate_ref"])
 substitutions=[
 ("\tpolicy.afterRecovery = func(restored *sql.DB) error {","\tvar sessionEvidence Object\n\tpolicy.afterRecovery = func(restored *sql.DB) error {"),
 ("\t\treturn ctx.Err()\n\t}\n\tvar sessionEvidence Object","\t\tif e := ctx.Err(); e != nil { return e }\n        policy.restored21SessionEvidence = sessionEvidence\n        return nil\n\t}"),
 ('    if result.Recovery != nil { result.Recovery["restored21_session_initialization"] = sessionEvidence }\n',"")]
 expected=oldhandler
 for a,b in substitutions:ck("unique_handler_delta_"+a[:70],expected.count(a)==1);expected=expected.replace(a,b)
 ck("handler_whole_independent_forward",expected+hook==handler)
 back=handler[:-len(hook)]
 # Reverse the deleted post-return line through its unique unchanged return anchor.
 back=back.replace("    return result, restoreErr\n}",substitutions[-1][0]+"    return result, restoreErr\n}")
 for a,b in reversed(substitutions[:-1]):back=back.replace(b,a)
 ck("handler_whole_independent_inverse",back==oldhandler)
 nl="\r\n" if "\r\n" in oldbackup else "\n"
 bsubs=[("\tpreserveRestored21UpgradeWorkspaces func(*sql.DB) error"+nl,"\tpreserveRestored21UpgradeWorkspaces func(*sql.DB) error"+nl+"\trestored21SessionEvidence Object"+nl)]
 branch="""        if policy.restored21SessionEvidence != nil {
            if e = upgradeRestored21PublishEvidence(policy, r.Recovery); e != nil { return r, e }
        }
""".replace("\n",nl)
 bsubs.append(('\t\tr.Recovery["local_upgrade"] = policy.purpose',branch+'\t\tr.Recovery["local_upgrade"] = policy.purpose'))
 expected=oldbackup
 for a,b in bsubs:ck("unique_backup_delta_"+a[:70],expected.count(a)==1);expected=expected.replace(a,b)
 ck("backup_whole_independent_forward",expected==backup)
 back=backup
 for a,b in reversed(bsubs):back=back.replace(b,a)
 ck("backup_whole_independent_inverse",back==oldbackup)
 needle=' if !ok || evidence["old_typed_rows_unchanged"]!=true || evidence["restored_barriers_refreshed"]!=false{t.Fatal("missing distinct session phase receipt")}\n'
 tsubs=[(needle,needle+' persistedRaw,err:=os.ReadFile(filepath.Join(opt.Destination,"restore-report.json"));if err!=nil{t.Fatal(err)}\n var persisted RestoreReport;if err=json.Unmarshal(persistedRaw,&persisted);err!=nil{t.Fatal(err)}\n if !bytes.Equal(Bytes(report.Recovery),Bytes(persisted.Recovery)){t.Fatal("returned and persisted Recovery differ")}\n')]
 needle=' if !reflect.DeepEqual(before,history20Rows(t,opt.Source)){t.Fatal("source typed rows changed")}\n'
 tsubs.append((needle,' for _,p:=range []string{filepath.Join(opt.Destination,"restore-report.json"),filepath.Join(opt.Snapshot,"restore-report.json")}{if _,err:=os.Stat(p);!os.IsNotExist(err){t.Fatalf("rejected source published restore report %s: %v",p,err)}}\n'+needle))
 needle="func TestRestored21PublicUpgradeFromH20PreservesSource(t *testing.T){"
 tsubs.append((needle,needle+"\n restored21ReportHookControls(t)"))
 expected=oldtest
 for a,b in tsubs:ck("unique_test_delta_"+a[:65],expected.count(a)==1);expected=expected.replace(a,b)
 ck("test_whole_independent_forward",expected+hooktest==test)
 back=test[:-len(hooktest)]
 for a,b in reversed(tsubs):back=back.replace(b,a)
 ck("test_whole_independent_inverse",back==oldtest)
 for rel in ("internal/domain/backup_upgrade.go","ops/backup/main.go"):ck("unchanged_entire_"+rel,raw(base/rel)==raw(candidate/rel))
 overlay=obj(C/"source-overlay.json")
 ck("only_three_changed",set(overlay["changed_paths"])=={"internal/domain/backup.go","internal/domain/backup_restored21_upgrade.go","internal/domain/backup_restored21_upgrade_test.go"})
 ck("old_profiles_and_SQL_not_overlaid",set(overlay["files"])=={v["target"] for v in inv["files"]} and not list(candidate.rglob("*.sql")))
 ck("base_profile_primitives_unchanged",handler[:handler.index("func upgradeRestored21Local(")]==oldhandler[:oldhandler.index("func upgradeRestored21Local(")])
 def function(s,name):
  start=s.index("func "+name+"(");end=s.find("\nfunc ",start+1)
  return s[start:end] if end>=0 else s[start:]
 oldb=oldbackup.replace("\r\n","\n");newb=backup.replace("\r\n","\n")
 for name in ("backupMAC","readBackupPolicy","backupWrite","backupNewStage"):
  ck("auth_publication_function_unchanged_"+name,function(newb,name)==function(oldb,name))
 ck("Purpose_plan_literal_unchanged",handler[handler.index("\tplan := Object"):handler.index("\tpolicy := &backupPolicy")]==oldhandler[oldhandler.index("\tplan := Object"):oldhandler.index("\tpolicy := &backupPolicy")])
 ck("full_Purpose_MAC_match_still_present",'Hash(m.Purpose) != Hash(policy.purpose)' in newb and 'm.MAC = backupMAC(m, key)' in newb)
 ck("no_Purpose_assignment_or_mutating_callback",not re.search(r'policy\.purpose\[[^\n]+\]\s*=',handler) and "restored21SessionEvidence Object" in newb)
 ck("migration_evidence_stays_outside_Purpose",handler.count("policy.restored21SessionEvidence = sessionEvidence")==1 and 'policy.purpose["restored21_session_initialization"]' not in handler)
 def ordered(name,s,parts):
  cursor=0;pos=[]
  for p in parts:
   x=s.index(p,cursor);pos.append(x);cursor=x+len(p)
  ck(name,pos==sorted(pos) and len(pos)==len(set(pos)))
 after=handler[handler.index("policy.afterRecovery ="):handler.index("    svc := &Service")]
 ordered("afterRecovery_checks_before_assign",after,["UPGRADE_WORKSPACE_IDENTITY_CHANGED","UPGRADE_TARGET_SCHEMA","upgradeRestored21RecoveryInvariant","UPGRADE_SOURCE_DRIFT","UPGRADE_RELEASE_CHANGED","UPGRADE_PROGRAM_CHANGED","ctx.Err()","policy.restored21SessionEvidence = sessionEvidence","return nil"])
 restore=function(newb,"restoreBackupPolicy")
 ordered("hook_write_rename_return_order",restore,["defer backupDiscard(stage)","policy.afterRecovery(db)","upgradeRestored21PublishEvidence(policy, r.Recovery)",'r.Recovery["local_upgrade"] = policy.purpose','backupWrite(filepath.Join(stage, "restore-report.json"), Bytes(r))',"os.Rename(stage, destination)","return r, nil"])
 ck("hook_error_immediate_return","if e = upgradeRestored21PublishEvidence(policy, r.Recovery); e != nil { return r, e }" in newb)
 ck("no_post_return_evidence_mutation","if result.Recovery != nil" not in handler and 'return result, restoreErr' in handler)
 ck("old_nil_policy_or_evidence_noop","if policy == nil || policy.restored21SessionEvidence == nil { return nil }" in hook)
 ck("fixed_plan_type_and_format_before_evidence",'plan, ok := policy.purpose["plan"].(Object)' in hook and 'if !ok || policy.format != localUpgradeFormat || plan["id"] != Restored21SessionUpgradePlan' in hook)
 fields="source_schema_hash session_schema_hash before_rows_hash after_rows_hash numbered_ledger_unchanged old_typed_rows_unchanged client_sessions_created_empty restore_fence_preserved restored_barriers_refreshed external_actions_dispatched"
 ck("exact_ten_fields",('upgradeQueueFields(evidence,"'+fields+'")') in hook and len(fields.split())==10)
 ck("four_hash_names_exact",'[]string{"source_schema_hash","session_schema_hash","before_rows_hash","after_rows_hash"}' in hook)
 ck("hash_string_prefix_and_64_lowerhex",'value, ok := evidence[name].(string)' in hook and 'if !ok || len(value) != 71 || value[:7] != "sha256:"' in hook and "if !((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))" in hook)
 ck("four_true_bool_fields_exact",'[]string{"numbered_ledger_unchanged","old_typed_rows_unchanged","client_sessions_created_empty","restore_fence_preserved"}' in hook and 'value, ok := evidence[name].(bool); if !ok || !value' in hook)
 ck("false_bool_int_zero_exact",'refreshed, ok := evidence["restored_barriers_refreshed"].(bool)' in hook and 'actions, typed := evidence["external_actions_dispatched"].(int)' in hook and 'if !ok || refreshed || !typed || actions != 0' in hook)
 ck("nil_recovery_rejected","if recovery == nil ||" in hook)
 ordered("all_validation_before_single_mutation",hook,["RESTORE_RESTORED21_REPORT_POLICY_MISMATCH","upgradeQueueFields",'.(string)',".(bool)",".(int)","actions != 0",'recovery["restored21_session_initialization"] = evidence',"return nil"])
 assignments=re.findall(r'^\s*([^\n]+?)\s=(?!=)',hook,re.M)
 ck("single_map_write_after_checks",len(re.findall(r'^\s*\w+\[[^\n]+\]\s*=',hook,re.M))==1 and 'recovery["restored21_session_initialization"] = evidence' in hook)
 ck("helper_does_not_execute_callbacks_or_io",not re.search(r'\b(?:os|db|tx|policy)\.(?:Exec|Write|Rename|afterRecovery|beforeRecovery)\s*\(',hook))
 invalids=re.search(r'for _, name := range \[\]string\{([^}]+)\}',hooktest).group(1)
 ck("seven_exact_invalid_test_controls",re.findall(r'"([^"]+)"',invalids)==["wrong-plan","wrong-format","missing-field","extra-field","wrong-type","wrong-hash","nonzero-actions"])
 ck("negative_tests_preserve_Recovery_and_Purpose",'!bytes.Equal(before,Bytes(recovery)) || !bytes.Equal(purposeBefore,Bytes(purpose))' in hooktest)
 ck("old_nil_test_declared",'old-plan nil hook changed report' in hooktest)
 ck("valid_test_preserves_Purpose_and_evidence",'Bytes(recovery["restored21_session_initialization"])' in hooktest and 'valid hook changed purpose or evidence' in hooktest)
 ck("tests_do_not_add_runs","t.Run(" not in hooktest and not re.search(r"^func Test",hooktest,re.M))
 names=re.findall(r"^func (Test\w+)\(",test,re.M);oldnames=re.findall(r"^func (Test\w+)\(",oldtest,re.M)
 ck("same_nine_parent_roster",names==oldnames and len(names)==9)
 ck("same_four_leafs",'[]string{"foreign","partial-session","session-addon","missing-restore-trigger"}' in test and test.count("t.Run(")==oldtest.count("t.Run(")==1)
 ck("persisted_full_Recovery_comparison_declared",'bytes.Equal(Bytes(report.Recovery),Bytes(persisted.Recovery))' in test)
 ck("early_rejection_assertion_not_late_runtime","rejected source published restore report" in test and obj(C/"receipt-contract.json")["public_late_failure_runtime"]=="OPEN")
 ck("original_941_mapping",H["new_original_failures"][0]["ordinal"] is None and H["new_original_failures"][0]["chunk_id"]=="4e57d0" and H["new_original_failures"][0]["origin_ref"]["sha256"]=="8072b969d9f6a2402c358555bd867848bcf8ce4716bb9f88a3be81e6b2aad60e" and H["new_original_failures"][0]["origin_ref"]["bytes"]==1820)
 ck("runtime_provenance_formal_remain_open",H["actual_test_count"]==0 and H["real21_22_program_provenance"]=="OPEN" and H["overall20to24"]=="OPEN" and H["formal_acceptance"] is False)
 for p in candidate.rglob("*.go"):
  clean=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|`[^`]*`|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',"",norm(p));stack=[];valid=True;pairs={")":"(","]":"[","}":"{"}
  for ch in clean:
   if ch in "([{":stack.append(ch)
   elif ch in pairs:
    if not stack or stack.pop()!=pairs[ch]:valid=False;break
  ck("lexical_only_balance_"+p.name,valid and not stack)
 ck("all_exact_inputs_stable_while_held",all(pin(v["path"])==v for v in refs))
 save("finding-disposition.json",dict(finding="R21-RECEIPT-01",source_status="ADDRESSED_IN_SOURCE",runtime_status="NOT_RUN",remaining_findings=[],evidence="Same original r.Recovery receives validated evidence before unchanged backupWrite and rename; handler no longer patches the return after publication.",public_late_failure="OPEN",program21_22_provenance="OPEN"))
finally:
 cleanup=g.close();save("source-guard.cleanup.actual.json",cleanup)
ck("guard_closed_zero_retained",cleanup["closed"] is True and not cleanup["errors"] and cleanup["retained_handles_count"]==0)
save("checks.json",checks);save("input-pins.json",refs)
save("result.json",dict(status="SOURCE_ACCEPTED_P2_ADDRESSED_PENDING_RUNTIME_QUALIFICATION",independent_checks=len(checks),finite_input_count=len(refs),P1_findings=0,P2_findings=0,original_P2_source_addressed=True,actual_tests=0,Go_AST_parser_compiler_SQL_native_Git_API_model=False,formal_acceptance=False,formal_case_accepted_delta=0,current_canonical_read_locked_written=False,new_original_failures=[]))
print(json.dumps(dict(status="PASS",checks=len(checks),input_count=len(refs),result_ref=pin(N/"result.json"),cleanup_ref=pin(N/"source-guard.cleanup.actual.json"))))

