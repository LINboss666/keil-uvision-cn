#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — PE 基线校验 / 双文件对照 + 整文件字节级差异审计（keil-uvision-cn）

用途:
    1. 单文件模式: 输出 SHA256 / 大小 / 架构 / 节表完整哈希 / 资源类型计数（固化基线）。
    2. 双文件对照模式（用于验收"汉化只改了 .rsrc"）:
         a) 逐节完整 SHA256 对比（不截短，判断用全值）;
         b) 整文件 byte-level changed-range 审计:
              - 文件大小必须一致（in-place 资源改写的前提）;
              - 所有变化字节必须落在 .rsrc 节内;
              - DOS/PE 头、节表、.text/.rdata/.data/.reloc、证书表、overlay 必须逐字节一致。
       任何违规 → FAIL + 退出码 1。

退出码: 0 = 通过; 1 = 校验失败; 2 = 用法错误。

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

# 受保护节: 这些节发生任何变化都直接 FAIL
PROTECTED_SECTIONS = {".text", ".rdata", ".data", ".pdata", "CODE", "DATA"}
# 允许发生字节变化的节（汉化的目标区域）
ALLOWED_CHANGE_SECTIONS = {".rsrc"}

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 1, 2


def section_hashes(pe: er.PEFile):
    """每节原始字节的完整 SHA256（判断用全值，打印时才截短）。"""
    out = {}
    for s in pe.sections:
        raw = pe.data[s.rawptr: s.rawptr + s.rawsize] if s.rawsize else b""
        out[s.name] = hashlib.sha256(raw).hexdigest()
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


def certificate_range(pe: er.PEFile):
    """证书表 (Security Directory, 目录项 4) 的 RVA 字段实际是文件偏移。"""
    if len(pe.data_dirs) > 4:
        off, size = pe.data_dirs[4]
        if off and size:
            return off, off + size
    return None


def region_of(pe: er.PEFile, off: int) -> str:
    """把文件偏移归类到逻辑区域（用于字节级审计）。"""
    cert = certificate_range(pe)
    if cert and cert[0] <= off < cert[1]:
        return "CertificateTable"
    raw_sections = [s for s in pe.sections if s.rawsize]
    for s in raw_sections:
        if s.rawptr <= off < s.rawptr + s.rawsize:
            return s.name
    first_raw = min(s.rawptr for s in raw_sections)
    if off < first_raw:
        return "PE-Headers"          # DOS 头 / PE-COFF / Optional / 节表
    return "Overlay"


def byte_diff_ranges(a: bytes, b: bytes, chunk: int = 65536):
    """等长字节串的连续差异区间 [(start, end), ...]，先按块粗筛再块内精扫。"""
    ranges = []
    n = min(len(a), len(b))
    i = 0
    while i < n:
        ca, cb = a[i:i + chunk], b[i:i + chunk]
        if ca != cb:
            j = 0
            m = len(ca)
            while j < m:
                if ca[j] != cb[j]:
                    k = j + 1
                    while k < m and ca[k] != cb[k]:
                        k += 1
                    ranges.append((i + j, i + k))
                    j = k
                else:
                    j += 1
        i += chunk
    # 合并跨块相邻区间
    merged = []
    for s, e in ranges:
        if merged and s == merged[-1][1]:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged


def audit_bytes(a_bytes: bytes, b_bytes: bytes):
    """整文件字节级审计。返回 dict(size_equal / changed_byte_count / ranges / by_region)。"""
    if len(a_bytes) != len(b_bytes):
        return {"size_equal": False, "changed_byte_count": -1,
                "ranges": [], "by_region": {}}
    ranges = byte_diff_ranges(a_bytes, b_bytes)
    pe = er.PEFile(a_bytes)
    by_region = {}
    for s, e in ranges:
        by_region.setdefault(region_of(pe, s), []).append((s, e))
    return {"size_equal": True,
            "changed_byte_count": sum(e - s for s, e in ranges),
            "ranges": ranges,
            "by_region": by_region}


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


