import { createHash } from "node:crypto";
import { readFile, writeFile, open, lstat } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { createInterface } from "node:readline";
import { Transform } from "node:stream";
import { gunzipSync } from "node:zlib";
import { fileURLToPath } from "node:url";
import { createAgentSession, DefaultResourceLoader, SessionManager, SettingsManager } from "@earendil-works/pi-coding-agent";
import { streamSimple as streamSimpleOpenAICompletions } from "@earendil-works/pi-ai/api/openai-completions";

const MAX_FRAME_BYTES = 64 * 1024;
const MAX_MODEL_SSE_BYTES = 2 * 1024 * 1024;
const MAX_RESULT_BYTES = 64 * 1024 * 1024;
const MAX_CALLS = 32;
const MAX_TOOLS = 16;
const MODEL_BODY_KEYS = new Set([
  "model", "messages", "stream", "stream_options", "max_tokens", "max_completion_tokens",
  "temperature", "top_p", "presence_penalty", "frequency_penalty", "reasoning_effort",
  "stop", "tools", "tool_choice", "parallel_tool_calls", "seed",
]);

const sha256 = (raw) => createHash("sha256").update(raw).digest("hex");
const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const requireString = (value, name) => {
  if (typeof value !== "string" || value.length === 0) throw new Error(`${name} must be a nonempty string`);
  return value;
};
const requireInteger = (value, name, max) => {
  if (!Number.isSafeInteger(value) || value < 1 || value > max) throw new Error(`${name} out of bounds`);
  return value;
};

export const STREAM_LIMITS = Object.freeze({ raw: MAX_MODEL_SSE_BYTES, fragment: 8192, window: 4, sdkEvents: 4096, observations: 262144, parts: 64 });
export const canonicalJSON = (value) => JSON.stringify(value, (_key, part) => object(part)
  ? Object.fromEntries(Object.keys(part).sort().map(key => [key, part[key]])) : part);
const digest = (raw) => `sha256:${sha256(raw)}`;
const EMPTY_DIGEST = digest(Buffer.alloc(0));
const exactKeys = (value, keys) => {
  if (!object(value) || Object.keys(value).sort().join("|") !== [...keys].sort().join("|")) throw new Error("MODEL_SSE_V1 exact keys mismatch");
};
// JSON.parse alone discards duplicate keys and accepts lone UTF-16 surrogates.
// The private wire has one bounded parser shared by control, ACK and auxiliary
// records; reject ambiguity before any state transition.
export function parseWireJSON(raw) {
  if (Buffer.byteLength(raw) > MAX_FRAME_BYTES) throw new Error("wire JSON frame bound exceeded");
  let cursor = 0;
  const space = () => { while (/[\t\r\n ]/.test(raw[cursor] ?? "x")) cursor++; };
  const string = () => {
    const start = cursor++;
    for (;;) {
      if (cursor >= raw.length) throw new Error("unterminated wire string");
      const char = raw[cursor++];
      if (char === "\\") { cursor++; continue; }
      if (char === '"') break;
    }
    const value = JSON.parse(raw.slice(start, cursor));
    if (Buffer.from(value).toString("utf8") !== value) throw new Error("invalid wire Unicode");
    return value;
  };
  const value = depth => {
    if (depth > 64) throw new Error("wire JSON depth bound exceeded");
    space();
    if (raw[cursor] === '"') { string(); return; }
    const open = raw[cursor];
    if (open === "{" || open === "[") {
      cursor++; space(); const end = open === "{" ? "}" : "]", keys = new Set();
      if (raw[cursor] === end) { cursor++; return; }
      for (;;) {
        space();
        if (open === "{") {
          if (raw[cursor] !== '"') throw new Error("invalid wire key");
          const key = string();
          if (keys.has(key)) throw new Error("duplicate wire key");
          keys.add(key); space();
          if (raw[cursor++] !== ":") throw new Error("invalid wire object");
        }
        value(depth + 1); space();
        const separator = raw[cursor++];
        if (separator === end) return;
        if (separator !== ",") throw new Error("invalid wire separator");
      }
    }
    const match = /^(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)/.exec(raw.slice(cursor));
    if (!match) throw new Error("invalid wire value");
    cursor += match[0].length;
    const parsed = JSON.parse(match[0]);
    if (typeof parsed === "number" && !Number.isFinite(parsed)) throw new Error("nonfinite wire number");
  };
  value(0); space();
  if (cursor !== raw.length) throw new Error("trailing wire bytes");
  return JSON.parse(raw);
}
export function createWireInput() {
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let lineBytes = 0;
  return new Transform({
    transform(bytes, _encoding, callback) {
      try {
        decoder.decode(bytes, { stream: true });
        for (const byte of bytes) {
          if (++lineBytes > MAX_FRAME_BYTES) throw new Error("stdin frame exceeds 64 KiB");
          if (byte === 10) lineBytes = 0;
        }
        callback(null, bytes);
      } catch (error) { callback(error); }
    },
    flush(callback) { try { decoder.decode(); callback(); } catch (error) { callback(error); } },
  });
}
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  // Some terminals race cancellation before their consumer has attached.
  promise.catch(() => {});
  return { promise, resolve, reject };
};
function abortable(promise, signal) {
  if (!signal) return promise;
  if (signal.aborted) return Promise.reject(signal.reason ?? new Error("MODEL stream aborted"));
  return new Promise((resolve, reject) => {
    const abort = () => { cleanup(); reject(signal.reason ?? new Error("MODEL stream aborted")); };
    const cleanup = () => signal.removeEventListener("abort", abort);
    signal.addEventListener("abort", abort, { once: true });
    promise.then(value => { cleanup(); resolve(value); }, error => { cleanup(); reject(error); });
  });
}

// The SDK producer owns an unawaited EventStream.push queue. An awaited Agent
// listener alone does not bound it. Count *all* actual pushes, then wait at the
// next provider hook for the prior batch's post-yield (listener-complete) mark.
export function boundedSDKStream(start, options = {}) {
  let pushed = 0, consumed = 0, peak = 0, failed;
  let progress = deferred();
  const controller = new AbortController();
  const signal = options.signal ? AbortSignal.any([controller.signal, options.signal]) : controller.signal;
  const stream = start({ ...options, signal, onProviderStreamEvent: async (...args) => {
    const previous = pushed;
    while (consumed < previous) {
      if (failed) throw failed;
      await abortable(progress.promise, signal);
    }
    if (failed) throw failed;
    await options.onProviderStreamEvent?.(...args);
  } });
  const originalPush = stream.push.bind(stream);
  const originalEnd = stream.end.bind(stream);
  stream.push = (event) => {
    if (failed) {
      // The SDK's own catch supplies the real failed result. Resolve it
      // directly without appending a 4097th queued event; the aborted iterator
      // already propagates the same failure into the awaited Agent loop.
      if (event.type === "error") originalEnd(event.error);
      return;
    }
    if (pushed - consumed >= STREAM_LIMITS.sdkEvents) {
      failed = new Error("MODEL SDK event batch bound exceeded");
      controller.abort(failed);
      progress.reject(failed);
      if (event.type === "error") { originalEnd(event.error); return; }
      throw failed;
    }
    pushed++;
    peak = Math.max(peak, pushed - consumed);
    originalPush(event);
  };
  const originalIterator = stream[Symbol.asyncIterator].bind(stream);
  stream[Symbol.asyncIterator] = async function* () {
    const iterator = originalIterator();
    try {
      for (;;) {
        const next = await abortable(iterator.next(), signal);
        if (next.done) return;
        yield next.value;
        consumed++;
        const old = progress; progress = deferred(); old.resolve();
      }
    } finally {
      await iterator.return?.();
    }
  };
  stream.streamMetrics = () => ({ pushed, consumed, peak, failed: !!failed });
  return stream;
}

