/**
 * RPC mode: Headless operation with a JSON protocol, over stdin/stdout or a transport the embedder passes.
 *
 * Used for embedding the agent in other applications.
 * Receives commands as JSON records, outputs events and responses as JSON records (see rpc-transport.ts).
 *
 * Protocol:
 * - Commands: JSON objects with `type` field, optional `id` for correlation
 * - Responses: JSON objects with `type: "response"`, `command`, `success`, and optional `data`/`error`
 * - Events: AgentSessionEvent objects streamed as they occur
 * - Extension UI: Extension UI requests are emitted, client responds with extension_ui_response
 */
import type { AgentSessionRuntime } from "../../core/agent-session-runtime.ts";
import { type RpcTransport } from "./rpc-transport.ts";
export type { RpcCommand, RpcExtensionUIRequest, RpcExtensionUIResponse, RpcResponse, RpcSessionState, } from "./rpc-types.ts";
/**
 * Run in RPC mode.
 * Listens for JSON commands on the transport (stdin by default), outputs events and responses on it (stdout).
 */
export declare function runRpcMode(runtimeHost: AgentSessionRuntime, transport?: RpcTransport): Promise<never>;
//# sourceMappingURL=rpc-mode.d.ts.map