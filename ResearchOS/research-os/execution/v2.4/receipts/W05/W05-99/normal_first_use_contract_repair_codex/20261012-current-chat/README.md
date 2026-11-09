# W05 Desktop first-use contract repair candidate

Source candidate commit: `90b72d19c760974af46dc4243c56107e886d7cf6` (isolated worktree). The six authorized files are copied under `source/`; hashes and full-input build binding are in `source-bundle.json`.

The validator now accepts a schema-valid `host.status` response with Core `revision:1` while preserving client, session, command, and schema checks. Native folder chooser requests now include required `requested_path:null`.

The final source-bound build has 6441 inputs, digest `e99cfe80d39fef7d797c505e4a6a3cf4906877f3b7cfcce3e05888164f35191b`, binary SHA-256 `cfdcbd5dd3c46cb5b44ad6c7e57b00b21a51126191ce2f3294de566d9399680e`, and no drift. Final HTTP boundary suite passed 182/182; final bound validator first-use revision suite passed. Earlier 180/181 failure and old bound build logs remain here unchanged as historical evidence. Initial sparse checkout and test-run failures remain in their raw logs.

Evidence covers source, native handler simulation, and bound HTTP/Electron test paths. It does not prove a human-operated Windows GUI folder picker or a complete normal Desktop first-use workflow. Formal W05 acceptance increment: 0. Independent review and Main integration remain with Root.
