#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_dialog_codec.py — PHASE 1B2.0/1B2.0a 无损 Dialog 编解码器门禁 (DIALOG-1..8)

用法:
    python tests/test_dialog_codec.py <UV4.exe 原版路径>

DIALOG-1  246 dialogs parse
DIALOG-2  246 dialogs serialize
DIALOG-3  246 dialogs parse → serialize → byte-identical
DIALOG-4  Standard 合成 fixture (string/ordinal class, string/ordinal title,
          creation size_bytes=6/payload=4 与 odd size_bytes=7/payload=5)
DIALOG-5  Extended 合成 fixture (helpID/exStyle/DS_SETFONT/weight/italic/charset/
          ordinal+string/extraCount=5)
DIALOG-6  语义验证器: 字段破坏必须被发现 (style 位翻转 / 标题篡改)
DIALOG-7  对齐突变测试: 文本奇偶长度变化后每个控件起始 offset % 4 == 0,
          且覆盖 0-byte pad → 2-byte pad 与 2-byte → 0-byte 两种变化 (std+ex)
DIALOG-8  语义破坏守卫: dialog helpID / dlgVer·signature / cDlgItems /
          control exStyle / creation data 同长度改 1 字节 /
          extraCount·size field 变化 → 必须全部 FAIL,
          serializer 自身拒绝 cDlgItems/extraCount/size_bytes 不一致

基线保护: 输入 SHA256 必须等于 µVision 5.43.1.0 固定基线。只读, 不修改文件。
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
    n = min(len(a), len(b))
    first, count = None, 0
    for i in range(n):
        if a[i] != b[i]:
            count += 1
            if first is None:
                first = i
    if len(a) != len(b):
        count += abs(len(a) - len(b))
    out, s = [], (first or 0)
    for _ in range(limit):
        e = min(n, s + 16)
        out.append(f"@file+0x{s:X}: {a[s:e].hex(' ')} | {b[s:e].hex(' ')}")
        s = e
        if s >= n:
            break
    return {"first_diff_offset": first, "diff_byte_count": count,
            "size_original": len(a), "size_rebuilt": len(b), "hex_context": out}


