#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
map_dynamic_strings.py — PHASE 1B1.1: 运行时菜单文本来源调查（只读）

背景: 用户真机 GUI 显示, 编辑器右键菜单与工程树右键的相当一部分条目
在 1B1 汉化后仍显示英文, 而 RT_MENU/RT_STRING 中对应条目已是中文 ——
符合 MFC WM_INITMENUPOPUP / ON_UPDATE_COMMAND_UI 阶段 CCmdUI::SetText()
运行时改写菜单文本的行为。本脚本**只读**地对每一条 GUI 观察文本做六路
来源搜索, 输出证据表, 不修改任何文件、不产出任何补丁。

搜索源:
    1. RT_STRING (LANGID 1033/2057/1041 分开记录)
    2. RT_MENU   (全部菜单项: 文本 + command ID + 路径)
    3. RT_240    (自定义列头资源, ANSI)
    4. .rdata / 其他节的 UTF-16LE 字节
    5. .rdata / 其他节的 ANSI 字节
    6. RT_DIALOG (仅查标题/控件文本, 不修改)

对每条观察文本输出: 各源命中 (资源 ID / LANGID / 原文 / 是否 %s 模板 / 是否已翻译),
以及 command ID 关联 (RT_MENU cmd → 同 ID 的 RT_STRING → RT_ACCELERATOR 快捷键)。

用法:
    python scripts/map_dynamic_strings.py [--exe backup/UV4_5.43.1.0_ORIGINAL.exe] \
        [--csv translations/keil_translation.csv] [--out docs/DYNAMIC_MENU_MAPPING.md]
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_resources as er   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---- 用户真机观察到的仍为英文的 GUI 文本 (第二项 = 归一化 %s 模板; None = 无参数) ----
OBSERVED = [
    ("Split Window horizontally", None, "编辑器右键"),
    ("Toggle Header/Code File", None, "编辑器右键"),
    ("Insert/Remove Breakpoint", None, "编辑器右键"),
    ("Enable/Disable Breakpoint", None, "编辑器右键"),
    ("Refresh Source Browser View", None, "编辑器右键"),
    ("Update Source Browser Information", None, "编辑器右键"),
    ("Go To Definition of 'main'", "Go To Definition of '%s'", "编辑器右键"),
    ("Go To Declaration of 'main'", "Go To Declaration of '%s'", "编辑器右键"),
    ("Go To Next Reference of 'main'", "Go To Next Reference of '%s'", "编辑器右键"),
    ("Go To Previous Reference of 'main'", "Go To Previous Reference of '%s'", "编辑器右键"),
    ("Show All References of 'main'", "Show All References of '%s'", "编辑器右键"),
    ("Insert/Remove Bookmark", None, "编辑器右键"),
    ("Undo", None, "编辑器右键"),
    ("Redo", None, "编辑器右键"),
    ("Cut", None, "编辑器右键"),
    ("Copy", None, "编辑器右键"),
    ("Paste", None, "编辑器右键"),
    ("Select All", None, "编辑器右键"),
    ("Options for Target 'rt-thread'...", "Options for Target '%s'...", "工程树右键/Project 菜单"),
    ("Add Group...", None, "工程树右键"),
    ("Manage Project Items...", None, "工程树右键"),
    ("Open Map File", None, "工程树右键"),
    ("Open Build Log", None, "工程树右键"),
    ("Show Include File Dependencies", None, "工程树右键"),
    ("New µVision Project...", None, "Project 菜单"),
    ("Remove Item", None, "Project 菜单/工程树"),
    ("Translate...", None, "Project 菜单/工程树"),
    ("Stop build", None, "Project 菜单/工程树"),
    ("Erase", None, "Flash 菜单"),
]


def strip_amp(t: str) -> str:
    return t.replace("&", "")


def template_regex(template: str):
    """'Go To Definition of '%s'' → 正则 (大小写不敏感, 宽松空白)。"""
    parts = [re.escape(p) for p in template.split("%s")]
    return re.compile(r"^\s*" + r"(.{0,64}?)".join(parts) + r"\s*$", re.IGNORECASE | re.DOTALL)


