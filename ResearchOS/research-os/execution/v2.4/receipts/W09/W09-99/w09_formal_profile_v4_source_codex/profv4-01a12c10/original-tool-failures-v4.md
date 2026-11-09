# V4 original tool failure 985

This new original failed before the Source sealer wrote HDF, MF, controls or diffs. No Native, Go, dispatcher, model, Main or Canon command ran. Root assigned global ordinal 985.

```js
const cmd="& 'C:\\Users\\yqyyds\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe' -I -S -B -X utf8 'execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v4_source_codex/profv4-01a12c10/make_packet_v4.py'\n$sourcePyExit=$LASTEXITCODE\nWrite-Output \"ROOT_SOURCE_PYTHON_EXIT=$sourcePyExit\"\nexit $sourcePyExit";const r=await tools.exec_command({cmd,workdir:"D:\\作品集\\ResearchOS\\research-os",max_output_tokens:1200});text(r);
```

```text
Traceback (most recent call last):
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v4_source_codex\profv4-01a12c10\make_packet_v4.py", line 55, in <module>
    assert pin(after) == prior_mf["target_after"]["execution/v2.4/formal_case_index.py"]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
ROOT_SOURCE_PYTHON_EXIT=1
```

Original tool result: `chunk_id=52dcb1`, `wall_time_seconds=0.8670099`, outer exit 1, Python exit 1, Native/Go/dispatcher/model numeric exits NULL. The failure arose from comparing a relocated v4 proposal reference's absolute path to the v3 proposal reference; the bytes and hash need separate comparison. Later corrected Source checks are distinct events and do not overwrite this original.