def compare(a: dict, b: dict) -> int:
    """对照两份 describe 结果。返回 EXIT_OK / EXIT_FAIL。"""
    fail_reasons = []
    print("=" * 72)
    print("对照模式")
    print(f"  原版: {a['path']}")
    print(f"        sha256={a['sha256']}")
    print(f"  汉化: {b['path']}")
    print(f"        sha256={b['sha256']}")
    if a["sha256"] == b["sha256"]:
        print("  !! 两个文件完全相同 (PASS)")

    # -- 文件大小 --
    if a["size"] != b["size"]:
        fail_reasons.append(
            f"文件大小不一致: {a['size']} != {b['size']} (in-place 资源改写要求大小不变)")

    # -- 逐节完整 SHA256 对比 --
    section_names = sorted(set(a["sections"]) | set(b["sections"]))
    changed_sections = [n for n in section_names
                        if a["sections"].get(n) != b["sections"].get(n)]
    print("-" * 72)
    print("逐节完整 SHA256 对比 (打印截短, 判断用全值):")
    for n in section_names:
        ha, hb = a["sections"].get(n), b["sections"].get(n)
        if ha is None or hb is None:
            print(f"  {n:<8} 缺失 ({'原版' if hb is None else '汉化版'}一侧没有该节)")
            fail_reasons.append(f"节 {n} 在一侧缺失 (PE 布局被改变)")
            continue
        print(f"  {n:<8} {'一致' if ha == hb else '不同'}"
              + ("" if ha == hb else f"  {ha[:16]}… vs {hb[:16]}…"))
    diff_protected = [n for n in changed_sections if n in PROTECTED_SECTIONS]
    if diff_protected:
        fail_reasons.append(f"受保护代码/数据节发生变化: {', '.join(diff_protected)}")
    diff_other = [n for n in changed_sections
                  if n not in PROTECTED_SECTIONS and n not in ALLOWED_CHANGE_SECTIONS]
    if diff_other:
        fail_reasons.append(f"非允许区域节发生变化: {', '.join(diff_other)}")

    # -- 资源类型计数 (信息性, 判定以字节级审计为准) --
    ra, rb = a["resources"], b["resources"]
    resource_names = sorted(set(ra) | set(rb))
    print("-" * 72)
    print("资源类型计数对照 (原版 → 汉化):")
    for n in resource_names:
        ca, cb = ra.get(n, 0), rb.get(n, 0)
        mark = "" if ca == cb else f"   <-- 数量变化 ({ca} → {cb})"
        print(f"  {n:<16} {ca} → {cb}{mark}")

    # -- 整文件字节级差异审计 --
    print("-" * 72)
    ba = Path(a["path"]).read_bytes()
    bb = Path(b["path"]).read_bytes()
    audit = audit_bytes(ba, bb)
    if not audit["size_equal"]:
        print("整文件字节级审计: 跳过 (大小不同, 已在上方判 FAIL)")
    else:
        print(f"整文件字节级审计: changed_byte_count={audit['changed_byte_count']}, "
              f"changed_ranges={len(audit['ranges'])}")
        for region in sorted(audit["by_region"]):
            rs = audit["by_region"][region]
            nbytes = sum(e - st for st, e in rs)
            first = rs[0]
            print(f"  [{region:<16}] {len(rs):<5} 处 / {nbytes:<8} 字节, "
                  f"首处 @0x{first[0]:X}-0x{first[1]:X}")
            if region not in ALLOWED_CHANGE_SECTIONS:
                fail_reasons.append(
                    f".rsrc 之外发现字节变化: 区域 {region} (首处 @0x{first[0]:X})")

    # -- 结论 --
    print("-" * 72)
    if fail_reasons:
        print("结论: FAIL")
        for r in fail_reasons:
            print("  ✗", r)
        print("=" * 72)
        return EXIT_FAIL
    print("结论: PASS — 变化仅限 .rsrc; PE 头/代码节/证书表/overlay 逐字节一致")
    print("=" * 72)
    return EXIT_OK


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) not in (1, 2):
        print(__doc__)
        return EXIT_USAGE
    files = [describe(Path(p)) for p in argv]
    for f in files:
        print("=" * 72)
        print("文件:", f["path"])
        print("大小:", f["size"], "bytes")
        print("SHA256:", f["sha256"])
        print("架构:", f["arch"], f"Machine={f['machine']}")
        print("节表完整 SHA256 (打印截短):")
        for n, h in f["sections"].items():
            print(f"  {n:<8} {h[:16]}…")
        print("资源计数:")
        for n, c in sorted(f["resources"].items()):
            print(f"  {n:<16} {c}")
    if len(files) == 2:
        print()
        return compare(files[0], files[1])
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
