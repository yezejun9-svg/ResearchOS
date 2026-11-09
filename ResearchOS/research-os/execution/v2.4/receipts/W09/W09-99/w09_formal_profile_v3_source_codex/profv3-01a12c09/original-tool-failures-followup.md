# V3 original failure follow-up

This file adds Root-assigned mappings and verbatim source-command outputs. It does not modify `original-tool-failures.md`. No Native, Go, dispatcher or model command ran in these failures.

Root mapped the fourth original in `original-tool-failures.md` to 974. Root separately reported its own original 975. The four originals below are 976–979.

## 976: Source control detects W07 prefix drift

```js
const cmd="& 'C:\\Users\\yqyyds\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe' -I -S -B -X utf8 'execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v3_source_codex/profv3-01a12c09/source_controls_v3.py'\n$sourcePyExit=$LASTEXITCODE\nWrite-Output \"ROOT_SOURCE_PYTHON_EXIT=$sourcePyExit\"\nexit $sourcePyExit";const r=await tools.exec_command({cmd,workdir:"D:\\作品集\\ResearchOS\\research-os",max_output_tokens:1500});text(r);
```

```text
Traceback (most recent call last):
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py", line 15, in <module>
    assert old[:51719] == index_raw[:51719]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
ROOT_SOURCE_PYTHON_EXIT=1
```

`chunk_id=ad6c1b`, `wall_time_seconds=0.8894075`, outer exit 1, Python exit 1, Native/Go/model NULL.

## 977: quoted Python `-c` syntax failure

```js
const cmd="& 'C:\\Users\\yqyyds\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe' -I -S -B -X utf8 -c \"from pathlib import Path; p=Path(r'execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v3_source_codex/profv3-01a12c09'); a=(p/'formal_case_index.before.py').read_bytes(); b=(p/'formal_case_index.after.py').read_bytes(); c=b.replace(b'\\n',b'\\r\\n'); print('candidate_bytes',len(c),'prefix_exact',c[:51719]==a[:51719],'old_guard_count',c.count(b'if __name__ == \\\"__main__\\\":'))\"\n$sourcePyExit=$LASTEXITCODE\nWrite-Output \"ROOT_SOURCE_PYTHON_EXIT=$sourcePyExit\"\nexit $sourcePyExit";const r=await tools.exec_command({cmd,workdir:"D:\\作品集\\ResearchOS\\research-os",max_output_tokens:350});text(r);
```

```text
  File "<string>", line 1
    from pathlib import Path; p=Path(r'execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v3_source_codex/profv3-01a12c09'); a=(p/'formal_case_index.before.py').read_bytes(); b=(p/'formal_case_index.after.py').read_bytes(); c=b.replace(b'\n',b'\r\n'); print('candidate_bytes',len(c),'prefix_exact',c[:51719]==a[:51719],'old_guard_count',c.count(b'if __name__ == \
                                                                                                                                                                                                                                                                                                                                                            ^
SyntaxError: unterminated string literal (detected at line 1)
ROOT_SOURCE_PYTHON_EXIT=1
```

`chunk_id=0a239f`, `wall_time_seconds=0.8308605`, outer exit 1, Python exit 1, Native/Go/model NULL.

## 978: strict three-key authority pin sent directly to two-key Reader API

```js
const cmd="& 'C:\\Users\\yqyyds\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe' -I -S -B -X utf8 'execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v3_source_codex/profv3-01a12c09/source_controls_v3.py'\n$sourcePyExit=$LASTEXITCODE\nWrite-Output \"ROOT_SOURCE_PYTHON_EXIT=$sourcePyExit\"\nexit $sourcePyExit";const r=await tools.exec_command({cmd,workdir:"D:\\作品集\\ResearchOS\\research-os",max_output_tokens:1100});text(r);
```

