//go:build windows

package domain

import (
 "database/sql"
 "fmt"
 "strings"
 "testing"
)

// Read every cell, not just table counts, so updates during supposedly read-only
// operations and rollback failures are observable.
func independentTranscriptState(t *testing.T, db *sql.DB) string {
 t.Helper()
 state := Object{}
 for _, table := range []string{"domain_objects", "domain_versions", "outbox", "uploaded_content", "idempotency", "client_sessions"} {
  rows, err := db.Query("SELECT * FROM " + table + " ORDER BY 1,2")
  if err != nil { t.Fatal(err) }
  cols, err := rows.Columns(); if err != nil { t.Fatal(err) }
  all := Empty()
  for rows.Next() {
   values := make([]any,len(cols)); ptrs := make([]any,len(cols))
   for i := range values {ptrs[i]=&values[i]}
   if err=rows.Scan(ptrs...); err != nil {t.Fatal(err)}
   all=append(all, values)
  }
  if err=rows.Err(); err != nil {t.Fatal(err)}
  rows.Close(); state[table]=all
 }
 return Hash(state)
}

func TestIndependentTranscriptMultipartExactReadOnly(t *testing.T) {
 f:=contextFixture(t); doc,sid:=transcriptSession(t,f,199)
 chunk:=strings.Repeat(" 空格🙂\n",3000)
 expected:=chunk+"\t  尾🙂  \r\n"
 sourceTx(t,f.db,func(tx *sql.Tx) error {
  var wm,rev,epoch int64
  if err:=tx.QueryRow(`SELECT event_watermark,revision,writer_epoch FROM client_sessions WHERE id=?`,sid).Scan(&wm,&rev,&epoch);err!=nil{return err}
  events:=[]Object{
   {"part_index":0,"phase":"START","text":"","content_offset_utf8_bytes":0},
   {"part_index":0,"phase":"DELTA","text":chunk,"content_offset_utf8_bytes":0},
   {"part_index":0,"phase":"DELTA","text":"\t  尾🙂  \r\n","content_offset_utf8_bytes":len(chunk)},
   {"part_index":0,"phase":"END","text":"","content_offset_utf8_bytes":len(expected)},
   {"part_index":1,"phase":"START","text":"","content_offset_utf8_bytes":0},
   {"part_index":1,"phase":"DELTA","text":" \t\n","content_offset_utf8_bytes":0},
   {"part_index":1,"phase":"END","text":"","content_offset_utf8_bytes":3},
  }
  for _,p:=range events {
   p["message_id"],p["role"]="multipart","SYSTEM";wm++
   ev:=&SessionEvent{EventID:strptr(ID()),SessionID:&sid,Sequence:&wm,CoreBuildID:strptr("fixture-build"),ProtocolVersion:strptr(ProtocolV2),Kind:strptr("MESSAGE"),Payload:Bytes(p)}
   if err:=AppendSessionEvent(ctxTranscript,tx,doc,f.project,ev,epoch,rev);err!=nil{return err};rev++
  }
  if err:=transcriptAppend(ctxTranscript,tx,doc,f.project,sid,"last"," 尾 \n");err!=nil{return err}
  return f.s.sealSessionTranscript(ctxTranscript,tx,doc,f.project,sid,f.owner)
 })
 before:=independentTranscriptState(t,f.db)
 if _,err:=f.db.Exec("PRAGMA query_only=ON");err!=nil{t.Fatal(err)}
 tx,err:=f.db.Begin();if err!=nil{t.Fatal(err)}
 snap,err:=BuildSessionSnapshot(ctxTranscript,tx,doc,f.project,sid);if err!=nil{t.Fatal(err)}
 msgs:=Arr(snap,"messages")
 if len(msgs)!=200||snap["has_earlier_messages"]!=true||Str(msgs[0].(Object),"message_id")!="m1"{t.Fatal("last-200 window incorrect")}
 earliest,_:=Num(snap,"earliest_event_sequence");if earliest!=4{t.Fatalf("earliest %d",earliest)}
 a,err:=load(tx,f.project,"Artifact",Str(snap["transcript_artifact_ref"].(Object),"id"));if err!=nil{t.Fatal(err)}
 var raw []byte;if err=tx.QueryRow(`SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`,f.project,a["storage_key"]).Scan(&raw);err!=nil{t.Fatal(err)}
 body,err:=Decode(raw);if err!=nil{t.Fatal(err)}
 full:=Arr(body,"messages");seq:=Arr(body,"message_sequences")
 if len(full)!=201||len(seq)!=201||len(raw)<=32768{t.Fatal("full history truncated")}
 m:=full[199].(map[string]any);parts:=Arr(m,"parts")
 if m["message_id"]!="multipart"||m["role"]!="SYSTEM"||m["complete"]!=true||len(parts)!=2||Str(parts[0].(map[string]any),"text")!=expected||Str(parts[1].(map[string]any),"text")!=" \t\n"{t.Fatal("multipart/whitespace bytes altered")}
 s:=seq[199].(map[string]any);start,_:=Num(s,"start_sequence");end,_:=Num(s,"end_sequence");through,_:=Num(body,"through_sequence")
 if start!=598||end!=604||through!=607||a["measurement_mode"]!="FIXTURE"||body["measurement_basis"]!="USER_JOURNAL_ONLY"{t.Fatalf("sequence/provenance %d %d %d",start,end,through)}
 if err=tx.Commit();err!=nil{t.Fatal(err)}
 if before!=independentTranscriptState(t,f.db){t.Fatal("read changed stored cell")}
 t.Logf("asserted 201 records, 2 exact parts, whitespace, SYSTEM role, sequence 598..604 through 607, %d bytes, query_only snapshot, all-cell equality",len(raw))
}

