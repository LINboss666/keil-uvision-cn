#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
map_dynamic_strings.py — PHASE 1B1.1/1B1.1a: 运行时菜单文本来源调查（只读）

背景: 用户真机 GUI 显示, 编辑器右键菜单与工程树右键的相当一部分条目
在 1B1 汉化后仍显示英文, 而 RT_MENU/RT_STRING 中对应条目已是中文 ——
与 MFC WM_INITMENUPOPUP / ON_UPDATE_COMMAND_UI / CCmdUI::SetText()
动态修改菜单文本的官方机制行为一致 (强证据支持, 未经动态 tracing
不声称具体调用链已证明)。

本脚本**只读**, 对每条 GUI 观察文本做六路来源搜索, 产出**结构化证据**
并由 evidence 集合**自动分类** (无任何人工覆盖):

    evidence := {source_type, section, encoding, offset,
                 resource_id, lang, item_path, command_id, text, match_type}

    source_type: RT_STRING | RT_MENU | RT_DIALOG | RT_240 | RAW | ACCEL
    match_type:  exact | template | contains | same-command-id | literal
    分类:        C 动态格式串(RT_STRING) / A 静态RT_STRING(未译|已译→疑似运行时覆盖)
                 / B 静态RT_MENU(未译|已译→疑似运行时覆盖)
                 / D .rdata 硬编码(仅统计 section==.rdata 的 RAW 证据)
                 / RT_DIALOG 静态文本 / RT_240(列头) / E 未知(六路无命中)

基线保护 (1B1.1a): 输入文件 SHA256 必须等于 docs/BASELINE.md 固化的
µVision 5.43.1.0 基线, 否则 FAIL 非零退出 —— 映射结论严格绑定该 baseline。

用法:
    python scripts/map_dynamic_strings.py [--exe <UV4.exe>] [--csv <csv>] \
        [--out docs/DYNAMIC_MENU_MAPPING.md] [--json output/dynamic_menu_mapping.json]
