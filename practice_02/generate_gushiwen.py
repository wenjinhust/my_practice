#!/usr/bin/env python3
"""生成 2026 人教部编版九年级语文古诗文 Markdown。"""

from __future__ import annotations

from pathlib import Path

from catalog_2026 import CHANGES_2026, LOWER_CATALOG, TEXTBOOK_META, UPPER_CATALOG
from gushiwen_data import ALL_WORKS

ROOT = Path(__file__).parent


def render_work(w: dict) -> str:
    meta = TEXTBOOK_META
    lines = [
        f"# {w['title']}",
        "",
        f"> **教材**：{meta['edition']}（{meta['standard']}）  ",
        f"> **出版社**：{meta['publisher']}  ",
        f"> **册别**：{w['volume']}  ",
        f"> **单元**：{w.get('unit', '—')}  ",
        f"> **课序**：{w.get('lesson', '—')}  ",
        f"> **作者**：{w['author']}  ",
        f"> **类型**：{w.get('kind', '课内')}",
        "",
        "## 原文",
        "",
        w["original"].strip(),
        "",
    ]
    if w.get("pinyin"):
        lines += ["## 拼音", "", w["pinyin"].strip(), ""]
    if w.get("notes"):
        lines += ["## 注释", ""]
        for term, meaning in w["notes"].items():
            lines.append(f"- **{term}**：{meaning}")
        lines.append("")
    if w.get("translation"):
        lines += ["## 译文", "", w["translation"].strip(), ""]
    return "\n".join(lines)


def render_index(works: list[dict], title: str, catalog: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"> {TEXTBOOK_META['edition']} · {TEXTBOOK_META['year']}学年",
        "",
        catalog,
        "",
        f"## 已整理篇目（{len(works)} 篇）",
        "",
        "| 序号 | 篇目 | 课序 | 作者 | 类型 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for i, w in enumerate(works, 1):
        lines.append(
            f"| {i} | [{w['title']}]({w['filename']}) | {w.get('lesson', '—')} | {w['author']} | {w.get('kind', '课内')} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    upper = [w for w in ALL_WORKS if w["volume"] == "九年级上册"]
    lower = [w for w in ALL_WORKS if w["volume"] == "九年级下册"]

    for w in ALL_WORKS:
        subdir = ROOT / w["volume"]
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / w["filename"]).write_text(render_work(w), encoding="utf-8")

    (ROOT / "九年级上册" / "README.md").write_text(
        render_index(upper, "九年级上册 · 古诗文目录", UPPER_CATALOG),
        encoding="utf-8",
    )
    (ROOT / "九年级下册" / "README.md").write_text(
        render_index(lower, "九年级下册 · 古诗文目录", LOWER_CATALOG),
        encoding="utf-8",
    )

    meta = TEXTBOOK_META
    readme = f"""# 人教部编版九年级语文 · 古诗文汇编（{meta['year']}）

> **教材版本**：义务教育教科书·语文，{meta['edition']}  
> **课标依据**：{meta['standard']}  
> **出版社**：{meta['publisher']}  
> **启用说明**：{meta['note']}  
> **内容说明**：收录课内文言文、古诗词、词曲及「课外古诗词诵读」篇目，含原文、拼音、注释与译文。

## 2026 新教材调整要点

{CHANGES_2026}

## 篇目索引

| 册别 | 篇数 | 目录 |
| --- | --- | --- |
| 九年级上册 | {len(upper)} | [查看目录](九年级上册/README.md) |
| 九年级下册 | {len(lower)} | [查看目录](九年级下册/README.md) |
| **合计** | **{len(ALL_WORKS)}** | — |

## 生成方式

```bash
python generate_gushiwen.py
```
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"Generated {len(ALL_WORKS)} works ({meta['year']} edition).")


if __name__ == "__main__":
    main()
