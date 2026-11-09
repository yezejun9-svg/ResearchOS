#!/usr/bin/env node
import { nameProcess } from "./cli/setup.js";
import { APP_NAME } from "./config.js";
import { configureHttpDispatcher } from "./core/http-dispatcher.js";
import { main } from "./main.js";
nameProcess(`${APP_NAME}-rpc`);
process.env.PI_CODING_AGENT = "true";
process.env.AI_AGENT = "pi";
process.emitWarning = (() => { });
configureHttpDispatcher();
main(["--mode", "rpc", ...process.argv.slice(2)]);
//# sourceMappingURL=rpc-entry.js.map