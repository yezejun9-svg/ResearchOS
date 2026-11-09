export interface ShellConfig {
    shell: string;
    args: string[];
    commandTransport?: "argv" | "stdin";
}
/**
 * Where Git for Windows puts its bash, in the order they are tried: the machine-wide installs, the per-user install,
 * then beside each git.exe on PATH (Git adds its `cmd` folder there), whose bash is in the `bin` folder next to it.
 * `exists` is asked only about git.exe; the caller checks the bash paths.
 */
export declare function gitBashCandidates(env: NodeJS.ProcessEnv, exists?: (path: string) => boolean): string[];
/**
 * Resolve shell configuration based on platform and an optional explicit shell path.
 * Resolution order:
 * 1. User-specified shellPath
 * 2. On Windows: Git Bash where Git for Windows installs it (see gitBashCandidates), then bash on PATH
 * 3. On Unix: /bin/bash, then bash on PATH, then fallback to sh
 */
export declare function getShellConfig(customShellPath?: string): ShellConfig;
export declare const POWERSHELL_ARGS: readonly ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command"];
/** Resolve PowerShell on Windows, preferring PowerShell 7 when available. */
export declare function getPowerShellConfig(): ShellConfig;
export declare function getShellEnv(): NodeJS.ProcessEnv;
/**
 * Sanitize binary output for display/storage.
 * Removes characters that crash string-width or cause display issues:
 * - Control characters (except tab, newline, carriage return)
 * - Lone surrogates
 * - Unicode Format characters (crash string-width due to a bug)
 * - Characters with undefined code points
 */
export declare function sanitizeBinaryOutput(str: string): string;
export declare function trackDetachedChildPid(pid: number): void;
export declare function untrackDetachedChildPid(pid: number): void;
export declare function killTrackedDetachedChildren(): void;
/**
 * Kill a process and all its children (cross-platform)
 */
export declare function killProcessTree(pid: number): void;
//# sourceMappingURL=shell.d.ts.map