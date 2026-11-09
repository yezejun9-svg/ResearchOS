# W13-03 NVDA read-screen observation — immutable run summary

Status: **BLOCKED for physical screen-reader navigation**. No NVDA pass or formal acceptance is claimed. Scope was a temporary ResearchOS Electron `settings` window and an isolated, portable NVDA 2026.2 Speech Viewer. The Viewer was confirmed as NVDA's own visible native RichEdit control in the same process. The OS foreground remained another process (PID 55104), while ResearchOS Electron had a different HWND/PID. `SetForegroundWindow` was denied; Electron `win.focus()` reported focused but did not change the OS foreground; a target-only `SwitchToThisWindow` also did not change it. No physical keyboard navigation was sent to a non-ResearchOS foreground window.

One bounded diagnostic used Playwright `keyboard.press('Tab')` on the ResearchOS page. It produced 34 DOM focus transitions, including navigation links and labelled settings fields, but NVDA Speech Viewer produced only `未知` on the first step and no corresponding announcements thereafter. This is DOM focus evidence, **not speech output for those controls**. The existing Playwright ARIA snapshot is also not a screen-reader test.

## Original receipt scope and attempt count

Exactly eight `screen_reader_run.py` attempts were made: seven `BLOCKED`, one `PARTIAL`; zero `PASS`. Each row names its original `observation.json` under `execution/v2.4/receipts/W13/W13-03/`.

| Original receipt directory | Status | Observed stop |
|---|---|---|
| `screen-reader-20261005T172612Z-3f5ce7b1/` | BLOCKED | Helper initially looked for NVDA in the worktree-local `.local`; source download was in the repository `.local`. |
| `screen-reader-20261005T172630Z-9a1f6c56/` | BLOCKED | Electron startup route was aborted before ready; the helper was updated to wait for the initial window. |
| `screen-reader-20261005T172756Z-4f66c89b/` | BLOCKED | External `SetForegroundWindow` failed before keyboard input. |
| `screen-reader-20261005T172849Z-6eebc2a8/` | BLOCKED | Attached-thread `SetForegroundWindow` returned access denied before keyboard input. |
| `screen-reader-20261005T172925Z-f5f232eb/` | BLOCKED | Electron's own focus request did not establish OS foreground. |
| `screen-reader-20261005T173006Z-682445ac/` | BLOCKED | Repeated focus observation confirmed different foreground HWND/PID. |
| `screen-reader-20261005T173057Z-7abc3b3a/` | PARTIAL | Scoped CDP Tab focused 34 Electron DOM controls; NVDA did not announce their names. |
| `screen-reader-20261005T173219Z-db28bc4b/` | BLOCKED | Target-only `SwitchToThisWindow` still left the OS foreground outside ResearchOS. |

The preparation stage had one separate failed extraction invocation because this tool shell omitted `PROCESSOR_ARCHITECTURE`; process-local `AMD64` was then supplied and the official portable-copy command succeeded. This preparation failure is not included in the eight UI attempts.

## Exact entry commands and bounded subprocesses

From `D:\作品集\ResearchOS\research-os\.local\worktrees\codex-w1303`, the following exact top-level command was issued eight times:

```powershell
C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe -X utf8 tests/ui/w1303/screen_reader_run.py
```

The signed download was obtained from `https://download.nvaccess.org/releases/2026.2/nvda_2026.2.exe` with PowerShell `Invoke-WebRequest -OutFile D:/作品集/ResearchOS/research-os/.local/nvda-w1303/nvda_2026.2.exe`; the successful portable-copy invocation set `PROCESSOR_ARCHITECTURE=AMD64` for that PowerShell process, then executed:

```powershell
& 'D:/作品集/ResearchOS/research-os/.local/nvda-w1303/nvda_2026.2.exe' --create-portable-silent '--portable-path=D:/作品集/ResearchOS/research-os/.local/nvda-w1303/portable'
```

The helper builds `./tests/ui/w1303/workspace_fixture` with the locked Go binary, launches only that temporary fixture and its Electron window, then launches the portable `nvda.exe --no-sr-flag --disable-addons --no-logging`. Generated fixture paths and ports vary by run; the helper source fixes their construction. The downloaded installer SHA256 is `F3F8D29974A88D687B3C4809BE192219EC579C5BDABCDA5AAF53635288BCA824`; Windows Authenticode status was `Valid`, signer subject `CN=NV Access Limited, O=NV Access Limited, L=Camp Mountain, S=Queensland, C=AU`. Official release listing: <https://download.nvaccess.org/releases/2026.2/>. Official portable-copy and Speech Viewer guidance: <https://download.nvaccess.org/releases/stable/documentation/en/userGuide.html>.

## Final helper source SHA256

These hashes identify the final helper files at summary creation. Earlier attempts used intermediate revisions; no per-attempt source hashes were recorded, so these hashes must not be represented as per-run attestations.

| File | SHA256 |
|---|---|
| `tests/ui/w1303/nvda_viewer.py` | `0D630F081ABF9EC528E70657AAF1BEB2BA34DD38136A8314DC6A5E13C85E8F50` |
| `tests/ui/w1303/screen_reader.cjs` | `74F9983A9F4390D5A734B1E777977C09D00A00A6E8E72A2138D0C67B62B0B0D5` |
| `tests/ui/w1303/screen_reader_run.py` | `0068CFC6E673C86677DD6FDDE7B1FD111B712F20A26A1CF0783CCDADD492D6CF` |

Final Python `py_compile` and Node `--check` passed. All NVDA, Electron, and fixture processes started by this probe exited. The helper kept its own `.local` configuration; no global installation, sign-in startup change, or system screen-reader flag change was made. This summary contains no content from the other foreground window or NVDA configuration.

Two probe-generated temporary directories remain under this worktree's `.local`: `researchos-w1303-nvda-2g3dgotv` and `researchos-w1303-nvda-t6wa1h50`. Earlier Python cleanup could not remove read-only fixture Git objects. A later scoped PowerShell recursive cleanup was rejected by automatic approval review as `blocked by policy`; it was not retried or bypassed.