const STREAM_BINDING_KEYS = ["project_id", "session_id", "task_id", "run_id", "runtime_epoch", "queue_generation", "dispatch_key", "manifest_hash", "process_identity", "effect_sequence", "effect_key", "request_hash", "stream_id"];
const STREAM_ENVELOPE_KEYS = ["version", "type", "binding", "sequence", "offset", "digest", "payload"];

// One original MODEL is active. Raw bytes have a hard 2 MiB ceiling; transport
// waiters <=4, public observation waiters <=1 (within the four-credit contract),
// visible parts <=64 and observation identities <=262144 per MODEL. No credit
// touches ordinary bridge sequencing, command consumption or effect authority.
export function createModelStreamTransport(send, getInitializedBinding) {
  let active = null;
  let lifetimeData = 0, lifetimeObservations = 0;
  const closed = new Map(); // <= configured max_calls, itself <=32.
  const fail = (state, error) => {
    if (!state || state.failed) return;
    state.failed = error;
    state.abort.abort(error);
    state.opened.reject(error);
    state.changed.resolve();
    for (const pending of state.observations.values()) pending.waiter.reject(error);
    state.observations.clear();
  };
  const wire = (state, type, sequence, offset, hash, payload) => send({ version: "MODEL_SSE_V1", type, binding: state.binding, sequence, offset, digest: hash, payload });
  const changed = state => { const old = state.changed; state.changed = deferred(); old.resolve(); };
  const checkFinal = state => {
    if (!state.terminal || !state.ack || state.failed) return;
    const ack = state.ack, terminal = state.terminal;
    exactKeys(ack, ["status", "content_type", "body_encoding", "stream_id", "body_sha256", "receipt_id", "raw_bytes", "data_sequence", "observation_sequence"]);
    if (ack.status !== 200 || ack.content_type !== "text/event-stream" || ack.body_encoding !== "MODEL_SSE_V1" ||
        ack.stream_id !== state.binding.stream_id || ack.body_sha256 !== state.hash || ack.receipt_id !== state.hash ||
        ack.raw_bytes !== state.raw.length || ack.data_sequence !== state.sequence ||
        ack.observation_sequence !== terminal.payload.observation_sequence) throw new Error("MODEL stream terminal ACK mismatch");
    state.confirmed = true;
    changed(state);
  };
  const transport = {
    begin(sequence, key, ordinal, callerSignal) {
      if (active) throw new Error("concurrent MODEL stream");
      const abort = new AbortController();
      const state = { sequence: 0, key, effectSequence: sequence, ordinal, binding: null, opened: deferred(), changed: deferred(), abort,
        raw: Buffer.alloc(0), rawStore: Buffer.alloc(STREAM_LIMITS.raw), rolling: createHash("sha256"), hash: EMPTY_DIGEST, data: [], dataHistory: [], observations: new Map(), credited: new Map(),
        observeSequence: 0, observeOffset: 0, observeDigest: EMPTY_DIGEST, parts: new Map(), ack: null, terminal: null, confirmed: false, failed: null };
      state.signal = AbortSignal.any([abort.signal, AbortSignal.timeout(90_000), ...(callerSignal ? [callerSignal] : [])]);
      state.signal.addEventListener("abort", () => fail(state, state.signal.reason), { once: true });
      active = state;
      return state;
    },
    async response(state, originalReply) {
      originalReply.then(reply => {
        try {
          if (reply?.body_encoding === "MODEL_SSE_V1") {
            if (!state.binding) throw new Error("MODEL stream ACK before open");
            state.ack = reply; checkFinal(state);
          } else {
            if (state.binding) throw new Error("buffered ACK after stream open");
            if (active === state) active = null;
            state.opened.resolve({ legacy: reply });
          }
        } catch (error) { fail(state, error); }
      }, error => fail(state, error));
      return await abortable(state.opened.promise, state.signal);
    },
    receive(frame) {
      exactKeys(frame, STREAM_ENVELOPE_KEYS);
      if (frame.version !== "MODEL_SSE_V1") throw new Error("MODEL stream version mismatch");
      exactKeys(frame.binding, STREAM_BINDING_KEYS);
      const state = active;
      if (!state) throw new Error("MODEL stream without active request");
      if (frame.type === "stream.open") {
        const initialized = getInitializedBinding();
        if (!initialized) throw new Error("MODEL stream before initialization ACK");
        for (const [key, value] of Object.entries(initialized)) if (canonicalJSON(frame.binding[key]) !== canonicalJSON(value)) throw new Error("MODEL stream initialized binding mismatch");
        const { stream_id: streamID, ...rest } = frame.binding;
        if (frame.binding.effect_sequence !== state.effectSequence || frame.binding.effect_key !== state.key ||
            !/^sha256:[0-9a-f]{64}$/.test(frame.binding.request_hash) || streamID !== digest(canonicalJSON(rest))) throw new Error("MODEL stream effect identity mismatch");
        exactKeys(frame.payload, ["status", "content_type"]);
        if (frame.sequence !== 0 || frame.offset !== 0 || frame.digest !== EMPTY_DIGEST || frame.payload.status !== 200 || frame.payload.content_type !== "text/event-stream") throw new Error("invalid MODEL stream open");
        if (state.binding) {
          if (canonicalJSON(state.open) !== canonicalJSON(frame)) throw new Error("changed MODEL stream open");
          return;
        }
        state.binding = frame.binding; state.open = frame;
        const body = new ReadableStream({
          pull: async controller => {
            try {
              for (;;) {
                if (state.failed) throw state.failed;
                const next = state.data[0];
                if (next && (!next.terminal || state.confirmed)) {
                  state.data.shift();
                  controller.enqueue(next.bytes);
                  // Terminal bytes are credited when safely held (below), to
                  // avoid a final-ACK circular wait. Ordinary bytes on pull.
                  if (!next.terminal) {
                    state.dataHistory[next.sequence - 1].credited = true;
                    await wire(state, "stream.transport_credit", next.sequence, next.offset, next.digest, {});
                  }
                  return;
                }
                if (state.confirmed && !next) { controller.close(); return; }
                await abortable(state.changed.promise, state.signal);
              }
            } catch (error) { fail(state, error); controller.error(error); }
          },
          cancel: reason => fail(state, reason instanceof Error ? reason : new Error("SDK stream cancelled")),
        }, { highWaterMark: 0 });
        state.opened.resolve({ response: new Response(body, { status: 200, headers: { "content-type": "text/event-stream" } }) });
        return;
      }
      if (!state.binding || canonicalJSON(frame.binding) !== canonicalJSON(state.binding)) throw new Error("MODEL stream binding changed");
      if (frame.type === "stream.data") {
        exactKeys(frame.payload, ["data_base64", "terminal"]);
        if (typeof frame.payload.data_base64 !== "string" || typeof frame.payload.terminal !== "boolean") throw new Error("invalid MODEL stream data");
        const bytes = Buffer.from(frame.payload.data_base64, "base64");
        if (!bytes.length || bytes.length > STREAM_LIMITS.fragment || bytes.toString("base64") !== frame.payload.data_base64) throw new Error("invalid MODEL stream bytes");
        if (Number.isSafeInteger(frame.sequence) && frame.sequence > 0 && frame.sequence <= state.sequence) {
          const old = state.dataHistory[frame.sequence - 1];
          if (!old || old.offset !== frame.offset || old.digest !== frame.digest || old.terminal !== frame.payload.terminal ||
              !state.raw.subarray(old.start, old.offset).equals(bytes)) throw new Error("changed MODEL stream duplicate");
          // Exact duplicates never enqueue or advance counters again.
          if (old.credited) void wire(state, "stream.transport_credit", frame.sequence, frame.offset, frame.digest, {}).catch(error => fail(state, error));
          return;
        }
        if (state.failed || state.terminal || frame.sequence !== state.sequence + 1 || frame.offset !== state.raw.length + bytes.length || frame.offset > STREAM_LIMITS.raw ||
            (state.sawTerminal && !frame.payload.terminal) || state.data.filter(item => !item.terminal).length >= STREAM_LIMITS.window) throw new Error("MODEL stream sequence/window violation");
        if (++lifetimeData > STREAM_LIMITS.observations) throw new Error("MODEL lifetime data descriptor bound exceeded");
        bytes.copy(state.rawStore, state.raw.length);
        state.raw = state.rawStore.subarray(0, frame.offset);
        state.rolling.update(bytes);
        state.hash = `sha256:${state.rolling.copy().digest("hex")}`;
        if (frame.digest !== state.hash) throw new Error("MODEL stream digest mismatch");
        state.sequence = frame.sequence;
        state.sawTerminal ||= frame.payload.terminal;
        const item = { bytes, sequence: frame.sequence, start: frame.offset - bytes.length, offset: frame.offset, digest: frame.digest, terminal: frame.payload.terminal, credited: frame.payload.terminal };
        state.data.push(item);
        const { bytes: _bytes, ...descriptor } = item;
        state.dataHistory.push(descriptor);
        if (item.terminal) void wire(state, "stream.transport_credit", frame.sequence, frame.offset, frame.digest, {}).catch(error => fail(state, error));
        changed(state);
      } else if (frame.type === "stream.terminal") {
        exactKeys(frame.payload, ["receipt_id", "observation_sequence"]);
        if (frame.sequence !== state.sequence || frame.offset !== state.raw.length || frame.digest !== state.hash || frame.payload.receipt_id !== state.hash ||
            !Number.isSafeInteger(frame.payload.observation_sequence) || frame.payload.observation_sequence < 0 || frame.payload.observation_sequence > state.observeSequence) throw new Error("MODEL stream terminal mismatch");
        if (state.terminal && canonicalJSON(state.terminal) !== canonicalJSON(frame)) throw new Error("changed MODEL stream terminal");
        state.terminal = frame; checkFinal(state);
      } else if (frame.type === "stream.observation_credit") {
        exactKeys(frame.payload, ["journal_event_ids", "session_watermark"]);
        if (!Array.isArray(frame.payload.journal_event_ids) || frame.payload.journal_event_ids.length > 2 || frame.payload.journal_event_ids.some(id => typeof id !== "string" || !id) ||
            !Number.isSafeInteger(frame.payload.session_watermark) || frame.payload.session_watermark < 0) throw new Error("invalid MODEL observation credit");
        const pending = state.observations.get(frame.sequence);
        if (!pending) {
          if (state.credited.get(frame.sequence) !== canonicalJSON(frame)) throw new Error("stale or changed MODEL observation credit");
          return;
        }
        if (pending.offset !== frame.offset || pending.digest !== frame.digest) throw new Error("MODEL observation credit mismatch");
        if ((pending.event === "text_start" || pending.event === "text_delta") && frame.payload.journal_event_ids.length === 0) throw new Error("MODEL observation lacks durable event");
        state.observations.delete(frame.sequence); state.credited.set(frame.sequence, canonicalJSON(frame)); pending.waiter.resolve();
      } else if (frame.type === "stream.fail") {
        exactKeys(frame.payload, ["code"]);
        if (frame.payload.code !== "MODEL_STREAM_ABORTED" || frame.sequence !== state.sequence || frame.offset !== state.raw.length || frame.digest !== state.hash) throw new Error("MODEL failure identity mismatch");
        fail(state, new Error("MODEL_STREAM_ABORTED"));
      } else throw new Error("wrong MODEL stream direction/type");
    },
    async observe(event, signal) {
      const state = active;
      if (!state?.binding || state.failed) return;
      let update;
      if (event.type === "message_update") update = event.assistantMessageEvent;
      else if (event.type === "message_end" && event.message?.role === "assistant") {
        if (["error", "aborted"].includes(event.message.stopReason)) { fail(state, new Error("SDK model failed")); return; }
        if (!state.confirmed) throw new Error("SDK terminal before original MODEL confirmation");
        update = { type: "message_end", contentIndex: 0 };
      }
      if (!update || !["text_start", "text_delta", "text_end", "message_end"].includes(update.type)) return;
      let part = 0;
      if (update.type !== "message_end") {
        if (!Number.isSafeInteger(update.contentIndex) || update.contentIndex < 0) throw new Error("invalid SDK content index");
        if (update.type === "text_start") {
          if (state.parts.has(update.contentIndex) || state.parts.size >= STREAM_LIMITS.parts) throw new Error("SDK text part bound/identity violation");
          state.parts.set(update.contentIndex, state.parts.size);
        }
        part = state.parts.get(update.contentIndex);
        if (part === undefined) throw new Error("SDK text without start");
      }
      const pieces = [];
      if (update.type === "text_delta") {
        if (typeof update.delta !== "string" || Buffer.from(update.delta).toString("utf8") !== update.delta) throw new Error("invalid SDK text UTF-8");
        let text = "", bytes = 0;
        for (const point of update.delta) {
          const size = Buffer.byteLength(point);
          if (bytes + size > STREAM_LIMITS.fragment) { pieces.push(text); text = ""; bytes = 0; }
          text += point; bytes += size;
        }
        if (text) pieces.push(text);
      } else pieces.push("");
      for (const text of pieces) {
        if (state.failed) throw state.failed;
        if (++state.observeSequence > STREAM_LIMITS.observations || ++lifetimeObservations > STREAM_LIMITS.observations || state.observations.size >= STREAM_LIMITS.window) throw new Error("MODEL observation bound exceeded");
        const payload = { event: update.type, message_ordinal: state.ordinal, text_part: part, sdk_content_index: update.contentIndex, text };
        state.observeOffset += Buffer.byteLength(text);
        state.observeDigest = digest(canonicalJSON({ previous: state.observeDigest, payload }));
        const pending = { waiter: deferred(), offset: state.observeOffset, digest: state.observeDigest, event: update.type };
        state.observations.set(state.observeSequence, pending);
        await wire(state, "stream.observe", state.observeSequence, state.observeOffset, state.observeDigest, payload);
        await abortable(pending.waiter.promise, signal ? AbortSignal.any([signal, state.signal]) : state.signal);
      }
      if (update.type === "message_end") {
        if (!state.confirmed || state.observations.size || state.data.length) throw new Error("MODEL stream did not drain");
        closed.set(state.effectSequence, { stream_id: state.binding.stream_id, digest: state.hash, observation_sequence: state.observeSequence });
        active = null;
      }
    },
    abort: error => fail(active, error ?? new Error("canonical cancellation")),
    closed: () => !active || !!active.failed,
    metrics: () => active ? { raw_bytes: active.raw.length, queued_data: active.data.length, observations: active.observations.size, parts: active.parts.size, closed: closed.size } : { closed: closed.size },
  };
  return transport;
}

