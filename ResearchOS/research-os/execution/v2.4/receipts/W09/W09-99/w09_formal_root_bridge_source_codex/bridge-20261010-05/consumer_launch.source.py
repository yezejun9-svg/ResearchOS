"""One finite consumer process: validate environment, then execute unchanged dispatcher."""
import hashlib
from pathlib import Path
import sys
import types

def main(args):
    if len(args) != 5:
        raise ValueError("SOURCE_PIN_AND_EXACT_ROUTE_REQUIRED")
    source = Path(__file__).resolve().parent / "w09_root_bridge.source.py"
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args[0] or len(raw) != int(args[1]):
        raise ValueError("BRIDGE_SOURCE_PIN")
    bridge = types.ModuleType("bridge03_consumer_environment")
    bridge.__file__ = str(source)
    exec(compile(raw, str(source), "exec"), bridge.__dict__)
    route = tuple(args[2:])
    bridge.need(route in bridge.ROUTES, "EXACT_CONSUMER_ROUTE")
    bridge.require_process_temp()
    bridge.resource_environment()
    dispatcher = bridge.ROOT / "execution/command_dispatcher/dispatch.py"
    observed = bridge.pin(dispatcher)
    bridge.need((observed["sha256"], observed["bytes"]) == bridge.TRUSTED[
        "execution/command_dispatcher/dispatch.py"], "PINNED_MAIN_DISPATCHER")
    # Dispatch retains its exact module/file and product argv; no Main bytes change.
    sys.argv = [str(dispatcher), route[0], "--task-id", "W09",
                "--check-id" if route[1] else "--case-id", route[1] or route[2], "--spec", "v2.4"]
    sys.path.insert(0, str(dispatcher.parent))
    import runpy
    runpy.run_path(str(dispatcher), run_name="__main__")

if __name__ == "__main__":
    main(sys.argv[1:])