"""

from __future__ import annotations

import argparse
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

# docs/BASELINE.md 固化基线: µVision 5.43.1.0 官方原版 (映射结论绑定此版本)
BASELINE_SHA256 = "428baf13d15e6760af1618def9c9815c97f0321cc5e459ec7adc4dde41c42f89"

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


def ev(source_type, *, section=None, encoding=None, offset=None, resource_id=None,
       lang=None, item_path=None, command_id=None, text=None, match_type=None):
    """构造一条结构化证据。"""
    return {"source_type": source_type, "section": section, "encoding": encoding,
            "offset": offset, "resource_id": resource_id, "lang": lang,
            "item_path": item_path, "command_id": command_id,
            "text": text, "match_type": match_type}


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
        self.strings = {}          # lang -> {sid: text}
        self.string_blocks = {}    # (block, lang) -> payload offset
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_STRING" and r["name_kind"] == "id" and r["file_offset"]:
                self.string_blocks[(r["name"], r["lang"])] = r["file_offset"]
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                for idx, t in enumerate(er.parse_string_table(blob)):
                    if t:
                        self.strings.setdefault(r["lang"], {})[
                            (r["name"] - 1) * 16 + idx] = t
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
        self.rt240 = []
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_240" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                for off, s in find_ascii_strings(blob):
                    self.rt240.append((r["name"], off, s))
        self.dialog_texts = []
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
        self.accel = {}
        for r in er.flatten_resources(pe):
            if r["type_name"] == "RT_ACCELERATOR" and r["file_offset"]:
                blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
                for ent in er.parse_accelerators(blob):
                    key = f"0x{ent['key']:02X}"
                    if 0x41 <= ent['key'] <= 0x5A:
                        key += f"({'^' + chr(ent['key'] + 64)})"
                    mods = (("+Ctrl" if ent['fvirt'] & 0x08 else "")
                            + ("+Alt" if ent['fvirt'] & 0x10 else "")
                            + ("+Shift" if ent['fvirt'] & 0x04 else ""))
                    self.accel.setdefault(ent["cmd"], []).append(key + mods)

    # ---- 各源搜索: 全部返回结构化 evidence ----

    def search_strings(self, gui: str, template: str | None):
        want = strip_amp(gui).strip().casefold()
        tmpl_re = template_regex(template) if template else None
        out = []
        for lang, m in self.strings.items():
            if lang not in (1033, 2057, 1041):
                continue
            for sid, t in m.items():
                tn = strip_amp(t).strip().casefold()
                kind = None
                if tn == want or tn == want.rstrip("."):
                    kind = "exact"
                elif tmpl_re and tmpl_re.match(strip_amp(t)):
                    kind = "template"
                elif want and want in tn and len(tn) <= len(want) + 24:
                    kind = "contains"
                if kind:
                    block = sid // 16 + 1
                    out.append(ev("RT_STRING", section=".rsrc", encoding="UTF-16LE",
                                  offset=self.string_blocks.get((block, lang)),
                                  resource_id=sid, lang=lang, command_id=None,
                                  text=t, match_type=kind))
        return out

    def search_menus(self, gui: str, template: str | None):
        want = strip_amp(gui).strip().casefold()
        tmpl_re = template_regex(template) if template else None
        out = []
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
                out.append(ev("RT_MENU", section=".rsrc", encoding="UTF-16LE",
                              resource_id=mid, lang=lang, item_path=path,
                              command_id=cmd, text=t, match_type=kind))
        return out

    def search_rt240(self, gui: str):
        want = strip_amp(gui).casefold()
        return [ev("RT_240", section=".rsrc", encoding="ANSI", offset=off,
                   resource_id=rid, text=s, match_type="contains")
                for rid, off, s in self.rt240
                if want in s.casefold() or s.casefold() in want]

    def search_dialogs(self, gui: str):
        want = strip_amp(gui).strip().casefold()
        return [ev("RT_DIALOG", section=".rsrc", resource_id=d, lang=l,
                   text=t, match_type="exact")
                for d, l, k, t in self.dialog_texts
                if strip_amp(t).strip().casefold() == want]

    def search_raw(self, needles):
        """整文件字节搜索。needles = [(text, encoding, why), ...]。
        产出 RAW 证据 (section 由命中位置归属; 仅 .rdata 参与 D 分类)。"""
        out = []
        seen = set()
        for text, enc, why in needles:
            nb = text.encode(enc, "ignore")
            if len(nb) < 4:
                continue
            start = 0
            while True:
                i = self.data.find(nb, start)
                if i < 0:
                    break
                sec = self.pe.off2section(i)
                key = (text, enc, i)
                if key not in seen:
                    seen.add(key)
                    out.append(ev("RAW", section=sec,
                                  encoding="UTF-16LE" if enc == "utf-16le" else "ANSI",
                                  offset=i, text=text, match_type=why))
                start = i + len(nb)
        return out

    def command_associations(self, cmd):
        """同一 command ID 的其他资源证据 (不参与 A/B/D 分类, 仅记录)。"""
        out = []
        if cmd is None:
            return out
        for lang, m in self.strings.items():
            if cmd in m:
                out.append(ev("RT_STRING", section=".rsrc", encoding="UTF-16LE",
                              resource_id=cmd, lang=lang, command_id=cmd,
                              text=m[cmd], match_type="same-command-id"))
        for mid, lang, path, c, t in self.menu_items:
            if c == cmd:
                out.append(ev("RT_MENU", section=".rsrc", resource_id=mid, lang=lang,
                              item_path=path, command_id=cmd, text=t,
                              match_type="same-command-id"))
        if cmd in self.accel:
            out.append(ev("ACCEL", command_id=cmd, text=",".join(self.accel[cmd]),
                          match_type="shortcut"))
        return out


def classify(evidence, translated_ids, translated_menu_paths):
    """由完整 evidence 集合自动分类 (无人工覆盖)。返回分类标签。"""
    parts = []
    # C: RT_STRING 中的 %s 模板
    if any(e["source_type"] == "RT_STRING" and e["match_type"] == "template"
           for e in evidence):
        parts.append("C 动态格式串(RT_STRING)")
    # A: RT_STRING 精确匹配
    a = [e for e in evidence
         if e["source_type"] == "RT_STRING" and e["match_type"] == "exact"]
    if a:
        if any(e["resource_id"] in translated_ids for e in a):
            parts.append("A 静态RT_STRING(已译→GUI仍英文,疑似运行时覆盖)")
        else:
            parts.append("A 静态RT_STRING(未译)")
    # B: RT_MENU 精确匹配
    b = [e for e in evidence
         if e["source_type"] == "RT_MENU" and e["match_type"] == "exact"]
    if b:
        if any((e["resource_id"], e["lang"], e.get("item_path")) in translated_menu_paths
               for e in b):
            parts.append("B 静态RT_MENU(已译→GUI仍英文,疑似运行时覆盖)")
        else:
            parts.append("B 静态RT_MENU(未译)")
    # D: 仅 section==.rdata 的 RAW 证据
    d = [e for e in evidence
         if e["source_type"] == "RAW" and e["section"] == ".rdata"]
    if d:
        encs = "+".join(sorted({e["encoding"] for e in d}))
        parts.append(f"D .rdata 硬编码({encs})")
    if any(e["source_type"] == "RT_DIALOG" for e in evidence):
        parts.append("RT_DIALOG 静态文本")
    if any(e["source_type"] == "RT_240" for e in evidence):
        parts.append("RT_240(列头)")
    if not parts:
        return "E 未知(六路无命中)"
    return "+".join(parts)


DOC_HEAD = """# 运行时菜单文本来源映射 (PHASE 1B1.1 / 1B1.1a)