function parseConfig(raw) {
  const config = JSON.parse(raw);
  if (!object(config)) throw new Error("worker.json must be an object");
  for (const field of ["ref", "api", "provider", "model", "endpoint", "route"]) {
    requireString(config[field], `worker.${field}`);
  }
  if (config.api !== "openai-completions") throw new Error("only openai-completions is supported");
  const endpoint = new URL(config.endpoint);
  if (!["https:", "http:"].includes(endpoint.protocol) || endpoint.username || endpoint.password) {
    throw new Error("model endpoint must be an HTTP(S) URL without embedded credentials");
  }
  requireInteger(config.max_output_tokens, "worker.max_output_tokens", 8192);
  requireInteger(config.max_calls, "worker.max_calls", MAX_CALLS);
  if (!Array.isArray(config.tools) || config.tools.length > MAX_TOOLS) throw new Error("worker.tools must be a bounded array");
  const names = new Set();
  for (const entry of config.tools) {
    if (!object(entry) || entry.type !== "function" || !object(entry.function)) {
      throw new Error("worker.tools requires full OpenAI function definitions");
    }
    const fn = entry.function;
    requireString(fn.name, "tool.function.name");
    requireString(fn.description, "tool.function.description");
    if (!object(fn.parameters) || fn.parameters.type !== "object") {
      throw new Error(`tool ${fn.name} requires an object parameters schema`);
    }
    if (fn.strict !== undefined && typeof fn.strict !== "boolean") throw new Error(`tool ${fn.name} strict must be boolean`);
    if (names.has(fn.name)) throw new Error(`duplicate tool ${fn.name}`);
    names.add(fn.name);
  }
  return config;
}

