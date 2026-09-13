#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
apply_translation.py — 官方原版 UV4.exe + 翻译数据库 → 本地汉化测试版 (UV4_CN_*_TEST.exe)

PHASE 1B1 支持: RT_STRING + RT_MENU。

流程（满足 GPT 审核强制要求）:
    0. 输入文件 SHA256 必须 == 固定 baseline (docs/BASELINE.md);
    1. 从 ORIGINAL 资源树解析目标 (BlockID/MenuID, LANGID) → payload 范围,
       绝不信任 CSV/manifest 中人为记录的 file_offset;
    2. 【菜单门禁】修改任何 RT_MENU 文本前, 必须全部 RT_MENU
       parse → serialize → byte-identical (40/40), 任一失败 → STOP;
    3. 逐条校验: 实际文本 == CSV Original; printf token 逐个一致;
       \t 后快捷键文本逐字一致; 助记键规则 (&&/悬空&/数量/字母变更须记录);
       同一弹出层不得引入新的助记键冲突;
    4. 写入 = 整资源重序列化 (RT_STRING 16 条契约 / RT_MENU version 0 模板),
       new_blob <= 原分配 (否则 RESOURCE_TOO_LARGE), 变短只在整块末尾补 0;
    5. 语义验证:
       - RT_STRING: 资源树布局不变; 每块 16 条; 目标 == Chinese;
         同块未列入条目与原版一致; 非目标资源逐字节一致;
       - RT_MENU: patched 重新解析后与 ORIGINAL 逐节点比较
         command ID / flags / popup 性 / 树形 / item 数量 / header offset 全部一致,
         只有 manifest 指定路径的 text 允许变化 (且必须 == Chinese);
    6. 输出 exe + manifest (供 verify.py --manifest 做载荷白名单审计)。

红线: 不覆盖正式 UV4.exe; 不运行产物; 不触碰 .text/.rdata/.data/.reloc/头部/
证书表/RT_DIALOG/RT_240/LANGID 9/1031/0x2000/1041。
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_resources as er    # noqa: E402
import verify                     # noqa: E402
import text_validators as tv      # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# docs/BASELINE.md 固化基线: µVision 5.43.1.0 官方原版
BASELINE_SHA256 = "428baf13d15e6760af1618def9c9815c97f0321cc5e459ec7adc4dde41c42f89"

DEFAULT_ORIGINAL = "backup/UV4_5.43.1.0_ORIGINAL.exe"
DEFAULT_CSV = "translations/keil_translation.csv"
DEFAULT_OUTPUT = "output/UV4_CN_1B1_TEST.exe"
DEFAULT_MANIFEST = "output/uv4_cn_1b1_manifest.json"


class ApplyError(Exception):
    """任何校验失败都以此异常中止, 不产出任何输出文件。"""


def fail(msg: str):
    raise ApplyError(msg)


def resources_index(pe: er.PEFile):
    """(type_name, resource_id, lang) -> (file_offset, size), 仅数值 ID 资源。"""
    index = {}
    for r in er.flatten_resources(pe):
        if r["file_offset"] and r["name_kind"] == "id":
            index[(r["type_name"], r["name"], r["lang"])] = (r["file_offset"], r["size"])
    return index


def menu_roundtrip_gate(pe: er.PEFile, data: bytes) -> int:
    """全部 RT_MENU parse→serialize→byte-identical; 任一失败 → STOP。"""
    total, bad = 0, []
    for r in er.flatten_resources(pe):
        if r["type_name"] == "RT_MENU" and r["file_offset"]:
            total += 1
            blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
            if er.serialize_menu_template(er.parse_menu_template(blob)) != blob:
                bad.append((r["name"], r["lang"]))
    if bad:
        fail(f"RT_MENU round-trip 门禁失败 {len(bad)}/{total}: {bad[:8]} — STOP, 不生成汉化菜单")
    return total


def parse_item_ref(ref: str):
    """MENU ItemRef '0/2/5' → 路径 [0, 2, 5]。"""
    try:
        path = [int(x) for x in str(ref).strip().split("/")]
    except ValueError:
        fail(f"MENU ItemRef 格式非法: {ref!r}")
    if not path or any(i < 0 for i in path):
        fail(f"MENU ItemRef 格式非法: {ref!r}")
    return path


