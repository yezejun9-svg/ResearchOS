//go:build windows

package store

import (
 "context"
 "testing"
)

func TestReviewMalformedModelEffectMustNotBeSafe(t *testing.T) {
 for _,body:=range []string{`{"payload":{"capability":"MODEL"}}`,`{"state":null,"payload":{"capability":"MODEL"}}`} {
  t.Run(body,func(t *testing.T){
   path,db,subject:=ownedStopSchema24Fixture(t)
   if _,err:=db.Exec(`INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)`,subject.Project,subject.Run,"review-malformed-state",body);err!=nil{t.Fatalf("fixture insertion refused by real schema: %v",err)}
   b,err:=AcquireOwnedStopBarrier(context.Background(),path);if err!=nil{t.Fatal(err)};defer b.Close()
   s,err:=b.SafetySnapshot(context.Background(),subject)
   if err!=nil{t.Logf("malformed effect refused: %v",err);return}
   t.Logf("NATIVE_SQLITE_SAFETY %+v safe=%v",s,s.ExactOldSubjectSafe())
   if s.ExactOldSubjectSafe(){t.Fatal("additional MODEL effect with absent/null state was accepted as exact old subject safe")}
  })
 }
}

func TestReviewFiniteEffectStateSemantics(t *testing.T) {
 cases:=[]struct{name,key,body string; sequence int; wantSafe bool}{
  {"additional null","extra",`{"state":null,"payload":{"capability":"MODEL"}}`,1,false},
  {"additional missing","extra",`{"payload":{"capability":"MODEL"}}`,1,false},
  {"additional boolean","extra",`{"state":true,"payload":{"capability":"MODEL"}}`,1,false},
  {"additional numeric","extra",`{"state":0,"payload":{"capability":"MODEL"}}`,1,false},
  {"additional array","extra",`{"state":[],"payload":{"capability":"MODEL"}}`,1,false},
  {"additional object","extra",`{"state":{},"payload":{"capability":"MODEL"}}`,1,false},
  {"additional empty string","extra",`{"state":"","payload":{"capability":"MODEL"}}`,1,false},
  {"additional unknown enum","extra",`{"state":"UNRECOGNIZED","payload":{"capability":"MODEL"}}`,1,false},
  {"additional UNKNOWN","extra",`{"state":"UNKNOWN","payload":{"capability":"MODEL"}}`,1,false},
  {"additional CONFIRMED","extra",`{"state":"CONFIRMED","payload":{"capability":"MODEL"}}`,1,false},
  {"missing capability","extra",`{"state":null}`,1,false},
  {"null capability","extra",`{"state":null,"payload":{"capability":null}}`,1,false},
  {"old latest null","old-model",`{"state":null,"payload":{"capability":"MODEL"}}`,2,false},
  {"old latest missing","old-model",`{"payload":{"capability":"MODEL"}}`,2,false},
  {"old history null before valid latest","old-model",`{"state":null,"payload":{"capability":"MODEL"}}`,0,true},
  {"old history UNKNOWN before valid latest","old-model",`{"state":"UNKNOWN","payload":{"capability":"MODEL"}}`,0,true},
 }
 for _,tc:=range cases {t.Run(tc.name,func(t *testing.T){
  path,db,subject:=ownedStopSchema24Fixture(t)
  if _,err:=db.Exec(`INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,?,?)`,subject.Project,subject.Run,tc.key,tc.sequence,tc.body);err!=nil{t.Fatalf("real schema insertion: %v",err)}
  b,err:=AcquireOwnedStopBarrier(context.Background(),path);if err!=nil{t.Fatal(err)};defer b.Close()
  s,err:=b.SafetySnapshot(context.Background(),subject)
  safe:=err==nil&&s.ExactOldSubjectSafe()
  t.Logf("FINITE_CASE name=%s safe=%v expected=%v snapshot=%+v error=%v",tc.name,safe,tc.wantSafe,s,err)
  if safe!=tc.wantSafe{t.Fatalf("unexpected safety result: got=%v want=%v",safe,tc.wantSafe)}
 })}
}