func TestIndependentTranscriptLegacyAndStaleShort(t *testing.T) {
 for _,count:=range []int{0,1,200,201}{t.Run(fmt.Sprint(count),func(t *testing.T){
  f:=contextFixture(t);doc,sid:=transcriptSession(t,f,count)
  before:=independentTranscriptState(t,f.db)
  tx,err:=f.db.Begin();if err!=nil{t.Fatal(err)}
  snap,err:=BuildSessionSnapshot(ctxTranscript,tx,doc,f.project,sid)
  if count<=200 {if err!=nil||len(Arr(snap,"messages"))!=count||snap["transcript_artifact_ref"]!=nil||snap["has_earlier_messages"]!=false{t.Fatalf("legacy short %v",err)}}else if err==nil{t.Fatal("long missing ref falsely complete")}
  tx.Rollback();if before!=independentTranscriptState(t,f.db){t.Fatal("legacy read wrote")}
 })}
 f:=contextFixture(t);doc,sid:=transcriptSession(t,f,1)
 sourceTx(t,f.db,func(tx *sql.Tx)error{return f.s.sealSessionTranscript(ctxTranscript,tx,doc,f.project,sid,f.owner)})
 tx,err:=f.db.Begin();if err!=nil{t.Fatal(err)};defer tx.Rollback()
 if err=transcriptAppend(ctxTranscript,tx,doc,f.project,sid,"after-seal","new");err!=nil{t.Fatal(err)}
 if _,err=BuildSessionSnapshot(ctxTranscript,tx,doc,f.project,sid);err==nil{t.Fatal("short stale ref accepted")}
}

func TestIndependentTranscriptRollbackAndReplayAllCells(t *testing.T) {
 f:=contextFixture(t);doc,sid:=transcriptSession(t,f,1);svc,env:=transcriptSend(t,f,doc,sid)
 if _,err:=f.db.Exec(`CREATE TRIGGER independent_seal_failure BEFORE UPDATE OF sealed ON uploaded_content WHEN CAST(NEW.bytes AS TEXT) LIKE '%researchos.session-transcript.v1%' BEGIN SELECT RAISE(ABORT,'independent seal failure'); END`);err!=nil{t.Fatal(err)}
 before:=independentTranscriptState(t,f.db)
 tx,err:=f.db.Begin();if err!=nil{t.Fatal(err)}
 _,_,err=svc.Execute(ctxTranscript,tx,env,f.owner)
 if err==nil||!strings.Contains(err.Error(),"independent seal failure"){t.Fatalf("fault not propagated %v",err)}
 tx.Rollback();if before!=independentTranscriptState(t,f.db){t.Fatal("rollback changed existing stored cells")}
 if _,err=f.db.Exec(`DROP TRIGGER independent_seal_failure`);err!=nil{t.Fatal(err)}
 sourceTx(t,f.db,func(tx *sql.Tx)error{res,replay,err:=svc.Execute(ctxTranscript,tx,env,f.owner);if err==nil&&(replay||deref(res.Status)!="COMPLETED"){t.Fatal("first execution")};return err})
 before=independentTranscriptState(t,f.db)
 sourceTx(t,f.db,func(tx *sql.Tx)error{res,replay,err:=svc.Execute(ctxTranscript,tx,env,f.owner);if err==nil&&(!replay||deref(res.Status)!="COMPLETED"){t.Fatal("replay response")};return err})
 if before!=independentTranscriptState(t,f.db){t.Fatal("replay changed any stored cell")}
 t.Log("USER rollback and same command replay compared every cell in six affected tables")
}
