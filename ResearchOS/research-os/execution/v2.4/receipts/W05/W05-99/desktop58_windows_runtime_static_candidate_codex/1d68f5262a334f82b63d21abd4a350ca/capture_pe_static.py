"""Pure byte reader of two explicit PE files; never loads or executes either."""
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
system32 = Path("C:/Windows/System32")
targets = {"cmd": system32 / "cmd.exe", "wldp": system32 / "wldp.dll"}

def u16(raw, at): return struct.unpack_from("<H", raw, at)[0]
def u32(raw, at): return struct.unpack_from("<I", raw, at)[0]
def u64(raw, at): return struct.unpack_from("<Q", raw, at)[0]

def cstr(raw, at):
    end = raw.find(b"\0", at, min(len(raw), at + 512))
    if end < 0: raise ValueError("PE_NAME_NOT_TERMINATED")
    return raw[at:end].decode("ascii", errors="strict")

def parse_pe(raw):
    if len(raw) < 0x100 or raw[:2] != b"MZ": raise ValueError("PE_DOS_HEADER_OPEN")
    pe = u32(raw, 0x3c)
    if pe + 24 > len(raw) or raw[pe:pe+4] != b"PE\0\0": raise ValueError("PE_SIGNATURE_OPEN")
    coff = pe + 4
    machine, nsections = u16(raw, coff), u16(raw, coff+2)
    opt = coff + 20
    optsize = u16(raw, coff+16)
    magic = u16(raw, opt)
    if magic == 0x20b:
        directory_at, image_base = opt + 112, u64(raw, opt + 24)
    elif magic == 0x10b:
        directory_at, image_base = opt + 96, u32(raw, opt + 28)
    else: raise ValueError("PE_OPTIONAL_MAGIC_OPEN")
    if opt + optsize > len(raw): raise ValueError("PE_OPTIONAL_HEADER_TRUNCATED")
    sections = []
    for idx in range(nsections):
        off = opt + optsize + idx * 40
        if off + 40 > len(raw): raise ValueError("PE_SECTION_TRUNCATED")
        sections.append({"name": raw[off:off+8].split(b"\0", 1)[0].decode("ascii", errors="replace"),
                         "virtual_size": u32(raw, off+8), "virtual_address": u32(raw, off+12),
                         "raw_size": u32(raw, off+16), "raw_offset": u32(raw, off+20)})
    def offset(rva):
        for s in sections:
            span = max(s["virtual_size"], s["raw_size"])
            if s["virtual_address"] <= rva < s["virtual_address"] + span:
                at = s["raw_offset"] + rva - s["virtual_address"]
                if at >= len(raw): raise ValueError("PE_RVA_OUTSIDE_FILE")
                return at
        if rva < opt + optsize and rva < len(raw): return rva
        raise ValueError("PE_RVA_UNMAPPED")
    def directory(index):
        if directory_at + index * 8 + 8 > opt + optsize: return (0, 0)
        return u32(raw, directory_at + index * 8), u32(raw, directory_at + index * 8 + 4)
    imports, delay_imports = [], []
    imp_rva, imp_size = directory(1)
    if imp_rva:
        base = offset(imp_rva)
        for idx in range(min(1024, max(1, imp_size // 20 + 4))):
            at = base + 20 * idx
            if at + 20 > len(raw): raise ValueError("PE_IMPORT_DESC_TRUNCATED")
            row = raw[at:at+20]
            if row == b"\0" * 20: break
            imports.append(cstr(raw, offset(u32(raw, at+12))))
    delay_rva, delay_size = directory(13)
    if delay_rva:
        base = offset(delay_rva)
        for idx in range(min(1024, max(1, delay_size // 32 + 4))):
            at = base + 32 * idx
            if at + 32 > len(raw): raise ValueError("PE_DELAY_DESC_TRUNCATED")
            row = raw[at:at+32]
            if row == b"\0" * 32: break
            flags, name_field = u32(raw, at), u32(raw, at+4)
            if flags & 1:
                name_rva = name_field
            else:
                name_rva = name_field - image_base
            delay_imports.append(cstr(raw, offset(name_rva)))
    return {"machine_hex": hex(machine), "pe_magic_hex": hex(magic),
            "image_base_hex": hex(image_base), "section_count": nsections,
            "import_directory_rva": imp_rva, "import_directory_size": imp_size,
            "delay_directory_rva": delay_rva, "delay_directory_size": delay_size,
            "imports": imports, "delay_imports": delay_imports,
            "sections": sections}

def inspect(path):
    chain = [Path(path.anchor), *reversed(path.parents[:-1]), path]
    # The explicit chain is deduplicated; no directory traversal occurs here.
    seen = set()
    parents = []
    for item in chain:
        key = str(item).casefold()
        if key in seen: continue
        seen.add(key)
        info = item.lstat()
        parents.append({"path": str(item), "is_symlink": item.is_symlink(),
                        "is_junction": bool(getattr(item, "is_junction", lambda: False)()),
                        "reparse": bool(getattr(info, "st_file_attributes", 0) & 0x400)})
    info = path.lstat()
    raw = path.read_bytes()
    out = {"path": str(path), "canonical_path": str(path.resolve(strict=True)),
           "canonical_system32_root": str(system32.resolve(strict=True)),
           "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
           "stat_size": info.st_size, "mtime_ns": info.st_mtime_ns,
           "is_regular": stat.S_ISREG(info.st_mode), "parents": parents}
    try: out["pe"] = parse_pe(raw)
    except BaseException as exc: out["pe_parse_error"] = type(exc).__name__ + ":" + str(exc)
    return out

result = {"schema": "researchos.desktop58-explicit-pe-static-read.v1",
          "stage": "SOURCE_RESOURCE_CANDIDATE_ONLY",
          "targets": {name: inspect(path) for name, path in targets.items()},
          "native_target_executed": False, "system32_tree_scanned": False}
with (here / "pe-explicit-static-read.json").open("xb") as stream:
    stream.write((json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
for name, item in result["targets"].items():
    pe = item.get("pe", {})
    print(name, item["sha256"], item["bytes"],
          "imports", len(pe.get("imports", [])), "delay", len(pe.get("delay_imports", [])),
          "error", item.get("pe_parse_error"))
