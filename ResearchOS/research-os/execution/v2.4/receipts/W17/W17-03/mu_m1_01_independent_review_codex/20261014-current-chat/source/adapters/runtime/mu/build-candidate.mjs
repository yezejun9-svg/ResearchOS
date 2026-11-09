import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { readFile, writeFile, mkdir, realpath, lstat } from "node:fs/promises";
import { dirname, resolve, join, isAbsolute, relative } from "node:path";
import { fileURLToPath } from "node:url";
export const CANDIDATE = Object.freeze({
  base: "7ec619a16a932ae02daa7c2e6132d266528a1da8",
  manifest: "9e5dd1e5d93f19c6a4aa5eb5c0e2ebd7f0d1e05a987f6ec03963b4b560139da9",
  patch: "f82f8b8f866ae920bb769b657faf0a1a8709844979422fa409cb5bbc5194ad67",
  review: "13c6ce9fbad76c6e6f2b2c8537bbaa2e662dc5539709c0161fa5219d06dd7489",
  protocol: "RESEARCHOS_PAUSE_V1",
});
const sha = (b) => createHash("sha256").update(b).digest("hex");
const here = dirname(fileURLToPath(import.meta.url)),
  worktree = resolve(here, "../../..");
const git = (cwd, args) =>
  execFileSync("git", args, {
    cwd,
    encoding: "utf8",
    maxBuffer: 32 << 20,
  }).trim();
