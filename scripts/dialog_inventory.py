#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
dialog_inventory.py — PHASE 1B2.0: RT_DIALOG 资源清单 (只读)

基线保护: 输入 SHA256 必须等于 µVision 5.43.1.0 固定基线, 否则 FAIL 非零退出。
输出: docs/DIALOG_INVENTORY.md + output/dialog_inventory.json
统计: standard/extended 数量、LANGID 直方图、控件总数、DS_SETFONT/DS_SHELLFONT、
带 menu / 自定义 windowClass 的对话框、ordinal/string 控件类、nonzero creation data
清单、round-trip 246/246 门禁、可识别的重要设置窗口。

用法: python scripts/dialog_inventory.py [--exe <UV4.exe>] [--out docs/DIALOG_INVENTORY.md]
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

MAJOR_KEYWORDS = [
    "Options for Target", "Debug Settings", "Flash", "Device", "Pack",
    "Run-Time Environment", "Manage Run-Time", "About", "License",
    "Select Device", "Target", "Download", "Erase", "Component",
]


def main(argv=None):
    ap = argparse.ArgumentParser(description="RT_DIALOG 资源清单 (只读)")
    ap.add_argument("--exe", default="backup/UV4_5.43.1.0_ORIGINAL.exe")
    ap.add_argument("--out", default="docs/DIALOG_INVENTORY.md")
    ap.add_argument("--json", default="output/dialog_inventory.json")
    args = ap.parse_args(argv)

    data = Path(args.exe).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != BASELINE_SHA256:
        print(f"FAIL: 输入 SHA256 {sha} 与 µVision 5.43.1.0 固定基线不一致 —— "
              f"版本不匹配，需要重新执行 PHASE 0。", file=sys.stderr)
        return 1
    pe = er.PEFile(data)

    dialogs, warnings = [], []
    for r in er.flatten_resources(pe):
        if r["type_name"] != "RT_DIALOG" or not r["file_offset"]:
            continue
        blob = data[r["file_offset"]: r["file_offset"] + r["size"]]
        try:
            ast = er.parse_dialog_ast(blob)
        except Exception as exc:
            warnings.append((r["name"], r["lang"], str(exc)))
            continue
        rebuilt = er.serialize_dialog_ast(ast)
        texts = [ast["title"]["value"]] + [
            c["title"]["display"] or "" for c in ast["controls"]]
        major = [kw for kw in MAJOR_KEYWORDS
                 if any(kw.casefold() in (t or "").casefold() for t in texts)]
        dialogs.append({
            "res_id": r["name"], "lang": r["lang"], "kind": ast["kind"],
            "size": r["size"], "style": ast["header"]["style"],
            "title": ast["title"]["value"],
            "ds_setfont": bool(ast["header"]["style"] & er.DS_SETFONT),
            "ds_shellfont": (ast["header"]["style"] & 0x48) == 0x48,
            "has_menu": ast["menu"]["kind"] != "none",
            "has_custom_class": ast["window_class"]["kind"] != "none",
            "controls": [{
                "id": c["id"], "class": c["window_class"],
                "title": c["title"],
                "helpid": c.get("helpid"),
                "creation": (c["creation_data"]["size_bytes"] if ast["kind"] == "std"
                             else c["extra_count"]),
            } for c in ast["controls"]],
            "roundtrip": rebuilt == blob,
            "trailing_len": len(ast.get("trailing", b"")),
            "trailing_all_zero": all(b == 0 for b in ast.get("trailing", b"")),
            "trailing_hex": ast.get("trailing", b"").hex(),
            "major_keywords": major,
        })

    # ---- 统计 ----
    total = len(dialogs)
    n_std = sum(1 for d in dialogs if d["kind"] == "std")
    n_ex = sum(1 for d in dialogs if d["kind"] == "ex")
    lang_hist = {}
    for d in dialogs:
        lang_hist[d["lang"]] = lang_hist.get(d["lang"], 0) + 1
    controls_total = sum(len(d["controls"]) for d in dialogs)
    n_setfont = sum(1 for d in dialogs if d["ds_setfont"])
    n_shellfont = sum(1 for d in dialogs if d["ds_shellfont"])
    n_menu = sum(1 for d in dialogs if d["has_menu"])
    n_class = sum(1 for d in dialogs if d["has_custom_class"])
    rt_ok = sum(1 for d in dialogs if d["roundtrip"])
    class_ord = class_str = title_ord = title_str = 0
    creation_nonzero = []
    for d in dialogs:
        for c in d["controls"]:
            k = c["class"]["kind"]
            if k == "ordinal":
                class_ord += 1
            elif k == "string":
                class_str += 1
            k = c["title"]["kind"]
            if k == "ordinal":
                title_ord += 1
            elif k == "string":
                title_str += 1
            if c["creation"]:
                szf = (c["creation"]["size_bytes"] if isinstance(c["creation"], dict)
                       and "size_bytes" in c["creation"] else c["creation"])
                creation_nonzero.append((d["res_id"], d["lang"], c["id"], szf))
    rt_total = n_std + n_ex

    # trailing / allocation slack 统计 (PHASE 1B2.0a 第 G 条)
    trailing_lens = [d["trailing_len"] for d in dialogs]
    n_trailing = sum(1 for L in trailing_lens if L > 0)
    total_trailing = sum(trailing_lens)
    max_trailing = max(trailing_lens, default=0)
    nonzero_trailing = [(d["res_id"], d["lang"], d["trailing_len"], d["trailing_hex"])
                        for d in dialogs
                        if d["trailing_len"] > 0 and not d["trailing_all_zero"]]
    candidate_slack = sum(1 for d in dialogs
                          if d["trailing_len"] > 0 and d["trailing_all_zero"])

    std_nz = [(x[0], x[1], x[2], x[3]) for x in creation_nonzero
              if isinstance(x[3], int) and x[3] > 0]
    # ---- 输出 ----
    lines = [
        "# RT_DIALOG 资源清单 (PHASE 1B2.0)",
        "",
        "- 由 `scripts/dialog_inventory.py` 自动生成（只读；基线 SHA256 校验通过，"
        "绑定 µVision 5.43.1.0）。原始数据：`output/dialog_inventory.json`（本地）。",
        f"- round-trip 门禁：**{rt_ok}/{rt_total} byte-identical**（parse → serialize）。",
        f"- parse warnings：{len(warnings)}（要求 0）。",
        "",
        "| 统计项 | 值 |",
        "|---|---|",
        f"| RT_DIALOG total | {total} |",
        f"| Standard DLGTEMPLATE | {n_std} |",
        f"| Extended DLGTEMPLATEEX | {n_ex} |",
        f"| LANGID histogram | {json.dumps(lang_hist, ensure_ascii=False)} |",
        f"| Controls total | {controls_total} |",
        f"| DS_SETFONT | {n_setfont} |",
        f"| DS_SHELLFONT | {n_shellfont} |",
        f"| dialogs with menu | {n_menu} |",
        f"| dialogs with custom windowClass | {n_class} |",
        f"| ordinal control classes | {class_ord} |",
        f"| string control classes | {class_str} |",
        f"| ordinal titles | {title_ord} |",
        f"| string titles | {title_str} |",
        f"| nonzero creation data | {len(std_nz)} |",
        f"| dialogs with trailing bytes | {n_trailing} |",
        f"| max trailing bytes | {max_trailing} |",
        f"| total trailing bytes | {total_trailing} |",
        f"| dialogs with NONZERO trailing | {len(nonzero_trailing)} |",
        f"| candidate slack (trailing 全 00) | {candidate_slack} |",
        "",
    ]
    if std_nz:
        lines += ["", "### nonzero creation data 明细", "",
                  "| Dialog ID | LANGID | Control ID | size_bytes |", "|---|---|---|---|"]
        for rid, lang, cid, sz in std_nz[:60]:
            lines.append(f"| {rid} | {lang} | {cid} | {sz} |")
    else:
        lines += ["", "nonzero creation data：**无**（std size_bytes 与 ex extraCount 均为 0，"
                  "UV4 样本不触发两种 size 语义差异；语义仍按微软标准分别实现并由合成 fixture 锁定）。"]
    lines += ["", "## 可识别的重要 Dialog（标题/控件文本关键词匹配）", ""]
    seen_titles = set()
    for d in dialogs:
        if d["major_keywords"] and (d["title"], d["res_id"]) not in seen_titles:
            seen_titles.add((d["title"], d["res_id"]))
            lines.append(f"- `{d['res_id']}` lang={d['lang']} title={d['title']!r} "
                         f"controls={len(d['controls'])} 关键词={d['major_keywords']}")
    lines += ["", "## 状态", "",
              "本阶段（PHASE 1B2.0）**只调查、不翻译**：未修改任何 RT_DIALOG payload，"
              "未生成任何汉化 EXE。后续正式 Dialog 汉化（PHASE 1B2.1，待批准）将只允许 "
              "Dialog title / Control title(text) 变化，其余字段以语义快照强制 identical。"]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(args.json).write_text(json.dumps(dialogs, ensure_ascii=False, indent=1),
                               encoding="utf-8")
    print(f"dialogs={total} (std {n_std} / ex {n_ex}), controls={controls_total}, "
          f"round-trip {rt_ok}/{rt_total}, warnings={len(warnings)}")
    print(f"已写入 {args.out} 与 {args.json}")
    return 0 if rt_ok == rt_total and not warnings else 1


if __name__ == "__main__":
    sys.exit(main())