function parseRequest(raw) {
  const request = JSON.parse(raw);
  if (!object(request)) throw new Error("request.json must be an object");
  for (const field of ["task_id", "run_id"]) requireString(request[field], `request.${field}`);
  requireInteger(request.epoch, "request.epoch", Number.MAX_SAFE_INTEGER);
  if (!Array.isArray(request.input_refs)) throw new Error("request.input_refs must be an array");
  if (request.context === undefined) throw new Error("request.context is required");
  if (typeof request.task_title !== "string" || typeof request.task_description !== "string") {
    throw new Error("request.task_title and task_description must be strings");
  }
  return request;
}

export function createProtocol(config, request, inputHash, restoredCounts) {
  let sequence = 0;
  let modelCalls = restoredCounts?.model_calls ?? 0;
  let toolCalls = restoredCounts?.tool_calls ?? 0;
  if (![modelCalls, toolCalls].every(n => Number.isSafeInteger(n) && n >= 0) || modelCalls > config.max_calls) throw new Error("invalid cumulative effect counts");
  const pending = new Map();
  let onControl;
  let fatal, effectFailure;
  let initializedBinding;
  const streams = createModelStreamTransport(frame => write(frame), () => initializedBinding);
  const input = createWireInput();
  process.stdin.pipe(input);
  const reader = createInterface({ input, crlfDelay: Infinity });
  input.on("error", error => {
    fatal = error; streams.abort(error);
    for (const waiter of pending.values()) waiter.reject(error);
    pending.clear(); reader.close();
  });
  reader.on("line", (line) => {
    try {
      if (Buffer.byteLength(line) > MAX_FRAME_BYTES) throw new Error("stdin acknowledgement exceeds frame limit");
      const reply = parseWireJSON(line);
      if (object(reply) && ((reply.version !== undefined && !reply.type?.startsWith("command.")) || reply.type?.startsWith("stream."))) {
        streams.receive(reply);
        return;
      }
      if (object(reply) && typeof reply.type === "string" && reply.type.startsWith("command.")) {
        if (!onControl) throw new Error("worker control is not ready");
        onControl(reply);
        return;
      }
      if (!object(reply) || !Number.isSafeInteger(reply.sequence) || typeof reply.key !== "string") {
        throw new Error("invalid effect acknowledgement");
      }
      const waiter = pending.get(reply.sequence);
      if (!waiter || waiter.key !== reply.key) throw new Error("unmatched effect acknowledgement");
      pending.delete(reply.sequence);
      if (reply.state !== "CONFIRMED") {
        const error = new Error(`effect ${reply.key} was ${reply.state}; ${reply.payload?.code ?? "unavailable"}`);
        waiter.reject(error);
        if (waiter.kind === "control") throw error;
        // A matched business refusal stops further effects, while the same
        // worker must still prove SDK idle and seal its original queue.
        effectFailure = error;
        return;
      }
      waiter.resolve(reply.payload);
    } catch (error) {
      fatal = error;
      streams.abort(error);
      for (const waiter of pending.values()) waiter.reject(error);
      pending.clear();
    }
  });
  reader.on("close", () => {
    const error = new Error("coordinator acknowledgement stream closed");
    fatal = error;
    streams.abort(error);
    for (const waiter of pending.values()) waiter.reject(error);
    pending.clear();
  });

  let writeChain = Promise.resolve();
  let pendingWrites = 0;
  async function write(actual) {
    if (fatal) throw fatal;
    const line = `${JSON.stringify(actual)}\n`;
    if (Buffer.byteLength(line) > MAX_FRAME_BYTES) throw new Error("protocol frame exceeds 64 KiB; refusing truncation");
    if (pendingWrites >= 64) throw new Error("worker stdout queue bound exceeded");
    pendingWrites++;
    writeChain = writeChain.then(() => new Promise((resolveWrite, rejectWrite) => {
      process.stdout.write(line, (error) => error ? rejectWrite(error) : resolveWrite());
    }));
    try { await writeChain; } finally { pendingWrites--; }
  }
  async function emit(frame, register) {
    if (fatal) throw fatal;
    const actual = { sequence: ++sequence, ...frame };
    register?.(actual.sequence);
    await write(actual);
    return actual.sequence;
  }

  async function effect(capability, payload, onRegistered) {
    if (fatal || effectFailure) throw fatal ?? effectFailure;
    const ordinal = capability === "MODEL" ? ++modelCalls : ++toolCalls;
    if (capability === "MODEL" && ordinal > config.max_calls) throw new Error("model call bound exceeded");
    const key = `${request.task_id}:${request.run_id}:${request.epoch}:${capability.toLowerCase()}:${ordinal}`;
    let resolveReply;
    let rejectReply;
    const answer = new Promise((resolve, reject) => { resolveReply = resolve; rejectReply = reject; });
    let next;
    try {
      await emit({ type: "effect.request", key, route: config.route, capability, payload }, (seq) => {
        next = seq;
        pending.set(seq, { key, kind: "effect", resolve: resolveReply, reject: rejectReply });
        onRegistered?.(seq, key, ordinal);
      });
      return await answer;
    } catch (error) {
      if (!pending.get(next)?.aborted) pending.delete(next);
      throw error;
    }
  }

  return {
    ready: () => emit({ type: "context.ready", payload: { input_hash: `sha256:${inputHash}`, ...(request.pause_protocol === PAUSE_PROTOCOL ? { pause_protocol: PAUSE_PROTOCOL } : {}) } }),
    effect,
    model: async (payload, signal) => {
      let state;
      const answer = effect("MODEL", payload, (seq, key, ordinal) => { state = streams.begin(seq, key, ordinal, signal); });
      if (!state) return { legacy: await answer };
      return streams.response(state, answer);
    },
    initialize: binding => { initializedBinding = binding; },
    streams,
    emit,
    acknowledged: async (frame, key, registered) => {
      let resolveReply, rejectReply;
      const answer = new Promise((resolve, reject) => { resolveReply = resolve; rejectReply = reject; });
      await emit(frame, (seq) => { pending.set(seq, { key, kind: "control", resolve: resolveReply, reject: rejectReply }); registered?.(seq); });
      return await answer;
    },
    control: (handler) => { onControl = handler; },
    abortEffects: () => {
      streams.abort();
      for (const waiter of pending.values()) {
        if (waiter.kind !== "effect") continue;
        waiter.aborted = true;
        waiter.reject(new Error("canonical cancellation"));
      }
      // Retain acknowledgement identities: a late exact broker reply is still
      // valid evidence and must not be mistaken for another request.
    },
    complete: (payload) => emit({ type: "turn.completed", path: "result.json", payload }),
    counts: () => ({ model_calls: modelCalls, tool_calls: toolCalls }),
    close: () => { reader.close(); process.stdin.unpipe(input); input.destroy(); process.stdin.pause(); },
  };
}

