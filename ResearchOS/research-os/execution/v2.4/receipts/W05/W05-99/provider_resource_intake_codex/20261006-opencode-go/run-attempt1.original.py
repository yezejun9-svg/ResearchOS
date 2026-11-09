import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import uuid

ROOT = pathlib.Path(r"D:\作品集\ResearchOS\research-os")
OUT = pathlib.Path(__file__).resolve().parent
GO = ROOT / ".local/tools/go1.27.1/go/bin/go.exe"
BINARY = ROOT / ".local/bin/resource-intake-opencode-go-20261006.exe"
PACKAGE = "./" + str((OUT / "intake").relative_to(ROOT)).replace("\\", "/")
ENV = dict(os.environ, GOROOT=str(GO.parent.parent), GOTOOLCHAIN="local", GOENV="off", GOPATH=str(ROOT / ".local/gopath"), GOCACHE=str(ROOT / ".local/gocache"), GOPROXY="off", GOSUMDB="off")


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(name, argv):
    start = stamp()
    p = subprocess.run(argv, cwd=ROOT, env=ENV, capture_output=True)
    (OUT / (name + ".stdout.raw")).write_bytes(p.stdout)
    (OUT / (name + ".stderr.raw")).write_bytes(p.stderr)
    save(name + ".invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": start, "finished_at": stamp(), "actual_exit": p.returncode, "stdout_sha256": sha(p.stdout), "stderr_sha256": sha(p.stderr), "environment": {k: ENV[k] for k in ["GOROOT", "GOTOOLCHAIN", "GOENV", "GOPATH", "GOCACHE", "GOPROXY", "GOSUMDB"]}})
    if p.returncode != 0:
        print(name + " failed; captured original raw evidence", flush=True)
        raise SystemExit(p.returncode)
    return p.stdout


def source_inputs():
    raw = command("go-list", [str(GO), "list", "-deps", "-json", PACKAGE]).decode("utf-8")
    decoder = json.JSONDecoder()
    paths = {GO, ROOT / "go.mod", ROOT / "go.sum", pathlib.Path(__file__)}
    index = 0
    while index < len(raw):
        while index < len(raw) and raw[index].isspace(): index += 1
        if index == len(raw): break
        row, index = decoder.raw_decode(raw, index)
        directory = pathlib.Path(row["Dir"])
        for field in ["GoFiles", "CgoFiles", "EmbedFiles", "CFiles", "HFiles", "SFiles", "SysoFiles"]:
            paths.update(directory / name for name in row.get(field, []))
        module = row.get("Module", {})
        for value in [module, module.get("Replace", {})]:
            if value.get("GoMod"): paths.add(pathlib.Path(value["GoMod"]))
    paths.update(ROOT / "spec/v2.0/contracts" / p.name for p in (ROOT / "spec/v2.0/contracts").glob("*.json"))
    paths.update((ROOT / "internal/api/contracts").glob("*.json"))
    paths.update((ROOT / "migrations/sqlite").glob("*.sql"))
    return {str(path): sha(path.read_bytes()) for path in sorted(paths)}


def main():
    assert sha(GO.read_bytes()) == "d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
    if sys.argv[1:] == ["build"]:
        command("gofmt", [str(GO.with_name("gofmt.exe")), "-w", str(OUT / "intake/main.go")])
        inputs = source_inputs()
        save("source-before.json", inputs)
        command("build", [str(GO), "build", "-trimpath", "-o", str(BINARY), PACKAGE])
        after = {name: sha(pathlib.Path(name).read_bytes()) for name in inputs}
        save("source-after.json", after)
        assert inputs == after
        save("build.json", {"binary": str(BINARY), "binary_sha256": sha(BINARY.read_bytes()), "input_count": len(inputs), "source_drift": False, "actual_exit": 0, "at": stamp()})
        print(json.dumps({"build": "PASS", "input_count": len(inputs), "binary_sha256": sha(BINARY.read_bytes())}), flush=True)
        return
    assert sys.argv[1:] == ["intake"]
    build = json.loads((OUT / "build.json").read_text(encoding="utf-8"))
    assert sha(BINARY.read_bytes()) == build["binary_sha256"]
    inputs = json.loads((OUT / "source-after.json").read_text(encoding="utf-8"))
    assert all(sha(pathlib.Path(name).read_bytes()) == value for name, value in inputs.items())
    private = ROOT / ".local/resources" / ("opencode-go-" + uuid.uuid4().hex)
    argv = [str(BINARY), str(ROOT), str(private), str(OUT)]
    start = stamp()
    print("Awaiting protected stdin credential; no value is logged", flush=True)
    with (OUT / "intake.stdout.raw").open("wb") as stdout, (OUT / "intake.stderr.raw").open("wb") as stderr:
        process = subprocess.run(argv, cwd=ROOT, env=ENV, stdin=sys.stdin, stdout=stdout, stderr=stderr)
    save("intake.invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": start, "finished_at": stamp(), "actual_exit": process.returncode, "stdin": "AUTHORIZED_SECRET_PIPE_NOT_LOGGED", "private_root": str(private), "stdout_sha256": sha((OUT / "intake.stdout.raw").read_bytes()), "stderr_sha256": sha((OUT / "intake.stderr.raw").read_bytes()), "binary_sha256": build["binary_sha256"], "input_count": len(inputs), "current_source_unchanged": all(sha(pathlib.Path(name).read_bytes()) == value for name, value in inputs.items()), "formal_acceptance_delta": 0})
    print(json.dumps({"actual_intake_exit": process.returncode, "result_path": str(OUT / "result.json"), "private_root": str(private)}), flush=True)
    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
