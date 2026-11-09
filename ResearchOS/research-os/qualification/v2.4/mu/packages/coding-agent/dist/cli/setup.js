import { APP_NAME } from "../config.js";
import { configureHttpDispatcher } from "../core/http-dispatcher.js";
/**
 * Whether naming the process is safe. On macOS, renaming a process that runs an app bundle's Electron binary as Node
 * (ELECTRON_RUN_AS_NODE, how the mu desktop app runs pi) registers it with LaunchServices as a foreground app: a Dock
 * icon that bounces until the process exits, one per session.
 */
export function canNameProcess(platform, electron) {
    return !(platform === "darwin" && electron);
}
export function nameProcess(title) {
    if (canNameProcess(process.platform, process.versions.electron))
        process.title = title;
}
export function setupCli() {
    nameProcess(APP_NAME);
    process.env.PI_CODING_AGENT = "true";
    process.env.AI_AGENT = "pi";
    process.emitWarning = (() => { });
    // Configure undici before provider SDKs issue requests. Settings are applied
    // once SettingsManager has loaded global/project configuration.
    configureHttpDispatcher();
}
//# sourceMappingURL=setup.js.map