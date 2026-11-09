import { track as trackChord, } from "@earendil-works/chord/delta";
class LegacyTracker {
    tracker;
    change;
    forceBase = true;
    constructor(initial) {
        this.tracker = trackChord(initial);
    }
    get state() {
        this.change ??= this.tracker.beginChange();
        return this.change.state;
    }
    get target() {
        return this.tracker.value;
    }
    get dirty() {
        return this.forceBase || this.change !== undefined;
    }
    flush() {
        let prepared;
        if (this.change !== undefined) {
            const change = this.change;
            this.change = undefined;
            prepared = change.prepare();
            // Pico3 adopts before storage. A storage failure faults the owning Session.
            this.tracker.adopt(prepared);
        }
        if (this.forceBase) {
            this.forceBase = false;
            return [["r", this.tracker.value]];
        }
        return (prepared?.ops ?? []);
    }
    rebase() {
        this.forceBase = true;
    }
}
export function track(initial) {
    return new LegacyTracker(initial);
}
//# sourceMappingURL=legacy-tracker.js.map