export async function buildCandidate({ source, output }) {
  source = resolve(source);
  output = resolve(output);
  const local = join(worktree, ".local");
  if (
    relative(local, output).startsWith("..") ||
    isAbsolute(relative(local, output))
  )
    throw Error("candidate output must be under worktree .local");
  // Refuse symlink/junction ancestors before creating or overwriting assets.
  for (let parent = dirname(output); ; parent = dirname(parent)) {
    try {
      const info = await lstat(parent);
      if (
        info.isSymbolicLink() ||
        resolve(await realpath(parent)).toLowerCase() !== parent.toLowerCase()
      )
        throw Error("candidate output reparse rejected");
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    if (parent === dirname(parent)) break;
  }
  for (const suffix of [
    "",
    ".build.json",
    ".inputs.json",
    ".metafile.json",
    ".audit.json",
  ]) {
    try {
      if (
        !(await lstat(output + suffix)).isFile() ||
        resolve(await realpath(output + suffix)).toLowerCase() !==
          (output + suffix).toLowerCase()
      )
        throw Error("candidate output file reparse rejected");
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
  }
  const common = git(worktree, ["rev-parse", "--git-common-dir"]),
    root = dirname(isAbsolute(common) ? common : resolve(worktree, common));
  const deps = join(root, "qualification/v2.4/mu/node_modules"),
    ai = join(root, "qualification/v2.4/mu/packages/ai/dist");
  const freeze = join(source, ".local/v6-final-20261014-r3");
  async function verified(path, hash) {
    const b = await readFile(path);
    if (sha(b) !== hash) throw Error("candidate provenance drift: " + path);
    return b;
  }
  const manifest = JSON.parse(
    await verified(join(freeze, "v6-final-manifest.json"), CANDIDATE.manifest),
  );
  await verified(join(freeze, "v6-source.patch"), CANDIDATE.patch);
  await verified(
    join(
      root,
      "execution/v2.4/receipts/W12/W12-02/mu_m0_v6_independent_review_codex/20261014-current-chat/report.json",
    ),
    CANDIDATE.review,
  );
  const census = JSON.parse(
    await verified(
      join(freeze, "compiled-inputs-census.json"),
      manifest.compiled_inputs_census_sha256,
    ),
  );
  const expected = new Map(
    census.map((x) => [resolve(x.realpath).toLowerCase(), x]),
  );
  async function audit() {
    if (git(source, ["rev-parse", "HEAD"]) !== CANDIDATE.base)
      throw Error("wrong complete candidate base");
    const allowed = new Set(manifest.source9.map((x) => x.path));
    const changed = git(source, ["diff", "--name-only", "HEAD"])
      .split(/\r?\n/)
      .filter(Boolean);
    if (changed.some((p) => !allowed.has(p)))
      throw Error("candidate delta outside exact9");
    for (const f of manifest.source9)
      await verified(join(source, f.path), f.sha256);
    const untracked = git(source, [
      "ls-files",
      "--others",
      "--exclude-standard",
    ])
      .split(/\r?\n/)
      .filter((p) => p && !p.startsWith(".local/"));
    if (untracked.some((p) => !allowed.has(p)))
      throw Error("untracked candidate source outside exact9");
    const patch = execFileSync(
      "git",
      [
        "diff",
        "--binary",
        "HEAD",
        "--",
        ...manifest.source9.map((x) => x.path),
      ],
      { cwd: source, maxBuffer: 32 << 20 },
    );
    if (sha(patch) !== CANDIDATE.patch)
      throw Error("actual candidate exact9 patch drift");
    return {
      head: CANDIDATE.base,
      patch_sha256: sha(patch),
      changed,
      source9: manifest.source9,
    };
  }
  const before = await audit();
  await mkdir(dirname(output), { recursive: true });
  const require = createRequire(import.meta.url),
    esbuild = require(join(deps, "esbuild"));
  if (esbuild.version !== "0.28.2") throw Error("esbuild version drift");
  const result = await esbuild.build({
    absWorkingDir: worktree,
    entryPoints: [join(here, "worker.mjs")],
    outfile: output,
    bundle: true,
    platform: "node",
    format: "esm",
    target: "node24",
    nodePaths: [deps],
    metafile: true,
    logLevel: "warning",
    banner: {
      js: "import {createRequire as workerRequire} from 'node:module';const require=workerRequire(import.meta.url);",
    },
    plugins: [
      {
        name: "accepted-source-only",
        setup(b) {
          b.onResolve(
            {
              filter:
                /^@earendil-works\/(pi-agent-core|pi-coding-agent|pi-ai)(?:\/.*)?$/,
            },
            async (args) => {
              const [, pkg, ...suffix] = args.path.split("/");
              const base =
                pkg === "pi-ai"
                  ? ai
                  : join(
                      source,
                      "packages",
                      pkg === "pi-agent-core" ? "agent" : "coding-agent",
                      "src",
                    );
              const path = join(
                base,
                (suffix.join("/") || "index") +
                  (pkg === "pi-ai" ? ".js" : ".ts"),
              );
              if (pkg === "pi-ai") {
                const exp = expected.get(
                  resolve(await realpath(path)).toLowerCase(),
                );
                if (!exp) throw Error("AI input absent from accepted census");
                await verified(path, exp.sha256);
              }
              return { path };
            },
          );
        },
      },
    ],
  });
  const inputs = [];
  for (const name of Object.keys(result.metafile.inputs)) {
    if (name.startsWith("<")) throw Error("unrecorded virtual input");
    const path = resolve(worktree, name),
      real = await realpath(path),
      bytes = await readFile(real),
      hash = sha(bytes),
      norm = real.replaceAll("\\", "/");
    if (
      /\/packages\/(agent|coding-agent)\/dist\//.test(norm) ||
      /node_modules\/@earendil-works\/pi-(agent-core|coding-agent)\//.test(norm)
    )
      throw Error("installed agent/session fallback");
    if (norm.includes("/packages/ai/dist/")) {
      const exp = expected.get(resolve(real).toLowerCase());
      if (!exp || exp.sha256 !== hash)
        throw Error("unverified AI distribution input");
    }
    const prior = expected.get(resolve(real).toLowerCase());
    if (prior && prior.sha256 !== hash)
      throw Error("accepted dependency changed");
    inputs.push({ path, realpath: real, sha256: hash, bytes: bytes.length });
  }
  for (const p of [
    "packages/agent/src/agent.ts",
    "packages/coding-agent/src/core/agent-session.ts",
  ])
    if (
      !inputs.some(
        (i) =>
          resolve(i.realpath).toLowerCase() ===
          resolve(source, p).toLowerCase(),
      )
    )
      throw Error("candidate production source missing");
  const after = await audit(),
    bundle = await readFile(output),
    worker = await readFile(join(here, "worker.mjs"));
  const metadata = {
    source_mode: "ACCEPTED_M0_CANDIDATE",
    candidate_manifest_sha256: CANDIDATE.manifest,
    candidate_base: CANDIDATE.base,
    candidate_patch_sha256: CANDIDATE.patch,
    independent_review_sha256: CANDIDATE.review,
    protocol_capability: CANDIDATE.protocol,
    source_sha256: sha(worker),
    bundle_sha256: sha(bundle),
    bundle_bytes: bundle.length,
    esbuild_version: esbuild.version,
    node_version: process.version,
    sdk_version: JSON.parse(
      await readFile(join(source, "packages/coding-agent/package.json")),
    ).version,
    ai_version: JSON.parse(
      await readFile(
        join(root, "qualification/v2.4/mu/packages/ai/package.json"),
      ),
    ).version,
    compiled_inputs: inputs.length,
    compiled_inputs_sha256: sha(JSON.stringify(inputs)),
    metafile_sha256: sha(JSON.stringify(result.metafile)),
  };
  await writeFile(output + ".inputs.json", JSON.stringify(inputs, null, 2));
  await writeFile(
    output + ".metafile.json",
    JSON.stringify(result.metafile, null, 2),
  );
  await writeFile(
    output + ".audit.json",
    JSON.stringify({ before, after }, null, 2),
  );
  await writeFile(output + ".build.json", JSON.stringify(metadata, null, 2));
  return metadata;
}
if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  if (process.argv.length !== 4)
    throw Error("usage: build-candidate.mjs accepted-source output");
  console.log(
    JSON.stringify(
      await buildCandidate({
        source: process.argv[2],
        output: process.argv[3],
      }),
    ),
  );
}
