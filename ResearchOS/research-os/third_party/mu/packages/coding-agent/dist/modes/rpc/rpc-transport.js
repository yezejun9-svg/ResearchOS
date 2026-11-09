import { flushRawStdout, takeOverStdout, waitForRawStdoutBackpressure, writeRawStdout, } from "../../core/output-guard.js";
import { attachJsonlLineReader } from "./jsonl.js";
/** stdin and stdout, one JSON line per record: the transport of `pi --mode rpc`. */
export function stdioRpcTransport() {
    return {
        start: takeOverStdout,
        write: (json) => writeRawStdout(`${json}\n`),
        drained: waitForRawStdoutBackpressure,
        flush: flushRawStdout,
        listen(onRecord, onEnd) {
            process.stdin.on("end", onEnd);
            const detach = attachJsonlLineReader(process.stdin, onRecord);
            return () => {
                detach();
                process.stdin.off("end", onEnd);
            };
        },
        close() {
            process.stdin.pause();
        },
    };
}
//# sourceMappingURL=rpc-transport.js.map