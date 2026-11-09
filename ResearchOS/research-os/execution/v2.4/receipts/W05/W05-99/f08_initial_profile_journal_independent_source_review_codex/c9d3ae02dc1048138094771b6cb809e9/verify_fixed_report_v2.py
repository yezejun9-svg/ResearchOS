from pathlib import Path
import json, hashlib, difflib, re
own=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_initial_profile_journal_independent_source_review_codex/c9d3ae02dc1048138094771b6cb809e9')
src=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_initial_profile_journal_revision_preparation_codex/bd3fe19a27f54a468431828f267cd02f')
def meta(path):
    b=path.read_bytes()
    return {"path":path.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def checked(ref):
    actual=meta(Path(ref["path"]))
    if (actual["sha256"],actual["bytes"])!=(ref["sha256"],ref["bytes"]): raise ValueError("frozen ref mismatch: "+ref["path"])
    return actual
m=json.loads((own/"inputs/manifest.json").read_text(encoding="utf-8"))
h=json.loads((own/"inputs/handoff.json").read_text(encoding="utf-8"))
members=[]
for ref in m["files"]:
    a=checked(ref)
    copied=meta(own/"inputs"/Path(ref["path"]).relative_to(src))
    if (copied["sha256"],copied["bytes"])!=(ref["sha256"],ref["bytes"]):raise ValueError("copy mismatch")
    members.append(a)
before=json.loads((own/"inputs/inputs.before.json").read_text(encoding="utf-8"))
after=json.loads((own/"inputs/inputs.seal-current.json").read_text(encoding="utf-8"))
bv={r["path"]:(r["sha256"],r["bytes"]) for r in before["files"]}
av={r["path"]:(r["sha256"],r["bytes"]) for r in after["files"]}
common=sorted(set(bv)&set(av))
drift=[p for p in common if bv[p]!=av[p]]
added=[r for r in after["files"] if r["path"] not in bv]
removed=[r for r in before["files"] if r["path"] not in av]
receipt_refs=[];unread_originals=[]
for ref in after["files"]:
    if "/execution/v2.4/receipts/" in ref["path"].replace("\\","/"):
        receipt_refs.append(checked(ref))
    else:unread_originals.append(ref)
bh=json.loads(Path(h["base_handoff_ref"]["path"]).read_text(encoding="utf-8"))
refs=[h["base_handoff_ref"],h["base_source_ref"],bh["test_proposal_ref"],h["independent_review_ref"],h["independent_review_text_ref"],h["driver_preparation_ref"]]
externals=[checked(r) for r in refs]
def apply_patch_lines(old,patch):
    lines=old.decode("utf-8").splitlines()
    plines=patch.decode("utf-8").splitlines()
    cursor=0;result=[];hunks=0;i=2
    while i<len(plines):
        hit=re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*",plines[i])
        if hit is None:raise ValueError("unified patch lacks hunk header")
        start=int(hit[1])-1;old_count=int(hit[2] or 1);new_count=int(hit[4] or 1)
        if start<cursor:raise ValueError("overlapping patch")
        result.extend(lines[cursor:start]);cursor=start;i+=1;oc=nc=0;hunks+=1
        while i<len(plines) and not plines[i].startswith("@@ "):
            line=plines[i]
            if line=="\\ No newline at end of file":i+=1;continue
            if not line or line[0] not in " +-":raise ValueError("invalid patch prefix")
            tag,content=line[0],line[1:]
            if tag in " -":
                if cursor>=len(lines) or lines[cursor]!=content:raise ValueError("patch OLD context differs")
                cursor+=1;oc+=1
            if tag in " +":result.append(content);nc+=1
            i+=1
        if (oc,nc)!=(old_count,new_count):raise ValueError("patch hunk length differs")
    result.extend(lines[cursor:])
    return result,hunks
stats={}
for label,base_name,final_name,patch_name in [
    ("source","source.b9.txt","client_cancel_finalization.v2.go.proposed.txt","client_cancel_finalization.v2.go.proposed.patch"),
    ("tests","tests.b9.txt","client_cancel_finalization_test.v2.go.proposed.txt","client_cancel_finalization_test.v2.go.proposed.patch")]:
    old=(own/"base"/base_name).read_bytes();new=(own/"inputs"/final_name).read_bytes();patch=(own/"inputs"/patch_name).read_bytes()
    a=old.decode("utf-8").splitlines(keepends=True);b=new.decode("utf-8").splitlines(keepends=True)
    ops=[x for x in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes() if x[0]!="equal"]
    inverse=b[:]
    for tag,i1,i2,j1,j2 in reversed(ops):inverse[j1:j2]=a[i1:i2]
    inverse_equal="".join(inverse).encode("utf-8")==old
    patched,hunks=apply_patch_lines(old,patch)
    final_lines=new.decode("utf-8").splitlines()
    patch_line_equal=patched==final_lines
    newline="\r\n" if b"\r\n" in new else "\n"
    rebuilt=(newline.join(patched)+(newline if new.endswith(b"\n") else "")).encode("utf-8")
    patch_byte_equal=rebuilt==new
    if not inverse_equal or not patch_line_equal or not patch_byte_equal:raise ValueError("exact frozen source/test patch validation differs")
    stats[label]={"base":meta(own/"base"/base_name),"final":meta(own/"inputs"/final_name),"base_lines":len(a),"final_lines":len(b),"inverse_bytes_equal":inverse_equal,"actual_supplied_patch_hunks":hunks,"actual_supplied_patch_forward_bytes_equal":patch_byte_equal,"delta":[{"tag":t,"old_start":i+1,"old_end":j,"new_start":k+1,"new_end":l} for t,i,j,k,l in ops]}
url_snapshot=meta(own/"inputs/additional-source-snapshots/04-url.go")
url_added_matches=len(added)==1 and (added[0]["sha256"],added[0]["bytes"])==(url_snapshot["sha256"],url_snapshot["bytes"])
record={"schema":"researchos.f08-independent-fixed-input-verification.v1","author_manifest":meta(src/"manifest.json"),"author_handoff":meta(src/"handoff.json"),"author_members":len(members),"author_physical_with_manifest":len(members)+1,"all_members_and_own_copies_verified":True,"member_refs":members,"external_handoff_refs_verified":externals,"full_source_test_bytes_loaded":True,"delta":stats,"public_vectors":{"before_count":len(before["files"]),"final_count":len(after["files"]),"common_count":len(common),"common_drift":drift,"added":added,"removed":removed,"duplicate_before":len(before["files"])-len(bv),"duplicate_final":len(after["files"])-len(av),"author_declared_final_drift":after["drift_count"],"added_url_matches_frozen_receipt_snapshot":url_added_matches},"public_receipt_refs_rehashed":receipt_refs,"nonreceipt_original_refs_not_read":unread_originals,"not_Main_stdlib_cache_or_first_read_authentication":True,"failed_original_script_not_changed_or_reexecuted":True,"failed_tool_origin":"4ddd35","this_is_a_distinct_post_shape_metadata_report":True,"candidate_execution":False,"Go_SQL_native_target_execution":False}
(own/"input-verification.json").write_bytes((json.dumps(record,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
print(json.dumps({"member_count":len(members),"physical_with_manifest":len(members)+1,"common":len(common),"before":len(bv),"final":len(av),"added_url_snapshot_matches":url_added_matches,"drift":len(drift),"receipts_rehashed":len(receipt_refs),"nonreceipt_originals_unread":len(unread_originals),"stats":{k:{x:y for x,y in v.items() if x not in ["delta","base","final"]} for k,v in stats.items()}},ensure_ascii=True))

