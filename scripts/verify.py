#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — PE 基线校验 / 双文件对照工具（keil-uvision-cn）

用途:
    1. 单文件模式: 输出 SHA256 / 大小 / 架构 / 节表哈希 / 资源类型计数,
       用于固化"原版基线"。
    2. 双文件模式: 对照两个 PE（例如 原版 UV4.exe 与 汉化版 UV4_CN.exe）,
       逐节比较哈希, 明确回答"汉化是否只动了 .rsrc, 代码节是否逐字节一致"。

安全原则:
    * 只读, 不修改任何输入文件。
    * 仅依赖 Python 标准库。

用法:
    python verify.py <file>                # 基线模式
    python verify.py <original> <patched>  # 对照模式
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_resources as er  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def section_hashes(pe: er.PEFile):
    out = {}
    for s in pe.sections:
        raw = pe.data[s.rawptr: s.rawptr + s.rawsize] if s.rawsize else b""
        out[s.name] = hashlib.sha256(raw).hexdigest()[:16] + (f" (len=0x{s.rawsize:X})" if s.rawsize else " (空)")
    return out


def resource_counts(pe: er.PEFile):
    try:
        res = er.flatten_resources(pe)
    except Exception as exc:
        return {"error": str(exc)}
    counts = {}
    for r in res:
        counts[r["type_name"]] = counts.get(r["type_name"], 0) + 1
    return counts


def describe(path: Path):
    data = path.read_bytes()
    pe = er.PEFile(data)
    return {
        "path": str(path),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "arch": pe.arch,
        "machine": f"0x{pe.machine:04X}",
        "sections": section_hashes(pe),
        "resources": resource_counts(pe),
    }


def compare(a: dict, b: dict):
    print("=" * 72)
    print("对照模式")
    print(f"  原版: {a['path']}")
    print(f"        sha256={a['sha256']}")
    print(f"  汉化: {b['path']}")
    print(f"        sha256={b['sha256']}")
    if a["sha256"] == b["sha256"]:
        print("  !! 两个文件完全相同")
    print("-" * 72)
    print("逐节哈希对照:")
    names = sorted(set(a["sections"]) | set(b["sections"]))
    changed = []
    for n in names:
        ha, hb = a["sections"].get(n, "(无此节)"), b["sections"].get(n, "(无此节)")
        same = ha == hb
        mark = "一致" if same else "不同"
        print(f"  {n:<8} {mark}")
        if not same:
            changed.append(n)
    print("-" * 72)
    ra, rb = a["resources"], b["resources"]
    if "error" in ra or "error" in rb:
        print("资源计数: 解析失败", ra.get("error"), rb.get("error"))
    else:
        names = sorted(set(ra) | set(rb))
        print("资源类型计数对照 (原版 → 汉化):")
        for n in names:
            ca, cb = ra.get(n, 0), rb.get(n, 0)
            mark = "" if ca == cb else f"   <-- 数量变化 ({ca} → {cb})"
            print(f"  {n:<16} {ca} → {cb}{mark}")
    print("-" * 72)
    code_sections = {n for n in names if n in (".text", ".rdata", ".data", ".pdata", "CODE", "DATA")}
    diff_code = [n for n in changed if n in code_sections]
    if diff_code:
        print(f"结论: 代码节被改动: {', '.join(diff_code)}  —— 需要人工审查!")
    else:
        print("结论: .text/.rdata/.data 等代码数据节完全一致, 变化仅出现在:",
              ", ".join(changed) if changed else "(无)")
    print("=" * 72)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) not in (1, 2):
        print(__doc__)
        return 2
    files = [describe(Path(p)) for p in argv]
    for f in files:
        print("=" * 72)
        print("文件:", f["path"])
        print("大小:", f["size"], "bytes")
        print("SHA256:", f["sha256"])
        print("架构:", f["arch"], f"Machine={f['machine']}")
        print("节表哈希:")
        for n, h in f["sections"].items():
            print(f"  {n:<8} {h}")
        print("资源计数:")
        for n, c in sorted(f["resources"].items()):
            print(f"  {n:<16} {c}")
    if len(files) == 2:
        print()
        compare(files[0], files[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
