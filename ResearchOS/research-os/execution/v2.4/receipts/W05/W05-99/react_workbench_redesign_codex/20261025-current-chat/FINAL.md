# Source13 React research workbench — delivery

Status: scoped source delivered for Root integration and independent review. Formal increment: **0**.

## Frozen source

- Source scope SHA256: `0483871074cfc46f0484257467324e822c71f3b7b9a5dcf726aa20ac4df85f7b`.
- Base: `4f4023c956f84d65743f39ce77d6c8899a21ada1`.
- Branch: `react-workbench-redesign-20261025`; commit: `7a06acebddcf6ba9b9e9c29f0dc980db1e330aee`; tree: `dc3bbdfbe8cb6c17b15391016e0a28b38c7af579`.
- Worktree: `D:/作品集/ResearchOS/research-os/.local/worktrees/react-workbench-redesign-20261025`; clean after commit.
- Eleven changed paths, all in the 13-path Source scope. `continuity.jsx` and `w13-react.test.js` remain byte-identical to their pinned baselines; the latter has no source-location assertion requiring migration. `SOURCE13-precommit.json` binds all six pinned baseline files; `SOURCE13-final.json` binds every committed source blob.
- Review patch: `source13.patch`, SHA256 `e40be1018831f7262112b3c9c1ab30ece1bed28cc300f4c7deec198b90a14684`.

## Product change

`apps/web/AGENTS.md` defines the Web directory ownership. Routing and labels now live in `navigation.jsx`, removing the entry/screens circular import. `AppShell`, shared UI primitives, and the three-region `WorkbenchLayout` render the real React app. Native research places sessions on the left, the current conversation in the center, and files, qualification, and coding authorization on the right. Browser workbench places current goal/tasks/planning in the main canvas and next action, state, sources, and accepted results in context. The existing service and bridge actions remain the controllers.

At 320/768/1024/1440, layout stays within the viewport in light and dark themes. Native run/qualification statuses use Chinese primary labels with raw values available in details or title. Writer ownership is a status when already held; acquiring it remains an action otherwise. Coding inputs are in an accessible disclosure while the current status, frozen summary, and explicit confirmation remain visible. The app continues to use the frozen green semantic tokens; supplementary layout CSS does not edit the token contract. The system font stack includes Segoe UI, Microsoft YaHei UI, and Microsoft YaHei.

## Executed checks and boundaries

- `npm run build`: final PASS, `commands/20261025T143549-npm-build-final-5059427c`. The active preview assets after disposable build cleanup are hashed in `CLEANUP.json`.
- `node --test tests/ui/desktop/w13-react.test.js`: 5/5 PASS, `commands/20261025T143226-w13-react-node-test-5c38d89a`. No test was weakened or deleted.
- `tests/ui/frontend-redesign.cjs` with a disposable, fully intercepted browser/native-shaped fixture: 60 checks, 12 screenshots, PASS, `browser-fixture-05/report.json`. Includes four widths, both themes, computed font, overflow, console/network fallthrough, message/pending, drawer focus/Escape, qualification confirmation dismissed without a call, and project profile error visibility. These are fixture observations only. First fixture failure and its repair remain in `browser-fixture/report.json` and `LEDGER.jsonl`.
- Real isolated loopback Core/SQLite/Owner browser flow against the final React build: PASS, `real-isolated-03/report.json`. A new project was created through the UI, research-cycle page opened, history back returned to the workbench, and no page error occurred. The Core process was task-owned and stopped. There were no provider/model/worker calls or original Desktop/Host actions. First locator failure remains in `real-isolated-01/report.json`.
- Root separately reported a 24-check mobile/navigation/focus/route/progress review and seven visual/semantic checks in `resume_cp528_codex/20261025-current-chat/root-react-browser-03/report.json`; Source13 does not call this an independent code acceptance.
- `git diff --cached --check` PASS, `commands/20261025T143620-staged-diff-check-02-2b493e0c`; source baseline, allowlist, patch, commit tree, and clean status were rechecked by `SOURCE13-precommit.json` and `SOURCE13-final.json`.

Native Desktop packaged behavior and full W13 CI were not run in this branch. Independent source/real-flow review is pending; no parent task or formal case was accepted here.

## Preview and CI references

The task-owned preview process was started with PID `89220` and serves `http://127.0.0.1:5197/`. To restart after it is stopped, from this worktree's `apps/web` directory run:

```powershell
& 'C:/nvm4w/nodejs/node.exe' 'node_modules/vite/bin/vite.js' preview --host 127.0.0.1 --port 5197 --strictPort
```

The ordinary URL does not inject Native bridge fixtures. To reproduce the visible Native screenshot, run `tests/ui/frontend-redesign.cjs` against that URL with `RESEARCHOS_PLAYWRIGHT_MODULE` pointing to an existing Playwright installation and an output directory under owned receipts. No fixture token or bridge stub is imported by production code.

`ops/ci/build.py:38`, `ops/ci/ui.py:55`, and `ops/release/build.py:299-312` still build the real `apps/web` production bundle. A separate integration issue remains: `ops/ci/ui.py:38-41` hashes only `apps/web/src/*` files and skips nested `src/components/*.jsx`; it also omits the new `tests/ui/*.cjs` fixtures. Source13 does not authorize editing that CI file. Root should include those files in the W13 source manifest before treating registered CI evidence as bound to this UI revision.