def resolve_menu_path(items, path):
    """按路径取出菜单项 (不弹层, 只定位节点)。"""
    cur = items
    for depth, i in enumerate(path):
        if i >= len(cur):
            fail(f"菜单路径越界: {'/'.join(map(str, path))} (深度 {depth} 只有 {len(cur)} 项)")
        node = cur[i]
        if depth == len(path) - 1:
            return node
        if not (node["flags"] & 0x10) or not node.get("children"):
            fail(f"菜单路径穿越了非弹出项: {'/'.join(map(str, path))}")
        cur = node["children"]
    fail("空菜单路径")


def load_translation_csv(path: Path):
    required = {"ResourceType", "ResourceID", "ItemRef", "LANGID",
                "Original", "Chinese", "Status"}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = required - set(reader.fieldnames or [])
        if missing:
            fail(f"CSV 缺少必需列: {sorted(missing)} (需要 ItemRef 列: STRING=StringID, MENU=路径)")
        rows = list(reader)
    entries, skipped = [], 0
    for r in rows:
        if (r.get("Status") or "").strip().upper() != "DONE":
            continue
        rtype = (r.get("ResourceType") or "").strip().upper()
        if rtype not in ("STRING", "MENU", "DIALOG"):
            skipped += 1
            continue
        entry = {
            "res_type": rtype,
            "res_id": int(r["ResourceID"]),
            "lang": int(r["LANGID"]),
            "original": r["Original"],
            "chinese": r["Chinese"],
            "notes": r.get("Notes") or "",
        }
        if not entry["chinese"]:
            fail(f"Chinese 为空: {rtype} {entry['res_id']} {r.get('ItemRef')}")
        if rtype == "STRING":
            entry["string_id"] = int(r["ItemRef"])
            if entry["res_id"] != entry["string_id"] // 16 + 1:
                fail(f"CSV 行 ResourceID 与 StringID 不自洽: {entry}")
        elif rtype == "MENU":
            entry["item_path"] = parse_item_ref(r["ItemRef"])
        else:  # DIALOG
            ref = (r.get("ItemRef") or "").strip()
            if ref == "title":
                entry["field"] = "dialog_title"
            elif ref.startswith("ctl:"):
                entry["field"] = "control_title"
                entry["control_index"] = int(ref.split(":", 1)[1])
                ctl_id = (r.get("CtlID") or "").strip()
                ctl_cls = (r.get("CtlClass") or "").strip()
                if not ctl_id or not ctl_cls:
                    fail(f"DIALOG 控件行缺少 CtlID/CtlClass 交叉校验列: {entry}")
                entry["control_id"] = int(ctl_id)
                entry["control_class"] = ctl_cls
            else:
                fail(f"DIALOG ItemRef 非法 (须为 title 或 ctl:<index>): {ref!r}")
        entries.append(entry)
    return entries, skipped


def menu_semantic_diff(orig_items, patched_items, expected_texts, base_path=""):
    """递归比较两棵菜单树: flags / command id / popup 性 / 层级 / 数量必须一致;
    text 只允许在 expected_texts 指定路径上变化 (且必须等于预期中文)。"""
    problems = []
    if len(orig_items) != len(patched_items):
        return [f"{base_path or '/'}: item 数量变化 {len(orig_items)} → {len(patched_items)}"]
    for i, (a, b) in enumerate(zip(orig_items, patched_items)):
        p = f"{base_path}/{i}" if base_path else str(i)
        if a["flags"] != b["flags"]:
            problems.append(f"{p}: flags 变化 {a['flags_hex']} → {b['flags_hex']}")
        if a["id"] != b["id"]:
            problems.append(f"{p}: command ID 变化 {a['id']} → {b['id']}")
        if bool(a["flags"] & 0x10) != bool(b["flags"] & 0x10):
            problems.append(f"{p}: MF_POPUP 属性变化")
        if p in expected_texts:
            if b["text"] != expected_texts[p]:
                problems.append(f"{p}: 目标文本 != 预期中文 ({b['text']!r})")
        elif a["text"] != b["text"]:
            problems.append(f"{p}: 非目标条目文本变化 {a['text']!r} → {b['text']!r}")
        problems += menu_semantic_diff(a["children"] or [], b["children"] or [],
                                       expected_texts, p)
    return problems


