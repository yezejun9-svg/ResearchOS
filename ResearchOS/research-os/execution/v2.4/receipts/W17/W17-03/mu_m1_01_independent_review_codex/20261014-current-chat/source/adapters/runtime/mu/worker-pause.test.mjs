import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, mkdir, writeFile, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createInterface } from "node:readline";
import { createHash } from "node:crypto";
import { gzipSync } from "node:zlib";
const bundle = process.env.RESEARCHOS_PAUSE_WORKER_BUNDLE;
assert.ok(bundle, "actual rebuilt candidate worker required");
const sha = (b) => createHash("sha256").update(b).digest("hex"),
  digest = (b) => "sha256:" + sha(b),
  version = "RESEARCHOS_PAUSE_V1";
const config = {
  ref: "fixture",
  api: "openai-completions",
  provider: "openai",
  model: "fixture",
  endpoint: "https://fixture.invalid",
  route: "broker",
  max_output_tokens: 128,
  max_calls: 8,
  tools: [],
};
const sse =
  "data: " +
  JSON.stringify({
    id: "fixture",
    object: "chat.completion.chunk",
    choices: [
      {
        index: 0,
        delta: { role: "assistant", content: "reply" },
        finish_reason: null,
      },
    ],
  }) +
  "\n\ndata: " +
  JSON.stringify({
    id: "fixture",
    object: "chat.completion.chunk",
    choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
  }) +
  "\n\ndata: [DONE]\n\n";