def mutation_detected(ast_mutated, snap_orig):
    """序列化被改 AST → 重解析 → 语义快照对比; 异常也视为发现。"""
    try:
        ser = er.serialize_dialog_ast(ast_mutated)
        ast2 = er.parse_dialog_ast(ser)
        snap2 = er.dialog_semantic_snapshot(ast2)
        return bool(er.compare_semantic_snapshots(snap_orig, snap2))
    except ValueError:
        return True


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

    # ---- DIALOG-1..3: 真实 246 全量门禁 ----
    parse_fail, kinds = [], {"std": 0, "ex": 0}
    asts, blobs = {}, {}
    for r in dialogs:
        blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
        blobs[(r["name"], r["lang"])] = blob
        try:
            ast = er.parse_dialog_ast(blob)
            asts[(r["name"], r["lang"])] = ast
            kinds[ast["kind"]] += 1
        except Exception as exc:
            parse_fail.append((r["name"], r["lang"], str(exc)))
    record(f"DIALOG-1 parse {len(asts)}/{len(dialogs)}", not parse_fail,
           f"kinds={kinds}; 失败: {parse_fail[:5]}" if parse_fail else "")

    ser_fail, rebuilt = [], {}
    for key, ast in asts.items():
        try:
            rebuilt[key] = er.serialize_dialog_ast(ast)
        except Exception as exc:
            ser_fail.append((key, str(exc)))
    record(f"DIALOG-2 serialize {len(rebuilt)}/{len(asts)}",
           not ser_fail and len(rebuilt) == len(dialogs),
           f"失败: {ser_fail[:5]}" if ser_fail else "")

    rt_ok = {"std": 0, "ex": 0}
    rt_total = {"std": 0, "ex": 0}
    mismatches = []
    for r in dialogs:
        key = (r["name"], r["lang"])
        kind = asts[key]["kind"]
        rt_total[kind] += 1
        if rebuilt[key] == blobs[key]:
            rt_ok[kind] += 1
        else:
            mismatches.append((key, kind, diff_summary(blobs[key], rebuilt[key])))
    record(f"DIALOG-3 byte-identical {rt_ok['std'] + rt_ok['ex']}/{len(dialogs)} "
           f"(std {rt_ok['std']}/{rt_total['std']}, ex {rt_ok['ex']}/{rt_total['ex']})",
           not mismatches and rt_ok["std"] + rt_ok["ex"] == len(dialogs))
    for (key, kind, rep) in mismatches[:5]:
        print(f"    MISMATCH {key} {kind}: first_diff=0x{rep['first_diff_offset']:X} "
              f"count={rep['diff_byte_count']} size {rep['size_original']}→{rep['size_rebuilt']}")
        for line in rep["hex_context"]:
            print(f"      {line}")

    # ---- 合成 fixture ----
    def std_fixture(title_text, creation):
        return {
            "kind": "std",
            "header": {"style": 0x50000440, "exstyle": 1, "cdit": 2,
                       "rect": [10, 20, 300, 200]},
            "menu": {"kind": "none", "value": None, "display": None},
            "window_class": {"kind": "ordinal", "value": 0x82, "display": "ordinal:0x82"},
            "title": {"kind": "string", "value": "测试对话框", "display": "测试对话框"},
            "font": {"pointsize": 9, "typeface": "宋体"},
            "controls": [
                {"offset": 0, "pad_before": b"", "style": 0x50010000, "exstyle": 0,
                 "rect": [5, 5, 60, 14], "id": 1001,
                 "window_class": {"kind": "string", "value": "MyButton",
                                  "display": "MyButton"},
                 "title": {"kind": "string", "value": title_text,
                           "display": title_text},
                 "creation_data": creation},
                {"offset": 0, "pad_before": b"", "style": 0x50010001, "exstyle": 0,
                 "rect": [5, 25, 60, 14], "id": 1002,
                 "window_class": {"kind": "ordinal", "value": 0x80, "display": "BUTTON"},
                 "title": {"kind": "ordinal", "value": 0x0101,
                           "display": "ordinal:257"},
                 "creation_data": {"size_bytes": 0, "data": b""}},
            ],
            "trailing": b"",
        }

    def ex_fixture(c1_title):
        return {
            "kind": "ex", "dlgver": 1, "signature": 0xFFFF,
            "header": {"helpid": 0x1234, "exstyle": 1, "style": 0x50000448,
                       "cdit": 2, "rect": [12, 24, 320, 220]},
            "menu": {"kind": "none", "value": None, "display": None},
            "window_class": {"kind": "ordinal", "value": 0x82, "display": "ordinal:0x82"},
            "title": {"kind": "string", "value": "扩展对话框", "display": "扩展对话框"},
            "font": {"pointsize": 9, "weight": 400, "italic": 0, "charset": 1,
                     "typeface": "Microsoft YaHei UI"},
            "controls": [
                {"offset": 0, "pad_before": b"", "helpid": 0x5678, "exstyle": 2,
                 "style": 0x50010000, "rect": [6, 6, 70, 15], "id": 2001,
                 "window_class": {"kind": "string", "value": "RichEdit20W",
                                  "display": "RichEdit20W"},
                 "title": {"kind": "string", "value": c1_title,
                           "display": c1_title},
                 "extra_count": 0, "creation_data": b""},
                {"offset": 0, "pad_before": b"", "helpid": 0, "exstyle": 0,
                 "style": 0x50010001, "rect": [6, 30, 70, 15], "id": 2002,
                 "window_class": {"kind": "ordinal", "value": 0x80, "display": "BUTTON"},
                 "title": {"kind": "ordinal", "value": 0x0202,
                           "display": "ordinal:514"},
                 "extra_count": 5,
                 "creation_data": bytes([0xDE, 0xAD, 0xBE, 0xEF, 0x01])},
            ],
            "trailing": b"",
        }

    def stable_roundtrip(ast):
        ser1 = er.serialize_dialog_ast(ast)
        ast2 = er.parse_dialog_ast(ser1)
        ser2 = er.serialize_dialog_ast(ast2)
        return ser1 == ser2, ast2

    def offsets_aligned(ast):
        return all(c["offset"] % 4 == 0 for c in ast["controls"])

    # ---- DIALOG-4: Standard 合成 fixture ----
    print("== TEST DIALOG-4: Standard 合成 fixture ==")
    f_a = std_fixture("确定", {"size_bytes": 6, "data": bytes([0x11, 0x22, 0x33, 0x44])})
    ok_a, a2 = stable_roundtrip(f_a)
    record("std: size_bytes=6/payload=4 round-trip 稳定", ok_a)
    record("std: nonzero creation data 保真",
           a2["controls"][0]["creation_data"] == f_a["controls"][0]["creation_data"])
    f_b = std_fixture("确定", {"size_bytes": 7, "data": bytes([1, 2, 3, 4, 5])})
    ok_b, b2 = stable_roundtrip(f_b)
    record("std: odd size_bytes=7/payload=5 round-trip 稳定", ok_b)
    record("std: 两 fixture 控件起始 offset 均 DWORD 对齐",
           offsets_aligned(a2) and offsets_aligned(b2),
           f"offsets={[[c['offset'] for c in x['controls']] for x in (a2, b2)]}")
    record("std: 语义一致",
           er.compare_semantic_snapshots(er.dialog_semantic_snapshot(f_a),
                                         er.dialog_semantic_snapshot(a2)) == [])
    # 防回归断言 (1B2.0b): 字段改名 (cb_word→size_bytes) 不可能再次静默漏掉
    import hashlib as _h
    snap4 = er.dialog_semantic_snapshot(a2)
    payload4 = bytes([0x11, 0x22, 0x33, 0x44])
    record("std 快照字段绑定: creation_size_bytes == 6",
           snap4["controls"][0]["creation_size_bytes"] == 6)
    record("std 快照字段绑定: creation_data_len == 4 且 creation_data_sha256 == sha256(payload)",
           snap4["controls"][0]["creation"]["creation_data_len"] == 4
           and snap4["controls"][0]["creation"]["creation_data_sha256"]
           == _h.sha256(payload4).hexdigest())

    # ---- DIALOG-5: Extended 合成 fixture ----
    print("== TEST DIALOG-5: Extended 合成 fixture ==")
    g_a = ex_fixture("内容")
    ok_g, g2 = stable_roundtrip(g_a)
    record("ex: round-trip 稳定", ok_g)
    record("ex: helpID/exStyle/weight/italic/charset/extraCount=5 保真",
           er.compare_semantic_snapshots(er.dialog_semantic_snapshot(g_a),
                                         er.dialog_semantic_snapshot(g2)) == []
           and g2["controls"][1]["extra_count"] == 5
           and g2["controls"][1]["creation_data"] == bytes([0xDE, 0xAD, 0xBE, 0xEF, 0x01]))
    record("ex: 控件起始 offset 均 DWORD 对齐", offsets_aligned(g2))
    # 显式断言 (1B2.0b): EX 快照字段逐项绑定
    import hashlib as _h2
    snap5 = er.dialog_semantic_snapshot(g2)
    payload5 = bytes([0xDE, 0xAD, 0xBE, 0xEF, 0x01])
    record("ex 快照字段绑定: dlgVer==1 / signature==0xFFFF / dialog helpID==0x1234",
           snap5["dlgver"] == 1 and snap5["signature"] == 0xFFFF
           and snap5["helpid"] == 0x1234)
    record("ex 快照字段绑定: control helpID==0x5678 / extraCount==5 / "
           "creation_data_len==5 / creation_data_sha256==sha256(payload)",
           snap5["controls"][0]["helpid"] == 0x5678
           and snap5["controls"][1]["creation_extra_count"] == 5
           and snap5["controls"][1]["creation"]["extra_count"] == 5
           and snap5["controls"][1]["creation"]["creation_data_len"] == 5
           and snap5["controls"][1]["creation"]["creation_data_sha256"]
           == _h2.sha256(payload5).hexdigest())

    # ---- DIALOG-6: 语义验证器破坏检测 ----
    print("== TEST DIALOG-6: 字段破坏 → 语义验证器必须发现 ==")
    target_key = next(key for key in asts
                      if key[1] == 1033 and asts[key]["controls"])
    ast_orig = copy.deepcopy(asts[target_key])
    snap_orig = er.dialog_semantic_snapshot(ast_orig)
    blob_orig = er.serialize_dialog_ast(ast_orig)
    corrupted = copy.deepcopy(ast_orig)
    corrupted["title"]["value"] = (
        "X" + corrupted["title"]["value"][1:] if corrupted["title"]["value"] else "X")
    corrupted["controls"][0]["style"] = corrupted["controls"][0]["style"] ^ 0xFF
    ser_c = er.serialize_dialog_ast(corrupted)
    snap_c = er.dialog_semantic_snapshot(er.parse_dialog_ast(ser_c))
    diffs = er.compare_semantic_snapshots(snap_orig, snap_c)
    record(f"DIALOG-6 破坏字段被语义验证器发现 ({target_key[0]},{target_key[1]})",
           len(diffs) >= 2 and ser_c != blob_orig, f"diffs={diffs[:3]}")

    # ---- DIALOG-7: 对齐突变 (0→2 / 2→0, std+ex) ----
    print("== TEST DIALOG-7: 文本长度奇偶突变 → 对齐自动重建 ==")
    f_even = std_fixture("确定", {"size_bytes": 6, "data": bytes([0x11, 0x22, 0x33, 0x44])})
    f_odd = std_fixture("确", {"size_bytes": 6, "data": bytes([0x11, 0x22, 0x33, 0x44])})
    p_even = [len(c["pad_before"]) for c in er.parse_dialog_ast(
        er.serialize_dialog_ast(f_even))["controls"]]
    p_odd = [len(c["pad_before"]) for c in er.parse_dialog_ast(
        er.serialize_dialog_ast(f_odd))["controls"]]
    even_ast = er.parse_dialog_ast(er.serialize_dialog_ast(f_even))
    odd_ast = er.parse_dialog_ast(er.serialize_dialog_ast(f_odd))
    record("std 对齐突变: 全部控件 offset % 4 == 0",
           offsets_aligned(even_ast) and offsets_aligned(odd_ast),
           f"pads even={p_even} odd={p_odd}")
    record("std 覆盖 0-byte→2-byte 与 2-byte→0-byte",
           p_even[1] == 0 and p_odd[1] == 2,
           f"c2 pad: 偶长度标题 {p_even[1]} 字节 ↔ 奇长度标题 {p_odd[1]} 字节")
    g_even = ex_fixture("内容")
    g_odd = ex_fixture("内")
    q_even = [len(c["pad_before"]) for c in er.parse_dialog_ast(
        er.serialize_dialog_ast(g_even))["controls"]]
    q_odd = [len(c["pad_before"]) for c in er.parse_dialog_ast(
        er.serialize_dialog_ast(g_odd))["controls"]]
    g_even_ast = er.parse_dialog_ast(er.serialize_dialog_ast(g_even))
    g_odd_ast = er.parse_dialog_ast(er.serialize_dialog_ast(g_odd))
    record("ex 对齐突变: 全部控件 offset % 4 == 0",
           offsets_aligned(g_even_ast) and offsets_aligned(g_odd_ast),
           f"pads even={q_even} odd={q_odd}")
    record("ex 覆盖 0-byte→2-byte 与 2-byte→0-byte",
           q_even[1] == 0 and q_odd[1] == 2,
           f"c2 pad: 偶长度标题 {q_even[1]} 字节 ↔ 奇长度标题 {q_odd[1]} 字节")
    snap_even = er.dialog_semantic_snapshot(er.parse_dialog_ast(
        er.serialize_dialog_ast(f_even)))
    snap_odd_t = er.dialog_semantic_snapshot(er.parse_dialog_ast(
        er.serialize_dialog_ast(f_odd)))
    semantic_ok = True
    for a, b in zip(snap_even["controls"], snap_odd_t["controls"]):
        x = dict(a); y = dict(b)
        x.pop("title"); y.pop("title")
        if x != y:
            semantic_ok = False
    record("std 突变前后除 title/text 外语义字段未变化", semantic_ok)

    # ---- DIALOG-8: 语义破坏守卫 ----
    print("== TEST DIALOG-8: 语义破坏守卫 (必须全部 FAIL/拒绝) ==")
    base = copy.deepcopy(g_a)
    snap_base = er.dialog_semantic_snapshot(base)

    m1 = copy.deepcopy(base)
    m1["header"]["helpid"] = m1["header"]["helpid"] ^ 0x100
    record("DIALOG-8.1 dialog helpID 改 1 bit → 发现", mutation_detected(m1, snap_base))

    m2 = copy.deepcopy(base)
    m2["signature"] = 0xFFFE
    record("DIALOG-8.2 signature 改变 → 发现", mutation_detected(m2, snap_base))

    m3 = copy.deepcopy(base)
    m3["header"]["cdit"] = 5
    rejected = False
    try:
        er.serialize_dialog_ast(m3)
    except ValueError:
        rejected = True
    record("DIALOG-8.3 cDlgItems 与控件数不一致 → serializer 拒绝", rejected)

    m4 = copy.deepcopy(base)
    m4["controls"][0]["exstyle"] = m4["controls"][0]["exstyle"] ^ 0x1
    record("DIALOG-8.4 control exStyle 改变 → 发现", mutation_detected(m4, snap_base))

    m5 = copy.deepcopy(base)
    m5["controls"][1]["creation_data"] = bytes([0xDE, 0xAD, 0xBE, 0xEF, 0x02])
    record("DIALOG-8.5 creation data 同长度改 1 字节 → 发现",
           mutation_detected(m5, snap_base))

    m6 = copy.deepcopy(base)
    m6["controls"][1]["extra_count"] = 6
    rejected6 = False
    try:
        er.serialize_dialog_ast(m6)
    except ValueError:
        rejected6 = True
    record("DIALOG-8.6 extraCount 与 creation data 不一致 → serializer 拒绝", rejected6)

    ms = copy.deepcopy(f_a)
    ms["controls"][0]["creation_data"]["size_bytes"] = 5
    rejected_s = False
    try:
        er.serialize_dialog_ast(ms)
    except ValueError:
        rejected_s = True
    record("DIALOG-8.7 std size_bytes 与 payload 不一致 → serializer 拒绝", rejected_s)

    mt = copy.deepcopy(base)
    mt["trailing"] = b"\x01"
    record("DIALOG-8.8 trailing 不透明字节变化 → 发现", mutation_detected(mt, snap_base))

    record("DIALOG-8.8 trailing 不透明字节变化 → 发现", mutation_detected(mt, snap_base))

    # ---- DIALOG-9: 语义白名单 + allocation padding (PHASE 1B2.1a) ----
    print("== TEST DIALOG-9: dialog_semantic_diff 白名单 + allocation padding ==")
    key129 = next(key for key in asts if key[0] == 129 and key[1] == 1033)
    d_orig = copy.deepcopy(asts[key129])
    d_allowed = {
        "dialog_title": "目标",
        "control_titles": {
            0: " 要添加的目标(&T): ", 2: "添加(&A)",
            3: "从当前目标复制全部设置(&C)", 4: " 可用目标(&A): ",
            6: "设为当前目标(&S)", 7: "移除目标(&R)",
        },
    }
    d_patch = copy.deepcopy(d_orig)
    d_patch["title"]["value"] = "目标"
    for idx, zh in d_allowed["control_titles"].items():
        d_patch["controls"][idx]["title"]["value"] = zh
    logical = er.serialize_dialog_ast(d_patch)
    blob_size = len(blobs[key129])
    alloc_pad = blob_size - len(logical)
    record("DIALOG-9.1 逻辑尺寸 <= 原分配 ( Fits Original Allocation )",
           len(logical) <= blob_size, f"{len(logical)} <= {blob_size}, padding {alloc_pad}")
    patched_payload = logical + b"\x00" * alloc_pad
    d_re = er.parse_dialog_ast(patched_payload)
    record("DIALOG-9.2 资源尾部 = 纯 00 allocation padding 且长度精确",
           d_re.get("trailing", b"") == b"\x00" * alloc_pad
           and d_orig.get("trailing", b"") == b"")
    o = copy.deepcopy(d_orig); o["trailing"] = b""
    p2 = copy.deepcopy(d_re); p2["trailing"] = b""
    diffs_ok = er.dialog_semantic_diff(o, p2, d_allowed)
    record("DIALOG-9.3 白名单内变化 → 语义 diff 为空", not diffs_ok,
           f"diffs={diffs_ok[:3]}" if diffs_ok else "")
    # 非白名单变化必须被发现
    d_bad = copy.deepcopy(d_patch)
    d_bad["controls"][1]["style"] = d_bad["controls"][1]["style"] ^ 0xFF  # EDIT 未列入 manifest
    o = copy.deepcopy(d_orig); o["trailing"] = b""
    p3 = copy.deepcopy(d_bad); p3["trailing"] = b""
    diffs_bad = er.dialog_semantic_diff(o, p3, d_allowed)
    record("DIALOG-9.4 非 manifest 字段变化 (EDIT style) → 发现",
           any("控件 1" in d for d in diffs_bad), f"diffs={diffs_bad[:2]}")
    # 非 manifest 控件 title 变化必须被发现: 用 Dialog 100 的 'Copy Info'
    # (string title, 未列入 1B2.1a manifest —— About 对话框按规则仅译标题与 OK)
    key100 = next(key for key in asts if key[0] == 100 and key[1] == 1033)
    d100_orig = copy.deepcopy(asts[key100])
    d100_patch = copy.deepcopy(d100_orig)
    d100_patch["title"]["value"] = "关于 µVision"
    d100_patch["controls"][9]["title"]["value"] = "确定"
    d100_allowed = {"dialog_title": "关于 µVision",
                    "control_titles": {9: "确定"}}
    o100 = copy.deepcopy(d100_orig); o100["trailing"] = b""
    p100 = copy.deepcopy(d100_patch); p100["trailing"] = b""
    diffs100 = er.dialog_semantic_diff(o100, p100, d100_allowed)
    record("DIALOG-9.5a About 白名单 (title + OK) → 语义 diff 为空", not diffs100,
           f"diffs={diffs100[:3]}" if diffs100 else "")
    d_bad2 = copy.deepcopy(d100_patch)
    d_bad2["controls"][7]["title"]["value"] = "未授权文本"  # Copy Info 未列入 manifest
    p_bad2 = copy.deepcopy(d_bad2); p_bad2["trailing"] = b""
    o_bad2 = copy.deepcopy(d100_orig); o_bad2["trailing"] = b""
    diffs_bad2 = er.dialog_semantic_diff(o_bad2, p_bad2, d100_allowed)
    record("DIALOG-9.5 非 manifest 控件 title 变化 (Copy Info) → 发现",
           any("控件 7" in d for d in diffs_bad2), f"diffs={diffs_bad2[:2]}")
    d_bad3 = copy.deepcopy(d_patch)
    d_bad3["title"]["value"] = "错误的中文"
    o = copy.deepcopy(d_orig); o["trailing"] = b""
    p5 = copy.deepcopy(d_bad3); p5["trailing"] = b""
    diffs_bad3 = er.dialog_semantic_diff(o, p5, d_allowed)
    record("DIALOG-9.6 dialog title 与预期中文不一致 → 发现",
           any("title" in d for d in diffs_bad3), f"diffs={diffs_bad3[:2]}")
    # RESOURCE_TOO_LARGE 条件演示: 超长中文标题 → logical > 原分配
    d_big = copy.deepcopy(d_orig)
    d_big["title"]["value"] = "目" * 400
    big = er.serialize_dialog_ast(d_big)
    record("DIALOG-9.7 超长文本 → logical > 原分配 (RESOURCE_TOO_LARGE 条件可触发)",
           len(big) > blob_size, f"{len(big)} > {blob_size}")

    print("=" * 72)
    if all(results):
        print(f"自测结论: {len(results)}/{len(results)} 项全部通过")
        return 0
    print(f"自测结论: {results.count(False)}/{len(results)} 项失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