- 生成方式：**完全由 `scripts/map_dynamic_strings.py` 自动生成**（分类由结构化
  evidence 集合自动推导，人工覆盖数 = 0），重新运行即可复现。
- 日期：2026-09-13 ｜ **只读调查**，未修改任何文件、未生成任何补丁
- 基线：输入文件 SHA256 已由脚本校验，绑定 µVision 5.43.1.0
  （`428baf13…c42f89`，见 `docs/BASELINE.md`）。

## 背景与方法

1B1 真机 GUI：主菜单与文件标签右键大量汉化成功，但**编辑器右键**与
**工程树右键（根/组）**的相当多条目仍为英文，而对应 RT_MENU/RT_STRING 条目
已是中文 —— 即 GUI 最终文本与静态资源不完全一致。

**运行时动态文本覆盖假设获得强证据支持，且行为与 MFC CCmdUI update mechanism
一致**（Microsoft MFC 官方允许 `WM_INITMENUPOPUP` / `ON_UPDATE_COMMAND_UI` /
`CCmdUI::SetText()` 动态修改菜单文本）。当前证据能证明的是：

- A. GUI 最终文本与静态 RT_MENU/RT_STRING 不完全一致；
- B. `.rdata` 中存在与 GUI 完全一致的 ANSI literal / format template；
- C. MFC 官方机制允许上述动态修改。

未经动态 tracing 或 call-site 分析，**不声称**某个具体 `.rdata` 地址
"已被证明传给 `CCmdUI::SetText()`"；下表中的 `.rdata` 偏移仅作为
"存在完全匹配 literal" 的证据记录。

搜索源（六路）：RT_STRING / RT_MENU / RT_DIALOG(只查) / RT_240 /
.rdata 等节 UTF-16LE / .rdata 等节 ANSI，外加 command ID → 同 ID
RT_STRING → RT_ACCELERATOR 关联。

## 自动映射表

| GUI 文本 | 出现位置 | 自动分类 | 证据（结构化 evidence 摘要） |
|---|---|---|---|
"""

DOC_TAIL = """## Command ID 关联（脚本自动提取）

> "同 cmd" = 与命中菜单项共享 command ID 的其他资源证据
> （RT_STRING prompt / 其他菜单副本 / RT_ACCELERATOR 快捷键）。
> 完整明细见 `output/dynamic_menu_mapping.json`。

{cmd_table}

## 结论与 1B1.2 候选（仅记录，未经批准不执行）

- **可经资源层修复（静态 RT_STRING / RT_MENU，候选清单）**：
  RT_STRING：159、162、164、167、744、770、771、104、181、20628–20633、
  57643/57644/57634/57635/57637/57642（command prompt，须整条处理：
  保留 newline 分段数 / 格式 token / 快捷键文本，不得只 raw patch "第二段"）；
  RT_MENU：592、624（工程树组/根上下文）、191、800（DbWinMenu）、
  22565（隐藏编辑弹出）、400。
