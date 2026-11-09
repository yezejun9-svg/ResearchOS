"""One-shot, content-free OpenAI tool-call protocol probe for the local candidate."""

import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
MODEL = "qwen3:4b-instruct"
URL = "http://127.0.0.1:11434/v1/chat/completions"
REQUEST = {
    "model": MODEL,
    "stream": False,
    "temperature": 0,
    "max_tokens": 128,
    "messages": [
        {
            "role": "user",
            "content": "Call protocol_probe once with marker LOCAL_ONLY. Do not answer in prose.",
        }
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "protocol_probe",
                "description": "Record a content-free local protocol marker.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "marker": {"type": "string", "enum": ["LOCAL_ONLY"]}
                    },
                    "required": ["marker"],
                    "additionalProperties": False,
                },
            },
        }
    ],
    "tool_choice": {"type": "function", "function": {"name": "protocol_probe"}},
}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    request_path = HERE / "probe_request.raw"
    request_json_path = HERE / "probe_request.json"
    response_path = HERE / "probe_response.raw"
    result_path = HERE / "probe_result.json"
    if any(path.exists() for path in (request_path, request_json_path, response_path, result_path)):
        raise SystemExit("Probe artifact exists; refusing to repeat the request")

    body = json.dumps(REQUEST, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request_path.write_bytes(body)
    write_json(request_json_path, REQUEST)
    started_utc = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    status = None
    headers = {}
    raw = b""
    error = None
    try:
        req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as response:
            status = response.status
            headers = dict(response.headers.items())
            raw = response.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        headers = dict(exc.headers.items())
        raw = exc.read()
        error = str(exc)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - start
    response_path.write_bytes(raw)

    parsed = None
    parse_error = None
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        parse_error = f"{type(exc).__name__}: {exc}"

    calls = None
    valid_call = False
    usage = None
    if isinstance(parsed, dict):
        usage = parsed.get("usage")
        choices = parsed.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                calls = message.get("tool_calls")
    if isinstance(calls, list) and len(calls) == 1 and isinstance(calls[0], dict):
        call = calls[0]
        function = call.get("function")
        if call.get("type") == "function" and isinstance(function, dict) and function.get("name") == "protocol_probe":
            try:
                valid_call = json.loads(function.get("arguments", "")) == {"marker": "LOCAL_ONLY"}
            except (TypeError, ValueError):
                pass
    write_json(result_path, {
        "schema": "researchos.local-model-protocol-probe.v1",
        "scope": "RESOURCE_PROTOCOL_ONLY",
        "model": MODEL,
        "endpoint": URL,
        "started_utc": started_utc,
        "elapsed_seconds": round(elapsed, 3),
        "http_status": status,
        "response_headers": headers,
        "request_sha256": hashlib.sha256(body).hexdigest(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "parse_error": parse_error,
        "request_error": error,
        "structured_tool_calls_count": len(calls) if isinstance(calls, list) else None,
        "valid_structured_tool_call": valid_call,
        "usage": usage,
        "cost_usd": None,
        "product_acceptance": False,
    })
    print(json.dumps({"http_status": status, "elapsed_seconds": round(elapsed, 3), "valid_structured_tool_call": valid_call, "error": error}, ensure_ascii=False))


if __name__ == "__main__":
    main()
