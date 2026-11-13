#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取得某一回的底本并写成 docs/chapterNN-source.txt。

按 docs/production/research.md 的规矩：底本必须来自真实来源，逐字保存，
去掉导航、样式与许可页脚，并记录版本、回目、来源地址、取得日期与文字处理方法。
本脚本从中文维基文库（zh.wikisource.org）取《紅樓夢》各回正文：
用 MediaWiki 的 action=raw 取到 wikitext，转成纯文本（去 <poem> 标记、拆行成段），
再用 OpenCC 转成简体——本项目既有底本（chapter10–12）均为简体。

用法：
    python3 scripts/fetch_chapter_source.py 13 14 15
    python3 scripts/fetch_chapter_source.py --force 13

注意：action=raw 的正文页含 {{样式:古典小說}}、回目录导航与 {{清朝作品}} 页脚，
这些都要去掉；「上一回／下一回」导航行同样去掉。
"""
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
API = 'https://zh.wikisource.org/w/index.php'
UA = 'HonglouStoryMap/1.0 (local research; contact: local)'

TITLE = '紅樓夢/第{n:03d}回'


def fetch_raw(n: int) -> str:
    """取回该回的 wikitext。

    维基文库对高频请求会返回 Wikimedia 错误页（正文里混着 CSS 的 `}}`），
    所以：先看本地缓存 /tmp/chNNN_raw.txt，再走带退避的重试。
    """
    cache = Path(f'/tmp/ch{n:03d}_raw.txt')
    if cache.exists():
        cached = cache.read_text(encoding='utf-8')
        if cached.lstrip().startswith('{{') or cached.lstrip().startswith('[['):
            return cached
    title = TITLE.format(n=n)
    url = f'{API}?title={title}&action=raw'
    last = ''
    for attempt in range(5):
        res = subprocess.run(
            ['curl', '-sS', '-m', '60', '-A', UA, url],
            capture_output=True, text=True, check=True)
        last = res.stdout
        if res.returncode == 0 and last.strip() and not last.lstrip().startswith('<!DOCTYPE html>'):
            cache.write_text(last, encoding='utf-8')
            return last
        time.sleep(6 * (attempt + 1))
    raise SystemExit(f'第{n}回取回失败（维基限流）：{last[:120]!r}')


def to_plain(raw: str) -> str:
    """wikitext -> 纯文本正文。"""
    text = raw
    # 章节标题行：保留纯文字，去掉 center/bold 标记。
    # 回目行与正文首句之间可能没有空行（第 20 回就没有）——单换行会被
    # 下面的并段逻辑折进同一段，回目于是粘在正文上。替换成「回目 + 空行」，
    # 让回目永远自成一段。
    text = re.sub(r"\{\{center\|'''(.*?)'''\}\}", r'\1\n\n', text, flags=re.S)
    text = re.sub(r'\{\{样式:[^}]*\}\}', '', text)
    text = re.sub(r'\{\{清朝作品\}\}', '', text)
    # 回目录导航
    text = re.sub(r'\[\[\.\./第\d{3}回\|[^\]]*\]\]', '', text)
    text = re.sub(r'\[\[\.\./\|[^\]]*\]\]', '', text)
    text = re.sub(r'\[\[([^\]|]*)\|([^\]]*)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    # 注释与模板（模板可嵌套，需反复剥到干净）
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    for _ in range(20):
        stripped = re.sub(r'\{\{[^{}]*\}\}', '', text)
        if stripped == text:
            break
        text = stripped
    # 诗体：<poem>…</poem> 的内容本身是正文，逐行保留，只去掉标签
    text = re.sub(r'</?poem>', '', text)
    # 分隔线
    text = re.sub(r'\n----\s*\n', '\n\n', text)
    # 段落内的换行（维基用单换行连缀同一段）→ 变成空格，保持段落完整
    lines = [ln.rstrip() for ln in text.split('\n')]
    paras, buf = [], []
    for ln in lines:
        if not ln.strip():
            if buf:
                paras.append(''.join(buf))
                buf = []
            continue
        buf.append(ln.strip())
    if buf:
        paras.append(''.join(buf))
    out = []
    for p in paras:
        p = re.sub(r'[ \t]+', '', p)
        if p:
            out.append(p)
    return '\n\n'.join(out) + '\n'


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv
    if not args:
        print(__doc__)
        return 1
    from opencc import OpenCC
    t2s = OpenCC('t2s')

    for raw_arg in args:
        n = int(raw_arg)
        out_path = DOCS / f'chapter{n:02d}-source.txt'
        if out_path.exists() and not force:
            print(f'第{n}回底本已存在，跳过（--force 可覆盖）：{out_path.name}')
            continue
        wikitext = fetch_raw(n)
        plain = to_plain(wikitext)
        simplified = t2s.convert(plain)
        # 简体化后再核一次：不该再有残留的维基标记
        for bad in ('{{', '}}', '[[', ']]', '<poem>', '上一回', '下一回', '回目录'):
            if bad in simplified:
                raise SystemExit(f'第{n}回清理不干净，仍含 {bad!r}')
        header = (
            f'《红楼梦》第{n:03d}回 · 底本\n'
            f'================================================\n'
            f'来源：中文维基文库（zh.wikisource.org）《紅樓夢》第{n:03d}回\n'
            f'来源地址：{API}?title={TITLE.format(n=n)}&action=raw\n'
            f'取得日期：{date.today().isoformat()}\n'
            f'版本说明：维基文库《紅樓夢》程乙本/高鹗本整理稿（繁体），'
            f'本文件由 OpenCC t2s 转为简体，去导航、样式与许可页脚，'
            f'并按维基段落拆行；正文未作增删。\n'
            f'================================================\n\n')
        out_path.write_text(header + simplified, encoding='utf-8')
        print(f'第{n}回底本已写入 {out_path.name}（{len(simplified)} 字）')
        time.sleep(2)
    return 0


if __name__ == '__main__':
    sys.exit(main())
