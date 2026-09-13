#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_dialog_codec.py — PHASE 1B2.0 无损 Dialog 编解码器门禁 (DIALOG-1..6)

用法:
    python tests/test_dialog_codec.py <UV4.exe 原版路径>

全部通过 → exit 0; 任一失败 → exit 1。
基线保护: 输入 SHA256 必须等于 µVision 5.43.1.0 固定基线, 否则直接 FAIL。
本测试只读原始 EXE (合成 fixture 在内存中构造), 不修改任何文件。
"""

from __future__ import annotations

import copy
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import extract_resources as er  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASELINE_SHA256 = "428baf13d15e6760af1618def9c9815c97f0321cc5e459ec7adc4dde41c42f89"


def diff_summary(a: bytes, b: bytes, limit: int = 3):
    """逐字节差异摘要 (PHASE 1B2.0 第 12 条 mismatch 报告要求)。"""
    n = min(len(a), len(b))
    first = None
    count = 0
    for i in range(n):
        if a[i] != b[i]:
            count += 1
            if first is None:
                first = i
    if len(a) != len(b):
        count += abs(len(a) - len(b))
    out = []
    if first is not None:
        s = max(0, first - 8)
        for k in range(limit):
            e = min(n, s + 16)
            out.append(f"@0x{s:X}: {a[s:e].hex(' ')} | {b[s:e].hex(' ')}")
            s = e
            if s >= n:
                break
    return {"first_diff_offset": first, "diff_byte_count": count,
            "size_original": len(a), "size_rebuilt": len(b), "hex_context": out}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    src = Path(argv[0])
    data = src.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != BASELINE_SHA256:
        print(f"FAIL: 输入 SHA256 {sha} 与 µVision 5.43.1.0 基线不一致 —— "
              f"版本不匹配，需要重新执行 PHASE 0。", file=sys.stderr)
        return 1
    pe = er.PEFile(data)
    dialogs = [r for r in er.flatten_resources(pe)
               if r["type_name"] == "RT_DIALOG" and r["file_offset"]]

    results = []

    def record(name, ok, detail=""):
        results.append(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print(f"RT_DIALOG 总数: {len(dialogs)}; 基线校验: 通过")

    # ---- DIALOG-1: 246 parse ----
    print("== TEST DIALOG-1: parse ==")
    parse_fail, kinds = [], {"std": 0, "ex": 0}
    asts = {}
    for r in dialogs:
        blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
        try:
            ast = er.parse_dialog_ast(blob)
            asts[(r["name"], r["lang"])] = ast
            kinds[ast["kind"]] += 1
        except Exception as exc:
            parse_fail.append((r["name"], r["lang"], str(exc)))
    record(f"parse {len(dialogs) - len(parse_fail)}/{len(dialogs)}",
           not parse_fail, f"kinds={kinds}; 失败: {parse_fail[:5]}" if parse_fail else "")

    # ---- DIALOG-2: 246 serialize ----
    print("== TEST DIALOG-2: serialize ==")
    ser_fail = []
    rebuilt = {}
    for key, ast in asts.items():
        try:
            rebuilt[key] = er.serialize_dialog_ast(ast)
        except Exception as exc:
            ser_fail.append((key, str(exc)))
    record(f"serialize {len(rebuilt)}/{len(asts)}",
           not ser_fail and len(rebuilt) == len(dialogs),
           f"失败: {ser_fail[:5]}" if ser_fail else "")

    # ---- DIALOG-3: 246 byte-identical ----
    print("== TEST DIALOG-3: parse → serialize → byte-identical ==")
    rt_ok = {"std": 0, "ex": 0}
    rt_total = {"std": 0, "ex": 0}
    mismatches = []
    for r in dialogs:
        key = (r["name"], r["lang"])
        blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
        kind = asts[key]["kind"]
        rt_total[kind] += 1
        if rebuilt[key] == blob:
            rt_ok[kind] += 1
        else:
            mismatches.append((key, kind, diff_summary(blob, rebuilt[key])))
    ok3 = not mismatches and rt_ok["std"] + rt_ok["ex"] == len(dialogs)
    record(f"byte-identical {rt_ok['std'] + rt_ok['ex']}/{len(dialogs)} "
           f"(std {rt_ok['std']}/{rt_total['std']}, ex {rt_ok['ex']}/{rt_total['ex']})",
           ok3)
    for (key, kind, rep) in mismatches[:5]:
        print(f"    MISMATCH {key} {kind}: first_diff=0x{rep['first_diff_offset']:X} "
              f"count={rep['diff_byte_count']} size {rep['size_original']}→{rep['size_rebuilt']}")
        for line in rep["hex_context"]:
            print(f"      {line}")

    # ---- DIALOG-4: Standard 合成 fixture ----
    print("== TEST DIALOG-4: Standard 合成 fixture (string/ordinal class, "
          "string/ordinal title, nonzero creation data) ==")
    TAB2 = b"\x00\x00"
    std_ast = {
        "kind": "std",
        "header": {"style": 0x50000440 | er.DS_SETFONT, "exstyle": 0x00000001,
                   "cdit": 2, "rect": [10, 20, 300, 200]},
        "menu": {"kind": "none", "value": None, "display": None},
        "window_class": {"kind": "ordinal", "value": 0x82, "display": "ordinal:0x82"},
        "title": {"kind": "string", "value": "测试对话框", "display": "测试对话框"},
        "font": {"pointsize": 9, "typeface": "宋体"},
        "controls": [
            {"pad_before": b"", "style": 0x50010000, "exstyle": 0x0,
             "rect": [5, 5, 60, 14], "id": 1001,
             "window_class": {"kind": "string", "value": "MyButton",
                              "display": "MyButton"},
             "title": {"kind": "string", "value": "确定", "display": "确定"},
             "creation_data": {"cb_word": 3, "data": bytes([0x11, 0x22, 0x33, 0x44])}},
            {"pad_before": b"", "style": 0x50010001, "exstyle": 0x0,
             "rect": [5, 25, 60, 14], "id": 1002,
             "window_class": {"kind": "ordinal", "value": 0x80, "display": "BUTTON"},
             "title": {"kind": "ordinal", "value": 0x0101, "display": "ordinal:257"},
             "creation_data": {"cb_word": 0, "data": b""}},
        ],
        "trailing": b"",
    }
    ser1 = er.serialize_dialog_ast(std_ast)
    ast2 = er.parse_dialog_ast(ser1)
    ser2 = er.serialize_dialog_ast(ast2)
    record("std 合成: serialize → parse → serialize 稳定", ser1 == ser2)
    record("std 合成: 语义一致 (ordinal/string/creation-data 保真)",
           er.compare_semantic_snapshots(er.dialog_semantic_snapshot(std_ast),
                                         er.dialog_semantic_snapshot(ast2)) == [])
    record("std 合成: nonzero creation data 保留",
           ast2["controls"][0]["creation_data"] == std_ast["controls"][0]["creation_data"])

    # ---- DIALOG-5: Extended 合成 fixture ----
    print("== TEST DIALOG-5: Extended 合成 fixture (helpID/exStyle/DS_SETFONT/"
          "weight/italic/charset/ordinal+string/nonzero extraCount) ==")
    ex_ast = {
        "kind": "ex", "dlgver": 1, "signature": 0xFFFF,
        "header": {"helpid": 0x1234, "exstyle": 0x00000001,
                   "style": 0x50000448, "cdit": 2, "rect": [12, 24, 320, 220]},
        "menu": {"kind": "none", "value": None, "display": None},
        "window_class": {"kind": "ordinal", "value": 0x82, "display": "ordinal:0x82"},
        "title": {"kind": "string", "value": "扩展对话框", "display": "扩展对话框"},
        "font": {"pointsize": 9, "weight": 400, "italic": 0, "charset": 1,
                 "typeface": "Microsoft YaHei UI"},
        "controls": [
            {"pad_before": b"", "helpid": 0x5678, "exstyle": 0x2, "style": 0x50010000,
             "rect": [6, 6, 70, 15], "id": 2001,
             "window_class": {"kind": "string", "value": "RichEdit20W",
                              "display": "RichEdit20W"},
             "title": {"kind": "string", "value": "内容", "display": "内容"},
             "extra_count": 5, "creation_data": bytes([0xDE, 0xAD, 0xBE, 0xEF, 0x01])},
            {"pad_before": b"\x00\x00\x00", "helpid": 0x0, "exstyle": 0x0, "style": 0x50010001,
             "rect": [6, 30, 70, 15], "id": 2002,
             "window_class": {"kind": "ordinal", "value": 0x80, "display": "BUTTON"},
             "title": {"kind": "ordinal", "value": 0x0202, "display": "ordinal:514"},
             "extra_count": 0, "creation_data": b""},
        ],
        "trailing": b"",
    }
    ser3 = er.serialize_dialog_ast(ex_ast)
    ast4 = er.parse_dialog_ast(ser3)
    ser4 = er.serialize_dialog_ast(ast4)
    record("ex 合成: serialize → parse → serialize 稳定", ser3 == ser4)
    record("ex 合成: 语义一致 (helpID/weight/italic/charset/extraCount 保真)",
           er.compare_semantic_snapshots(er.dialog_semantic_snapshot(ex_ast),
                                         er.dialog_semantic_snapshot(ast4)) == [])
    record("ex 合成: nonzero extraCount 保留",
           ast4["controls"][0]["extra_count"] == 5
           and ast4["controls"][0]["creation_data"] == bytes([0xDE, 0xAD, 0xBE, 0xEF, 0x01]))

    # ---- DIALOG-6: 语义验证器必须发现字段被破坏 ----
    print("== TEST DIALOG-6: 字段破坏 → 语义验证器必须发现 ==")
    target_key = None
    for key in asts:
        if key[1] == 1033 and asts[key]["controls"]:
            target_key = key
            break
    ast_orig = copy.deepcopy(asts[target_key])
    snap_orig = er.dialog_semantic_snapshot(ast_orig)
    blob_orig = er.serialize_dialog_ast(ast_orig)
    corrupted = copy.deepcopy(ast_orig)
    # 等长破坏: 保持模板格式合法 (不改变任何长度字段/creation data 定位)
    corrupted["title"]["value"] = (
        "X" + corrupted["title"]["value"][1:] if corrupted["title"]["value"] else "X")
    corrupted["controls"][0]["style"] = corrupted["controls"][0]["style"] ^ 0xFF
    ser_c = er.serialize_dialog_ast(corrupted)
    snap_c = er.dialog_semantic_snapshot(er.parse_dialog_ast(ser_c))
    diffs = er.compare_semantic_snapshots(snap_orig, snap_c)
    record(f"破坏字段被语义验证器发现 ({target_key[0]},{target_key[1]})",
           len(diffs) >= 2 and ser_c != blob_orig,
           f"diffs={diffs[:3]}")

    print("=" * 72)
    if all(results):
        print(f"自测结论: {len(results)}/{len(results)} 项全部通过")
        return 0
    print(f"自测结论: {results.count(False)}/{len(results)} 项失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