export function createCommandController(session, protocol, request, pause = {}) {
  const ledger = new Map((pause.restored?.commands ?? []).map(entry => [entry.details.command_id, structuredClone(entry)]));
  let pausing = false;
  let binding, initialized = false, cancelled = false, preparing = null, sealed = false;
  let chain = Promise.resolve();
  let resolveSeal, rejectSeal;
  let resolveReady;
  const ready = new Promise((resolve) => { resolveReady = resolve; });
  const finished = new Promise((resolve, reject) => { resolveSeal = resolve; rejectSeal = reject; });
  const emit = (type, extra = {}) => protocol.emit({ type, payload: { ...binding, ...extra } });
  const outstanding = () => [...ledger.values()].filter((entry) => entry.state !== "CONSUMED" && entry.state !== "DROPPED");
  const idle = async () => {
    if (!initialized || sealed || pausing || !session.isIdle || session.agent.hasQueuedMessages()) return;
    if (outstanding().length) return;
    await emit("command.idle", { through: preparing ?? 0, sdk_queue_empty: true, sdk_idle: true, cancelled });
  };
  const enqueue = (action) => {
    chain = chain.then(action).catch((error) => { rejectSeal(error); });
  };
  session.subscribe((event) => {
    if (event.type === "message_start" && event.message?.role === "custom" && event.message.customType === "researchos.command.v1") {
      const details = event.message.details;
      const entry = ledger.get(details?.command_id);
      if (!entry || JSON.stringify(entry.details) !== JSON.stringify(details)) { rejectSeal(new Error("unbound SDK consumption")); return; }
      // Mark synchronously, before SDK can declare the run idle.
      if (entry.state !== "CONSUMED") {
        entry.state = "CONSUMED";
        enqueue(() => emit("command.consumed", { ...entry.details, message_id: entry.message_id }));
      }
    }
    if (event.type === "agent_end") setImmediate(() => enqueue(idle));
  });
  const bind = (frame) => {
    if (!object(frame.binding) || frame.binding.task_id !== request.task_id || frame.binding.run_id !== request.run_id ||
        frame.binding.runtime_epoch !== request.epoch || frame.binding.process_identity?.pid !== process.pid ||
        typeof frame.binding.queue_generation !== "string" || typeof frame.binding.dispatch_key !== "string" ||
        typeof frame.binding.manifest_hash !== "string" ||
        ["project_id", "session_id", "queue_generation", "dispatch_key", "manifest_hash"].some(key => typeof frame.binding[key] !== "string" || !frame.binding[key]) ||
        ["process_created_ns", "job", "appcontainer_sid", "profile", "staging_directory"].some(key => typeof frame.binding.process_identity[key] !== "string" || !frame.binding.process_identity[key])) throw new Error("control binding mismatch");
    for (const [key, value] of Object.entries(request.queue_binding ?? {})) {
      if (frame.binding[key] !== value) throw new Error("control differs from frozen request");
    }
    if (!binding) binding = frame.binding;
    if (JSON.stringify(binding) !== JSON.stringify(frame.binding)) throw new Error("control generation changed");
  };
  protocol.control((frame) => enqueue(async () => {
    bind(frame);
    if (!initialized && !(frame.type === "command.deliver" && frame.initialize === true && frame.command === null)) throw new Error("control before initialization");
    if (sealed) throw new Error("control after seal");
    if (frame.type === "command.deliver") {
      if (frame.initialize === true && frame.command === null) {
        if (!initialized) {
          if (request.pause_protocol === PAUSE_PROTOCOL && frame.pause_protocol !== PAUSE_PROTOCOL) throw new Error("pause capability not negotiated");
          initialized = true;
          await protocol.acknowledged({ type: "command.accepted", payload: { ...binding, initialized: true, ...(request.pause_protocol === PAUSE_PROTOCOL ? { pause_protocol: PAUSE_PROTOCOL } : {}) } }, "command.initialize");
          protocol.initialize(binding);
          resolveReady();
        }
        return;
      }
      if (!initialized || frame.command === null) throw new Error("command before initialization");
      const command = frame.command;
      if (pausing || cancelled || !object(command) || !["STEER", "FOLLOW_UP"].includes(command.delivery) ||
          typeof command.command_id !== "string" || typeof command.message_id !== "string" ||
          typeof command.content !== "string" || Buffer.byteLength(command.content) > 32 * 1024 ||
          command.content_hash !== `sha256:${sha256(command.content)}` ||
          !Number.isSafeInteger(command.queue_sequence) || command.queue_sequence < 1 ||
          (preparing !== null && command.queue_sequence > preparing)) throw new Error("invalid queued command");
      const old = ledger.get(command.command_id);
      if (old) { if (old.frozen !== JSON.stringify(command)) throw new Error("conflicting command replay"); return; }
      if ([...ledger.values()].some(entry => entry.details.queue_sequence === command.queue_sequence || entry.message_id === command.message_id)) throw new Error("duplicate command sequence or message identity");
      if (ledger.size >= 32) throw new Error("worker queue lifetime bound exceeded");
      const parsed = JSON.parse(command.content);
      if (typeof parsed.text !== "string" || !Array.isArray(parsed.attachments)) throw new Error("invalid command content");
      const content = [{ type: "text", text: parsed.text }];
      for (const attachment of parsed.attachments) {
        if (typeof attachment.text !== "string" || !object(attachment.ref)) throw new Error("invalid queued attachment");
        content.push({ type: "text", text: attachment.text });
      }
      const details = { command_id: command.command_id, queue_generation: binding.queue_generation, queue_sequence: command.queue_sequence, content_hash: command.content_hash };
      ledger.set(command.command_id, { frozen: JSON.stringify(command), details, message_id: command.message_id, state: "SDK_ACCEPTED" });
      // This method may start and await a whole prompt when idle. Never await
      // it in the control actor: effect ACK and abort must remain responsive.
      const turn = session.sendCustomMessage({ customType: "researchos.command.v1", content, display: true, details }, { deliverAs: command.delivery === "STEER" ? "steer" : "followUp", triggerTurn: true });
      turn.then(() => enqueue(idle), rejectSeal);
      await emit("command.accepted", { ...details, message_id: command.message_id });
    } else if (frame.type === "command.pause") {
      if (request.pause_protocol !== PAUSE_PROTOCOL || frame.version !== PAUSE_PROTOCOL || cancelled || pausing || preparing !== null ||
          typeof frame.pause_id !== "string" || !/^[a-zA-Z0-9_-]{1,128}$/.test(frame.pause_id) || typeof session.requestPause !== "function") throw new Error("pause unsupported or fenced");
      pausing = true;
      // Do not block the command actor: SDK consumption receipts already queued
      // must drain before capturing the immutable command cut.
      session.requestPause().then(() => enqueue(async () => {
        if (!session.isIdle || !protocol.streams.closed()) throw new Error("pause before SDK/stream drain");
        const sdk = session.exportPauseCheckpoint({ leaseEpoch: request.epoch, inputHash: pause.inputHash });
        const snapshot = { version: PAUSE_PROTOCOL, pause_id: frame.pause_id, binding, input_hash: pause.inputHash,
          config_hash: pause.configHash, counts: protocol.counts(), commands: [...ledger.values()], sdk };
        snapshot.queue_state = pauseQueueState(snapshot);
        validatePauseLedger(snapshot);
        const raw = Buffer.from(JSON.stringify(snapshot));
        if (raw.length > MAX_CHECKPOINT_BYTES) throw new Error("pause checkpoint exceeds 12 MiB");
        const file = await open(join(pause.outputDir, PAUSE_FILE), "wx", 0o600);
        try { await file.writeFile(raw); await file.sync(); } finally { await file.close(); }
        const payload = { version: PAUSE_PROTOCOL, pause_id: frame.pause_id, binding, content_hash: `sha256:${sha256(raw)}`, bytes: raw.length,
          input_hash: pause.inputHash, ...protocol.counts(), queue_cut: snapshot.queue_state.queue_cut,
          command_ledger_hash: snapshot.queue_state.command_ledger_hash, sdk_watermarks: snapshot.queue_state.sdk_watermarks, sdk_session_id: sdk.payload.binding.sessionId };
        let checkpointSequence;
        const ack = await protocol.acknowledged({ type: "checkpoint", key: "checkpoint.sealed", path: PAUSE_FILE, payload }, "checkpoint.sealed", seq => { checkpointSequence = seq; });
        if (!object(ack) || ack.type !== "checkpoint.sealed" || ack.version !== PAUSE_PROTOCOL || ack.checkpoint_sequence !== checkpointSequence ||
            ack.content_hash !== payload.content_hash || ack.pause_id !== frame.pause_id || canonicalJSON(ack.binding) !== canonicalJSON(binding) ||
            ["checkpoint_artifact_id", "checkpoint_use_receipt_hash", "checkpoint_use_principal", "journal_checkpoint_hash"].some(k => typeof ack[k] !== "string" || !ack[k]) ||
            ![ack.checkpoint_use_receipt_hash, ack.journal_checkpoint_hash].every(h => /^sha256:[a-f0-9]{64}$/.test(h))) throw new Error("checkpoint durable seal ACK mismatch");
        sealed = true;
        await protocol.emit({ type: "turn.paused", payload: { ...payload, checkpoint_sequence: checkpointSequence, checkpoint_artifact_id: ack.checkpoint_artifact_id, checkpoint_use_receipt_hash: ack.checkpoint_use_receipt_hash, checkpoint_use_principal: ack.checkpoint_use_principal, journal_checkpoint_hash: ack.journal_checkpoint_hash } });
        resolveSeal({ paused: true });
      }), rejectSeal);
    } else if (pausing) {
      throw new Error("control during pause requires reconciliation");
    } else if (frame.type === "command.prepare_seal") {
      if (!initialized) throw new Error("seal before initialization");
      if (!Number.isSafeInteger(frame.through) || frame.through < 0 || (preparing !== null && preparing !== frame.through)) throw new Error("invalid seal watermark");
      if ([...ledger.values()].some(entry => entry.details.queue_sequence > frame.through)) throw new Error("seal omits accepted command");
      preparing = frame.through;
      await idle();
    } else if (frame.type === "command.commit_seal") {
      if (preparing === null || preparing !== frame.through || ledger.size !== frame.through || !session.isIdle || session.agent.hasQueuedMessages() || outstanding().length || !protocol.streams.closed()) throw new Error("seal before SDK settlement");
      sealed = true;
      await emit("command.sealed", { through: preparing, sdk_queue_empty: true, sdk_idle: true, cancelled });
      resolveSeal({ cancelled });
    } else if (frame.type === "command.clear_abort") {
      cancelled = true;
      session.clearQueue();
      protocol.abortEffects();
      for (const entry of outstanding()) {
        entry.state = "DROPPED";
        await emit("command.cleared", { ...entry.details, message_id: entry.message_id });
      }
      session.abort().then(() => enqueue(async () => { await emit("command.abort_observed", { sdk_idle: session.isIdle, sdk_queue_empty: !session.agent.hasQueuedMessages() }); await idle(); }), rejectSeal);
    } else throw new Error("unknown command control");
  }));
  return { ready, finished, idle: () => enqueue(idle) };
}