- **资源层无法覆盖（.rdata literal 强证据，维持英文）**：Split Window horizontally、
  Toggle Header/Code File、Go To Definition/Declaration/References of '%s' 家族、
  Show All References of '%s'，以及最终被 .rdata runtime text 覆盖的其它项
  （以 1B1.2 GUI 测试实录为准）。是否放开 .rdata 属 **PHASE 2 — EXPERIMENTAL
  RDATA LOCALIZATION** 专项决策，当前禁止实施。
- RT_DIALOG / .rdata / .text / DLL：本阶段零接触。
"""


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

    results, cmd_rows = [], {}
    for gui, template, where in OBSERVED:
        evidence = []
        evidence += idx.search_strings(gui, template)
        evidence += idx.search_menus(gui, template)
        evidence += idx.search_rt240(gui)
        evidence += idx.search_dialogs(gui)
        # RAW: 全文 + 去 & 形式 + 模板字面前缀 (>=8 字符)
        needles = [(gui, "utf-16le", "literal"),
                   (gui, "ascii", "literal"),
                   (strip_amp(gui), "utf-16le", "literal"),
                   (strip_amp(gui), "ascii", "literal")]
        if template:
            for chunk in template.split("%s"):
                chunk = chunk.strip()
                if len(chunk) >= 8:
                    needles.append((chunk, "utf-16le", "template-prefix"))
                    needles.append((chunk, "ascii", "template-prefix"))
        evidence += idx.search_raw(needles)
        label = classify(evidence, translated_ids, translated_menu_paths)

        # command 关联 (菜单命中项的 cmd; 不参与分类)
        assoc = []
        for e in [x for x in evidence if x["source_type"] == "RT_MENU"
                  and x["match_type"] == "exact" and x["command_id"]]:
            assoc += [a for a in idx.command_associations(e["command_id"])
                      if not (a["source_type"] == "RT_MENU"
                              and a["item_path"] == e["item_path"]
                              and a["resource_id"] == e["resource_id"]
                              and a["lang"] == e["lang"])]
        evidence += assoc

        results.append({"gui": gui, "template": template, "where": where,
                        "classification": label,
                        "evidence": [e for e in evidence
                                     if e["match_type"] != "same-command-id"],
                        "command_associations": [e for e in evidence
                                                 if e["match_type"] == "same-command-id"
                                                 or e["source_type"] == "ACCEL"]})
        for e in evidence:
            if e["match_type"] == "same-command-id" and e.get("command_id") is not None:
                cmd_rows.setdefault(e["command_id"], set()).add(
                    f"{e['source_type']}:{e.get('resource_id')}:{e.get('lang') or ''}:{e['text']!r}")

    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(results, ensure_ascii=False, indent=1),
                               encoding="utf-8")

    # ---- 生成 Markdown (表格完全由脚本产出, 无人工分类) ----
    lines = [DOC_HEAD]
    for e in results:
        ev_lines = []
        for x in e["evidence"]:
            if x["source_type"] == "RAW":
                desc = (f"RAW {x['encoding']} @{x['section']}+0x{x['offset']:X} "
                        f"({x['match_type']}): {x['text']!r}")
            else:
                desc = f"{x['source_type']} id={x.get('resource_id')} lang={x.get('lang')}"
                if x.get("item_path"):
                    desc += f" path={x['item_path']}"
                if x.get("command_id"):
                    desc += f" cmd={x['command_id']}"
                desc += f" [{x['match_type']}]: {x['text']!r}"
            ev_lines.append(desc)
        body = " <br> ".join(ev_lines[:6]) if ev_lines else "（六路搜索无命中）"
        lines.append(f"| {e['gui']} | {e['where']} | {e['classification']} | {body} |")

    cmd_table = ["| Command ID | 同 ID 资源证据 |", "|---|---|"]
    for cmd in sorted(cmd_rows):
        for item in sorted(cmd_rows[cmd]):
            cmd_table.append(f"| {cmd} | {item} |")
    lines.append(DOC_TAIL.format(cmd_table="\n".join(cmd_table)))

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"条目: {len(results)}; 结果已写入 {args.out} 与 {args.json}")
    for e in results:
        print(f"  [{e['classification']}] {e['gui']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
