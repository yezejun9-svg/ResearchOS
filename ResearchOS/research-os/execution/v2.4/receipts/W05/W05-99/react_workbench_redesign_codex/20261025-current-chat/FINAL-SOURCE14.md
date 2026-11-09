# ResearchOS React workbench — final Source14 candidate

**Delivered for independent review; no formal case accepted.** The final branch is `react-workbench-redesign-20261025` at `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e` (tree `de59625ee5c1d360c741c95ec3f84b6f2764bb0e`). Its parent is the preserved Source13 UI commit `7a06acebddcf6ba9b9e9c29f0dc980db1e330aee`, based on Main `4f4023c956f84d65743f39ce77d6c8899a21ada1`. The worktree is clean. `SOURCE14-SEAL.json` binds the 12 actually changed paths within the 14-path authorized scope (SHA256 `32d51c0ba52c5c02094ae06ca735d188dea2fc0c9f6501f61f4d51bb526a3b24`), final tree, source hashes, and evidence. `source14-full.patch` SHA256 is `4f70ad36e61a73725ec844ad53f621275fbda294b0c7e20127bddacfb463da48`.

The production React app now shares an AppShell, navigation module, UI primitives, and a focused three-region Native research layout. Browser workbench prioritizes current goal, tasks, and next valid action; context and results occupy the right side. Writer ownership, pending commands, qualification and coding authorization remain explicit. The model configuration and coding forms retain their actions and state while lengthy optional fields use disclosure. Routing, original service actions, native/browser split, state guards, and frozen semantic token values remain in place. Details and original evidence boundaries are in `FINAL.md` and `SOURCE13-final.json`.

The Source14 amendment changed only `ops/ci/ui.py`: its source manifest now recursively includes `apps/web/src/**/*` and UI `tests/ui/**/*.js`/`**/*.cjs`, while retaining all original patterns and selectors. `SOURCE14-CI-PROBE.json` parsed the actual file AST, evaluated the glob list, and verified SHA256 binding for all three new component files, both new CJS test files, and the existing W13 React test. It found 571 source manifest entries. `CI-REFS.json` names the build and release entry points. The registered W13 suite itself was not run for this enumeration-only repair.

Execution evidence remains separated:

- Build: `npm run build` PASS (`commands/20261025T143549-npm-build-final-5059427c`); 5/5 W13 React node tests PASS (`commands/20261025T143226-w13-react-node-test-5c38d89a`).
- Browser/native-shaped fixture: 60 checks and 12 screenshots PASS (`browser-fixture-05/report.json`). It fully intercepts business requests and proves rendering and interactions only.
- Real isolated loopback Core/SQLite/Owner: new project through the browser UI, research-cycle navigation, history back, and no page errors PASS (`real-isolated-03/report.json`). The final normally connected screenshot is `real-isolated-03/real-project-workbench.png`. The owned Core was stopped, and the task-owned data and credentials were removed after evidence capture.
- Root reported 31 additional browser checks in its own CP534 receipt. This is Root observation, not this branch's independent code acceptance.
- The Native Desktop packaged app was not launched; independent source/real-flow review is pending; formal increment is 0.

Failed attempts and their repairs remain append-only in `LEDGER.jsonl` and raw command receipts. Disposable obsolete build assets and test credentials were removed (`CLEANUP.json`). The live task-owned Vite preview still returned HTTP 200 on `http://127.0.0.1:5197/` with PID 89220 at final check. Restart command from `D:/作品集/ResearchOS/research-os/.local/worktrees/react-workbench-redesign-20261025/apps/web`:

```powershell
& 'C:/nvm4w/nodejs/node.exe' 'node_modules/vite/bin/vite.js' preview --host 127.0.0.1 --port 5197 --strictPort
```

Direct browsing shows the actual app with its normal authentication gate. Native-shaped screenshots require the disposable Playwright bridge fixture from `tests/ui/frontend-redesign.cjs`; its bridge is not in the production bundle. The normally connected, real service screenshot above is the representative browser workbench view.
