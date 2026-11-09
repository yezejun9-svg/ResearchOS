/**
 * Whether naming the process is safe. On macOS, renaming a process that runs an app bundle's Electron binary as Node
 * (ELECTRON_RUN_AS_NODE, how the mu desktop app runs pi) registers it with LaunchServices as a foreground app: a Dock
 * icon that bounces until the process exits, one per session.
 */
export declare function canNameProcess(platform: NodeJS.Platform, electron: string | undefined): boolean;
export declare function nameProcess(title: string): void;
export declare function setupCli(): void;
//# sourceMappingURL=setup.d.ts.map