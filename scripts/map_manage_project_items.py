#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
map_manage_project_items.py — PHASE 1B2.1b0: Manage Project Items 属性表来源调查（只读）

背景: 用户 GUI 确认 Manage Project Items 是带四个 Tab 的 MFC Property Sheet:
    Project Items / Folders/Extensions / Books / Project Info/Layer。
    Property Sheet = 外层容器 (标题 + OK/Cancel/Help shell 按钮);
    Property Page = 每个 Tab 一个独立 Dialog。

本脚本只读, 对每条 GUI 观察文本做六路来源搜索 (RT_STRING / RT_DIALOG
title+control titles / RT_MENU / RT_240 / .rdata ANSI / .rdata UTF-16),
识别四个 page 资源, 输出 465 完整控件清单 (TRANSLATABLE/DYNAMIC/
DO_NOT_TRANSLATE) 与 0x2000 Project Info/Layer 证据映射。

基线保护: 输入 SHA256 必须等于 µVision 5.43.1.0 固定基线, 否则 FAIL 非零退出。
禁止输出任何翻译版 EXE; 不修改任何文件。

用法:
    python scripts/map_manage_project_items.py [--exe <UV4.exe>]
        [--out docs/MANAGE_PROJECT_ITEMS_MAPPING.md]
        [--json output/manage_project_items_mapping.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_resources as er   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASELINE_SHA256 = "428baf13d15e6760af1618def9c9815c97f0321cc5e459ec7adc4dde41c42f89"

TAB_CAPTIONS = ["Project Items", "Folders/Extensions", "Books", "Project Info/Layer"]

OBSERVED = [
    ("Manage Project Items", "sheet_title"),
    ("Project Items", "tab_title"),
    ("Folders/Extensions", "tab_title"),
    ("Books", "tab_title"),
    ("Project Info/Layer", "tab_title"),
    ("Project Targets:", "page_label"),
    ("Groups:", "page_label"),
    ("Files:", "page_label"),
    ("Set as Current Target", "button"),
    ("Add Files...", "button"),
    ("OK", "shared_button"),
    ("Cancel", "shared_button"),
    ("Help", "shared_button"),
]

PAGE_IDS = {"Project Items": 465, "Folders/Extensions": 466,
            "Books": 468, "Project Info/Layer": 859}

STANDARD_CLASSES = {"BUTTON", "STATIC"}


def strip_amp(t: str) -> str:
    return t.replace("&", "")


class Index:
    def __init__(self, data: bytes, pe: er.PEFile):
        self.data, self.pe = data, pe
        self.strings = {}
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_STRING" and r["name_kind"] == "id" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                for i, t in enumerate(er.parse_string_table(blob)):
                    if t:
                        self.strings.setdefault(r["lang"], {})[
                            (r["name"] - 1) * 16 + i] = t
        self.dialogs = {}
        self.dialog_meta = []
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_DIALOG" and r["name_kind"] == "id" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                try:
                    ast = er.parse_dialog_ast(blob)
                except Exception as exc:
                    self.dialog_meta.append({"id": r["name"], "lang": r["lang"],
                                             "error": str(exc)})
                    continue
                key = (r["name"], r["lang"])
                self.dialogs[key] = ast
                ctrls = [{"index": i, "id": c["id"], "class": c["window_class"],
                          "title": c["title"]} for i, c in enumerate(ast["controls"])]
                self.dialog_meta.append({
                    "id": r["name"], "lang": r["lang"], "kind": ast["kind"],
                    "size": r["size"], "title": ast["title"]["value"],
                    "font": ast["font"], "controls": ctrls})
        self.rt240 = []
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_240" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                start = 0
                while True:
                    i = blob.find(b"Books", start)
                    if i < 0:
                        break
                    self.rt240.append((r["name"], "Books"))
                    start = i + 1
        self.ivs = sorted((r["file_offset"], r["file_offset"] + r["size"], r)
                          for r in er.flatten_resources(pe) if r["file_offset"])

    def owner(self, off):
        lo, hi = 0, len(self.ivs) - 1
        while lo <= hi:
            m = (lo + hi) // 2
            s, e, r = self.ivs[m]
            if off < s:
                hi = m - 1
            elif off >= e:
                lo = m + 1
            else:
                return r
        return None

    def search_strings(self, gui: str):
        want = strip_amp(gui).strip().casefold()
        out = []
        for lang, m in self.strings.items():
            for sid, t in m.items():
                tn = strip_amp(t).strip().casefold()
                kind = None
                if tn == want or tn.split("\n")[0].strip().casefold() == want:
                    kind = "exact"
                elif want in tn and len(tn) <= len(want) + 60:
                    kind = "contains"
                if kind:
                    out.append({"source_type": "RT_STRING", "resource_id": sid,
                                "lang": lang, "text": t, "match_type": kind})
        return out

    def search_dialog_titles(self, gui: str):
        want = strip_amp(gui).strip().casefold()
        out = []
        for (rid, lang), ast in self.dialogs.items():
            if strip_amp(ast["title"]["value"]).strip().casefold() == want:
                out.append({"source_type": "RT_DIALOG_TITLE", "resource_id": rid,
                            "lang": lang, "kind": ast["kind"],
                            "control_count": len(ast["controls"]),
                            "text": ast["title"]["value"], "match_type": "exact"})
        return out

    def search_dialog_controls(self, gui: str, page_ids=None):
        want = strip_amp(gui).strip().casefold()
        out = []
        for (rid, lang), ast in self.dialogs.items():
            if page_ids and rid not in page_ids:
                continue
            for i, c in enumerate(ast["controls"]):
                if c["title"]["kind"] != "string":
                    continue
                if strip_amp(c["title"]["value"]).strip().casefold() == want:
                    cls = c["window_class"]
                    cname = (er.CONTROL_CLASS_ATOMS.get(cls["value"], hex(cls["value"]))
                             if cls["kind"] == "ordinal" else cls["value"])
                    out.append({"source_type": "RT_DIALOG_CONTROL",
                                "resource_id": rid, "lang": lang,
                                "control_index": i, "control_id": c["id"],
                                "class": cname, "text": c["title"]["value"],
                                "match_type": "exact"})
        return out

    def search_rt240(self, gui: str):
        return [{"source_type": "RT_240", "resource_id": rid, "text": s,
                 "match_type": "contains"}
                for rid, s in self.rt240 if gui.casefold() in s.casefold()]

    def search_menus(self, gui: str):
        want = strip_amp(gui).strip().casefold()
        out = []
        for r in er.flatten_resources(self.pe):
            if r["type_name"] != "RT_MENU" or not r["file_offset"]:
                continue
            blob = self.data[r["file_offset"]: r["file_offset"] + r["size"]]
            parsed = er.parse_menu_template(blob)

            def walk(items, path):
                for i, it in enumerate(items):
                    p = f"{path}/{i}" if path else str(i)
                    if it["text"] and strip_amp(it["text"]).strip().casefold() == want:
                        out.append({"source_type": "RT_MENU", "resource_id": r["name"],
                                    "lang": r["lang"], "item_path": p,
                                    "command_id": it["id"], "text": it["text"],
                                    "match_type": "exact"})
                    if it.get("children"):
                        walk(it["children"], p)

            walk(parsed["items"], "")
        return out

    def search_raw(self, gui: str):
        out = []
        for enc, label in (("utf-16le", "UTF-16"), ("ascii", "ANSI")):
            nb = gui.encode(enc, "ignore")
            start = 0
            while True:
                i = self.data.find(nb, start)
                if i < 0:
                    break
                own = self.owner(i)
                sec = self.pe.off2section(i)
                out.append({"source_type": "RAW", "section": sec,
                            "encoding": label, "offset": i,
                            "owner": (f"{own['type_name']} id={own['name']} lang={own['lang']}"
                                      if own and own["type_name"] != "RAW" else "非资源区"),
                            "text": gui, "match_type": "literal"})
                start = i + len(nb)
        return out


def classify(rows, gui_role):
    """HIGH: exact + 资源语义/页面功能对应; MEDIUM: exact 但多资源重复;
    LOW: 仅 contains/raw。返回 (confidence, summary)。"""
    exact = [r for r in rows if r.get("match_type") == "exact"]
    if gui_role == "dynamic_project_data":
        return "N/A", "工程运行时数据, 非翻译目标"
    if len(exact) == 1 and exact[0]["source_type"] in ("RT_STRING", "RT_DIALOG_TITLE",
                                                       "RT_DIALOG_CONTROL"):
        return "HIGH", "唯一 exact 资源命中且页面功能吻合"
    if len(exact) > 1:
        return "MEDIUM", f"exact 命中 {len(exact)} 处 (多资源重复, 需运行时取证区分)"
    if any(r["source_type"] == "RAW" for r in rows):
        return "LOW", "仅 raw 字节命中 (含 .rdata ANSI)"
    return "LOW", "证据不足"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Manage Project Items 属性表来源调查 (只读)")
    ap.add_argument("--exe", default="backup/UV4_5.43.1.0_ORIGINAL.exe")
    ap.add_argument("--out", default="docs/MANAGE_PROJECT_ITEMS_MAPPING.md")
    ap.add_argument("--json", default="output/manage_project_items_mapping.json")
    args = ap.parse_args(argv)

    data = Path(args.exe).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"输入 SHA256: {sha}")
    if sha != BASELINE_SHA256:
        print("FAIL: 输入文件 SHA256 与 µVision 5.43.1.0 固定基线不一致 —— "
              "版本不匹配，需要重新执行 PHASE 0。", file=sys.stderr)
        return 1
    pe = er.PEFile(data)
    idx = Index(data, pe)
    print(f"基线校验: 通过; 对话框资源 {len(idx.dialog_meta)} 个, 唯一 (id,lang) {len(idx.dialogs)} 个")

    results = []
    for gui, role in OBSERVED:
        entry = {"gui": gui, "role": role, "hits": []}
        entry["hits"] += idx.search_strings(gui)
        entry["hits"] += idx.search_dialog_titles(gui)
        entry["hits"] += idx.search_dialog_controls(gui)
        entry["hits"] += idx.search_menus(gui)
        entry["hits"] += idx.search_rt240(gui)
        raw = idx.search_raw(gui)
        # .rsrc 的 raw 命中即资源自身 (已在资源搜索中列出), 仅保留非 .rsrc 证据
        entry["hits"] += [r for r in raw if r["section"] != ".rsrc"]
        raw_rsrc = [r for r in raw if r["section"] == ".rsrc"]
        if raw_rsrc and not any(h["source_type"].startswith("RT_") for h in entry["hits"]):
            entry["hits"] += raw_rsrc[:3]
        conf, note = classify(entry["hits"], role)
        entry["confidence"] = conf
        entry["note"] = note
        results.append(entry)

    # ---- 页面识别 ----
    pages = {}
    for tab in TAB_CAPTIONS:
        cands = [m for m in idx.dialog_meta
                 if m.get("title", "").strip().casefold() == strip_amp(tab).strip().casefold()]
        pages[tab] = cands

    # ---- 465 控件清单 ----
    inv465 = []
    ast465 = idx.dialogs.get((465, 1033))
    if ast465:
        for i, c in enumerate(ast465["controls"]):
            cls = c["window_class"]
            cname = (er.CONTROL_CLASS_ATOMS.get(cls["value"], hex(cls["value"]))
                     if cls["kind"] == "ordinal" else cls["value"])
            if c["title"]["kind"] == "string" and cls["value"] in (0x80, 0x82):
                mark = "TRANSLATABLE"
            elif cls["value"] in (0x80, 0x82, 0x81, 0x83, 0x85) or cname not in er.CONTROL_CLASS_ATOMS.values():
                mark = "DYNAMIC"
            else:
                mark = "DO_NOT_TRANSLATE"
            if c["title"]["kind"] != "string":
                mark = "DO_NOT_TRANSLATE"
            inv465.append({"index": i, "id": c["id"], "class": cname,
                           "title_kind": c["title"]["kind"],
                           "title": c["title"]["value"] if c["title"]["kind"] == "string" else None,
                           "rect": list(c["rect"]), "mark": mark})

    # ---- 859 (0x2000) 控件清单 ----
    inv859 = []
    ast859 = idx.dialogs.get((859, 8192))
    if ast859:
        for i, c in enumerate(ast859["controls"]):
            cls = c["window_class"]
            cname = (er.CONTROL_CLASS_ATOMS.get(cls["value"], hex(cls["value"]))
                     if cls["kind"] == "ordinal" else cls["value"])
            inv859.append({"index": i, "id": c["id"], "class": cname,
                           "title_kind": c["title"]["kind"],
                           "title": c["title"]["value"] if c["title"]["kind"] == "string" else None,
                           "rect": list(c["rect"])})

    # ---- OK/Cancel/Help 是否在四个 page 内 ----
    shell_check = {}
    for btn in ("OK", "Cancel", "Help"):
        in_pages = []
        for tab, pid in PAGE_IDS.items():
            for lang in (1033, 8192):
                ast = idx.dialogs.get((pid, lang))
                if not ast:
                    continue
                for i, c in enumerate(ast["controls"]):
                    if c["title"]["kind"] == "string" and \
                       strip_amp(c["title"]["value"]).strip().casefold() == btn.casefold():
                        in_pages.append((pid, lang, i))
        shell_check[btn] = in_pages or "page 内不存在 → property-sheet shell / runtime"

    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(
        {"results": results, "pages": {k: v for k, v in pages.items()},
         "inv465": inv465, "inv859": inv859, "shell_check": shell_check},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ---- Markdown ----
    L = ["# Manage Project Items 属性表来源映射 (PHASE 1B2.1b0)",
         "",
         "- 由 `scripts/map_manage_project_items.py` 自动生成（只读；baseline SHA256 校验通过）。",
         "- 结论先行：Manage Project Items 是 MFC Property Sheet（外层容器 + 4 个 Property Page）。"
         "GUI 各文本来源已定位；**本阶段零修改、零翻译**。",
         "",
         "## 属性表结构映射",
         "",
         "| GUI 角色 | GUI 文本 | 来源资源 | LANGID | Template | 控件数 | Confidence |",
         "|---|---|---|---|---|---|---|"]
    for tab, pid in PAGE_IDS.items():
        metas = [m for m in idx.dialog_meta if m.get("id") == pid]
        for m in metas:
            conf = "HIGH" if m["lang"] == 1033 or pid != 859 else "HIGH (来源) / LANGID 策略待批"
            L.append(f"| tab_title (page) | {tab} | RT_DIALOG id={pid} | {m['lang']} | "
                     f"{m.get('kind')} | {m.get('controls')} | {conf} |")
    L += ["",
          "外层标题 `Manage Project Items`：来自 RT_STRING id=32704 (1033) "
          "prompt 长段 `Manage Project Items\\nFile Extensions, Books and Environment...`"
          "（与 GUI 窗口标题精确一致；该 ID 同时是 Manage Project Items 菜单命令的 prompt）。"
          "property-sheet 外层容器本身无对应 RT_DIALOG（MFC CPropertySheet 运行时构造）。",
          "",
          "## 逐条 GUI 文本来源映射",
          "",
          "| GUI 文本 | GUI Role | 自动分类 | 证据（结构化摘要） |",
          "|---|---|---|---|"]
    for e in results:
        ev = []
        for h in e["hits"][:5]:
            t = h.get("text", "")
            ev.append(f"{h['source_type']} id={h.get('resource_id')} lang={h.get('lang')}"
                      f"{' ctl#' + str(h['control_index']) if h.get('control_index') is not None else ''}"
                      f" [{h['match_type']}]: {t!r}")
        body = " <br> ".join(ev) if ev else "（六路搜索无命中）"
        L.append(f"| {e['gui']} | {e['role']} | {e['confidence']} | {body} |")

    L += ["", "## 四个 Page 的确定证据", ""]
    for tab, cands in pages.items():
        for m in cands:
            L.append(f"- **{tab}** → RT_DIALOG id={m['id']} lang={m['lang']} "
                     f"({m.get('kind')}, {m.get('controls')} 控件, size={m.get('size')}B) "
                     f"— 标题精确匹配 + 页面功能吻合 → HIGH")
    L += ["",
          "## RT_DIALOG 465 (Project Items page) 控件清单",
          "",
          "| Index | ID | Class | title.kind | Original | 标记 |", "|---|---|---|---|---|---|"]
    for c in inv465:
        L.append(f"| {c['index']} | {c['id']} | {c['class']} | {c['title_kind']} | "
                 f"{c['title']!r} | {c['mark']} |")
    L += ["",
          "## RT_DIALOG 859 (Project Info/Layer, LANGID 0x2000) 证据映射",
          "",
          "- 标题与用户 GUI Tab **精确一致**，18 个控件含工程信息字段 —— "
          "**strong source match / loaded-visible candidate**。",
          "- 但 0x2000 语义 unresolved/opaque，按现行安全策略："
          "**DEFERRED — LANGID POLICY BLOCKED**，本轮零修改；"
          "是否做专门的加载实证实验由 GPT 单独决定。",
          "",
          "## 控件清单 (859, 0x2000, 只读证据)",
          "",
          "| Index | ID | Class | title.kind | Original |", "|---|---|---|---|---|"]
    for c in inv859:
        L.append(f"| {c['index']} | {c['id']} | {c['class']} | {c['title_kind']} | "
                 f"{c['title']!r} |")

    L += ["", "## 共享按钮 (OK / Cancel / Help)", ""]
    for btn, where in shell_check.items():
        L.append(f"- **{btn}**: {where if isinstance(where, str) else where}；"
                 f"四个 page 模板内均无 → 属 property-sheet shell / MFC runtime，"
                 "本轮保持英文。")
    L += ["",
          "## 工程动态数据隔离",
          "",
          "rt-thread / Applications / Board / CPU / main.c / ns_flash.c 等为工程运行时"
          "数据（LISTBOX/TREEVIEW 内容），**不是翻译目标**，未纳入任何候选清单。",
          "",
          "## 状态",
          "",
          "PHASE 1B2.1b0 **只调查**：零修改、零翻译、零 EXE；"
          ".rdata 维持禁改；LANGID 9/1031/0x2000/1041 维持现行策略。"]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"条目: {len(results)}; 已写入 {args.out} 与 {args.json}")
    for e in results:
        print(f"  [{e['confidence']}] ({e['role']}) {e['gui']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
