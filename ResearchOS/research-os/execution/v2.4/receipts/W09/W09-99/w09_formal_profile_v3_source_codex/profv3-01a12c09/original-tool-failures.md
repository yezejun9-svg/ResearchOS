# V3 original tool failures

Source-only record. These were tool-input failures; no Native, dispatcher, Go, model or formal acceptance command ran. The root agent owns global failure numbering.

## Original 971 (Root assigned)

```js
const p="*** Begin Patch\n*** Update File: D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v3_source_codex/profv3-01a12c09/formal_profile_w09.after.py\n@@\n             api.stamp(item[\"native_started_at\"], \"native start\")\n+            <= api.stamp(item[\"native_event_started_at\"], \"Go first event\")\n+            <= api.stamp(item[\"native_event_ended_at\"], \"Go last event\")\n             <= api.stamp(item[\"native_ended_at\"], \"native end\")\n@@\n         api.stamp(item[\"native_started_at\"], \"native start\")\n+        <= api.stamp(item[\"native_event_started_at\"], \"Go first event\")\n+        <= api.stamp(item[\"native_event_ended_at\"], \"Go last event\")\n         <= api.stamp(item[\"native_ended_at\"], \"native end\")\n*** End Patch";text(await tools.apply_patch(p));
```

```text
Script failed
Wall time 0.0 seconds
Output: Script error:
apply_patch verification failed: Failed to find expected lines in D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\formal_profile_w09.after.py:
        api.stamp(item["native_started_at"], "native start")
        <= api.stamp(item["native_ended_at"], "native end")
```

Outer shell, Python, Native and model numeric exits: NULL.

## Original 972 (Root assigned)

```js
const r=await tools.exec_command({cmd:"rg -n '\"id\": \"W09-99\"|\"root_capture|\"context_ref\"|\"evidence_refs\"' execution/v2.4/step_state.json execution/v2.4/*.json | Select-Object -First 28",workdir:"D:\\作品集\\ResearchOS\\research-os",max_output_tokens:1000});text(r);
```

```json
{"chunk_id":"50cbef","wall_time_seconds":0.9304298,"exit_code":1,"original_token_count":23,"output":"rg: execution/v2.4/*.json: 文件名、目录名或卷标语法不正确。 (os error 123)\n"}
```

Outer shell exit: 1. Python, Native and model numeric exits: NULL.

## Original 973 (Root assigned)

```js
const r=await tools.exec_command({cmd:"rg -n '\"id\": \"W09-99\"|\"evidence_refs\"|\"root_capture' 'execution/v2.4/step_state.json'",workdir:"D:\\作品集\\ResearchOS\\research-os",max_output_tokens:700});text(r);
```

```json
{"chunk_id":"6024ee","wall_time_seconds":0.6834019,"exit_code":1,"original_token_count":0,"output":""}
```

Outer shell exit: 1. Python, Native and model numeric exits: NULL.

## Unassigned original after 973

```js
const p="*** Begin Patch\n*** Update File: D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v3_source_codex/profv3-01a12c09/source_controls_v3.py\n@@\n go_report = {\"started_at\": \"2026-10-01T00:00:00Z\", \"ended_at\": \"2026-10-01T00:10:00Z\"}\n reject(\"F2_PINNED_FUTURE_GO_STREAM_REJECTED\", lambda: profile[\"_native_event_interval\"](\n     api, go_raw, go_report, [\"TestW09Synthetic\"], \"synthetic\"), \"GO_EVENT_CLOCK\")\n+reviewer_example = (R / \"execution/v2.4/receipts/W09/W09-99/\"\n+                    \"w09_formal_profile_v2_independent_review_codex/profv2r-01a12b31/\"\n+                    \"synthetic-counterexamples.json\")\n+reviewer_raw = reviewer_example.read_bytes()\n+assert len(reviewer_raw) == 5259 and hashlib.sha256(reviewer_raw).hexdigest() == (\n+    \"4c82c2faa0779fdedbeb6c5cd8a4f14e43896089d189237230c0e3efd2c4e99b\")\n+reviewer_f2 = json.loads(reviewer_raw)[\"F2\"]\n+reviewer_go = b\"\".join((json.dumps(event) + \"\\n\").encode(\"utf-8\")\n                       for event in reviewer_f2[\"events\"])\n+reject(\"F2_EXACT_V2_REVIEW_COUNTEREXAMPLE_REJECTED\", lambda: profile[\"_native_event_interval\"](\n+    api, reviewer_go, reviewer_f2[\"report_times\"], [\"TestW09Synthetic\"], \"synthetic\"),\n+    \"GO_EVENT_CLOCK\")\n*** End Patch";text(await tools.apply_patch(p));
```

```text
Script failed
Wall time 0.0 seconds
Output: Script error:
apply_patch verification failed: Failed to find expected lines in D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py:
go_report = {"started_at": "2026-10-01T00:00:00Z", "ended_at": "2026-10-01T00:10:00Z"}
reject("F2_PINNED_FUTURE_GO_STREAM_REJECTED", lambda: profile["_native_event_interval"](
    api, go_raw, go_report, ["TestW09Synthetic"], "synthetic"), "GO_EVENT_CLOCK")
                      for event in reviewer_f2["events"])
```

Outer shell, Python, Native and model numeric exits: NULL.
