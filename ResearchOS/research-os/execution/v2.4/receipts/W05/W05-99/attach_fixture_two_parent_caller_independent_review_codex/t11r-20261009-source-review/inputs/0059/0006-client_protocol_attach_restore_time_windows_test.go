//go:build windows

package domain

import (
	"bytes"
	"testing"
	"time"
)

// Pure time facts exercise the production accumulator without creating runtime
// observations, granting authority, or claiming native positive acceptance.
func TestClientAttachRestoreTimestampOrdering(t *testing.T) {
	for _, pair := range [][2]string{
		{"2026-10-09T00:00:00.1Z", "2026-10-09T00:00:00.11Z"},
		{"2026-10-09T00:00:00Z", "2026-10-09T00:00:00.000000001Z"},
		{"2026-10-09T08:00:00.1+08:00", "2026-10-09T00:00:00.11Z"},
	} {
		older, ok := clientAttachRestoreTime(pair[0])
		if !ok { t.Fatal(pair[0]) }
		newer, ok := clientAttachRestoreTime(pair[1])
		if !ok || !newer.After(older) || older.Location() != time.UTC || newer.Location() != time.UTC { t.Fatal(pair) }
		for _, reverse := range []bool{false, true} {
			var order clientAttachObservationOrder
			if reverse {
				order.add(newer, false)
				order.add(older, true)
			} else {
				order.add(older, true)
				order.add(newer, false)
			}
			if !order.seen || order.valid || !order.latest.Equal(newer) { t.Fatalf("later partial hidden: %+v", order) }
		}
	}
	a, _ := clientAttachRestoreTime("2026-10-09T00:00:00.1Z")
	b, _ := clientAttachRestoreTime("2026-10-09T08:00:00.100+08:00")
	for _, reverse := range []bool{false, true} {
		var order clientAttachObservationOrder
		if reverse { order.add(b, false); order.add(a, true) } else { order.add(a, true); order.add(b, false) }
		if !a.Equal(b) || order.valid { t.Fatal("same-instant partial discarded") }
	}
}

func TestClientAttachRestoreRelatedTimestampParsing(t *testing.T) {
	// The same production parser serves barrier, observation, handoff effective
	// time and writer expiry; malformed input has no usable chronological order.
	for _, raw := range []string{"", "unknown", "!2026-10-09T00:00:00Z", "2026-10-09", "2026-02-30T00:00:00Z", "2026-10-09T00:00:00", "0001-01-01T00:00:00Z"} {
		if _, valid := clientAttachRestoreTime(raw); valid { t.Fatalf("accepted unknown time %q", raw) }
	}
	barrier, _ := clientAttachRestoreTime("2026-10-09T00:00:00.1Z")
	observation, _ := clientAttachRestoreTime("2026-10-09T00:00:00.11Z")
	handoff, _ := clientAttachRestoreTime("2026-10-09T00:00:00.111Z")
	expiry, _ := clientAttachRestoreTime("2026-10-09T00:00:00.1111Z")
	if !observation.After(barrier) || !handoff.After(observation) || !expiry.After(handoff) { t.Fatal("related times compared as strings") }
}

// These are artificial rejection fixtures only. The earlier settled shape is
// paired with a later partial or unorderable fact. They never provide a genuine
// post-restore native observation or serve as a valid-fresh positive fixture.
func TestClientAttachRestoreRejectsMisorderedOrUnknownObservationTime(t *testing.T) {
	for _, mode := range []string{"fractional-later-partial", "same-instant-partial", "malformed-observation", "malformed-barrier"} {
		t.Run(mode, func(t *testing.T) {
			o := orchestrationSetup(t)
			f := o.f
			task := o.task("attach-time-rejection", Empty(), Empty())
			run := o.claim(task)
			runID := Str(run.run, "id")
			epoch, err := Num(run.run, "lease_epoch")
			if err != nil { t.Fatal(err) }
			service, sid, _ := handlerTypedSession(t, f, "attach-time-owner")
			barrier := "2026-10-09T00:00:00.09Z"
			if mode == "malformed-barrier" { barrier = "unknown" }
			if _, err = f.db.Exec("UPDATE client_sessions SET run_id=?,lease_expires_at=? WHERE id=?", runID, time.Now().UTC().Add(5*time.Minute).Format(time.RFC3339Nano), sid); err != nil { t.Fatal(err) }
			if _, err = f.db.Exec("INSERT INTO backup_restore_barriers(project,run,restored_at) VALUES(?,?,?)", f.project, runID, barrier); err != nil { t.Fatal(err) }
			if _, err = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','RECONCILING','$.children_stopped',json('true'),'$.queue_empty',json('true'),'$.lease_expires_at','1970-01-01T00:00:00Z') WHERE project=? AND kind='Run' AND id=?", f.project, runID); err != nil { t.Fatal(err) }
			newer := "2026-10-09T00:00:00.11Z"
			if mode == "same-instant-partial" { newer = "2026-10-09T08:00:00.100+08:00" }
			if mode == "malformed-observation" { newer = "!unknown" }
			for i, timestamp := range []string{"2026-10-09T00:00:00.1Z", newer} {
				observation := Object{"spec": Object{"run_id":runID,"task_id":run.run["task_id"],"epoch":epoch}, "children_stopped":true,"queue_empty":i==0}
				if _, err = f.db.Exec("INSERT INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,?,?,?,?)", f.project, runID, epoch, Hash(observation), string(Bytes(observation)), timestamp); err != nil { t.Fatal(err) }
			}
			before := attachContractRead(t, f, sid)
			var runBefore string
			if err = f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND id=?", f.project, runID).Scan(&runBefore); err != nil { t.Fatal(err) }
			for _, client := range []string{before.writer, "attach-time-other-client"} {
				env := attachContractCommand(f, sid, client, before.revision)
				first, replay := handlerCommand(t, f, service, env)
				if replay || deref(first.Status)!="REJECTED" || deref(first.ErrorCode)!="SESSION_BUSY" || attachContractRead(t,f,sid)!=before || attachContractEventCount(t,f,sid,deref(env.CommandID))!=0 { t.Fatalf("timestamp bypass: %s",Bytes(first)) }
				again, replay := handlerCommand(t,f,service,env)
				if !replay || !bytes.Equal(Bytes(first),Bytes(again)) || attachContractRead(t,f,sid)!=before { t.Fatal("timestamp rejection replay wrote state") }
			}
			var runAfter, barrierAfter string
			if err = f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND id=?", f.project, runID).Scan(&runAfter); err != nil { t.Fatal(err) }
			if err = f.db.QueryRow("SELECT restored_at FROM backup_restore_barriers WHERE project=? AND run=?", f.project, runID).Scan(&barrierAfter); err != nil { t.Fatal(err) }
			if runBefore!=runAfter || barrierAfter!=barrier { t.Fatal("timestamp gate changed restore state") }
		})
	}
}
