package recoveryauthority

import (
    "bytes"
    "encoding/json"
    "errors"
    "fmt"
    "strconv"
    "time"
)

var requiredHistoryRoles = []string{"original-authority","clock","once","go","contract","probe","lifecycle","invoke-admit","invoke-execute","stdout-admit","stderr-admit","stdout-execute","stderr-execute","source-manifest","binary-host","original-tool-io"}

func historyObject(raw []byte) (map[string]any,error) {
    d:=json.NewDecoder(bytes.NewReader(raw)); d.UseNumber(); var v map[string]any
    err:=d.Decode(&v); return v,err
}
func obj(m map[string]any,k string) map[string]any { v,_:=m[k].(map[string]any); return v }
func text(m map[string]any,k string) string { v,_:=m[k].(string); return v }
func number(m map[string]any,k string) string { v,_:=m[k].(json.Number); return string(v) }
func yes(m map[string]any,k string) bool { return m[k]==true }
func emptyErrors(m map[string]any) bool { v,ok:=m["errors"].([]any); return ok && len(v)==0 }
func readHistorical(raw map[string][]byte,t Tuple,pins []RawPin) (HistoricalObserver,string,string,error) {
    fail:=func() (HistoricalObserver,string,string,error) { return HistoricalObserver{},"","",errors.New("AUTHORITY_HISTORICAL_RAW_INCONSISTENCY") }
    for _,role:=range requiredHistoryRoles { if _,ok:=raw[role]; !ok { return fail() } }
    parsed:=map[string]map[string]any{}
    for _,role:=range []string{"clock","once","go","contract","probe","lifecycle","invoke-admit","invoke-execute"} {
        v,e:=historyObject(raw[role]); if e!=nil { return fail() }; parsed[role]=v
    }
    clock,once:=parsed["clock"],parsed["once"]
    started,se:=time.Parse(time.RFC3339Nano,text(clock,"started_utc")); deadline,de:=time.Parse(time.RFC3339Nano,text(clock,"deadline_utc"))
    if se!=nil || de!=nil || !deadline.Equal(started.Add(300*time.Second)) || time.Now().Before(deadline) || clock["clock_reset_permitted"]!=false || text(once,"state")!="CONSUMED_FOR_HOST_GO" || text(once,"qualification_run_id")!=t.RunID { return fail() }
    contract,probe,life:=parsed["contract"],parsed["probe"],parsed["lifecycle"]
    goGrant:=parsed["go"]
    if text(goGrant,"qualification_run_id")!=t.RunID || text(goGrant,"started_utc")!=text(clock,"started_utc") || text(life,"state")!="FAILED_EXECUTION_CLOSED" || text(life,"error")=="" || !yes(life,"go_sent") { return fail() }
    // Every reference captured by the original read guards must be pinned and
    // held now too. This includes historical source, binaries and original IO;
    // a manifest digest alone cannot silently replace its entire closure.
    byPath:=map[string]RawPin{}; for _,p:=range pins { byPath[p.Path]=p }
    checkRef:=func(ref map[string]any) bool {
        p,ok:=byPath[text(ref,"path")]
        return ok && p.SHA256=="sha256:"+text(ref,"sha256") && strconv.FormatInt(p.Bytes,10)==number(ref,"bytes")
    }
    if !checkRef(obj(goGrant,"execution_authority_ref")) || !checkRef(obj(goGrant,"coordinator_source_ref")) { return fail() }
    guardClosures,ok:=life["source_guard_cleanup"].([]any); if !ok || len(guardClosures)==0 { return fail() }
    for _,entry:=range guardClosures {
        guard,ok:=entry.(map[string]any)
        if !ok || !yes(guard,"closed") || text(guard,"verification")!="PASSED" || text(guard,"share_mode")!="FILE_SHARE_READ_ONLY" || number(guard,"retained_handles_count")!="0" || !emptyErrors(guard) { return fail() }
        entries,ok:=guard["entries"].([]any); if !ok || len(entries)==0 { return fail() }
        for _,value:=range entries { ref,ok:=value.(map[string]any); if !ok || !yes(ref,"verified") || !yes(ref,"final_path_match") || !yes(ref,"closed") || !checkRef(ref) { return fail() } }
    }
    held:=obj(contract,"held_identity")
    if !bytes.Equal(encoded(held),encoded(obj(probe,"held_identity"))) || !yes(held,"captured_before_resume") || !yes(held,"held_job_handle") || !yes(held,"held_primary_handle") || !yes(probe,"captured_before_resume") || !yes(probe,"in_job") || !yes(probe,"descendant_of_root") || !yes(probe,"direct_CreateProcess_from_root") || !yes(probe,"actual_IsProcessInJob_return") { return fail() }
    if number(contract,"root_pid")!=number(held,"owner_pid") || number(probe,"root_pid")!=number(held,"owner_pid") || number(once,"owner_pid")!=number(held,"owner_pid") || number(contract,"host_pid")!=number(held,"runner_pid") || number(probe,"host_pid")!=number(held,"runner_pid") || text(contract,"root_job_id")!=text(held,"job_binding_id") || text(probe,"root_job_id")!=text(held,"job_binding_id") || text(contract,"deadline_utc")!=text(clock,"deadline_utc") || number(life,"actual_parent_pid")!=number(held,"owner_pid") || life["provider_requests"]!=nil || life["automatic_retry"]!=false { return fail() }
    jobs,ok:=life["jobs"].([]any); if !ok || len(jobs)!=2 { return fail() }
    seen:=map[string]bool{}; closedMono:=""
    for _,entry:=range jobs {
        j,ok:=entry.(map[string]any); if !ok { return fail() }
        label:=text(j,"label"); if (label!="host-admit-only" && label!="host-execute-admitted") || seen[label] { return fail() }; seen[label]=true
        cleanup:=obj(j,"cleanup"); proof:=obj(cleanup,"proof"); watchdog:=obj(cleanup,"watchdog"); producer:=obj(cleanup,"producer")
        if !yes(cleanup,"closed") || !yes(proof,"captured_before_resume") || !yes(proof,"held_job_handle") || !yes(proof,"held_primary_handle") || number(proof,"active_processes")!="0" || !yes(proof,"primary_exit_confirmed") || !yes(proof,"pid_match") || !yes(proof,"creation_match") || !emptyErrors(proof) || !yes(watchdog,"duplicate_handle_closed") || !emptyErrors(watchdog) || !yes(producer,"closed") || !yes(producer,"job_handle_closed") || !yes(producer,"primary_handle_closed") || !emptyErrors(producer) || text(producer,"run_uuid")!=text(proof,"run_uuid") || number(producer,"owner_pid")!=number(proof,"owner_pid") || number(proof,"owner_pid")!=number(held,"owner_pid") { return fail() }
        role:="invoke-admit"; if label=="host-execute-admitted" { role="invoke-execute" }
        inv:=parsed[role]; result:=obj(inv,"result"); jc:=obj(result,"job_cleanup")
        if number(result,"owned_child_pid")!=number(proof,"runner_pid") || number(result,"creation_time_100ns")!=number(proof,"creation_time_100ns") || number(result,"actual_exit")!=number(proof,"primary_exit_code") || number(inv,"native_exit")!=number(proof,"primary_exit_code") || !yes(result,"resumed") || !yes(jc,"assigned_before_resume") || !yes(jc,"unnamed_exclusive_job") || !yes(jc,"kill_on_job_close_configured") || number(jc,"active_processes_last_observed")!="0" || !yes(jc,"job_idle_confirmed") || !yes(jc,"primary_exit_confirmed") || !yes(jc,"handles_closed") || !emptyErrors(jc) { return fail() }
        suffix:="admit"; if role=="invoke-execute" { suffix="execute" }
        for _,stream:=range []string{"stdout","stderr"} {
            ref:=obj(inv,stream+"_ref"); data:=raw[stream+"-"+suffix]
            if "sha256:"+text(ref,"sha256")!=digest(data) || number(ref,"bytes")!=strconv.Itoa(len(data)) { return fail() }
        }
        if label=="host-execute-admitted" {
            for _,k:=range []string{"run_uuid","job_binding_id"} { if text(proof,k)!=text(held,k) { return fail() } }
            for _,k:=range []string{"owner_pid","runner_pid","creation_time_100ns"} { if number(proof,k)!=number(held,k) { return fail() } }
            if number(proof,"primary_exit_code")!="1" || text(inv,"error")=="" || len(raw["stderr-execute"])==0 { return fail() }
            closedMono=number(proof,"observed_monotonic")
        }
    }
    owner,oe:=strconv.ParseUint(number(held,"owner_pid"),10,32); host,he:=strconv.ParseUint(number(held,"runner_pid"),10,32)
    if oe!=nil || he!=nil || closedMono=="" { return fail() }
    return HistoricalObserver{OwnerPID:uint32(owner),HostPID:uint32(host),HostBirth100ns:number(held,"creation_time_100ns"),HostJobID:text(held,"job_binding_id"),RunUUID:text(held,"run_uuid"),ClosedObservedMonotonic:closedMono},text(clock,"started_utc"),text(clock,"deadline_utc"),nil
}

func validatePinRoles(pins []RawPin) error {
    seen:=map[string]bool{}; paths:=map[string]bool{}
    for _,p:=range pins {
        if p.Role=="" || seen[p.Role] || paths[p.Path] || !validHash(p.SHA256) || p.Bytes<0 || p.Path=="" { return fmt.Errorf("AUTHORITY_PIN_INVALID_OR_DUPLICATE") }
        seen[p.Role]=true; paths[p.Path]=true
    }
    for _,role:=range requiredHistoryRoles { if !seen[role] { return fmt.Errorf("AUTHORITY_PIN_REQUIRED:%s",role) } }
    return nil
}
