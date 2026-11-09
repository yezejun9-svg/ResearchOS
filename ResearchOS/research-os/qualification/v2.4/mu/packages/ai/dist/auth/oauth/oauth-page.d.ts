/**
 * The page a sign-in ends on in the browser: mu's mark, one line saying whether it worked, and the
 * provider's own sentence. Every OAuth flow here (ChatGPT, Claude, OpenRouter, Radius) and mu's own
 * Google sign-ins render it, so a person sees the same page whichever account they connect.
 */
export declare function oauthSuccessHtml(message: string): string;
export declare function oauthErrorHtml(message: string, details?: string): string;
//# sourceMappingURL=oauth-page.d.ts.map