function makeTools(config, protocol) {
  return config.tools.map(({ function: fn }) => ({
    name: fn.name,
    label: fn.name,
    description: fn.description,
    parameters: fn.parameters,
    constrainedSampling: fn.strict === true ? { type: "json_schema", strict: "require" } : false,
    execute: async (_toolCallId, args) => {
      const reply = await protocol.effect("TOOL", { name: fn.name, arguments: args });
      if (!object(reply) || !Array.isArray(reply.content) || reply.content.some((part) =>
        !object(part) || part.type !== "text" || typeof part.text !== "string")) {
        throw new Error(`invalid confirmed result for tool ${fn.name}`);
      }
      return { content: reply.content, details: reply.details ?? {} };
    },
  }));
}

export const PAUSE_PROTOCOL = "RESEARCHOS_PAUSE_V1";
export const PAUSE_FILE = "pause-checkpoint.json";
export const MAX_CHECKPOINT_BYTES = 12 * 1024 * 1024;
export function registerCommandPauseSchema(agent) {
  agent.registerPauseDataSchema({ kind: "message", role: "custom", customType: "researchos.command.v1", version: "1", schema: {
    type: "object", properties: { role: { type: "literal", value: "custom" }, customType: { type: "literal", value: "researchos.command.v1" },
      content: { type: "array", items: { type: "object", properties: { type: { type: "literal", value: "text" }, text: { type: "string" } } } },
      display: { type: "boolean" }, timestamp: { type: "number" }, details: { type: "object", properties: {
        command_id: { type: "string" }, queue_generation: { type: "string" }, queue_sequence: { type: "number" }, content_hash: { type: "string" } } } } } });
}
// These are the fixed data contracts returned by the production Host tools.
// A checkpoint cannot invent a schema or authorize an unknown extension type.
export function registerToolPauseSchemas(agent, tools) {
  const schema = fields => ({ type: "object", properties: Object.fromEntries(Object.entries(fields).map(([key, type]) => [key, { type }])) });
  const write = { path: "string", content_hash: "string", size_bytes: "number", operation: "string" };
  const registered = {
    read: { path: "string", content_hash: "string", next_offset: "number", truncated: "boolean", size_bytes: "number" },
    write, edit: write,
    run_check: { check_id: "string", exit_code: "number", timed_out: "boolean", stdout_hash: "string", stderr_hash: "string", source_manifest_hash: "string",
      source_count: "number", frozen_policy_hash: "string", toolchain_hash: "string", vendor_hash: "string", job_total_processes: "number",
      children_stopped: "boolean", streams_drained: "boolean", cleanup_complete: "boolean", stdout_truncated: "boolean", stderr_truncated: "boolean",
      stdout_omitted_bytes: "number", stderr_omitted_bytes: "number", stdout_raw_bytes: "number", stderr_raw_bytes: "number", stdout_utf8_replaced: "boolean", stderr_utf8_replaced: "boolean" },
  };
  for (const { function: fn } of tools) {
    if (registered[fn.name]) agent.registerPauseDataSchema({ kind: "toolDetails", toolName: fn.name, version: "researchos.host-tool.v1", schema: schema(registered[fn.name]) });
  }
}
export function pauseQueueState(snapshot) {
  const agent = snapshot.sdk.payload.agent;
  return { queue_cut: Math.max(0, ...snapshot.commands.map(e => e.details.queue_sequence)),
    command_ledger_hash: digest(canonicalJSON(snapshot.commands)),
    sdk_watermarks: { steering: agent.steering.lastConsumedSequence, follow_up: agent.followUp.lastConsumedSequence },
    sdk_pending_mapping: [["STEER", agent.steering], ["FOLLOW_UP", agent.followUp]].flatMap(([delivery, queue]) =>
      queue.pending.filter(p => p.message.customType === "researchos.command.v1").map(p => ({ delivery, sdk_sequence: p.sequence, command_id: p.message.details.command_id }))) };
}
export function validatePauseLedger(snapshot) {
  if (!Array.isArray(snapshot.commands) || snapshot.commands.length > 32 || !object(snapshot.counts) ||
      ![snapshot.counts.model_calls, snapshot.counts.tool_calls].every(n => Number.isSafeInteger(n) && n >= 0)) throw new Error("invalid checkpoint ledger/counts");
  const agent = snapshot.sdk.payload.agent, pending = [...agent.steering.pending, ...agent.followUp.pending].map(p => p.message);
  const ids = new Set(), sequences = new Set(), messages = new Set();
  for (const entry of snapshot.commands) {
    const command = JSON.parse(entry.frozen), d = entry.details;
    if (!object(d) || ids.has(d.command_id) || sequences.has(d.queue_sequence) || messages.has(entry.message_id) ||
        d.queue_generation !== snapshot.binding.queue_generation || !Number.isSafeInteger(d.queue_sequence) || d.queue_sequence < 1 ||
        command.command_id !== d.command_id || command.message_id !== entry.message_id || command.content_hash !== d.content_hash ||
        command.queue_sequence !== d.queue_sequence || d.content_hash !== `sha256:${sha256(command.content)}` ||
        !["SDK_ACCEPTED", "CONSUMED", "DROPPED"].includes(entry.state)) throw new Error("invalid checkpoint command mapping");
    ids.add(d.command_id);sequences.add(d.queue_sequence);messages.add(entry.message_id);
    const matches = pending.filter(m => m.customType === "researchos.command.v1" && m.details?.command_id === d.command_id);
    if (entry.state === "SDK_ACCEPTED" ? matches.length !== 1 : matches.length !== 0) throw new Error("checkpoint queue/ledger mismatch");
    if (matches.length && canonicalJSON(matches[0].details) !== canonicalJSON(d)) throw new Error("checkpoint queue content mismatch");
  }
  if (pending.some(m => m.customType === "researchos.command.v1" && !ids.has(m.details?.command_id))) throw new Error("unmapped SDK command");
  for (const entry of snapshot.commands.filter(e => e.state === "CONSUMED")) {
    const consumed = agent.messages.filter(m => m.customType === "researchos.command.v1" && m.details?.command_id === entry.details.command_id);
    if (consumed.length !== 1 || canonicalJSON(consumed[0].details) !== canonicalJSON(entry.details)) throw new Error("consumed command missing from SDK history");
  }
  if (canonicalJSON(snapshot.queue_state) !== canonicalJSON(pauseQueueState(snapshot))) throw new Error("checkpoint SDK watermark/mapping mismatch");
}
export async function loadPauseActivation(inputDir, request, configHash) {
  const a = request.pause_activation;
  if (request.pause_protocol !== PAUSE_PROTOCOL || request.queue_control !== true || !object(a) || a.version !== PAUSE_PROTOCOL ||
      !Number.isSafeInteger(a.previous_epoch) || a.previous_epoch < 1 || a.new_epoch !== request.epoch || a.new_epoch !== a.previous_epoch + 1 ||
      ["checkpoint_artifact_id", "checkpoint_use_receipt_hash", "checkpoint_use_principal", "carry_use_receipt_hash"].some(k => typeof a[k] !== "string" || !a[k]) ||
      ![a.checkpoint_hash,a.checkpoint_use_receipt_hash,a.carry_use_receipt_hash].every(h => /^sha256:[a-f0-9]{64}$/.test(h))) throw new Error("invalid pause activation");
  const path=join(inputDir, PAUSE_FILE), info=await lstat(path);
  if (!info.isFile() || info.isSymbolicLink() || info.size > MAX_CHECKPOINT_BYTES) throw new Error("invalid checkpoint file");
  const file=await open(path,"r");let raw;
  try { raw=Buffer.alloc(MAX_CHECKPOINT_BYTES+1);const {bytesRead}=await file.read(raw,0,raw.length,0);raw=raw.subarray(0,bytesRead); } finally {await file.close();}
  if (raw.length > MAX_CHECKPOINT_BYTES || `sha256:${sha256(raw)}` !== a.checkpoint_hash) throw new Error("checkpoint bytes/hash mismatch");
  const s=JSON.parse(raw), b=s.binding, old=s.sdk?.payload.binding;
  if (s.version !== PAUSE_PROTOCOL || s.config_hash !== configHash || s.input_hash !== a.original_input_hash || old?.inputHash !== s.input_hash ||
      old.leaseEpoch !== a.previous_epoch || b.runtime_epoch !== a.previous_epoch || b.task_id !== request.task_id || b.run_id !== request.run_id ||
      ["project_id", "session_id", "queue_generation"].some(k => b[k] !== request.queue_binding?.[k])) throw new Error("checkpoint original identity mismatch");
  validatePauseLedger(s);return s;
}

