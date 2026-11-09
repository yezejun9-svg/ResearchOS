from review_tools import E,W,write,pin
old=E/'overlay-domain-runtime_pause_windows_test.go'
raw=old.read_text(encoding='utf-8')
needle='pauseCAS(tx,intent,"CHECKPOINT_SEALED",nil)'
assert raw.count(needle)==1
raw=raw.replace(needle,'pauseCAS(tx,intent,"CHECKPOINT_SEALED",Object{"checkpoint_sequence":1,"checkpoint_artifact":"fixture-artifact","checkpoint_use_receipt_hash":"fixture-use","checkpoint_use_principal":"executor","checkpoint_hash":"fixture-hash","checkpoint_bytes":1,"native_session_ref":"native","sdk_session_id":"sdk","queue_cut":0,"command_ledger_hash":"ledger","sdk_watermarks_json":"{}","model_calls":1,"tool_calls":0,"journal_checkpoint_hash":"journal"})')
target=E/'overlay-domain-runtime_pause_windows_test-v2.go';target.write_text(raw,encoding='utf-8')
write(E/'domain-overlay-v2.json',{'Replace':{str(W/'internal/domain/runtime_pause_windows_test.go'):str(target)}})
write(E/'domain-overlay-v2-inputs.json',{'classification':'FIXTURE_CONSTRUCTION_CORRECTION','previous_overlay':pin(old),'overlay':pin(target),'reason':'Sealed state fixture must include all required checkpoint columns; prior failed attempt retained, no production change.'})