def menu_sibling_conflicts(items):
    """收集每层兄弟项的助记键冲突: {层路径: 冲突字母集}。"""
    out = {}

    def walk(nodes, base):
        texts = [n["text"] or "" for n in nodes if not (n["flags"] & 0x800)]  # 忽略分隔符
        conf = tv.sibling_mnemonic_conflicts(texts)
        if conf:
            out[base or "/"] = conf
        for i, n in enumerate(nodes):
            if n.get("children"):
                walk(n["children"], f"{base}/{i}" if base else str(i))

    walk(items, "")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="PHASE 1B1 翻译写入器 (RT_STRING + RT_MENU)")
    ap.add_argument("--original", default=DEFAULT_ORIGINAL)
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--output", default=DEFAULT_OUTPUT)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    args = ap.parse_args(argv)

    original_path = Path(args.original)
    print("=" * 72)
    print("PHASE 1B1: 应用 RT_STRING + RT_MENU 翻译")
    print(f"  原版   : {original_path}")
    print(f"  翻译库 : {args.csv}")
    print(f"  输出   : {args.output}")
    print("-" * 72)

    # ---- 0. 基线校验 ----
    data = original_path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"  输入 SHA256: {sha}")
    if sha != BASELINE_SHA256:
        fail("输入文件 SHA256 与固定 baseline 不一致 — 拒绝执行 "
             "(版本不匹配, 必须重新走 PHASE 0 提取/分析流程)")
    pe = er.PEFile(data)
    index = resources_index(pe)
    print(f"  基线校验: 通过")

    # ---- 1. 翻译库 ----
    entries, skipped = load_translation_csv(Path(args.csv))
    str_entries = [e for e in entries if e["res_type"] == "STRING"]
    menu_entries = [e for e in entries if e["res_type"] == "MENU"]
    print(f"  有效条目: STRING {len(str_entries)} 条 + MENU {len(menu_entries)} 条 "
          f"(跳过其他类型/非 DONE: {skipped})")

    # ---- 2. 菜单门禁: 40/40 round-trip ----
    if menu_entries:
        total = menu_roundtrip_gate(pe, data)
        print(f"  RT_MENU round-trip 门禁: {total}/{total} byte-identical ✓")

    patched = bytearray(data)
    modified = []          # (type_name, res_id, lang)
    targets_for_manifest = {}

    # ---- 3. RT_STRING 写入 ----
    grouped_str = {}
    for e in str_entries:
        grouped_str.setdefault((e["res_id"], e["lang"]), []).append(e)
    missing = [k for k in grouped_str if ("RT_STRING", k[0], k[1]) not in index]
    if missing:
        fail(f"翻译表引用了不存在的 RT_STRING 块: {missing} (禁止创建不存在的资源)")

    str_original_texts = {}
    for (block_id, lang) in sorted(grouped_str):
        off, size = index[("RT_STRING", block_id, lang)]
        blob = bytes(patched[off: off + size])
        strings = er.parse_string_table(blob)
        str_original_texts[(block_id, lang)] = list(strings)
        for e in grouped_str[(block_id, lang)]:
            idx = e["string_id"] - (block_id - 1) * 16
            if not (0 <= idx < 16):
                fail(f"StringID {e['string_id']} 超出块 {block_id} 范围")
            if strings[idx] != e["original"]:
                fail(f"Original 不一致: block={block_id} StringID={e['string_id']} "
                     f"CSV={e['original']!r} 实际={strings[idx]!r}")
            problems = tv.check_entry(e["original"], e["chinese"], e["notes"])
            if problems:
                fail(f"机械校验失败 StringID={e['string_id']}: {problems}")
            strings[idx] = e["chinese"]
        new_blob = er.serialize_string_table(strings)      # 强制 16 条
        if len(new_blob) > size:
            fail(f"RESOURCE_TOO_LARGE: RT_STRING block={block_id} lang={lang} "
                 f"{len(new_blob)} > {size} — 拒绝生成")
        patched[off: off + size] = new_blob + b"\x00" * (size - len(new_blob))
        modified.append(("RT_STRING", block_id, lang))
        targets_for_manifest[("RT_STRING", block_id, lang)] = \
            sorted(str(e["string_id"]) for e in grouped_str[(block_id, lang)])
        print(f"  写回 RT_STRING block={block_id:<5} lang={lang} "
              f"({size} → {len(new_blob)} 字节) StringID={targets_for_manifest[('RT_STRING', block_id, lang)]}")

    # ---- 4. RT_MENU 写入 ----
    grouped_menu = {}
    for e in menu_entries:
        grouped_menu.setdefault((e["res_id"], e["lang"]), []).append(e)
    missing = [k for k in grouped_menu if ("RT_MENU", k[0], k[1]) not in index]
    if missing:
        fail(f"翻译表引用了不存在的 RT_MENU 资源: {missing}")

    menu_expected_texts = {}
    menu_before_texts = {}
    for (rid, lang) in sorted(grouped_menu):
        off, size = index[("RT_MENU", rid, lang)]
        parsed = er.parse_menu_template(bytes(patched[off: off + size]))
        expected = {}
        rows_by_path = {}
        for e in grouped_menu[(rid, lang)]:
            path_key = "/".join(map(str, e["item_path"]))
            node = resolve_menu_path(parsed["items"], e["item_path"])
            if node["flags"] & 0x800:
                fail(f"MENU {rid} {path_key}: 不允许翻译分隔符")
            if node["text"] != e["original"]:
                fail(f"Original 不一致: MENU={rid} 路径={path_key} "
                     f"CSV={e['original']!r} 实际={node['text']!r}")
            problems = tv.check_entry(e["original"], e["chinese"], e["notes"])
            if problems:
                fail(f"机械校验失败 MENU={rid} 路径={path_key}: {problems}")
            expected[path_key] = e["chinese"]
            rows_by_path[path_key] = e
        conflicts_before = menu_sibling_conflicts(parsed["items"])
        for path_key, e in rows_by_path.items():
            node = resolve_menu_path(parsed["items"], e["item_path"])
            node["text"] = e["chinese"]
        conflicts_after = menu_sibling_conflicts(parsed["items"])
        new_conflicts = {k: v for k, v in conflicts_after.items()
                         if v - conflicts_before.get(k, set())}
        if new_conflicts:
            fail(f"MENU={rid} 引入新的同级助记键冲突: {new_conflicts}")
        new_blob = er.serialize_menu_template(parsed)      # 仅 version 0, 结构由解析结果决定
        if len(new_blob) > size:
            fail(f"RESOURCE_TOO_LARGE: RT_MENU id={rid} lang={lang} "
                 f"{len(new_blob)} > {size} — 拒绝生成")
        patched[off: off + size] = new_blob + b"\x00" * (size - len(new_blob))
        modified.append(("RT_MENU", rid, lang))
        menu_expected_texts[(rid, lang)] = expected
        menu_before_texts[(rid, lang)] = conflicts_before
        targets_for_manifest[("RT_MENU", rid, lang)] = sorted(expected)
        print(f"  写回 RT_MENU id={rid:<6} lang={lang} ({size} → {len(new_blob)} 字节) "
              f"路径={sorted(expected)}")

    # ---- 3.5 RT_DIALOG 写入 (PHASE 1B2.1a: 仅 Dialog title / BUTTON·STATIC string title) ----
    dlg_entries = [e for e in entries if e["res_type"] == "DIALOG"]
    grouped_dlg = {}
    for e in dlg_entries:
        grouped_dlg.setdefault((e["res_id"], e["lang"]), []).append(e)
    missing = [k for k in grouped_dlg if ("RT_DIALOG", k[0], k[1]) not in index]
    if missing:
        fail(f"翻译表引用了不存在的 RT_DIALOG 资源: {missing}")
    dialog_mods = []
    for (rid, lang) in sorted(grouped_dlg):
        off, size = index[("RT_DIALOG", rid, lang)]
        ast = er.parse_dialog_ast(bytes(patched[off: off + size]))
        orig_ast_copy = copy.deepcopy(ast)
        if ast.get("trailing", b"") != b"":
            fail(f"RT_DIALOG {rid}: 原版 logical trailing 非空, 不符合 246 全量基线")
        allowed = {"dialog_title": None, "control_titles": {}}
        for e in sorted(grouped_dlg[(rid, lang)], key=lambda x: x["field"]):
            if e["field"] == "dialog_title":
                if ast["title"]["kind"] != "string":
                    fail(f"RT_DIALOG {rid}: dialog title 非 string, 禁止修改")
                if ast["title"]["value"] != e["original"]:
                    fail(f"Original 不一致: RT_DIALOG {rid} title CSV={e['original']!r} "
                         f"实际={ast['title']['value']!r}")
                problems = tv.check_entry(e["original"], e["chinese"], e["notes"])
                if problems:
                    fail(f"机械校验失败 RT_DIALOG {rid} title: {problems}")
                allowed["dialog_title"] = e["chinese"]
                ast["title"]["value"] = e["chinese"]
            else:
                idx = e["control_index"]
                if idx >= len(ast["controls"]):
                    fail(f"RT_DIALOG {rid}: control_index {idx} 越界")
                c = ast["controls"][idx]
                cls_disp = c["window_class"]["display"]
                if c["id"] != e["control_id"]:
                    fail(f"locator 交叉校验失败: RT_DIALOG {rid} 控件 {idx} "
                         f"实际 id={c['id']} != manifest {e['control_id']}")
                if cls_disp != e["control_class"]:
                    fail(f"locator 交叉校验失败: RT_DIALOG {rid} 控件 {idx} "
                         f"实际 class={cls_disp!r} != manifest {e['control_class']!r}")
                if c["title"]["kind"] != "string":
                    fail(f"RT_DIALOG {rid} 控件 {idx}: title 非 string (ordinal title 禁改)")
                if cls_disp not in ("BUTTON", "STATIC"):
                    fail(f"RT_DIALOG {rid} 控件 {idx}: 首轮仅允许 BUTTON/STATIC, "
                         f"实际 {cls_disp}")
                if c["title"]["value"] != e["original"]:
                    fail(f"Original 不一致: RT_DIALOG {rid} 控件 {idx} "
                         f"CSV={e['original']!r} 实际={c['title']['value']!r}")
                problems = tv.check_entry(e["original"], e["chinese"], e["notes"])
                if problems:
                    fail(f"机械校验失败 RT_DIALOG {rid} 控件 {idx}: {problems}")
                c["title"]["value"] = e["chinese"]
                allowed["control_titles"][idx] = e["chinese"]
        logical = er.serialize_dialog_ast(ast)
        if len(logical) > size:
            fail(f"RESOURCE_TOO_LARGE: RT_DIALOG {rid} lang={lang} "
                 f"logical {len(logical)} 字节 > 原分配 {size} 字节 - 拒绝生成")
        alloc_pad = size - len(logical)
        patched[off: off + size] = logical + b"\x00" * alloc_pad
        modified.append(("RT_DIALOG", rid, lang))
        targets_for_manifest[("RT_DIALOG", rid, lang)] = sorted(
            ("title" if e["field"] == "dialog_title"
             else f"ctl:{e['control_index']}") for e in grouped_dlg[(rid, lang)])
        dialog_mods.append({"rid": rid, "lang": lang, "off": off, "size": size,
                            "orig_ast": orig_ast_copy, "allowed": allowed,
                            "alloc_pad": alloc_pad, "logical_len": len(logical),
                            "kind": ast["kind"]})
        print(f"  写回 RT_DIALOG id={rid:<6} lang={lang} ({size} -> {len(logical)} 字节, "
              f"allocation padding {alloc_pad}) 路径={targets_for_manifest[('RT_DIALOG', rid, lang)]}")

    # ---- 5. 语义验证 ----
    print("-" * 72)
    print("语义验证:")
    patched_pe = er.PEFile(bytes(patched))
    index2 = resources_index(patched_pe)
    if index2 != index:
        fail("资源树布局发生变化 (块偏移/大小/清单不一致) — FAIL")
    print("  ✓ 资源树布局不变 (所有资源偏移/大小/清单完全一致)")

    for (block_id, lang), rows in sorted(grouped_str.items()):
        off, size = index[("RT_STRING", block_id, lang)]
        strings2 = er.parse_string_table(bytes(patched[off: off + size]))
        if len(strings2) != 16:
            fail(f"RT_STRING block={block_id} 验证时条目数 != 16")
        before = str_original_texts[(block_id, lang)]
        target_idx = {e["string_id"] - (block_id - 1) * 16: e["chinese"]
                      for e in rows}
        for i in range(16):
            want = target_idx.get(i)
            if want is not None:
                if strings2[i] != want:
                    fail(f"RT_STRING 目标 StringID {(block_id - 1) * 16 + i} 未正确写入")
            elif strings2[i] != before[i]:
                fail(f"RT_STRING block={block_id} 未列入条目 {i} 发生变化")
    if grouped_str:
        print("  ✓ RT_STRING: 目标 == Chinese; 同块非目标条目与原版一致")

    for (rid, lang), rows in sorted(grouped_menu.items()):
        off, size = index[("RT_MENU", rid, lang)]
        orig_parsed = er.parse_menu_template(data[off: off + size])
        patched_parsed = er.parse_menu_template(bytes(patched[off: off + size]))
        expected = menu_expected_texts[(rid, lang)]
        problems = menu_semantic_diff(orig_parsed["items"], patched_parsed["items"], expected)
        if problems:
            fail(f"MENU={rid} 语义验证失败: {problems[:6]}")
        if patched_parsed.get("header_offset") != orig_parsed.get("header_offset"):
            fail(f"MENU={rid} header_offset 变化")
        conflicts_before = menu_before_texts[(rid, lang)]
        conflicts_after = menu_sibling_conflicts(patched_parsed["items"])
        new_conflicts = {k: v for k, v in conflicts_after.items()
                         if v - conflicts_before.get(k, set())}
        if new_conflicts:
            fail(f"MENU={rid} 验证时发现新的同级助记键冲突: {new_conflicts}")
    if grouped_menu:
        print("  ✓ RT_MENU: command ID / flags / 树形 / 数量 / header_offset 不变; "
              "仅目标路径文本变化; 无新同级助记键冲突")

    for dm in dialog_mods:
        ast2 = er.parse_dialog_ast(bytes(patched[dm["off"]: dm["off"] + dm["size"]]))
        expected_pad = b"\x00" * dm["alloc_pad"]
        if ast2.get("trailing", b"") != expected_pad:
            fail(f"RT_DIALOG {dm['rid']} 资源尾部不是预期长度/内容的纯 00 allocation padding")
        o = copy.deepcopy(dm["orig_ast"]); o["trailing"] = b""
        p2 = copy.deepcopy(ast2); p2["trailing"] = b""
        problems = er.dialog_semantic_diff(o, p2, dm["allowed"])
        if problems:
            fail(f"RT_DIALOG {dm['rid']} 语义验证失败: {problems[:6]}")
    if dialog_mods:
        print("  ✓ RT_DIALOG: 仅 manifest 指定 title 路径变化; "
              "style/exStyle/rect/ID/class/font/helpID/creation data 全部一致; "
              "资源尾部仅含机械生成的 00 allocation padding")

    modified_keys = set(modified)
    for r in er.flatten_resources(pe):
        off, size = r["file_offset"], r["size"]
        if off is None:
            continue
        if (r["type_name"], r["name"], r["lang"]) in modified_keys:
            continue
        if patched[off: off + size] != data[off: off + size]:
            fail(f"非目标资源发生变化: {(r['type_name'], r['name'], r['lang'])} — FAIL")
    print("  ✓ 所有非目标 resource payload 与原版逐字节一致")

    audit = verify.audit_bytes(data, bytes(patched))
    allowed = [{"resource_type": t, "resource_id": i, "lang": l,
                "start": index[(t, i, l)][0], "end": index[(t, i, l)][0] + index[(t, i, l)][1]}
               for t, i, l in sorted(modified_keys)]
    non_target = 0
    for s, e in audit["ranges"]:
        covered = sum(max(0, min(e, al["end"]) - max(s, al["start"])) for al in allowed)
        non_target += (e - s) - covered
    if non_target:
        fail(f"存在允许载荷之外的字节变化: {non_target} 字节 — FAIL")
    print(f"  ✓ changed_byte_count={audit['changed_byte_count']}, "
          f"changed_ranges={len(audit['ranges'])}, 全部 ⊆ 目标资源载荷")

    # ---- 6. 产出 ----
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(patched)
    patched_sha = hashlib.sha256(patched).hexdigest()
    manifest = {
        "version": 2,
        "generator": "apply_translation.py (PHASE 1B1)",
        "baseline": "docs/BASELINE.md — µVision 5.43.1.0",
        "original_sha256": sha,
        "patched_sha256": patched_sha,
        "targets": [{"resource_type": t, "resource_id": i, "lang": l,
                     "item_refs": targets_for_manifest[(t, i, l)]}
                    for t, i, l in sorted(modified_keys)],
    }
    Path(args.manifest).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print("-" * 72)
    print(f"已写出: {out_path}")
    print(f"        SHA256 = {patched_sha}")
    print(f"已写出: {args.manifest}")
    print("注意: 未经 GPT 审核与用户确认, 不要运行该测试版, 更不要覆盖正式 UV4.exe。")
    print("=" * 72)
    return verify.EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApplyError as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        sys.exit(verify.EXIT_FAIL)