```text
Traceback (most recent call last):
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py", line 29, in reject
    function()
    ~~~~~~~~^^
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py", line 274, in <lambda>
    reject("F5_INVENTED_SOURCE_STRING_REJECTED", lambda: profile["_root_original"](
                                                         ~~~~~~~~~~~~~~~~~~~~~~~~~^
        api, index["Reader"](root), issuance, "independent-reviewer",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"context": root / "unused-context.json"}), "ROOT_ORIGINAL_EVENT")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "formal_profile_w09.after.py", line 551, in _root_original
  File "formal_profile_w09.after.py", line 543, in _capture_registry
  File "formal_case_index.after.py", line 178, in ref
  File "formal_case_index.after.py", line 92, in fields
  File "formal_case_index.after.py", line 48, in require
w09_v3_synthetic_index.InvalidEvidence: UNKNOWN_FIELD: reference: ['bytes']

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py", line 274, in <module>
    reject("F5_INVENTED_SOURCE_STRING_REJECTED", lambda: profile["_root_original"](
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        api, index["Reader"](root), issuance, "independent-reviewer",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"context": root / "unused-context.json"}), "ROOT_ORIGINAL_EVENT")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py", line 31, in reject
    assert exc.code == code, (label, exc.code)
           ^^^^^^^^^^^^^^^^
AssertionError: ('F5_INVENTED_SOURCE_STRING_REJECTED', 'UNKNOWN_FIELD')
ROOT_SOURCE_PYTHON_EXIT=1
```

`chunk_id=fb400c`, `wall_time_seconds=1.0486138`, outer exit 1, Python exit 1, Native/Go/model NULL.

## 979: observed plain item has `input_text`, not `text`

```js
const cmd="& 'C:\\Users\\yqyyds\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe' -I -S -B -X utf8 'execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v3_source_codex/profv3-01a12c09/source_controls_v3.py'\n$sourcePyExit=$LASTEXITCODE\nWrite-Output \"ROOT_SOURCE_PYTHON_EXIT=$sourcePyExit\"\nexit $sourcePyExit";const r=await tools.exec_command({cmd,workdir:"D:\\作品集\\ResearchOS\\research-os",max_output_tokens:1250});text(r);
```

```text
Traceback (most recent call last):
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py", line 29, in reject
    function()
    ~~~~~~~~^^
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py", line 293, in <lambda>
    reject("F5_REAL_NONFORMAL_SAMPLE_CANNOT_AUTHORIZE_W09", lambda: profile["_root_original"](
                                                                    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        api, index["Reader"](root), issuance, binding["sender"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"context": root / "unused-context.json"}), "ROOT_ORIGINAL_EVENT")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "formal_profile_w09.after.py", line 622, in _root_original
  File "formal_case_index.after.py", line 48, in require
w09_v3_synthetic_index.InvalidEvidence: ROOT_ORIGINAL_PLAINTEXT_REQUIRED: encrypted or mixed message content

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py", line 293, in <module>
    reject("F5_REAL_NONFORMAL_SAMPLE_CANNOT_AUTHORIZE_W09", lambda: profile["_root_original"](
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        api, index["Reader"](root), issuance, binding["sender"],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        {"context": root / "unused-context.json"}), "ROOT_ORIGINAL_EVENT")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\w09_formal_profile_v3_source_codex\profv3-01a12c09\source_controls_v3.py", line 31, in reject
    assert exc.code == code, (label, exc.code)
           ^^^^^^^^^^^^^^^^
AssertionError: ('F5_REAL_NONFORMAL_SAMPLE_CANNOT_AUTHORIZE_W09', 'ROOT_ORIGINAL_PLAINTEXT_REQUIRED')
ROOT_SOURCE_PYTHON_EXIT=1
```

`chunk_id=d0305e`, `wall_time_seconds=0.9640882`, outer exit 1, Python exit 1, Native/Go/model NULL.

The Source candidate was then repaired. A later independent invocation of the 37 control assertions exited 0. Those later passes do not erase these originals.
