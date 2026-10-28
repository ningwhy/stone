#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从维基文库抓取《红楼梦》第 N 回原文底本。

用法：python3 tools/fetch_chapter_source.py 005 006

输出：docs/chapterNN-source.txt
处理：取 MediaWiki revisions.content 原文 wikitext，去除样式模板、排版标签、版权模板、
      导航行；保留繁体原文用字与异体写法，不做简繁转换。
"""
import json
import re
import subprocess
import sys
import time
import urllib.parse

API = "https://zh.wikisource.org/w/api.php"
UA = "WorkBuddy-research/1.0 (chapter source fetch)"

# 需整体剔除的模板（按名字匹配整块 {{...}}）
DROP_TEMPLATES = [
    "样式:古典小说", "樣式:古典小說", "未校订", "未校訂",
    "清朝作品", "Copyrighted", "PD-old", "小說家", "小说家",
]
# 需整体剔除的标签
DROP_TAGS = ["center", "poem", "div", "references", "ref"]
# 顶部/底部导航行
NAV_PATTERNS = [
    re.compile(r"^\s*上一回\s*回目录\s*下一回\s*$"),
    re.compile(r"^\s*上一回\s*回目錄\s*下一回\s*$"),
    re.compile(r"^\s*<\s*上一回.*?下一回\s*>\s*$"),
]


def strip_templates(text: str) -> str:
    """反复移除 {{Name|...}} / {{Name}} 形式的模板块。"""
    out = text
    for name in DROP_TEMPLATES:
        # {{Name}} / {{Name|args}} / {{Name|args subst}}
        pattern = re.compile(r"\{\{\s*" + re.escape(name) + r"\b[^}]*\}\}", re.S)
        while pattern.search(out):
            out = pattern.sub("", out)
    return out


def strip_tags(text: str) -> str:
    for tag in DROP_TAGS:
        out = re.sub(r"</?%s[^>]*>" % re.escape(tag), "", text, flags=re.S | re.I)
        text = out
    return text


def extract_title(raw: str) -> str:
    """从 {{center|'''第五回　...'''}} 中取出回目名（含字一回目）。"""
    m = re.search(r"\{\{center\s*\|\s*'''\s*([^']*?)\s*'''", raw, re.S)
    if m:
        return re.sub(r"\s+", "　", m.group(1).strip())
    m = re.search(r"\{\{center\s*\|\s*([^{}|]*?)\s*\}\}", raw, re.S)
    if m:
        return re.sub(r"\s+", "　", m.group(1).strip())
    return ""


def clean(raw: str) -> str:
    title = extract_title(raw)
    text = raw
    # ① 先摘掉 <ref>…</ref> 注释块（内含各版本回目异文与书目），再摘其它标签
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S | re.I)
    text = re.sub(r"<ref[^>]*/>", "", text)
    text = strip_templates(text)
    text = strip_tags(text)
    # ② 剩余模板（有限次配平删除）
    for _ in range(8):
        new = re.sub(r"\{\{[^{}]*\}\}", "", text)
        if new == text:
            break
        text = new
    # ③ 标题标记 == 与章节锚点
    text = re.sub(r"^\s*={2,}\s*", "", text, flags=re.M)
    text = re.sub(r"\s*={2,}\s*$", "", text, flags=re.M)
    # ④ 水平分隔线 ----
    text = re.sub(r"^\s*-{4,}\s*$", "", text, flags=re.M)
    # ⑤ 粗体标记
    text = text.replace("'''", "")
    # ⑥ 链接
    text = re.sub(r"\[\[([^\[\]|]*)\|([^\[\]]*)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\[\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[(?:https?|ftp)://[^\s\]]+\s+([^\]]*)\]", r"\1", text)
    text = re.sub(r"\[(?:https?|ftp)://[^\s\]]+\]", "", text)
    # ⑦ 注释与 section 标记（<section begin="賦" /> 是维基文库的分区标记，非正文）
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"</?section[^>]*>", "", text)
    # ⑧ HTML 实体
    for ent, ch in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')):
        text = text.replace(ent, ch)

    lines = [ln.rstrip() for ln in text.split("\n")]
    kept = []
    for ln in lines:
        if any(p.match(ln) for p in NAV_PATTERNS):
            continue
        if re.match(r"^\s*回目录\s*$", ln) or re.match(r"^\s*回目錄\s*$", ln):
            continue
        if re.match(r"^\s*={0,2}\s*注释\s*={0,2}\s*$", ln):
            break  # 末尾注释段整体丢弃
        kept.append(ln)
    # 压缩连续空行
    out_lines = []
    blank = 0
    for ln in kept:
        if ln.strip() == "":
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        out_lines.append(ln)
    body = "\n".join(out_lines).strip()
    if title:
        body = title + "\n\n" + body
    return body + "\n"


def fetch(num: str) -> str:
    title = "紅樓夢/第%s回" % num
    params = {
        "action": "query", "prop": "revisions", "rvprop": "content",
        "rvslots": "main", "format": "json", "formatversion": "2", "titles": title,
    }
    url = API + "?" + urllib.parse.urlencode(params)
    # 维基文库对 urllib 的默认 UA/并发较敏感，改用 curl 取回
    proc = subprocess.run(
        ["curl", "-sS", "--compressed", "-m", "60", "-A", UA, url],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise SystemExit("curl 失败：%s" % proc.stderr.strip())
    data = json.loads(proc.stdout)
    pages = data.get("query", {}).get("pages", [])
    for pg in pages:
        if pg.get("missing"):
            continue
        revs = pg.get("revisions") or []
        if not revs:
            continue
        return revs[0]["slots"]["main"]["content"]
    raise SystemExit("未取到第%s回正文" % num)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for num in sys.argv[1:]:
        # 统一为三位回号用于抓取、两位回号用于落盘，与既有 chapter01~04-source.txt 一致
        num3 = num.zfill(3)
        raw = fetch(num3)
        text = clean(raw)
        path = "docs/chapter%s-source.txt" % num.zfill(2)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        chars = len(text.replace("\n", ""))
        print("%s -> %s  字符 %d  行 %d" % (num3, path, chars, text.count("\n")))
        time.sleep(3)


if __name__ == "__main__":
    main()