def find_ascii_strings(buf: bytes, min_len: int = 4):
    out, start = [], None
    for i, b in enumerate(buf):
        if 0x20 <= b < 0x7F:
            if start is None:
                start = i
        else:
            if start is not None and i - start >= min_len:
                out.append((start, buf[start:i].decode("ascii")))
            start = None
    return out


class SourceIndex:
    def __init__(self, data: bytes, pe: er.PEFile):
        self.data, self.pe = data, pe
        # 1. RT_STRING
        self.strings = {}          # lang -> {sid: text}
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_STRING" and r["name_kind"] == "id" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                for idx, t in enumerate(er.parse_string_table(blob)):
                    if t:
                        self.strings.setdefault(r["lang"], {})[
                            (r["name"] - 1) * 16 + idx] = t
        # 2. RT_MENU
        self.menu_items = []       # (menu_id, lang, path, cmd, text)
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_MENU" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                parsed = er.parse_menu_template(blob)

                def walk(items, path):
                    for i, it in enumerate(items):
                        p = f"{path}/{i}" if path else str(i)
                        if it["text"] and not (it["flags"] & 0x800):
                            self.menu_items.append((r["name"], r["lang"], p,
                                                    it["id"], it["text"]))
                        if it.get("children"):
                            walk(it["children"], p)

                walk(parsed["items"], "")
        # 3. RT_240 (自定义, ANSI)
        self.rt240 = []
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_240" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                for off, s in find_ascii_strings(blob):
                    self.rt240.append((r["name"], s))
        # 4. RT_DIALOG (标题+控件文本, 只查不改)
        self.dialog_texts = []     # (dialog_id, lang, kind, text)
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_DIALOG" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                try:
                    parsed = er.parse_dialog_template(blob)
                except Exception:
                    continue
                if parsed.get("title"):
                    self.dialog_texts.append((r["name"], r["lang"], "title", parsed["title"]))
                for it in parsed.get("items", []):
                    if isinstance(it.get("text"), str) and it["text"].strip():
                        self.dialog_texts.append((r["name"], r["lang"],
                                                  f"ctl:{it['id']}", it["text"]))
        # 5. RT_ACCELERATOR
        self.accel = {}
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_ACCELERATOR" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                for ent in er.parse_accelerators(blob):
                    self.accel.setdefault(ent["cmd"], []).append(
                        f"0x{ent['key']:02X}({'^' + chr(ent['key'] + 64) if 0x41 <= ent['key'] <= 0x5A else ent['key']})"
                        f"{'+Ctrl' if ent['fvirt'] & 0x08 else ''}{'+Alt' if ent['fvirt'] & 0x10 else ''}"
                        f"{'+Shift' if ent['fvirt'] & 0x04 else ''}")

    def search_strings(self, gui: str, template: str | None):
        hits = []
        want = gui.strip()
        want_n = strip_amp(want).casefold()
        tmpl_re = template_regex(template) if template else None
        for lang, m in self.strings.items():
            for sid, t in m.items():
                tn = strip_amp(t).strip().casefold()
                kind = None
                if tn == want_n or tn == want_n.rstrip("."):
                    kind = "exact"
                elif tmpl_re and tmpl_re.match(strip_amp(t)):
                    kind = "template"
                elif want_n and want_n in tn and len(tn) <= len(want_n) + 24:
                    kind = "contains"
                if kind:
                    hits.append(("RT_STRING", lang, sid, t, kind))
        return hits

    def search_menus(self, gui: str, template: str | None):
        hits = []
        want = strip_amp(gui).strip().casefold()
        tmpl_re = template_regex(template) if template else None
        for mid, lang, path, cmd, t in self.menu_items:
            tn = strip_amp(t).strip().casefold()
            kind = None
            if tn == want or tn == want.rstrip("."):
                kind = "exact"
            elif tmpl_re and tmpl_re.match(strip_amp(t)):
                kind = "template"
            elif want and want in tn and len(tn) <= len(want) + 16:
                kind = "contains"
            if kind:
                hits.append(("RT_MENU", lang, (mid, path, cmd), t, kind))
        return hits

    def search_rt240(self, gui: str):
        want = strip_amp(gui).casefold()
        return [(rid, s) for rid, s in self.rt240
                if want in s.casefold() or s.casefold() in want]

    def search_dialogs(self, gui: str):
        want = strip_amp(gui).strip().casefold()
        return [(d, l, k, t) for d, l, k, t in self.dialog_texts
                if strip_amp(t).strip().casefold() == want]

    def search_raw(self, text: str):
        """整文件字节搜索 (UTF-16LE 与 ANSI), 命中归属到节。"""
        out = {}
        for enc, label in (("utf-16le", "UTF-16"), ("ascii", "ANSI")):
            for needle in (text, strip_amp(text)):
                nb = needle.encode(enc, "ignore")
                if len(nb) < 4:
                    continue
                start, found = 0, []
                while True:
                    i = self.data.find(nb, start)
                    if i < 0:
                        break
                    found.append((i, self.pe.off2section(i)))
                    start = i + len(nb)
                if found:
                    out.setdefault(label, []).append((needle, found[:6]))
        return out


