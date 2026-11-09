import test from "node:test";
import assert from "node:assert/strict";
import { readFile, mkdir } from "node:fs/promises";
import { resolve, join } from "node:path";
import { createHash } from "node:crypto";
import { buildCandidate, CANDIDATE } from "./build-candidate.mjs";
const source = process.env.RESEARCHOS_ACCEPTED_MU_SOURCE;
assert.ok(source, "explicit accepted candidate source required");
const sha = (b) => createHash("sha256").update(b).digest("hex");
test(
  "candidate builder compiles real agent and session source with accepted full base and records every input",
  { timeout: 60000 },
  async () => {
    const output = resolve(".local/m1-01/build-test/mu-worker.mjs"),
      meta = await buildCandidate({ source, output });
    assert.equal(meta.source_mode, "ACCEPTED_M0_CANDIDATE");
    assert.equal(meta.candidate_base, CANDIDATE.base);
    assert.equal(meta.candidate_manifest_sha256, CANDIDATE.manifest);
    assert.ok(!("mu_commit" in meta));
    const inputs = JSON.parse(await readFile(output + ".inputs.json")),
      audit = JSON.parse(await readFile(output + ".audit.json"));
    assert.equal(inputs.length, meta.compiled_inputs);
    assert.equal(sha(JSON.stringify(inputs)), meta.compiled_inputs_sha256);
    assert.deepEqual(audit.before, audit.after);
    for (const name of [
      "packages/agent/src/agent.ts",
      "packages/coding-agent/src/core/agent-session.ts",
    ])
      assert.ok(
        inputs.some((x) => resolve(x.realpath) === resolve(source, name)),
      );
    assert.ok(
      inputs.every(
        (x) =>
          !/[\\/]packages[\\/](agent|coding-agent)[\\/]dist[\\/]/.test(
            x.realpath,
          ),
      ),
    );
    for (const input of inputs)
      assert.equal(
        sha(await readFile(input.realpath)),
        input.sha256,
        "actual input remains exact: " + input.path,
      );
    assert.equal(sha(await readFile(output)), meta.bundle_sha256);
  },
);
test("candidate builder rejects output outside separate local assets root", async () => {
  await assert.rejects(
    buildCandidate({
      source,
      output: resolve("adapters/runtime/mu/forbidden.mjs"),
    }),
    /worktree .local/,
  );
});
test("installed legacy source cannot masquerade as accepted candidate", async () => {
  await assert.rejects(
    buildCandidate({
      source: resolve("third_party/mu"),
      output: resolve(".local/m1-01/rejected/mu-worker.mjs"),
    }),
    /ENOENT|provenance|candidate/,
  );
});