async function run(
  t,
  {
    snapshot,
    ack = "valid",
    epoch = 1,
    mutateActivation,
    withTool = false,
  } = {},
) {
  const root = await mkdtemp(join(tmpdir(), "researchos-production-pause-"));
  await mkdir(join(root, "input"));
  await mkdir(join(root, "output"));
  const binding = {
    project_id: "p",
    session_id: "s",
    task_id: "t",
    run_id: "r",
    runtime_epoch: epoch,
    queue_generation: "g",
    dispatch_key: "d" + epoch,
    manifest_hash: digest("manifest" + epoch),
  };
  const request = {
    task_id: "t",
    run_id: "r",
    epoch,
    input_refs: [],
    context: {},
    task_title: "pause evidence",
    task_description: "original prompt once",
    queue_control: true,
    queue_binding: { ...binding },
    pause_protocol: version,
  };
  if (snapshot) {
    request.pause_activation = {
      version,
      previous_epoch: 1,
      new_epoch: epoch,
      checkpoint_hash: digest(snapshot),
      checkpoint_artifact_id: "a",
      checkpoint_use_receipt_hash: digest("u"),
      checkpoint_use_principal: "executor",
      carry_use_receipt_hash: digest("carry"),
      original_input_hash: JSON.parse(snapshot).input_hash,
    };
    mutateActivation?.(request.pause_activation);
    await writeFile(join(root, "input", "pause-checkpoint.json"), snapshot);
  }
  await writeFile(join(root, "input", "request.json"), JSON.stringify(request));
  await writeFile(
    join(root, "input", "worker.json"),
    JSON.stringify({
      ...config,
      tools: withTool
        ? [
            {
              type: "function",
              function: {
                name: "read",
                description: "Read a declared file",
                parameters: {
                  type: "object",
                  properties: { path: { type: "string" } },
                  required: ["path"],
                },
              },
            },
          ]
        : [],
    }),
  );
  const child = spawn(
    process.execPath,
    [bundle, join(root, "input", "request.json")],
    { cwd: root, stdio: ["pipe", "pipe", "pipe"] },
  );
  const exited = new Promise((resolve) => child.once("exit", resolve));
  let stderr = "";
  child.stderr.on("data", (x) => (stderr += x));
  t.after(async () => {
    if (child.exitCode === null) child.kill();
    await exited;
    await rm(root, {
      recursive: true,
      force: true,
      maxRetries: 5,
      retryDelay: 50,
    });
  });
  binding.process_identity = {
    pid: child.pid,
    process_created_ns: "1",
    job: "j" + epoch,
    appcontainer_sid: "sid",
    profile: "profile",
    staging_directory: root,
  };
  const send = (x) => child.stdin.write(JSON.stringify(x) + "\n"),
    control = (x) => send({ ...x, binding });
  const frames = [],
    effects = [];
  let checkpoint,
    prepared = false,
    committed = false;
  const finished = new Promise((resolve, reject) => {
    const reader = createInterface({ input: child.stdout });
    reader.on("line", (line) => {
      try {
        const f = JSON.parse(line);
        frames.push(f);
        assert.equal(f.sequence, frames.length);
        if (f.type === "context.ready")
          control({
            type: "command.deliver",
            initialize: true,
            command: null,
            pause_protocol: version,
          });
        if (f.type === "command.accepted" && f.payload.initialized)
          send({
            sequence: f.sequence,
            key: "command.initialize",
            state: "CONFIRMED",
            payload: {},
          });
        if (f.type === "effect.request") {
          effects.push(f);
          if (
            !snapshot &&
            (withTool ? f.capability === "TOOL" : effects.length === 1)
          ) {
            for (const [i, delivery] of ["STEER", "FOLLOW_UP"].entries()) {
              const content = JSON.stringify({
                text: "queued-" + i,
                attachments: [],
              });
              control({
                type: "command.deliver",
                command: {
                  command_id: "c" + i,
                  message_id: "m" + i,
                  queue_sequence: i + 1,
                  content,
                  content_hash: digest(content),
                  delivery,
                },
              });
            }
            control({ type: "command.pause", version, pause_id: "pause-1" });
          }
          const toolSSE =
            "data: " +
            JSON.stringify({
              id: "fixture",
              object: "chat.completion.chunk",
              choices: [
                {
                  index: 0,
                  delta: {
                    role: "assistant",
                    tool_calls: [
                      {
                        index: 0,
                        id: "call-1",
                        type: "function",
                        function: {
                          name: "read",
                          arguments: JSON.stringify({ path: "file.txt" }),
                        },
                      },
                    ],
                  },
                  finish_reason: null,
                },
              ],
            }) +
            "\n\ndata: " +
            JSON.stringify({
              id: "fixture",
              object: "chat.completion.chunk",
              choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }],
            }) +
            "\n\ndata: [DONE]\n\n";
          const body =
            withTool && !snapshot && f.capability === "MODEL" ? toolSSE : sse;
          if (f.capability === "TOOL") {
            setTimeout(
              () =>
                send({
                  sequence: f.sequence,
                  key: f.key,
                  state: "CONFIRMED",
                  payload: {
                    content: [{ type: "text", text: "tool-result-preserved" }],
                    details: {
                      path: "file.txt",
                      content_hash: digest("tool-result-preserved"),
                      next_offset: 21,
                      truncated: false,
                      size_bytes: 21,
                    },
                  },
                }),
              50,
            );
            return;
          }
          setTimeout(
            () =>
              send({
                sequence: f.sequence,
                key: f.key,
                state: "CONFIRMED",
                payload: {
                  status: 200,
                  content_type: "text/event-stream",
                  body_encoding: "gzip+base64",
                  body_gzip_base64: gzipSync(body).toString("base64"),
                  body_sha256: digest(body),
                },
              }),
            50,
          );
        }
        if (f.type === "checkpoint") {
          checkpoint = f;
          const payload = {
            type: "checkpoint.sealed",
            version,
            pause_id: f.payload.pause_id,
            binding,
            checkpoint_sequence: f.sequence,
            content_hash: f.payload.content_hash,
            checkpoint_artifact_id: "a",
            checkpoint_use_receipt_hash: digest("u"),
            checkpoint_use_principal: "executor",
            journal_checkpoint_hash: digest("journal"),
          };
          if (ack === "boolean") {
            delete payload.type;
            payload.persisted = true;
          }
          if (ack === "wrong-hash") payload.content_hash = digest("wrong");
          if (ack === "old-epoch")
            payload.binding = { ...binding, runtime_epoch: 0 };
          send({
            sequence: f.sequence,
            key: "checkpoint.sealed",
            state: "CONFIRMED",
            payload,
          });
        }
        if (snapshot && f.type === "command.idle") {
          if (!prepared) {
            prepared = true;
            control({ type: "command.prepare_seal", through: 2 });
          } else if (!committed) {
            committed = true;
            control({ type: "command.commit_seal", through: 2 });
          }
        }
      } catch (e) {
        reject(e);
        child.kill();
      }
    });
    child.once("error", reject);
    child.once("exit", (code) => resolve({ code, stderr }));
  });
  const terminal = await finished;
  let raw;
  if (checkpoint)
    raw = await readFile(join(root, "output", "pause-checkpoint.json"));
  let result;
  if (terminal.code === 0 && snapshot)
    result = JSON.parse(await readFile(join(root, "output", "result.json")));
  return { ...terminal, frames, effects, checkpoint, raw, result };
}
test(
  "actual production worker pauses both SDK queues and restores same Run with cumulative effects and no prompt replay",
  { timeout: 30000 },
  async (t) => {
    const first = await run(t);
    assert.equal(first.code, 0, first.stderr);
    assert.equal(first.frames.at(-1).type, "turn.paused");
    assert.ok(first.frames.at(-1).sequence > first.checkpoint.sequence);
    const snapshot = JSON.parse(first.raw);
    assert.equal(snapshot.counts.model_calls, 1);
    assert.equal(snapshot.commands.length, 2);
    assert.equal(snapshot.queue_state.queue_cut, 2);
    assert.equal(snapshot.queue_state.sdk_pending_mapping.length, 2);
    assert.equal(
      snapshot.queue_state.command_ledger_hash,
      digest(
        JSON.stringify(snapshot.commands, (_key, value) =>
          value !== null && typeof value === "object" && !Array.isArray(value)
            ? Object.fromEntries(
                Object.keys(value)
                  .sort()
                  .map((k) => [k, value[k]]),
              )
            : value,
        ),
      ),
    );
    assert.equal(snapshot.sdk.payload.agent.steering.pending.length, 1);
    assert.equal(snapshot.sdk.payload.agent.followUp.pending.length, 1);
    const oldEpoch = snapshot.sdk.payload.binding.leaseEpoch,
      oldId = snapshot.sdk.payload.binding.sessionId;
    const resumed = await run(t, { snapshot: first.raw, epoch: 2 });
    assert.equal(resumed.code, 0, resumed.stderr);
    assert.equal(resumed.frames.at(-1).type, "turn.completed");
    assert.equal(resumed.result.model_calls, resumed.effects.length + 1);
    assert.deepEqual(
      resumed.frames
        .filter((f) => f.type === "command.consumed")
        .map((f) => f.payload.command_id),
      ["c0", "c1"],
    );
    assert.equal(
      resumed.frames.filter(
        (f) => f.type === "command.accepted" && f.payload.command_id,
      ).length,
      0,
    );
    assert.ok(resumed.effects.every((f) => f.key.startsWith("t:r:2:model:")));
    assert.equal(resumed.effects[0].key, "t:r:2:model:2");
    assert.equal(
      resumed.result.messages.filter(
        (m) =>
          m.role === "user" &&
          JSON.stringify(m.content).includes("original prompt once"),
      ).length,
      1,
    );
    assert.equal(
      JSON.parse(first.raw).sdk.payload.binding.leaseEpoch,
      oldEpoch,
    );
    assert.equal(JSON.parse(first.raw).sdk.payload.binding.sessionId, oldId);
    t.diagnostic(
      JSON.stringify({
        evidence: "PRODUCTION_WORKER_PROCESS_SYNTHETIC_BROKER_NO_MODEL",
        first_frames: first.frames.map((f) => [f.sequence, f.type]),
        resume_frames: resumed.frames.map((f) => [f.sequence, f.type]),
        counts: resumed.result.model_calls,
      }),
    );
  },
);
for (const ack of ["boolean", "wrong-hash", "old-epoch"])
  test(
    "production worker rejects " + ack + " checkpoint ACK",
    { timeout: 15000 },
    async (t) => {
      const r = await run(t, { ack });
      assert.notEqual(r.code, 0);
      assert.ok(!r.frames.some((f) => f.type === "turn.paused"));
      assert.match(r.stderr, /seal ACK mismatch/);
    },
  );