def classify(hits, translated_ids, translated_menu_paths):
    """按证据给分类: A 静态 RT_STRING / B 静态 RT_MENU / C 动态格式串 /
    D .rdata 硬编码 / E 未知。"""
    for src, lang, key, text, kind in hits:
        if src == "RT_STRING" and kind == "template":
            return "C 动态格式串 (RT_STRING)"
    for src, lang, key, text, kind in hits:
        if src == "RT_STRING" and kind == "exact":
            sid = key
            if sid in translated_ids:
                return "A 静态 RT_STRING (已翻译, GUI 仍英文 → 疑似运行时覆盖)"
            return "A 静态 RT_STRING (未翻译)"
    for src, lang, key, text, kind in hits:
        if src == "RT_MENU" and kind == "exact":
            mid, path, cmd = key
            if (mid, lang, path) in translated_menu_paths:
                return "B 静态 RT_MENU (已翻译, GUI 仍英文 → 疑似运行时覆盖)"
            return "B 静态 RT_MENU (未翻译)"
    if any(s == "RT_DIALOG" for s, *_ in hits):
        return "RT_DIALOG 静态文本"
    for label in ("UTF-16", "ANSI"):
        for src, lang, key, text, kind in hits:
            if src.startswith(".rdata") or label:
                break
    return "E 未知 (需进一步取证)"


