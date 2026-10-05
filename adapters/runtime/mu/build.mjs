import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { lstat, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const worktree = resolve(here, "../../..");
const commonRaw = execFileSync("git", ["rev-parse", "--git-common-dir"], { cwd: worktree, encoding: "utf8" }).trim();
const commonDir = isAbsolute(commonRaw) ? commonRaw : resolve(worktree, commonRaw);
const mainRepo = dirname(commonDir);
const mu = join(mainRepo, "third_party", "mu");
const dependencies = join(mu, "node_modules");
const FIXED_MU_COMMIT = "8dfebe36508ac0c2508735bb866756dab9283e74";
const componentLock = JSON.parse(await readFile(join(mainRepo, "execution", "v2.4", "component_lock.json"), "utf8"));
const vendorOrigin = await readFile(join(mainRepo, "third_party", "VENDORED_FROM.md"), "utf8");
const manifest = JSON.parse(await readFile(join(mainRepo, "third_party", "mu.MANIFEST.json"), "utf8"));
if (componentLock.mu?.commit !== FIXED_MU_COMMIT || componentLock.mu?.file_count !== 5083 ||
    !vendorOrigin.split(/\r?\n/).includes(`Commit: ${FIXED_MU_COMMIT}`) ||
    manifest.files !== 5083 || !manifest.entries || Object.keys(manifest.entries).length !== 5083) {
  throw new Error("vendored Mu provenance differs from fixed W02 source commit");
}
const vendoredEntries = Object.entries(manifest.entries);
let nextEntry = 0;
await Promise.all(Array.from({ length: 16 }, async () => {
  while (nextEntry < vendoredEntries.length) {
    const [relative, expected] = vendoredEntries[nextEntry++];
    if (!relative.startsWith("third_party/mu/") || relative.includes("..")) throw new Error("invalid Mu source manifest path");
    const path = join(mainRepo, relative);
    const info = await lstat(path);
    if (!info.isFile() || info.size !== expected.size) throw new Error(`Mu source size/type drift: ${relative}`);
    const raw = await readFile(path);
    if (createHash("sha256").update(raw).digest("hex") !== expected.sha256) {
      throw new Error(`Mu source hash drift: ${relative}`);
    }
  }
}));
const require = createRequire(import.meta.url);
const esbuild = require(join(dependencies, "esbuild"));
const packageVersion = JSON.parse(await readFile(join(mu, "packages", "coding-agent", "package.json"), "utf8")).version;
const aiVersion = JSON.parse(await readFile(join(mu, "packages", "ai", "package.json"), "utf8")).version;
if (packageVersion !== "0.87.1" || aiVersion !== "0.87.1" || esbuild.version !== "0.28.2") {
  throw new Error("Mu SDK or esbuild version differs from pinned local references");
}
for (const path of [
  join(mu, "packages", "coding-agent", "dist", "index.js"),
  join(mu, "packages", "ai", "dist", "api", "openai-completions.js"),
]) await readFile(path);

const output = process.argv[2] ? resolve(process.argv[2]) : join(worktree, ".local", "w1401-mu-worker", "mu-worker.mjs");
if (!output.startsWith(join(worktree, ".local") + "\\") && !output.startsWith(join(worktree, ".local") + "/")) {
  throw new Error("bundle output must be under this worktree's ignored .local tree");
}
await mkdir(dirname(output), { recursive: true });
await esbuild.build({
  entryPoints: [join(here, "worker.mjs")],
  bundle: true,
  platform: "node",
  format: "esm",
  target: "node24",
  nodePaths: [dependencies],
  banner: { js: "import { createRequire as createRequireForMuWorker } from 'node:module'; const require = createRequireForMuWorker(import.meta.url);" },
  outfile: output,
  logLevel: "warning",
});
const bundle = await readFile(output);
const source = await readFile(join(here, "worker.mjs"));
const metadata = {
  bundle: output,
  bundle_sha256: createHash("sha256").update(bundle).digest("hex"),
  bundle_bytes: bundle.length,
  source_sha256: createHash("sha256").update(source).digest("hex"),
  sdk_version: packageVersion,
  ai_version: aiVersion,
  esbuild_version: esbuild.version,
  mu_commit: FIXED_MU_COMMIT,
  vendored_files_verified: vendoredEntries.length,
};
await writeFile(`${output}.build.json`, `${JSON.stringify(metadata, null, 2)}\n`);
process.stdout.write(`${JSON.stringify(metadata)}\n`);
