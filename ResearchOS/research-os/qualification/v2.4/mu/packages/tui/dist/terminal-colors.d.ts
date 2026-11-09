export interface RgbColor {
    r: number;
    g: number;
    b: number;
}
export type TerminalColorScheme = "dark" | "light";
/** OSC color slots: 10 is the terminal's default foreground, 11 its default background. */
export type OscColorSlot = 10 | 11;
/**
 * Parse an OSC 10/11 color reply. Returns undefined when `data` is not such a reply;
 * `rgb` is undefined when it is a reply with an unparseable color.
 */
export declare function parseOscColorResponse(data: string): {
    slot: OscColorSlot;
    rgb: RgbColor | undefined;
} | undefined;
export declare function parseOsc11BackgroundColor(data: string): RgbColor | undefined;
export declare function parseTerminalColorSchemeReport(data: string): TerminalColorScheme | undefined;
//# sourceMappingURL=terminal-colors.d.ts.map