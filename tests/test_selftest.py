#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_selftest.py — PHASE 0.1 验证器/解析器自测（对应 GPT REVIEW 要求 VERIFY-1..5）

用法:
    python tests/test_selftest.py <UV4.exe 原版路径>

原则:
    * 使用系统临时目录的副本做字节翻转实验, 绝不修改输入文件;
    * 临时 PE 与测试产物不会进入 Git（temp 均在系统临时目录, .gitignore 双保险）;
    * 全部通过时退出码 0, 任一失败退出码 1。

用例:
    TEST VERIFY-1  原版 vs 原版                        → PASS (exit 0)
    TEST VERIFY-2  临时副本 .rsrc 内改 1 字节           → 仅报告 .rsrc 变化 → PASS (exit 0)
    TEST VERIFY-3  临时副本 .text 内改 1 字节           → FAIL (exit != 0)
    TEST VERIFY-4  临时副本 PE 头部改 1 字节            → FAIL (exit != 0)
    TEST VERIFY-5  RT_STRING parse → serialize 无修改往返 → 与原块逐字节一致
"""

from __future__ import annotations

import shutil
import struct
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import extract_resources as er   # noqa: E402
import verify                    # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return verify.EXIT_USAGE

    src = Path(argv[0])
    data = src.read_bytes()
    pe = er.PEFile(data)

    def section(name):
        for s in pe.sections:
            if s.name == name:
                return s
        raise SystemExit(f"找不到节 {name}")

    results = []

    def record(name, ok, detail=""):
        results.append(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}"
              + (f" — {detail}" if detail else ""))

    tmp = Path(tempfile.mkdtemp(prefix="kcn_selftest_"))
    try:
        print("== TEST VERIFY-1: 原版 vs 原版 ==")
        rc = verify.compare(verify.describe(src), verify.describe(src))
        record("Original vs Original → PASS", rc == verify.EXIT_OK, f"exit={rc}")

        print("== TEST VERIFY-2: .rsrc 内 1 字节变化 ==")
        s_rsrc = section(".rsrc")
        off = s_rsrc.rawptr + s_rsrc.rawsize // 2
        mutated = bytearray(data)
        mutated[off] ^= 0xFF
        p2 = tmp / "rsrc_flip.exe"
        p2.write_bytes(mutated)
        rc = verify.compare(verify.describe(src), verify.describe(p2))
        audit = verify.audit_bytes(data, bytes(mutated))
        record(".rsrc 1 字节 → PASS 且仅 .rsrc 报变化",
               rc == verify.EXIT_OK
               and list(audit["by_region"].keys()) == [".rsrc"]
               and audit["changed_byte_count"] == 1,
               f"exit={rc}, regions={list(audit['by_region'])}, count={audit['changed_byte_count']}")

        print("== TEST VERIFY-3: .text 内 1 字节变化 ==")
        s_text = section(".text")
        off = s_text.rawptr + 0x100
        mutated = bytearray(data)
        mutated[off] ^= 0xFF
        p3 = tmp / "text_flip.exe"
        p3.write_bytes(mutated)
        rc = verify.compare(verify.describe(src), verify.describe(p3))
        audit = verify.audit_bytes(data, bytes(mutated))
        record(".text 1 字节 → FAIL(non-zero)",
               rc == verify.EXIT_FAIL and ".text" in audit["by_region"],
               f"exit={rc}, regions={list(audit['by_region'])}")

        print("== TEST VERIFY-4: PE 头部 1 字节变化 ==")
        mutated = bytearray(data)
        mutated[0x02] ^= 0xFF          # DOS 头保留字节, 不影响 PE 解析, 属头部区域
        p4 = tmp / "hdr_flip.exe"
        p4.write_bytes(mutated)
        rc = verify.compare(verify.describe(src), verify.describe(p4))
        audit = verify.audit_bytes(data, bytes(mutated))
        record("PE 头部 1 字节 → FAIL(non-zero)",
               rc == verify.EXIT_FAIL and "PE-Headers" in audit["by_region"],
               f"exit={rc}, regions={list(audit['by_region'])}")

        print("== TEST VERIFY-5: RT_STRING parse → serialize 无修改往返 ==")
        blocks_ok, blocks_bad = 0, []
        for r in er.flatten_resources(pe):
            if r["type_name"] != "RT_STRING" or not r["file_offset"]:
                continue
            blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
            strings = er.parse_string_table(blob)
            rebuilt = er.serialize_string_table(strings)
            if rebuilt == blob:
                blocks_ok += 1
            else:
                blocks_bad.append(r["name"])
        total = blocks_ok + len(blocks_bad)
        record(f"RT_STRING 往返一致 ({blocks_ok}/{total} 块)",
               not blocks_bad,
               f"不一致块: {blocks_bad[:10]}" if blocks_bad else "")

        # 附加: 重序列化长度守卫演示 (缩短→整块变短; 由 PHASE 1A 保证末尾补零语义)
        sample = None
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_STRING" and r["name"] == 10:
                sample = er.parse_string_table(data[r["file_offset"]: r["file_offset"] + r["size"]])
                break
        if sample is not None:
            for r in er.flatten_resources(pe):
                if r["type_name"] == "RT_STRING" and r["name"] == 10:
                    blob10 = data[r["file_offset"]: r["file_offset"] + r["size"]]
                    break
            shorter = list(sample)
            shorter[0] = "X"
            sh = er.serialize_string_table(shorter)
            record("重序列化: 缩短条目后整块变短 (剩余空间留给整块末尾补零)",
                   len(sh) < len(blob10),
                   f"原块 {len(blob10)} 字节 → 缩短后 {len(sh)} 字节")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 72)
    if all(results):
        print(f"自测结论: {len(results)}/{len(results)} 项全部通过")
        return verify.EXIT_OK
    print(f"自测结论: {results.count(False)}/{len(results)} 项失败")
    return verify.EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
