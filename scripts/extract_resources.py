#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_resources.py — Keil µVision UV4.exe PE 资源只读扫描器（PHASE 0 工具）

用途:
    在做任何"汉化"之前, 对官方原版 UV4.exe 做完整的只读分析:
      * PE 头 / 架构 / 节表 / 数据目录 / 导入表
      * 资源目录树（类型 → 名字 → 语言 → 数据）
      * RT_STRING 字符串表解码（UTF-16LE, 字符串 ID 换算）
      * RT_MENU 菜单模板解码（含命令 ID / 加速键标记 &）
      * RT_DIALOG 对话框模板解码（含控件 ID / 类 / 文本）
      * RT_ACCELERATOR 加速键表解码
      * "硬编码字符串"启发式扫描（.text/.rdata/.data 中的 UI 相关字符串）

安全原则:
      * 只读 —— 不写入、不修改输入文件。
      * 仅依赖 Python 标准库, 无需 pip 安装任何东西。
      * 不解析、不触碰任何许可证/授权相关数据, 只枚举 UI 资源。

用法:
    python extract_resources.py <UV4.exe 路径> [--json 输出.json] [--samples N]

注意:
    --json 输出包含 UV4 的完整英文 UI 字符串, 仅限本地研究,
    严禁提交进 Git 仓库（.gitignore 已排除 output/ 与 backup/）。
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import struct
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RESOURCE_TYPE_NAMES = {
    1: "RT_CURSOR", 2: "RT_BITMAP", 3: "RT_ICON", 4: "RT_MENU",
    5: "RT_DIALOG", 6: "RT_STRING", 7: "RT_FONTDIR", 8: "RT_FONT",
    9: "RT_ACCELERATOR", 10: "RT_RCDATA", 11: "RT_MESSAGETABLE",
    12: "RT_GROUP_CURSOR", 14: "RT_GROUP_ICON", 16: "RT_VERSION",
    23: "RT_HTML", 24: "RT_MANIFEST",
}

MACHINE_NAMES = {
    0x014C: "x86 (i386)", 0x8664: "x64 (AMD64)",
    0x01C0: "ARM", 0xAA64: "ARM64", 0x01C4: "ARMNT",
}

SUBSYSTEM_NAMES = {1: "NATIVE", 2: "WINDOWS_GUI", 3: "WINDOWS_CUI"}

CONTROL_CLASS_ATOMS = {
    0x80: "BUTTON", 0x81: "EDIT", 0x82: "STATIC",
    0x83: "LISTBOX", 0x84: "SCROLLBAR", 0x85: "COMBOBOX",
}

# 用户指定的探针字符串: 验证主菜单/常用命令是否存在于标准资源中
PROBE_STRINGS = [
    "&File", "&Edit", "&View", "&Project", "&Flash", "&Debug",
    "&Tools", "&Window", "&Help",
    "File", "Edit", "View", "Project", "Flash", "Debug", "Tools",
    "SVCS", "Window", "Help",
    "Build Target", "Rebuild all target files", "Options for Target",
    "Manage Run-Time Environment", "Select Device for Target",
    "Start/Stop Debug Session", "Download", "Clean Targets",
]

HARDCODED_SCAN_PATTERNS = PROBE_STRINGS + [
    "Cannot open file '%s'", "Error", "Warning", "Target DLL",
]


# --------------------------------------------------------------------------
# 基础解码工具
# --------------------------------------------------------------------------

def decode_utf16z(buf: bytes, pos: int):
    """读取 null 结尾的 UTF-16LE 字符串。返回 (text, 越过终止符之后的位置)。"""
    n = len(buf)
    end = pos
    while end + 1 < n and not (buf[end] == 0 and buf[end + 1] == 0):
        end += 2
    text = buf[pos:end].decode("utf-16le", errors="replace")
    return text, min(end + 2, n)


def read_sz_or_ord(buf: bytes, pos: int):
    """MENU/DIALOG 共用的 sz-or-ord 字段:
    0x0000=无 | 0xFFFF+WORD 序号 | null 结尾 UTF-16 字符串。"""
    if pos + 2 > len(buf):
        return None, pos
    (w,) = struct.unpack_from("<H", buf, pos)
    if w == 0x0000:
        return None, pos + 2
    if w == 0xFFFF:
        if pos + 4 > len(buf):
            return None, pos + 2
        (ordinal,) = struct.unpack_from("<H", buf, pos + 2)
        return int(ordinal), pos + 4
    return decode_utf16z(buf, pos)


# --------------------------------------------------------------------------
# PE 解析（最小实现, 只读）
# --------------------------------------------------------------------------

class Section:
    __slots__ = ("name", "vsize", "vaddr", "rawsize", "rawptr", "chars")