test(
  "restore rejects epoch relabel and changed checkpoint hash before model",
  { timeout: 30000 },
  async (t) => {
    const first = await run(t);
    assert.equal(first.code, 0, first.stderr);
    const r = await run(t, {
      snapshot: first.raw,
      epoch: 2,
      mutateActivation: (a) => (a.original_input_hash = "0".repeat(64)),
    });
    assert.notEqual(r.code, 0);
    assert.equal(r.effects.length, 0);
    assert.match(r.stderr, /original identity mismatch/);
  },
);

test(
  "completed production TOOL result and cumulative tool count survive restore without effect replay",
  { timeout: 30000 },
  async (t) => {
    const first = await run(t, { withTool: true });
    assert.equal(first.code, 0, first.stderr);
    const checkpoint = JSON.parse(first.raw);
    assert.equal(checkpoint.counts.tool_calls, 1);
    assert.equal(
      checkpoint.sdk.payload.agent.messages.filter(
        (m) => m.role === "toolResult",
      ).length,
      1,
    );
    const resumed = await run(t, {
      withTool: true,
      snapshot: first.raw,
      epoch: 2,
    });
    assert.equal(resumed.code, 0, resumed.stderr);
    assert.equal(resumed.result.tool_calls, 1);
    assert.ok(resumed.effects.every((f) => f.capability === "MODEL"));
    const result = resumed.result.messages.find((m) => m.role === "toolResult");
    assert.equal(result.content[0].text, "tool-result-preserved");
    assert.equal(result.details.path, "file.txt");
  },
);
