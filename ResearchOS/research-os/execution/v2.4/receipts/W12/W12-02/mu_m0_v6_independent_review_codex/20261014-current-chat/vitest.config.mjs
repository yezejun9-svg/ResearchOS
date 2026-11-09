export default {
  cacheDir: "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m0-v6-independent-review-20261014/vite-cache",
  test: {
    globals: true,
    environment: "node",
    testTimeout: 30000,
    reporters: ["dot"],
    silent: "passed-only",
    include: ["test/agent.test.ts"],
  },
  resolve: {
    alias: [
      { find: /^@earendil-works\/pi-agent-core$/, replacement: "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012/packages/agent/src/index.ts" },
      { find: /^@earendil-works\/pi-ai\/compat$/, replacement: "D:/作品集/ResearchOS/research-os/qualification/v2.4/mu/packages/ai/dist/compat.js" },
      { find: /^@earendil-works\/pi-ai$/, replacement: "D:/作品集/ResearchOS/research-os/qualification/v2.4/mu/packages/ai/dist/index.js" },
      { find: /^@earendil-works\/pi-telemetry$/, replacement: "D:/作品集/ResearchOS/research-os/qualification/v2.4/mu/packages/telemetry/dist/index.js" },
    ],
  },
};


