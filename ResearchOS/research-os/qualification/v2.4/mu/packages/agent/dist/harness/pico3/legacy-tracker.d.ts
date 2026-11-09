import { type Op } from "@earendil-works/chord/delta";
/** Temporary compatibility surface for Pico3's flush-based document handling. */
export interface Tracker<T extends object> {
    readonly state: T;
    readonly target: T;
    readonly dirty: boolean;
    flush(): Op[];
    rebase(): void;
}
export declare function track<T extends object>(initial: T): Tracker<T>;
//# sourceMappingURL=legacy-tracker.d.ts.map