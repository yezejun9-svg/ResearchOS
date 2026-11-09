# Public toolchain follow-up — 2026-10-09

Root read the public primary repositories in this turn. This record grants no Source adoption, product acceptance, new paid request, or new construction session.

- DeepSeek Harness: https://github.com/deepseek-ai/deepseek-harness . Its tools documentation describes typed output declarations, execution policy, cooperative timeouts and concurrency metadata: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/tools.md . The repository declares MIT at https://github.com/deepseek-ai/deepseek-harness/blob/master/LICENSE . Existing local archived revision remains the versioned reference; mutable master documentation is discovery only.
- Anthropic Python Agent SDK: https://github.com/anthropics/claude-agent-sdk-python . The current README explains that its default transport starts the bundled Claude Code CLI, while custom tools can be in-process MCP functions and hooks control lifecycle. This is a wider execution boundary than the existing ResearchOS Mu/Pi adapter and does not establish compatibility with the requested DeepSeek endpoint. No SDK installation or second agent loop was performed.

Current decision: retain the existing owned CLI/runtime. Use narrowly scoped typed result, timeout, cancellation and immutable tool-call evidence concepts where a specific frozen ResearchOS card calls for them. Any reused source must pin its exact version and receive current-input independent review. Keep original provider trial reconciliation and the missing full W05/W09 acceptance branches OPEN.