async function main() {
  if (process.argv.length !== 3) throw new Error("usage: mu-worker.mjs request.json");
  // stdout is reserved for BridgeFrame JSON lines, including when dependencies log.
  console.log = (...args) => console.error(...args);
  globalThis.fetch = () => { throw new Error("direct fetch is disabled; use confirmed MODEL effect"); };

  const manifest = resolve(process.argv[2]);
  const inputDir = dirname(manifest);
  const [requestRaw, configRaw] = await Promise.all([
    readFile(manifest), readFile(join(inputDir, "worker.json"), "utf8"),
  ]);
  const request = parseRequest(requestRaw.toString("utf8"));
  const config = parseConfig(configRaw);
  const restored = request.pause_activation ? await loadPauseActivation(inputDir, request, sha256(configRaw)) : null;
  const protocol = createProtocol(config, request, sha256(requestRaw), restored?.counts);

  const model = {
    id: config.model, name: config.model, provider: config.provider, api: config.api,
    baseUrl: config.endpoint, reasoning: false, input: ["text"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: 1_000_000, maxTokens: config.max_output_tokens,
    compat: { supportsStore: false, supportsStrictMode: true },
  };
  const settingsManager = SettingsManager.inMemory({
    cacheWarming: "off", compaction: { enabled: false }, retry: { enabled: false },
    providerRetry: { maxRetries: 0 },
  });
  const cwd = process.cwd();
  const sessionCwd = restored?.sdk.payload.session.payload.header.cwd ?? cwd;
  const sessionManager = restored ? SessionManager.fromPauseCheckpoint(sessionCwd, restored.sdk.payload.session, restored.sdk.payload.binding.sessionId) : SessionManager.inMemory(cwd);
  const resourceLoader = new DefaultResourceLoader({
    cwd, agentDir: cwd, settingsManager,
    noExtensions: true, noSkills: true, noPromptTemplates: true,
    noThemes: true, noContextFiles: true,
  });
  resourceLoader.getSystemPrompt = () =>
    "You are the ResearchOS task worker. Use only the supplied task, context, and explicitly declared tools. Preserve relevant evidence in the final answer. Do not assume access to files, shell commands, network, or credentials.";
  const modelRuntime = new Proxy({}, {
    get(_target, key) {
      if (key === "hasConfiguredAuth") return () => true;
      if (key === "streamSimple") return (sdkModel, context, sdkOptions) =>
        boundedSDKStream(options => streamSimpleOpenAICompletions(sdkModel, context, options), {
          ...sdkOptions,
          apiKey: "local-broker-placeholder",
          maxTokens: config.max_output_tokens,
          maxRetries: 0,
          cacheRetention: "none",
          onPayload: async (params, payloadModel) => {
            const changed = await sdkOptions?.onPayload?.(params, payloadModel);
            if (JSON.stringify((changed ?? params).messages) !== JSON.stringify(params.messages)) {
              throw new Error("SDK payload hook changed frozen request messages");
            }
            return { ...(changed ?? params), tools: config.tools };
          },
          fetch: async (input, init) => {
            const requestObject = new Request(input, init);
            const raw = await requestObject.text();
            let body;
            try { body = JSON.parse(raw); } catch { throw new Error("SDK model request is not JSON"); }
            if (!object(body) || Object.keys(body).some((key) => !MODEL_BODY_KEYS.has(key)) ||
                body.model !== config.model || body.stream !== true ||
                !Array.isArray(body.messages) ||
                JSON.stringify(body.tools) !== JSON.stringify(config.tools)) {
              throw new Error("SDK model request differs from frozen model configuration or broker body schema");
            }
            const modelReply = await protocol.model({ body }, sdkOptions?.signal);
            if (modelReply.response) return modelReply.response;
            const reply = modelReply.legacy;
            if (!object(reply) || !Number.isInteger(reply.status) || reply.status < 100 || reply.status > 599 ||
                typeof reply.content_type !== "string" || reply.body_encoding !== "gzip+base64" ||
                typeof reply.body_gzip_base64 !== "string" || !/^[A-Za-z0-9+/]*={0,2}$/.test(reply.body_gzip_base64)) {
              throw new Error("invalid confirmed MODEL response");
            }
            const packed = Buffer.from(reply.body_gzip_base64, "base64");
            if (packed.toString("base64") !== reply.body_gzip_base64) throw new Error("invalid MODEL response encoding");
            const decoded = gunzipSync(packed, { maxOutputLength: MAX_MODEL_SSE_BYTES });
            if (`sha256:${sha256(decoded)}` !== reply.body_sha256) throw new Error("MODEL response hash mismatch");
            const sse = new TextDecoder("utf-8", { fatal: true }).decode(decoded);
            return new Response(sse, { status: reply.status, headers: { "content-type": reply.content_type } });
          },
        });
      throw new Error(`unexpected ModelRuntime operation ${String(key)}`);
    },
  });
  const customTools = makeTools(config, protocol);
  const { session, extensionsResult } = await createAgentSession({
    cwd: sessionCwd, agentDir: cwd, sessionManager, settingsManager, resourceLoader,
    modelRuntime, model, thinkingLevel: "off", noTools: "builtin",
    tools: customTools.map((tool) => tool.name), customTools,
  });
  if (request.pause_protocol === PAUSE_PROTOCOL) { registerCommandPauseSchema(session.agent); registerToolPauseSchemas(session.agent, config.tools); }
  if (restored) session.restorePauseCheckpoint(restored.sdk, restored.sdk.payload.binding);
  if (extensionsResult.extensions.length !== 0) throw new Error("extensions unexpectedly loaded");
  // Agent listeners are awaited by the real SDK; AgentSession.subscribe is
  // intentionally retained only for its existing synchronous command ledger.
  session.agent.subscribe((event, signal) => protocol.streams.observe(event, signal));
  const attachments = [];
  for (const artifact of request.artifact_inputs ?? []) {
    if (!object(artifact) || typeof artifact.id !== "string" ||
        !/^[a-zA-Z0-9_-]+$/.test(artifact.id) || artifact.path !== `artifacts/${artifact.id}` ||
        !(artifact.media_type?.startsWith("text/") || artifact.media_type === "application/json")) {
      throw new Error("attachment requires a bounded text artifact; binary inputs need an explicit reader");
    }
    const raw = await readFile(join(inputDir, artifact.path));
    if (`sha256:${sha256(raw)}` !== artifact.content_hash) throw new Error("attachment content hash mismatch");
    const text = new TextDecoder("utf-8", { fatal: true }).decode(raw);
    attachments.push({ id: artifact.id, content_hash: artifact.content_hash, media_type: artifact.media_type, text });
  }
  const { queue_control: _queueControl, queue_binding: _queueBinding, pause_protocol: _pauseProtocol, pause_activation: _pauseActivation, ...taskRequest } = request;
  const prompt = JSON.stringify({ ...taskRequest, attachments });
  if (Buffer.byteLength(prompt) > MAX_FRAME_BYTES) throw new Error("task prompt exceeds 64 KiB; refusing hidden truncation");
  const controller = request.queue_control === true ? createCommandController(session, protocol, request, { restored, inputHash: sha256(requestRaw), configHash: sha256(configRaw), outputDir: join(dirname(inputDir), "output") }) : null;
  await protocol.ready();
  if (controller) await controller.ready;
  let promptError;
  try { if (restored) await session.resumePause(); else await session.prompt(prompt); } catch (error) { promptError = error; }
  if (controller) { controller.idle(); const terminal = await controller.finished; if (terminal.paused) { session.dispose(); protocol.close(); return; } }
  if (promptError) throw promptError;
  if (!session.isIdle) throw new Error("SDK session did not settle after one prompt");
  const finalMessage = session.messages.at(-1);
  if (finalMessage?.role !== "assistant" || finalMessage.stopReason !== "stop" ||
      session.messages.some((message) => message.role === "assistant" &&
        ["error", "aborted"].includes(message.stopReason)) ||
      session.messages.some((message) => message.role === "toolResult" && message.isError)) {
    throw new Error("SDK turn ended with model or tool error");
  }
  const result = {
    task_id: request.task_id, run_id: request.run_id, epoch: request.epoch,
    model_ref: config.ref, model: config.model, ...protocol.counts(),
    actual_cost: null, sdk_cost_is_placeholder: true,
    messages: session.messages,
  };
  const resultRaw = JSON.stringify(result);
  if (Buffer.byteLength(resultRaw) > MAX_RESULT_BYTES) throw new Error("result exceeds 64 MiB; refusing truncation");
  await writeFile(join(dirname(inputDir), "output", "result.json"), resultRaw, { flag: "wx" });
  await protocol.complete(protocol.counts());
  session.dispose();
  protocol.close();
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch((error) => {
  console.error(error?.stack ?? String(error));
  process.exitCode = 1;
  process.stdin.destroy();
});
