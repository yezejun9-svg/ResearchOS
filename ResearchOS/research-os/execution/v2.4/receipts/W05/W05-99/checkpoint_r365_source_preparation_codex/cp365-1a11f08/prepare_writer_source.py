import ast,difflib,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
BASE=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r364-component-actuals-source-ready/checkpoint_component_actuals.atomic.py')
def pin(p):
 raw=Path(p).read_bytes();return dict(path=str(Path(p).resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
original=BASE.read_bytes();source=original.decode('utf-8');changes=[]
def change(old,new):
 global source
 count=source.count(old);assert count>0,old
 source=source.replace(old,new);changes.append(dict(before=old,after=new,count=count))
change('researchos.root-cp364-component-actuals-source-ready.v1','researchos.root-cp365-c12-failed-archive-and-h20-component-facts.v1')
change('("9e67531bd3b1f0fbd9bc5e239b3a240a39f668db2d367714a399ba4fd8bfeb25",4223052)','("6ed349c5b8380ad6b099ae2237c33513f4e2717afc7789398968366a8cddf6dd",4237636)')
change('before["revision"]==363 and len(before["failure_counters"])==893','before["revision"]==364 and len(before["failure_counters"])==900')
change('assert c["revision"]==363 and o["revision"]==168','assert c["revision"]==364 and o["revision"]==168')
change('range(896,903)','range(903,925)')
change('==900 and c["failure_counters"][:893]','==922 and c["failure_counters"][:900]')
change('expected_previous_revision=363,revision=364','expected_previous_revision=364,revision=365')
change('r364_registered_failure_count=900,r364_highest_observed_diagnostic_ordinal_at_cutoff=902,r364_next_failure_ordinal_at_cutoff=903,mu_sdk_r364_facts_ref=fr,later_diagnostics_observed_after_cutoff=[],root_next_failure_ordinal_live=903','r365_registered_failure_count=922,r365_highest_observed_diagnostic_ordinal_at_cutoff=924,r365_next_failure_ordinal_at_cutoff=925,mu_sdk_r365_facts_ref=fr,later_diagnostics_observed_after_cutoff=[],root_next_failure_ordinal_live=925')
change('["revision"]==364\nfinally:','["revision"]==365\nfinally:')
change('old893_failure_records_semantic_equal','old900_failure_records_semantic_equal')
change('old893_raw_array_prefix_preserved','old900_raw_array_prefix_preserved')
change('registered_failures=900,highest_observed_diagnostic_ordinal_at_cutoff=902,later_diagnostics_pending=[],live_next_failure_ordinal=903','registered_failures=922,highest_observed_diagnostic_ordinal_at_cutoff=924,later_diagnostics_pending=[],live_next_failure_ordinal=925')
change('RESUME.r364.original.json','RESUME.r365.original.json')
change('researchos.root-resume-component-actuals-source-ready.v1','researchos.root-resume-c12-failed-archive-and-h20-component.v1')
change('checkpoint_revision=364','checkpoint_revision=365')
change('registered_failures=900,highest_registered_ordinal=902,next_failure_ordinal_at_cutoff=903,later_diagnostics_pending=[],live_next_failure_ordinal=903','registered_failures=922,highest_registered_ordinal=924,next_failure_ordinal_at_cutoff=925,later_diagnostics_pending=[],live_next_failure_ordinal=925')
change('C12_prepared_actual="NOT_RUN",H20_Source="SEALED_PENDING_NONAUTHOR_REVIEW"','C12_actual="FAILED_ORIGINAL_SERVE_EXIT1_GRANT_UNPUBLISHED",C12_wholeSQL="SCHEMA1_TO23_UNCHANGED",C12_explicit_fixture_release=False,C12_fixture_retained_window_expired=True,C12_native_acceptance=False,H20R2_actual="9_TERMINAL_PASS_COMPONENT_A20_TO_PLAIN21_ONLY",public_archive="61_FULL_TEMP_PIN_CLOSURE_COMPONENT_ACCEPTED",W09r2_Source="PENDING_INDEPENDENT_SOURCE_REVIEW_NO_ACTUAL_SCOPE"')
change('CHECKPOINT_SAVED_T11_N12_COMPONENT_ACTUALS_C12_H20_SOURCE_READY','CHECKPOINT_SAVED_C12_FAILED_CLOSED_PUBLIC61_ARCHIVE_H20R2_COMPONENT_ACCEPTED')
change('registered_failures=900,highest_registered_ordinal=902','registered_failures=922,highest_registered_ordinal=924')
change('fr=verify(dict(path=str(O/"checkpoint.execution.facts.json"),sha256=sys.argv[1],bytes=int(sys.argv[2])))','assert len(sys.argv)==3, "usage: writer FACTS_SHA256 FACTS_BYTES"\nfr=verify(dict(path=str(O/"checkpoint.execution.facts.json"),sha256=sys.argv[1],bytes=int(sys.argv[2])))')
change('other_bytes=[p.read_bytes() for p in others]','other_bytes=[p.read_bytes() for p in others]\nassert [pin(p) for p in (cp,ow,*others)]==facts["canonical_refs"]\nassert facts["registered_before"]==900 and facts["registered_after"]==922 and facts["highest_observed_ordinal"]==924 and facts["next_failure_ordinal"]==925')
change('refs += [verify(v["origin_ref"]) for v in pending]+[verify(v) for v in facts["actual_refs"]]','refs += [verify(v["origin_ref"]) for v in pending]+[verify(v) for v in facts["actual_refs"]]+[verify(v) for v in facts["qualification_refs"]]')
old_append='c["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=n,immutable_origin_ref=ref,actual_outer_exit=v["actual_outer_exit"],actual_python_exit=v["actual_python_exit"],actual_native_exit=v["actual_native_exit"],diagnostic=v["description"]),counted_once=True,counter_reset=False,automatic_retry=False))'
new_append='c["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=n,immutable_origin_ref=ref,actual_outer_exit=v["actual_outer_exit"],actual_python_exit=v["actual_python_exit"],actual_native_exit=v["actual_native_exit"],diagnostic=v["description"],origin_selector=v["origin_selector"],exit_qualification=v["exit_qualification"]),counted_once=True,counter_reset=False,automatic_retry=False))'
change(old_append,new_append)
ast.parse(source)
target=N/'checkpoint_c12_failed_archived.atomic.py'
with target.open('xb') as f:f.write(source.encode('utf-8'))
old=original.decode().splitlines(keepends=True);new=source.splitlines(keepends=True);ops=[]
for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():ops.append(dict(op=tag,old_start=a,old_end=b,new_start=c,new_end=d,old_lines=old[a:b],new_lines=new[c:d]))
assert ''.join(x for op in ops for x in op['old_lines']).encode()==original
assert ''.join(x for op in ops for x in op['new_lines']).encode()==target.read_bytes()
with (N/'writer-source-provenance.json').open('xb') as f:f.write((json.dumps(dict(base_ref=pin(BASE),new_ref=pin(target),changes=changes,opcodes=ops,whole_original_byte_inverse=True,whole_candidate_byte_forward=True,writer_executed=False),ensure_ascii=False,indent=2)+'\n').encode())
assert BASE.read_bytes()==original
print(json.dumps(dict(status='ATOMIC_WRITER_SOURCE_ONLY',writer_ref=pin(target),change_rules=len(changes)),ensure_ascii=False))