def main(argv=None):
    ap = argparse.ArgumentParser(description="运行时菜单文本来源调查 (只读)")
    ap.add_argument("--exe", default="backup/UV4_5.43.1.0_ORIGINAL.exe")
    ap.add_argument("--csv", default="translations/keil_translation.csv")
    ap.add_argument("--out", default="docs/DYNAMIC_MENU_MAPPING.md")
    ap.add_argument("--json", default="output/dynamic_menu_mapping.json")
    args = ap.parse_args(argv)

    data = Path(args.exe).read_bytes()
    pe = er.PEFile(data)
    idx = SourceIndex(data, pe)

    translated_ids, translated_menu_paths = set(), set()
    csv_path = Path(args.csv)
    if csv_path.exists():
        import csv as _csv
        for row in _csv.DictReader(open(csv_path, encoding="utf-8-sig", newline="")):
            if (row.get("Status") or "").upper() != "DONE":
                continue
            if row["ResourceType"] == "STRING":
                translated_ids.add(int(row["ItemRef"]))
            elif row["ResourceType"] == "MENU":
                translated_menu_paths.add((int(row["ResourceID"]),
                                           int(row["LANGID"]), row["ItemRef"]))

    results = []
    for gui, template, where in OBSERVED:
        entry = {"gui": gui, "template": template, "where": where, "hits": []}
        s_hits = idx.search_strings(gui, template)
        for lang, sid, t, kind in [(h[1], h[2], h[3], h[4]) for h in s_hits]:
            mark = " ✔已翻译" if sid in translated_ids else ""
            entry["hits"].append(f"RT_STRING lang={lang} id={sid} {kind}: {t!r}{mark}")
        for lang, (mid, path, cmd), t, kind in [(h[1], h[2], h[3], h[4]) for h in idx.search_menus(gui, template)]:
            mark = " ✔已翻译" if (mid, lang, path) in translated_menu_paths else ""
            entry["hits"].append(f"RT_MENU id={mid} path={path} cmd={cmd} {kind}: {t!r}{mark}")
            # command ID 关联: 同 ID 的其他 RT_STRING / 加速键
            if cmd:
                for sl, sm in idx.strings.items():
                    if cmd in sm and sm[cmd] != t:
                        entry["hits"].append(
                            f"  └ 同 cmd 的 RT_STRING lang={sl} id={cmd}: {sm[cmd]!r}"
                            + (" ✔已翻译" if cmd in translated_ids else ""))
                if cmd in idx.accel:
                    entry["hits"].append(f"  └ 加速键 cmd={cmd}: {idx.accel[cmd]}")
                twins = [(m2, p2) for m2, l2, p2, c2, t2 in idx.menu_items
                         if c2 == cmd and (m2, p2) != (mid, path)]
                if twins:
                    entry["hits"].append(f"  └ 同 cmd 的其他菜单项: {twins[:4]}")
        for rid, s in idx.search_rt240(gui):
            entry["hits"].append(f"RT_240 id={rid}: {s!r}")
        for d, l, k, t in idx.search_dialogs(gui):
            entry["hits"].append(f"RT_DIALOG id={d} lang={l} {k}: {t!r}")
        raw = idx.search_raw(gui)
        for label, arr in raw.items():
            for needle, offs in arr[:1]:
                secs = {}
                for off, sec in offs:
                    secs[sec] = secs.get(sec, 0) + 1
                entry["hits"].append(f"{label} 字节命中 ({needle!r}): {secs}")
        entry["classification"] = classify(s_hits + idx.search_menus(gui, template),
                                           translated_ids, translated_menu_paths)
        results.append(entry)

    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(results, ensure_ascii=False, indent=1),
                               encoding="utf-8")

    # ---- 生成 Markdown 草稿 ----
    lines = [
        "# 运行时菜单文本来源映射 (PHASE 1B1.1)",
        "",
        "- 日期：2026-09-13 ｜ 只读调查，未修改任何文件",
        "- 背景：1B1 真机 GUI 显示，RT_STRING/RT_MENU 已汉化的部分条目在",
        "  编辑器右键/工程树右键仍显示英文 —— 符合 MFC `WM_INITMENUPOPUP` /",
        "  `ON_UPDATE_COMMAND_UI` 阶段 `CCmdUI::SetText()` 运行时改写菜单文本的行为。",
        "- 证据基础：对每条 GUI 观察文本做六路来源搜索",
        "  （RT_STRING / RT_MENU / RT_DIALOG(只查) / RT_240 / .rdata UTF-16 / .rdata ANSI），",
        "  并关联 command ID → 同 ID RT_STRING → RT_ACCELERATOR 快捷键。",
        "",
        "| GUI 文本 | 出现位置 | 分类 | 关键证据 |",
        "|---|---|---|---|",
    ]
    for e in results:
        key_evidence = " <br> ".join(e["hits"][:4]) if e["hits"] else "（六路搜索无命中）"
        lines.append(f"| {e['gui']} | {e['where']} | {e['classification']} | {key_evidence} |")
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"条目: {len(results)}; 结果已写入 {args.out} 与 {args.json}")
    for e in results:
        print(f"  [{e['classification']}] {e['gui']}")


if __name__ == "__main__":
    main()