class PEFile:
    def __init__(self, data: bytes):
        self.data = data
        if data[:2] != b"MZ":
            raise ValueError("不是 MZ/PE 文件")
        (e_lfanew,) = struct.unpack_from("<I", data, 0x3C)
        if data[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
            raise ValueError("缺少 PE 签名")
        coff = e_lfanew + 4
        (self.machine, self.num_sections, self.timestamp, _, _,
         opt_size, self.characteristics) = struct.unpack_from("<HHIIIHH", data, coff)
        opt = coff + 20
        (self.magic,) = struct.unpack_from("<H", data, opt)
        if self.magic == 0x10B:
            self.arch = "PE32 (32 位)"
            nrvas_ofs, dd_ofs = opt + 92, opt + 96
            (self.image_base,) = struct.unpack_from("<I", data, opt + 28)
        elif self.magic == 0x20B:
            self.arch = "PE32+ (64 位)"
            nrvas_ofs, dd_ofs = opt + 108, opt + 112
            (self.image_base,) = struct.unpack_from("<Q", data, opt + 24)
        else:
            raise ValueError(f"未知 OptionalHeader magic: 0x{self.magic:X}")
        (self.entry_rva,) = struct.unpack_from("<I", data, opt + 16)
        (self.subsystem,) = struct.unpack_from("<H", data, opt + 68)
        (self.dll_chars,) = struct.unpack_from("<H", data, opt + 70)
        (self.checksum,) = struct.unpack_from("<I", data, opt + 64)
        (nrvas,) = struct.unpack_from("<I", data, nrvas_ofs)
        nrvas = min(nrvas, 16)
        self.data_dirs = []
        for i in range(nrvas):
            rva, size = struct.unpack_from("<II", data, dd_ofs + 8 * i)
            self.data_dirs.append((rva, size))

        self.sections = []
        sec_ofs = opt + opt_size
        for i in range(self.num_sections):
            (name, vsize, vaddr, rawsize, rawptr, _pr, _pl, _nr, _nl,
             chars) = struct.unpack_from("<8sIIIIIIHHI", data, sec_ofs + 40 * i)
            s = Section()
            s.name = name.rstrip(b"\x00").decode("ascii", "replace")
            s.vsize, s.vaddr, s.rawsize, s.rawptr, s.chars = vsize, vaddr, rawsize, rawptr, chars
            self.sections.append(s)

    # -- 帮助函数 ----------------------------------------------------------

    def rva2off(self, rva: int):
        for s in self.sections:
            if s.vaddr <= rva < s.vaddr + max(s.vsize, s.rawsize):
                d = rva - s.vaddr
                if d < s.rawsize:
                    return s.rawptr + d
                return None
        return None

    def off2section(self, off: int) -> str:
        for s in self.sections:
            if s.rawsize and s.rawptr <= off < s.rawptr + s.rawsize:
                return s.name
        first_raw = min((s.rawptr for s in self.sections if s.rawsize), default=0)
        if off < first_raw:
            return "PE-header"
        return "overlay(节表之外)"

    def imports(self):
        out = []
        try:
            if len(self.data_dirs) < 2:
                return out
            rva, _ = self.data_dirs[1]
            off = self.rva2off(rva)
            if off is None:
                return out
            while len(out) < 256:
                ilt, _ts, _fw, name_rva, _ft = struct.unpack_from("<IIIII", self.data, off)
                if ilt == 0 and name_rva == 0:
                    break
                no = self.rva2off(name_rva)
                if no is None:
                    break
                end = self.data.find(b"\x00", no)
                out.append(self.data[no:end].decode("ascii", "replace"))
                off += 20
        except Exception:
            pass
        return out

    def timestamp_iso(self) -> str:
        try:
            return datetime.datetime.fromtimestamp(
                self.timestamp, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            return "?"

    def dll_characteristics_names(self):
        names = []
        flags = {0x0020: "HIGH_ENTROPY_VA", 0x0040: "DYNAMIC_BASE(ASLR)",
                 0x0100: "NX_COMPAT(DEP)", 0x0400: "NO_SEH",
                 0x4000: "GUARD_CF", 0x8000: "TERMINAL_SERVER_AWARE"}
        for bit, nm in flags.items():
            if self.dll_chars & bit:
                names.append(nm)
        return names


# --------------------------------------------------------------------------
# 资源目录树
# --------------------------------------------------------------------------

def walk_resource_dir(data: bytes, base: int, off: int, depth: int = 0):
    if depth > 8:
        return []
    _chars, _ts = struct.unpack_from("<II", data, off)
    nnamed, nid = struct.unpack_from("<HH", data, off + 12)
    entries = []
    for i in range(nnamed + nid):
        name_f, off_f = struct.unpack_from("<II", data, off + 16 + 8 * i)
        if name_f & 0x80000000:
            so = base + (name_f & 0x7FFFFFFF)
            if so + 2 > len(data):
                key = ("name", "?")
            else:
                (slen,) = struct.unpack_from("<H", data, so)
                key = ("name", data[so + 2: so + 2 + 2 * slen].decode("utf-16le", "replace"))
        else:
            key = ("id", name_f & 0xFFFF)
        if off_f & 0x80000000:
            entries.append((key, walk_resource_dir(data, base, base + (off_f & 0x7FFFFFFF), depth + 1), None))
        else:
            drva, dsize, _cp, _res = struct.unpack_from("<IIII", data, base + off_f)
            entries.append((key, None, (drva, dsize)))
    return entries


def flatten_resources(pe: PEFile):
    """返回资源条目列表: dict(type/type_name/name/lang/rva/size/file_offset)"""
    if len(pe.data_dirs) < 3:
        return []
    rsrc_rva, rsrc_size = pe.data_dirs[2]
    if not rsrc_rva:
        return []
    base = pe.rva2off(rsrc_rva)
    if base is None:
        raise ValueError(".rsrc RVA 无法映射到文件偏移")

    tree = walk_resource_dir(pe.data, base, base)
    out = []
    for (tkind, tval), tsub, tdata in tree:
        if tdata is not None or tsub is None:
            continue
        for (nkind, nval), nsub, ndata in tsub:
            if ndata is not None or nsub is None:
                continue
            for (lkind, lval), lsub, ldata in nsub:
                if ldata is None:
                    continue
                drva, dsize = ldata
                out.append({
                    "type": tval if tkind == "id" else -1,
                    "type_name": (RESOURCE_TYPE_NAMES.get(tval, f"RT_{tval}")
                                  if tkind == "id" else str(tval)),
                    "name_kind": nkind,
                    "name": nval,
                    "lang": lval if lkind == "id" else f"named:{lval}",
                    "rva": drva,
                    "size": dsize,
                    "file_offset": pe.rva2off(drva),
                })
    return out


# --------------------------------------------------------------------------
# 各资源类型解码器
# --------------------------------------------------------------------------

def parse_string_table(buf: bytes):
    """RT_STRING: 16 个 [WORD 长度][UTF-16] 顺序条目。"""
    out, pos = [], 0
    for _ in range(16):
        if pos + 2 > len(buf):
            out.append("")
            continue
        (n,) = struct.unpack_from("<H", buf, pos)
        pos += 2
        out.append(buf[pos:pos + 2 * n].decode("utf-16le", "replace"))
        pos += 2 * n
    return out


def serialize_string_table(strings):
    """把 16 条字符串重序列化为完整 RT_STRING 块字节 ([WORD 长度][UTF-16LE] × 16)。

    PHASE 1A 的写入路径是"整块重序列化", 而不是逐字符串原位覆盖:
      * 长度计数按 UTF-16 编码单元数 (len(utf16_bytes)//2), 与 Windows 语义一致;
      * 强制恰好 16 条 (RT_STRING 块的槽位契约), 否则抛错拒绝;
      * 调用方需保证 len(new_blob) <= 原资源分配大小; 更短时只在整块末尾补 0,
        绝不在字符串之间塞 0 (否则会破坏后续条目的索引定位)。
    """
    if len(strings) != 16:
        raise ValueError(
            f"RT_STRING 块必须恰好包含 16 条字符串, 实际 {len(strings)} 条 — 拒绝序列化")
    out = bytearray()
    for s in strings:
        b = s.encode("utf-16le")
        out += struct.pack("<H", len(b) // 2)
        out += b
    return bytes(out)


def parse_menu_template(buf: bytes):
    if len(buf) < 4:
        return {"error": "buffer too small"}
    # MENUITEMTEMPLATEHEADER: WORD wVersion; WORD offset;
    # offset = 从头部末尾 (byte 4) 到第一个 MENUITEMTEMPLATE 的字节数 (可为 0)
    ver, woffset = struct.unpack_from("<HH", buf, 0)
    if ver == 1:
        return _parse_menu_ex(buf)
    if ver != 0:
        return {"error": f"未知菜单模板版本 {ver}"}

    n = len(buf)

    def items(pos):
        out = []
        while True:
            if pos + 2 > n:
                return out, pos, "truncated"
            (flags,) = struct.unpack_from("<H", buf, pos)
            pos += 2
            # MF_POPUP(0x10) 项没有 ID 字, 直接跟字符串; 普通项才有 WORD id
            if flags & 0x10:
                mid = None
            else:
                if pos + 2 > n:
                    return out, pos, "truncated"
                (mid,) = struct.unpack_from("<H", buf, pos)
                pos += 2
            if flags & 0x0200:  # MF_BITMAP: 跟随 WORD 而非字符串
                if pos + 2 > n:
                    return out, pos, "truncated"
                text = struct.unpack_from("<H", buf, pos)[0]
                pos += 2
            else:
                text, pos = decode_utf16z(buf, pos)
            it = {"flags": flags, "flags_hex": f"0x{flags:04X}",
                  "id": mid, "text": text, "children": None}
            if flags & 0x10:  # MF_POPUP
                sub, pos, err = items(pos)
                it["children"] = sub
                if err:
                    it["parse_note"] = err
            out.append(it)
            if flags & 0x80:  # MF_END
                return out, pos, None

    tree, consumed, err = items(4 + woffset)
    return {"version": 0, "header_offset": woffset, "items": tree,
            "consumed_bytes": consumed, "total_bytes": n, "parse_note": err}


def serialize_menu_template(menu):
    """把 parse_menu_template 的结果重序列化为 RT_MENU 模板字节（仅 version 0）。

    PHASE 1B1 的写入路径: 与 parse 严格互逆 —— 头部 (wVersion=0, wOffset) +
    [WORD flags][WORD id(仅非 popup)][null 结尾 UTF-16 文本] + 子层级。
    flags / id / 层级 / 顺序完全由解析结果决定, 调用方只允许改 text。
    MF_BITMAP 项的 text 为 WORD 序号 (int), 原样写回。
    """
    if menu.get("version") != 0:
        raise ValueError(
            f"serialize_menu_template 仅支持 version 0 菜单, 实际 {menu.get('version')!r} — 拒绝序列化")
    out = bytearray()
    out += struct.pack("<HH", 0, int(menu.get("header_offset", 0)))

    def emit(items):
        for it in items:
            flags = it["flags"]
            out.extend(struct.pack("<H", flags))
            if not (flags & 0x10):                     # 非 popup 项才有 ID 字
                out.extend(struct.pack("<H", it["id"] or 0))
            if flags & 0x0200:                         # MF_BITMAP: WORD 序号
                out.extend(struct.pack("<H", int(it["text"])))
            else:
                out.extend((it["text"] or "").encode("utf-16le"))
                out.extend(b"\x00\x00")
            if flags & 0x10:                           # popup: 子项紧随其后
                emit(it["children"] or [])

    emit(menu["items"])
    return bytes(out)


def _parse_menu_ex(buf: bytes):
    # MENUEX_TEMPLATE_HEADER: WORD wVersion(=1); WORD wOffset; DWORD dwHelpId
    # wOffset 从 WORD 对之后 (byte 4) 量起, 通常为 4 → 首个 MENUEX_TEMPLATE_ITEM 在 byte 8
    n = len(buf)
    ver, woffset = struct.unpack_from("<HH", buf, 0)
    helpid = struct.unpack_from("<I", buf, 4)[0] if n >= 8 else 0

    def items(pos):
        out = []
        while True:
            pos = (pos + 3) & ~3
            if pos + 14 > n:
                return out, pos, "truncated"
            mtype, mstate, mid = struct.unpack_from("<III", buf, pos)
            (resinfo,) = struct.unpack_from("<H", buf, pos + 12)
            pos += 14
            text, pos = decode_utf16z(buf, pos)
            it = {"type": mtype, "state": mstate, "resinfo": resinfo,
                  "id": mid, "text": text, "children": None}
            if resinfo & 0x01:  # popup
                if pos + 4 <= n:
                    it["helpid"] = struct.unpack_from("<I", buf, pos)[0]
                    pos += 4
                sub, pos, err = items(pos)
                it["children"] = sub
                if err:
                    it["parse_note"] = err
            out.append(it)
            if resinfo & 0x80:
                return out, pos, None

    tree, consumed, err = items(4 + woffset)
    return {"version": 1, "header_offset": woffset, "helpid": helpid,
            "items": tree, "consumed_bytes": consumed,
            "total_bytes": n, "parse_note": err}


# ======================================================================
# 无损 Dialog 编解码器 (PHASE 1B2.0)
#
# 设计目标: parse → serialize → byte-identical。
# AST 中保留全部原始字段与原始类型 (sz_or_ord 用结构化 kind 表示,
# 不把 ordinal class atom 永久替换成人类可读字符串; display 仅作展示)。
# alignment padding 按原样捕获 (pad_before / trailing), 不假设全零。
# STANDARD creation data 语义: 首 WORD S 非零时, S 包含 size WORD 自身
# (Windows 标准语义, 16 位遗留), 即总消耗 S*2 字节; EXTENDED extraCount
# 则仅表示其后的字节数 (不含字段本身)。两种格式不混用同一 size 语义。
# ======================================================================

DS_SETFONT = 0x40
DS_SHELLFONT = 0x48  # DS_SETFONT | DS_FIXEDSYS


def parse_sz_or_ord_ast(buf: bytes, pos: int, context: str = "generic"):
    """无损解析 sz_Or_Ord 字段。返回 ({kind, value, display}, new_pos)。"""
    if pos + 2 > len(buf):
        raise ValueError("sz_or_ord 越界")
    (w,) = struct.unpack_from("<H", buf, pos)
    if w == 0x0000:
        return {"kind": "none", "value": None, "display": None}, pos + 2
    if w == 0xFFFF:
        if pos + 4 > len(buf):
            raise ValueError("ordinal 越界")
        (v,) = struct.unpack_from("<H", buf, pos + 2)
        if context in ("window_class", "class") and v in CONTROL_CLASS_ATOMS:
            disp = CONTROL_CLASS_ATOMS[v]
        else:
            disp = f"ordinal:{v}"
        return {"kind": "ordinal", "value": v, "display": disp}, pos + 4
    text, pos2 = decode_utf16z(buf, pos)
    return {"kind": "string", "value": text, "display": text}, pos2


def serialize_sz_or_ord_ast(node) -> bytes:
    k = node["kind"]
    if k == "none":
        return struct.pack("<H", 0)
    if k == "ordinal":
        return struct.pack("<HH", 0xFFFF, node["value"])
    if k == "string":
        return node["value"].encode("utf-16le") + b"\x00\x00"
    raise ValueError(f"未知 sz_or_ord kind: {k!r}")


def _parse_dialog_ast_std(buf: bytes):
    n = len(buf)
    style, exstyle = struct.unpack_from("<II", buf, 0)
    (cdit,) = struct.unpack_from("<H", buf, 8)
    x, y, cx, cy = struct.unpack_from("<hhhh", buf, 10)
    pos = 18
    dmenu, pos = parse_sz_or_ord_ast(buf, pos, "menu")
    dclass, pos = parse_sz_or_ord_ast(buf, pos, "window_class")
    title, pos = decode_utf16z(buf, pos)
    font = None
    if style & DS_SETFONT:
        if pos + 2 > n:
            raise ValueError("font 越界 (std)")
        (pt,) = struct.unpack_from("<H", buf, pos)
        pos += 2
        face, pos = decode_utf16z(buf, pos)
        font = {"pointsize": pt, "typeface": face}
    controls = []
    for i in range(cdit):
        aligned = (pos + 3) & ~3
        pad_before = buf[pos:aligned]          # 原样捕获 (可能非全零)
        pos = aligned
        if pos + 18 > n:
            raise ValueError(f"控件 {i} 头越界 (std)")
        st, ex = struct.unpack_from("<II", buf, pos)
        ix, iy, icx, icy = struct.unpack_from("<hhhh", buf, pos + 8)
        (cid,) = struct.unpack_from("<H", buf, pos + 16)
        pos += 18
        wcls, pos = parse_sz_or_ord_ast(buf, pos, "class")
        wtitle, pos = parse_sz_or_ord_ast(buf, pos, "title")
        if pos + 2 > n:
            raise ValueError(f"控件 {i} creation size 越界 (std)")
        (S,) = struct.unpack_from("<H", buf, pos)
        if S == 0:
            creation = {"cb_word": 0, "data": b""}
            pos += 2
        else:
            total = S * 2                       # S 包含 size WORD 自身
            if pos + total > n:
                raise ValueError(f"控件 {i} creation data 越界 (std)")
            creation = {"cb_word": S, "data": buf[pos + 2: pos + total]}
            pos += total
        controls.append({"pad_before": pad_before, "style": st, "exstyle": ex,
                         "rect": [ix, iy, icx, icy], "id": cid,
                         "window_class": wcls, "title": wtitle,
                         "creation_data": creation})
    trailing = buf[pos:]
    return {"kind": "std", "header": {"style": style, "exstyle": exstyle,
            "cdit": cdit, "rect": [x, y, cx, cy]},
            "menu": dmenu, "window_class": dclass,
            "title": {"kind": "string", "value": title, "display": title},
            "font": font, "controls": controls, "trailing": trailing}


def _parse_dialog_ast_ex(buf: bytes):
    n = len(buf)
    dlgver, signature = struct.unpack_from("<HH", buf, 0)
    helpid, exstyle, style = struct.unpack_from("<III", buf, 4)
    (cdit,) = struct.unpack_from("<H", buf, 16)
    x, y, cx, cy = struct.unpack_from("<hhhh", buf, 18)
    pos = 26
    dmenu, pos = parse_sz_or_ord_ast(buf, pos, "menu")
    dclass, pos = parse_sz_or_ord_ast(buf, pos, "window_class")
    title, pos = decode_utf16z(buf, pos)
    font = None
    if style & DS_SETFONT:                     # DS_SETFONT / DS_SHELLFONT
        if pos + 6 > n:
            raise ValueError("font 越界 (ex)")
        pt, weight = struct.unpack_from("<HH", buf, pos)
        italic, charset = buf[pos + 4], buf[pos + 5]
        pos += 6
        face, pos = decode_utf16z(buf, pos)
        font = {"pointsize": pt, "weight": weight, "italic": italic,
                "charset": charset, "typeface": face}
    controls = []
    for i in range(cdit):
        aligned = (pos + 3) & ~3
        pad_before = buf[pos:aligned]
        pos = aligned
        if pos + 24 > n:
            raise ValueError(f"控件 {i} 头越界 (ex)")
        chelpid, cex, cst = struct.unpack_from("<III", buf, pos)
        ix, iy, icx, icy = struct.unpack_from("<hhhh", buf, pos + 12)
        (cid,) = struct.unpack_from("<I", buf, pos + 20)
        pos += 24
        wcls, pos = parse_sz_or_ord_ast(buf, pos, "class")
        wtitle, pos = parse_sz_or_ord_ast(buf, pos, "title")
        if pos + 2 > n:
            raise ValueError(f"控件 {i} extraCount 越界 (ex)")
        (cb,) = struct.unpack_from("<H", buf, pos)
        pos += 2                               # EX: cb 不含字段自身
        data = buf[pos: pos + cb]
        if len(data) != cb:
            raise ValueError(f"控件 {i} creation data 越界 (ex)")
        pos += cb
        controls.append({"pad_before": pad_before, "helpid": chelpid,
                         "exstyle": cex, "style": cst,
                         "rect": [ix, iy, icx, icy], "id": cid,
                         "window_class": wcls, "title": wtitle,
                         "extra_count": cb, "creation_data": data})
    trailing = buf[pos:]
    return {"kind": "ex", "dlgver": dlgver, "signature": signature,
            "header": {"helpid": helpid, "exstyle": exstyle, "style": style,
                       "cdit": cdit, "rect": [x, y, cx, cy]},
            "menu": dmenu, "window_class": dclass,
            "title": {"kind": "string", "value": title, "display": title},
            "font": font, "controls": controls, "trailing": trailing}


def parse_dialog_ast(buf: bytes):
    """无损解析 DLGTEMPLATE / DLGTEMPLATEEX 为 lossless AST。失败抛 ValueError。"""
    if len(buf) < 4:
        raise ValueError("buffer too small")
    dlgver, signature = struct.unpack_from("<HH", buf, 0)
    if dlgver == 1 and signature == 0xFFFF:
        return _parse_dialog_ast_ex(buf)
    return _parse_dialog_ast_std(buf)


def dialog_semantic_snapshot(ast):
    """结构语义快照 (与具体 padding/字节布局无关, 用于语义级比较)。"""
    def sz(node):
        if node is None or node["kind"] == "none":
            return None
        if node["kind"] == "ordinal":
            return ("ordinal", node["value"])
        return ("string", node["value"])

    snap = {
        "kind": ast["kind"],
        "style": ast["header"]["style"],
        "exstyle": ast["header"]["exstyle"],
        "rect": list(ast["header"]["rect"]),
        "menu": sz(ast["menu"]),
        "window_class": sz(ast["window_class"]),
        "title": ast["title"]["value"],
        "font": dict(ast["font"]) if ast["font"] else None,
        "control_count": len(ast["controls"]),
        "controls": [],
    }
    for c in ast["controls"]:
        clen = (len(c["creation_data"]["data"])
                if ast["kind"] == "std" and c["creation_data"]["cb_word"]
                else len(c.get("creation_data", b"")))
        snap["controls"].append({
            "helpid": c.get("helpid"),
            "style": c["style"], "exstyle": c["exstyle"], "rect": list(c["rect"]),
            "id": c["id"], "class": sz(c["window_class"]), "title": sz(c["title"]),
            "creation_len": clen,
        })
    return snap


def compare_semantic_snapshots(a, b, path=""):
    """比较两份语义快照, 返回差异列表 (空 = 语义一致)。"""
    diffs = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            diffs += compare_semantic_snapshots(a.get(k), b.get(k),
                                                f"{path}.{k}" if path else k)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f"{path}: 数量 {len(a)} → {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                diffs += compare_semantic_snapshots(x, y, f"{path}[{i}]")
    elif a != b:
        diffs.append(f"{path}: {a!r} → {b!r}")
    return diffs


def parse_dialog_template(buf: bytes):
    """兼容旧输出形状的分析视图 (内部基于无损 AST 投影)。"""
    try:
        ast = parse_dialog_ast(buf)
    except ValueError as exc:
        return {"error": str(exc)}
    return _project_dialog(ast)


def _project_dialog(ast):
    ctrl = []
    for c in ast["controls"]:
        cname = c["window_class"]["display"] if c["window_class"]["kind"] != "none" else None
        ttext = c["title"]["display"] if c["title"]["kind"] != "none" else ""
        ctrl.append({"id": c["id"], "class": cname, "text": ttext,
                     "rect": list(c["rect"]), "style": c["style"],
                     "exstyle": c["exstyle"]})
    common = {"style": ast["header"]["style"], "exstyle": ast["header"]["exstyle"],
              "title": ast["title"]["value"], "font": ast["font"],
              "items": ctrl,
              "item_count_expected": ast["header"]["cdit"],
              "item_count_parsed": len(ctrl),
              "parse_note": None}
    if ast["kind"] == "std":
        return {"version": 0, **common}
    return {"version": 1, "helpid": ast["header"]["helpid"], **common}


def parse_accelerators(buf: bytes):
    entries, pos = [], 0
    while pos + 8 <= len(buf) and len(entries) < 2048:
        fvirt, _pad, key, cmd = struct.unpack_from("<BBHH", buf, pos)
        pos += 8
        entries.append({"fvirt": fvirt, "key": key, "cmd": cmd})
        if fvirt & 0x80:
            break
    return entries


# --------------------------------------------------------------------------
# 辅助分析
# --------------------------------------------------------------------------

def flatten_menu_items(items, out=None):
    if out is None:
        out = []
    for it in items or []:
        out.append(it)
        if it.get("children"):
            flatten_menu_items(it["children"], out)
    return out


def scan_hardcoded(data: bytes, pe: PEFile, patterns):
    """在整份文件里查找 UTF-16LE / ASCII 字符串, 按所在节归类。"""
    results = {}
    for pat in patterns:
        entry = {}
        for enc in ("utf-16le", "ascii"):
            needle = pat.encode(enc)
            if len(needle) < 2:
                continue
            hits, start = {}, 0
            while True:
                i = data.find(needle, start)
                if i < 0:
                    break
                sec = pe.off2section(i)
                hits[sec] = hits.get(sec, 0) + 1
                start = i + len(needle)
            if hits:
                entry[enc] = hits
        if entry:
            results[pat] = entry
    return results


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------

def analyze(path: Path):
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    pe = PEFile(data)
    res = flatten_resources(pe)

    by_type = {}
    for r in res:
        e = by_type.setdefault(r["type_name"], {"count": 0, "bytes": 0, "langs": set()})
        e["count"] += 1
        e["bytes"] += r["size"]
        e["langs"].add(r["lang"])

    # ---- 字符串表 (按语言分桶: 同一块 ID 可能存在 1033/1041/2057 多语言副本) ----
    strings_by_lang = {}
    blocks = []
    for r in res:
        if r["type_name"] == "RT_STRING" and r["name_kind"] == "id" and r["file_offset"]:
            buf = data[r["file_offset"]: r["file_offset"] + r["size"]]
            block_id = r["name"]
            texts = parse_string_table(buf)
            blocks.append({"block_id": block_id, "lang": r["lang"], "size": r["size"]})
            bucket = strings_by_lang.setdefault(str(r["lang"]), {})
            for idx, t in enumerate(texts):
                sid = (block_id - 1) * 16 + idx
                bucket[sid] = t
    # 合并视图: 1033 优先, 其次 2057, 其余语言仅存档不覆盖
    strings = {}
    for lang in ("1033", "2057", "1041"):
        for sid, t in strings_by_lang.get(lang, {}).items():
            strings.setdefault(sid, t)
    nonempty = {k: v for k, v in strings.items() if v}
    nonempty_count_by_lang = {k: sum(1 for t in b.values() if t)
                              for k, b in strings_by_lang.items()}

    # ---- 菜单 ----
    menus = []
    for r in res:
        if r["type_name"] == "RT_MENU" and r["file_offset"]:
            buf = data[r["file_offset"]: r["file_offset"] + r["size"]]
            parsed = parse_menu_template(buf)
            flat = flatten_menu_items(parsed.get("items")) if "items" in parsed else []
            menus.append({
                "res_id": r["name"], "lang": r["lang"], "size": r["size"],
                "item_total": len(flat),
                "parse_note": parsed.get("parse_note") or parsed.get("error"),
                **{k: parsed[k] for k in ("version", "header_offset", "items",
                                          "consumed_bytes", "total_bytes") if k in parsed},
            })

    # ---- 对话框 ----
    dialogs = []
    for r in res:
        if r["type_name"] == "RT_DIALOG" and r["file_offset"]:
            buf = data[r["file_offset"]: r["file_offset"] + r["size"]]
            parsed = parse_dialog_template(buf)
            dialogs.append({
                "res_id": r["name"], "lang": r["lang"], "size": r["size"],
                "title": parsed.get("title"), "font": parsed.get("font"),
                "item_count": len(parsed.get("items", [])),
                "parse_note": parsed.get("parse_note") or parsed.get("error"),
                **{k: parsed[k] for k in ("version", "items") if k in parsed},
            })

    # ---- 加速键 ----
    accelerators = []
    for r in res:
        if r["type_name"] == "RT_ACCELERATOR" and r["file_offset"]:
            buf = data[r["file_offset"]: r["file_offset"] + r["size"]]
            accelerators.append({
                "res_id": r["name"], "lang": r["lang"], "size": r["size"],
                "entries": parse_accelerators(buf),
            })

    # ---- MANIFEST ----
    manifest = None
    for r in res:
        if r["type_name"] == "RT_MANIFEST" and r["file_offset"]:
            buf = data[r["file_offset"]: r["file_offset"] + r["size"]]
            manifest = buf.decode("utf-8", "replace")
            break

    # ---- 探针字符串命中 ----
    probe_hits = {}
    for probe in PROBE_STRINGS:
        hits = []
        for sid, text in nonempty.items():
            exact = (text == probe)
            contains = (probe.lstrip("&") in text)
            if exact or contains:
                hits.append({"string_id": sid, "text": text, "exact": exact})
            if len(hits) >= 8:
                break
        if hits:
            probe_hits[probe] = hits

    # ---- 探针字符串 → 所属资源 (按文件偏移归属, 找出菜单标题/命令文本的真实存放处) ----
    ivs = sorted((r["file_offset"], r["file_offset"] + r["size"], r)
                 for r in res if r["file_offset"])

    def owner(off):
        lo, hi = 0, len(ivs) - 1
        while lo <= hi:
            m = (lo + hi) // 2
            s, e, r = ivs[m]
            if off < s:
                hi = m - 1
            elif off >= e:
                lo = m + 1
            else:
                return r
        return None

    probe_owner = {}
    for probe in PROBE_STRINGS:
        nb = probe.encode("utf-16le")
        hits, start = {}, 0
        while True:
            i = data.find(nb, start)
            if i < 0:
                break
            r = owner(i)
            if r is None:
                key = "非资源区域"
            elif r["type_name"] == "RT_STRING":
                key = f"RT_STRING block={r['name']} lang={r['lang']}"
            else:
                key = f"{r['type_name']} id={r['name']} lang={r['lang']}"
            hits[key] = hits.get(key, 0) + 1
            start = i + len(nb)
        if hits:
            probe_owner[probe] = hits
    menu_probe_hits = {}
    for m in menus:
        for it in flatten_menu_items(m.get("items")):
            t = it.get("text") or ""
            for probe in PROBE_STRINGS:
                if probe.lstrip("&") in t:
                    menu_probe_hits.setdefault(probe, []).append(
                        {"menu_id": m["res_id"], "item_id": it.get("id"), "text": t})

    # ---- 硬编码扫描 ----
    hardcoded = scan_hardcoded(data, pe, HARDCODED_SCAN_PATTERNS)

    # ---- 自动观察 ----
    obs = []
    menu_named = [m["res_id"] for m in menus if m.get("res_id") is not None]
    obs.append(f"资源目录共 {len(res)} 个叶子节点, 覆盖 {len(by_type)} 种资源类型。")
    if menus:
        obs.append(f"RT_MENU 共 {len(menus)} 个菜单资源 (ID: {menu_named[:20]}"
                   f"{' ...' if len(menu_named) > 20 else ''}), 主菜单以标准菜单模板存放, 可通过重写模板汉化。")
    if dialogs:
        obs.append(f"RT_DIALOG 共 {len(dialogs)} 个对话框资源, 控件文本位于模板内, 可按控件逐条汉化。")
    if strings:
        obs.append(f"RT_STRING 共 {len(blocks)} 个块 / {len(nonempty)} 条非空字符串, "
                   f"全部为 UTF-16LE, 字符串 ID 连续可映射, 可原位换文案。")
    if accelerators:
        obs.append(f"RT_ACCELERATOR 共 {len(accelerators)} 个加速键表, 汉化菜单时需同步保留对应 & 助记键。")
    other_hits = {k: v for k, v in hardcoded.items()
                  if any(sec not in (".rsrc", "PE-header", "overlay(节表之外)")
                         for enc in v.values() for sec in enc)}
    if other_hits:
        obs.append("部分探针字符串也出现在代码节数据中 (.text/.rdata/.data), "
                   "属于程序内硬编码/格式字符串 —— Phase 1 不处理, 记录清单留待后续评估。")
    obs.append("资源语言 ID 见 summary.langs; 保持原 LANGID 不变即可, Windows 按资源 ID 加载, 不受影响。")

    return {
        "file": {"path": str(path), "size": len(data), "sha256": sha},
        "pe": {
            "machine": f"0x{pe.machine:04X} ({MACHINE_NAMES.get(pe.machine, '?')})",
            "arch": pe.arch,
            "subsystem": f"{pe.subsystem} ({SUBSYSTEM_NAMES.get(pe.subsystem, '?')})",
            "timestamp": pe.timestamp_iso(),
            "entry_rva": f"0x{pe.entry_rva:X}",
            "image_base": f"0x{pe.image_base:X}",
            "checksum": f"0x{pe.checksum:08X}",
            "dll_characteristics": pe.dll_characteristics_names(),
            "sections": [{"name": s.name, "vsize": s.vsize, "vaddr": s.vaddr,
                          "rawsize": s.rawsize, "rawptr": s.rawptr, "chars": s.chars}
                         for s in pe.sections],
            "data_directories": {i: v for i, v in enumerate(pe.data_dirs) if v[0]},
            "imports": pe.imports(),
        },
        "resources": {
            "summary": {t: {"count": e["count"], "bytes": e["bytes"],
                            "langs": sorted(map(str, e["langs"]))}
                        for t, e in sorted(by_type.items())},
            "menu_count": len(menus),
            "dialog_count": len(dialogs),
            "string_table": {
                "blocks": blocks,
                "nonempty_count": len(nonempty),
                "nonempty_count_by_lang": nonempty_count_by_lang,
                "strings": strings,
            },
            "accelerator_tables": len(accelerators),
            "probe_in_string_tables": probe_hits,
            "probe_resource_owner": probe_owner,
            "probe_in_menus": menu_probe_hits,
            "hardcoded_scan": hardcoded,
            "manifest": manifest,
        },
        "menus": menus,
        "dialogs": dialogs,
        "observations": obs,
    }


def print_summary(inv):
    f, pe, res = inv["file"], inv["pe"], inv["resources"]
    print("=" * 72)
    print("文件:", f["path"])
    print("大小:", f["size"], "bytes")
    print("SHA256:", f["sha256"])
    print("-" * 72)
    print(f"架构: {pe['arch']}  Machine={pe['machine']}  Subsystem={pe['subsystem']}")
    print(f"链接时间: {pe['timestamp']}   Entry=0x...{pe['entry_rva']}  ImageBase={pe['image_base']}")
    print(f"DllCharacteristics: {', '.join(pe['dll_characteristics']) or '(无)'}")
    print("-" * 72)
    print("节表:")
    for s in pe["sections"]:
        print(f"  {s['name']:<8} vsize=0x{s['vsize']:<8X} vaddr=0x{s['vaddr']:<8X} "
              f"raw=0x{s['rawsize']:<8X}@0x{s['rawptr']:<8X} chars=0x{s['chars']:08X}")
    mfc = [d for d in pe["imports"] if d.lower().startswith(("mfc", "msvcp", "vcruntime"))]
    print(f"导入 DLL 共 {len(pe['imports'])} 个; 关键运行库: {', '.join(mfc) or '(无 MFC/VC 运行库?)'}")
    print("-" * 72)
    print("资源类型汇总:")
    for t, e in res["summary"].items():
        print(f"  {t:<16} count={e['count']:<5} bytes={e['bytes']:<9} langs={','.join(e['langs'])}")
    print("-" * 72)
    print(f"菜单: {res['menu_count']} 个   对话框: {res['dialog_count']} 个   "
          f"加速键表: {res['accelerator_tables']} 个   "
          f"字符串表: {len(res['string_table']['blocks'])} 块 / "
          f"{res['string_table']['nonempty_count']} 条非空")
    print("-" * 72)
    print("探针字符串 → 菜单命中 (前 12 条):")
    shown = 0
    for probe, hits in res["probe_in_menus"].items():
        for h in hits[:2]:
            print(f"  MENU {h['menu_id']}  item_id={h['item_id']}  text={h['text']!r}")
            shown += 1
        if shown >= 12:
            break
    print("探针字符串 → 字符串表命中 (前 12 条):")
    shown = 0
    for probe, hits in res["probe_in_string_tables"].items():
        for h in hits[:2]:
            print(f"  STRING id={h['string_id']}  text={h['text']!r}")
            shown += 1
        if shown >= 12:
            break
    print("-" * 72)
    print("探针字符串 → 所属资源 (UTF-16LE, 定位主菜单标题等文本的真实存放处):")
    for probe, hits in res.get("probe_resource_owner", {}).items():
        print(f"  {probe!r}: {hits}")
    print("-" * 72)
    print("对话框标题样本 (前 15 个):")
    for d in inv["dialogs"][:15]:
        print(f"  res_id={d['res_id']}  title={d['title']!r}  items={d['item_count']}")
    print("-" * 72)
    print("硬编码字符串扫描 (全部命中按节归类; .rsrc 内的命中来自标准资源):")
    for pat, encs in inv["resources"]["hardcoded_scan"].items():
        print(f"  {pat!r}: {encs}")
    print("-" * 72)
    print("自动观察:")
    for o in inv["observations"]:
        print("  *", o)
    print("=" * 72)


def main(argv=None):
    ap = argparse.ArgumentParser(description="UV4.exe PE 资源只读扫描器")
    ap.add_argument("exe", help="待分析的 PE 文件路径")
    ap.add_argument("--json", help="完整 JSON 清单输出路径")
    ap.add_argument("--samples", type=int, default=15, help="打印样本条数")
    args = ap.parse_args(argv)

    path = Path(args.exe)
    inv = analyze(path)
    print_summary(inv)

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(inv, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print(f"完整清单已写入: {out}")


if __name__ == "__main__":
    main()
