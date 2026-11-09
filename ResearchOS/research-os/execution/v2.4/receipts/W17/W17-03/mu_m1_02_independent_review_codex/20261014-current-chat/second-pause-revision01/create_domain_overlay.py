from review_tools import E,W,write,pin
src=W/'internal/domain/runtime_pause_windows_test.go'
raw=src.read_text(encoding='utf-8')
raw=raw.replace('"path/filepath"','"path/filepath"\n"strings"')
needle='\t\terr = recordPauseEffectCutoff(tx, intent)'
assert raw.count(needle)==1
raw=raw.replace(needle,'''\t\tif strings.HasPrefix(t.Name(),"TestReviewPauseEffectPurpose") {
			for _, state := range []string{"PREPARED","STARTED","CONFIRMED","NOT_APPLIED","UNKNOWN"} {
				effect := Object{"project_id":"p","run_id":"r","key":state,"request_hash":"hash-"+state,"epoch":2,"state":state}
				if err = effectAppend(tx,"p","r",state,effect); err != nil { t.Fatal(err) }
			}
		}
'''+needle)
raw+='''
func TestReviewPauseEffectPurpose(t *testing.T) {
	cases := []struct{name,kind,key,hash string;want bool}{
		{"read-prepared","effect-read","PREPARED","",true},
		{"start-prepared","effect-start","PREPARED","hash-PREPARED",true},
		{"start-started-denied","effect-start","STARTED","hash-STARTED",false},
		{"observe-started","effect-observe","STARTED","hash-STARTED",true},
		{"observe-confirmed","effect-observe","CONFIRMED","hash-CONFIRMED",true},
		{"continue-started","effect-continue","STARTED","hash-STARTED",true},
		{"continue-confirmed-denied","effect-continue","CONFIRMED","hash-CONFIRMED",false},
		{"finish-confirmed","effect-finish","CONFIRMED","hash-CONFIRMED",true},
		{"finish-not-applied","effect-finish","NOT_APPLIED","hash-NOT_APPLIED",true},
		{"unknown-denied","effect-read","UNKNOWN","",false},
		{"foreign-hash-denied","effect-continue","STARTED","foreign",false},
		{"new-key-denied","effect-read","new-key","",false},
		{"unknown-purpose-denied","launch","STARTED","hash-STARTED",false},
		{"old-epoch-denied","effect-continue","STARTED","hash-STARTED",false},
		{"changed-prepared-sequence-denied","effect-start","PREPARED","hash-PREPARED",false},
		{"sealed-effect-denied","effect-observe","STARTED","hash-STARTED",false},
	}
	for _, tc := range cases { t.Run(tc.name,func(t *testing.T) {
		db,task,run,dispatch := runtimePausePurposeFixture(t,true)
		tx,err := db.Begin();if err != nil {t.Fatal(err)};defer tx.Rollback()
		if tc.name=="old-epoch-denied" || tc.name=="changed-prepared-sequence-denied" {
			effect,readErr := latestEffect(tx,"p","r",tc.key);if readErr!=nil {t.Fatal(readErr)}
			if tc.name=="old-epoch-denied" {effect["epoch"]=1}
			if err=effectAppend(tx,"p","r",tc.key,effect);err!=nil {t.Fatal(err)}
		}
		if tc.name=="sealed-effect-denied" {
			intent,readErr:=pauseIntent(tx,"p","r",2);if readErr!=nil {t.Fatal(readErr)}
			if _,err=pauseCAS(tx,intent,"CHECKPOINT_SEALED",nil);err!=nil {t.Fatal(err)}
		}
		current,err:=pauseDispatchPurposeGate(tx,"p",task,run,dispatch,&runtimePauseGatePurpose{kind:tc.kind,effectKey:tc.key,requestHash:tc.hash})
		if got:=err==nil&&current!=nil;got!=tc.want {t.Fatalf("purpose %s allow=%v want=%v error=%v",tc.kind,got,tc.want,err)}
	}) }
}

func TestReviewLocalLaunchMalformedHistoricalHold(t *testing.T) {
	for _, name:=range []string{"epoch-leading-zero","epoch-plus","epoch-decimal","epoch-zero","epoch-future","reservation","basis","empty-time","empty-id","bad-receipt","nonzero","wrong-currency","wrong-event","wrong-policy"} {
		t.Run(name,func(t *testing.T) {
			o:=orchestrationSetup(t);task:=o.task("review-historical-hold",Empty(),Empty());r:=o.claim(task);runID:=Str(r.run,"id")
			tx,err:=o.f.db.Begin();if err!=nil {t.Fatal(err)};defer tx.Rollback()
			goal,err:=load(tx,o.f.project,"Goal",Str(task,"goal_id"));if err!=nil {t.Fatal(err)}
			suffix:="1";switch name {case "epoch-leading-zero":suffix="01";case "epoch-plus":suffix="+1";case "epoch-decimal":suffix="1.0";case "epoch-zero":suffix="0";case "epoch-future":suffix="3"}
			request:="runtime-local-launch/"+runID+"/"+suffix
			hold:=Merge(Base(o.f.project),Object{"policy_id":goal["budget_policy_id"],"run_id":runID,"operation":"RESERVE","money":Object{"amount":"0","currency":"USD"},"provider_request_id":request,"provider_event_id":request,"reservation_id":nil,"cost_basis":"UPPER_BOUND","occurred_at":Now()});delete(hold,"updated_at")
			switch name {case "reservation":hold["reservation_id"]="other";case "basis":hold["cost_basis"]="ACTUAL";case "empty-time":hold["occurred_at"]="";case "empty-id":hold["id"]="";case "nonzero":hold["money"]=Object{"amount":"1","currency":"USD"};case "wrong-currency":hold["money"]=Object{"amount":"0","currency":"EUR"};case "wrong-event":hold["provider_event_id"]="other";case "wrong-policy":hold["policy_id"]="other"}
			hold["receipt_hash"]=Receipt(hold);if name=="bad-receipt" {hold["receipt_hash"]="bad"}
			if _,err=tx.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable) VALUES(?,'BudgetLedgerEntry',?,1,?,?,1)`,o.f.project,hold["id"],Bytes(hold),Hash(hold));err!=nil {t.Fatal(err)}
			if err=tx.Commit();err!=nil {t.Fatal(err)}
			before:=runtimeLocalLaunchRows(t,o,runID)
			if err=runtimeLocalLaunchEpoch(t,o,runID,2);err==nil {t.Fatal("malformed historical hold accepted")}
			if Hash(before)!=Hash(runtimeLocalLaunchRows(t,o,runID)) {t.Fatal("rejection changed ledger")}
		})
	}
}
'''
target=E/'overlay-domain-runtime_pause_windows_test.go';target.write_text(raw,encoding='utf-8')
write(E/'domain-overlay.json',{'Replace':{str(src):str(target)}})
write(E/'domain-overlay-inputs.json',{'classification':'INDEPENDENT_FIXTURE_PROBES_TEST_ONLY','source':pin(src),'overlay':pin(target)})
