import type { TUI } from "@earendil-works/pi-tui";
import type { SettingsManager } from "../../../core/settings-manager.ts";
import { type TerminalTheme, type Theme } from "./theme.ts";
type ThemeResult = {
    success: boolean;
    error?: string;
};
export declare class InteractiveThemeController {
    private readonly ui;
    private readonly getSettingsManager;
    private readonly showError;
    private readonly onChanged;
    private currentThemeSetting;
    private terminalTheme;
    private terminalColors;
    private activeThemeName;
    private autoSyncEnabled;
    private terminalColorSchemeUnsubscribe;
    constructor(ui: TUI, options: {
        getSettingsManager: () => SettingsManager;
        showError: (message: string) => void;
        onChanged: () => void;
        initialThemeSetting?: string;
    });
    rebindTui(): void;
    applyFromSettings(): Promise<void>;
    getThemeSelection(): string | undefined;
    setThemeName(themeName: string, showError?: boolean): ThemeResult;
    setThemeSetting(themeSetting: string): Promise<void>;
    setThemeInstance(themeInstance: Theme): ThemeResult;
    preview(themeSettingOrName: string): void;
    disableAutoSync(): void;
    dispose(): void;
    getTerminalTheme(): TerminalTheme;
    private applyThemeName;
    /**
     * Query the terminal's default colors, which themes use for tokens set to "". Startup does not
     * wait for the replies; the UI re-renders when they arrive. Returns the background reply.
     */
    private queryTerminalDefaultColors;
    private notifyChanged;
    private setAutoSync;
    private bindTerminalColorSchemeListener;
    private applyTerminalTheme;
}
export {};
//# sourceMappingURL=theme-controller.d.ts.map