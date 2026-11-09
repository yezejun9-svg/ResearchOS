import { createRequire } from "node:module";
import { existsSync } from "node:fs";
import path from "node:path";
const require = createRequire(import.meta.url);
const esbuild = require("D:/作品集/ResearchOS/research-os/qualification/v2.4/mu/node_modules/esbuild/lib/main.js");
const root = "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012";
const modules = "D:/作品集/ResearchOS/research-os/qualification/v2.4/mu/node_modules";
const candidatePlugin = {
  name: "candidate-sdk",
  setup(build) {
    build.onResolve({ filter: /^@earendil-works\/(pi-agent-core|pi-ai)(?:\/.*)?$/ }, args => {
      const [scope, name, ...rest] = args.path.split("/");
      const pkg = name === "pi-agent-core" ? "agent" : "ai";
      const base = name === "pi-agent-core" ? path.join(root, "packages", pkg, "src") : "D:/作品集/ResearchOS/research-os/qualification/v2.4/mu/packages/ai/dist";
      const suffix = rest.join("/");
      const extension = name === "pi-agent-core" ? ".ts" : ".js";
      const file = path.join(base, suffix ? suffix + extension : "index" + extension);
      if (existsSync(file)) return { path: file };
      const index = path.join(base, suffix, "index" + extension);
      if (existsSync(index)) return { path: index };
      throw new Error("Candidate source path unavailable: " + args.path);
    });
  },
};

const targets = [
 ['author-agent',root+'/packages/agent/test/pause-checkpoint.test.ts'],
 ['author-session',root+'/packages/coding-agent/test/pause-checkpoint.test.ts'],
 ['independent-agent',new URL('./independent-agent.test.ts',import.meta.url).pathname.slice(1)],
 ['independent-session',new URL('./independent-session.test.ts',import.meta.url).pathname.slice(1)],
];
const out = "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012/.local/bundles";
require('node:fs').mkdirSync(out, { recursive: true });
for (const [name,entry] of targets) {
 const result=await esbuild.build({entryPoints:[decodeURIComponent(entry)],outfile:path.join(out,name+'.mjs'),bundle:true,platform:'node',format:'esm',target:'node24',nodePaths:[modules],plugins:[candidatePlugin],metafile:true,logLevel:'warning',banner:{js:'import { createRequire as createRequireForBundle } from "node:module"; const require = createRequireForBundle(import.meta.url);'}});
 require('node:fs').writeFileSync(path.join(out,name+'.metafile.json'),JSON.stringify(result.metafile,null,2));
 process.stdout.write(name+' candidate bundle compiled\n');
}

