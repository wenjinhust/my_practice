#!/usr/bin/env python3
"""Generate 2025 Shanghai exam handbook English vocabulary markdown."""

import csv
import re
from pathlib import Path

import eng_to_ipa as ipa
import xlwt

SOURCE = Path(__file__).parent / "exam_handbook_vocab_source.txt"
OUTPUT = Path(__file__).parent / "上海市初中英语考纲词汇表.md"
OUTPUT_EN_PHONETIC = Path(__file__).parent / "上海市初中英语考纲词汇表_英音标.md"
OUTPUT_POS_MEANING = Path(__file__).parent / "上海市初中英语考纲词汇表_词义.md"
OUTPUT_XLS = Path(__file__).parent / "上海市初中英语考纲词汇表.xls"
OUTPUT_EN_PHONETIC_XLS = Path(__file__).parent / "上海市初中英语考纲词汇表_英音标.xls"
OUTPUT_POS_MEANING_XLS = Path(__file__).parent / "上海市初中英语考纲词汇表_词义.xls"
OUTPUT_CSV = Path(__file__).parent / "上海市初中英语考纲词汇表.csv"
OUTPUT_EN_PHONETIC_CSV = Path(__file__).parent / "上海市初中英语考纲词汇表_英音标.csv"
OUTPUT_POS_MEANING_CSV = Path(__file__).parent / "上海市初中英语考纲词汇表_词义.csv"

HEADERS = ("序号", "英文单词", "音标", "词性", "中文含义")

_POS = (
    r"aux\.?\s*v\.?"
    r"|v\.?\s*aux\.?"
    r"|(?:abbr|aux|adj|adv|prep|conj|pron|int|num|vi|vt|n|v|a)(?:\.?\s*&\s*"
    r"(?:abbr|aux|adj|adv|prep|conj|pron|int|num|vi|vt|n|v|a)\.?)*"
    r"|n\.?\s*&\s*num\.?"
    r"|n\.?\s*&\s*adj\.?"
    r"|adj\.?\s*&\s*(?:prep|adv|n)\.?"
    r"|prep\.?\s*&\s*(?:adv|conj)\.?"
    r"|adv\.?\s*&\s*(?:n|conj|num)\.?"
    r"|conj\.?\s*&\s*adv\.?"
)

# pos 后可无空格，如 n.高度 / adj.远的
_POS_SUFFIX = r"\.?\s*"

POS_LINE = re.compile(rf"^(?P<pos>{_POS}){_POS_SUFFIX}(?P<meaning>.+)$", re.I)
ENTRY_LINE = re.compile(rf"^(?P<word>.+?)\s+(?P<pos>{_POS}){_POS_SUFFIX}(?P<meaning>.+)$", re.I)
LETTER = re.compile(r"^[A-Z]$")
PAGE_NUM = re.compile(r"^\d{1,3}$")
NO_POS = {
    "A.M. (a.m.)": "上午",
    "P.M. (p.m.)": "下午",
    "P. E.": "体育",
    "P.E.": "体育",
}
NO_POS_LINE = re.compile(
    r"^(?P<word>(?:A\.M\. \(a\.m\.\)|P\.M\. \(p\.m\.\)|P\.E\.))\s+(?P<meaning>.+)$",
    re.I,
)
WORD_MEANING = re.compile(r"^(?P<word>[A-Za-z].+?)\s+(?P<meaning>[\u4e00-\u9fff].+)$")
WORD_ONLY = re.compile(r"^[A-Za-z].*[\)）]$|^[A-Za-z].*\)$")


def extract_vocab_text(raw: str) -> str:
    start = raw.find("\nA\n")
    end = raw.find("\n词组(Phrases and Expressions)")
    if start == -1 or end == -1:
        raise ValueError("Cannot locate vocabulary section in source file")
    return raw[start + 1 : end]


def get_phonetic(word: str) -> str:
    clean = re.sub(r"\([^)]*\)", "", word)
    clean = re.sub(r"(复\s*)?", "", clean)
    clean = clean.replace("the ", "").strip()
    if not re.search(r"[a-zA-Z]", clean):
        return ""
    parts = re.split(r"[\s\-/=]+", clean)
    phonetics = []
    for part in parts:
        part = part.strip(".,;")
        if not part or not re.match(r"^[a-zA-Z]", part):
            continue
        p = ipa.convert(part.lower())
        if p and p != "*":
            phonetics.append(f"/{p}/")
    return " ".join(phonetics)


def _append_pos(current: dict, pos: str, meaning: str) -> None:
    pos = pos.strip().rstrip(".")
    meaning = meaning.strip()
    if current["pos"]:
        current["pos"] += " / " + pos
        current["meaning"] += "；" + meaning
    else:
        current["pos"] = pos
        current["meaning"] = meaning


def parse_vocab(text: str) -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or LETTER.match(line) or PAGE_NUM.match(line):
            continue
        if line.startswith("单词(Vocabulary)"):
            continue

        if line in NO_POS:
            if current:
                entries.append(current)
                current = None
            entries.append({"word": line, "pos": "", "meaning": NO_POS[line]})
            continue

        no_pos = NO_POS_LINE.match(line)
        if no_pos:
            if current:
                entries.append(current)
            current = None
            word = no_pos.group("word")
            if word.upper().replace(".", "").replace(" ", "") == "PE":
                word = "P.E."
            entries.append({"word": word, "pos": "", "meaning": no_pos.group("meaning").strip()})
            continue

        cont = POS_LINE.match(line)
        if cont and current and not ENTRY_LINE.match(line):
            _append_pos(current, cont.group("pos"), cont.group("meaning"))
            continue

        entry = ENTRY_LINE.match(line)
        if entry:
            if current:
                entries.append(current)
            current = {
                "word": entry.group("word").strip(),
                "pos": entry.group("pos").strip().rstrip("."),
                "meaning": entry.group("meaning").strip(),
            }
            continue

        wm = WORD_MEANING.match(line)
        if wm and not re.search(rf"\b({_POS})\.", line, re.I):
            if current:
                entries.append(current)
            current = {
                "word": wm.group("word").strip(),
                "pos": "",
                "meaning": wm.group("meaning").strip(),
            }
            continue

        if WORD_ONLY.match(line) and not POS_LINE.match(line):
            if current:
                entries.append(current)
            current = {"word": line, "pos": "", "meaning": ""}
            continue

        if current:
            if re.match(r"^\d+\s", line):
                current["meaning"] += "；" + line
            else:
                current["meaning"] += line

    if current:
        entries.append(current)
    return entries


def _normalize_pos(pos: str) -> str:
    return pos.replace(".", "").strip()


def _entry_rows(entries: list[dict]) -> list[tuple[int, str, str, str, str]]:
    rows = []
    for idx, e in enumerate(entries, 1):
        word = e["word"].replace("|", "\\|")
        phonetic = get_phonetic(e["word"])
        pos = _normalize_pos(e["pos"]).replace("|", "\\|")
        meaning = e["meaning"].replace("|", "\\|")
        rows.append((idx, word, phonetic, pos, meaning))
    return rows


def _table_header() -> list[str]:
    return [
        "| 序号 | 英文单词 | 音标 | 词性 | 中文含义 |",
        "| --- | --- | --- | --- | --- |",
    ]


def _meta_lines(title_suffix: str, note: str, count: int) -> list[str]:
    return [
        f"# 上海市初中英语考纲词汇表（2025考试手册{title_suffix}）",
        "",
        "> 数据来源：《2025年上海市初中毕业统一学业考试手册》英语词汇表",
        "> （上海市教育考试院发布，2025版配套教辅标注约1730词，本表按手册词表顺序整理）。",
        "> 表（一）单词；不含附录中的人称代词、数词和冠词。",
        f"> {note}",
        f"> 共收录 **{count}** 个单词/词条。",
        "",
    ]


def generate_full_markdown(entries: list[dict]) -> str:
    lines = _meta_lines("", "完整版：含英文、音标、词性、中文含义。", len(entries))
    lines.extend(_table_header())
    for idx, word, phonetic, pos, meaning in _entry_rows(entries):
        lines.append(f"| {idx} | {word} | {phonetic} | {pos} | {meaning} |")
    return "\n".join(lines) + "\n"


def generate_en_phonetic_markdown(entries: list[dict]) -> str:
    lines = _meta_lines(
        "·英音标",
        "练习版：仅保留序号、英文单词、音标；词性、中文含义留空。",
        len(entries),
    )
    lines.extend(_table_header())
    for idx, word, phonetic, _, _ in _entry_rows(entries):
        lines.append(f"| {idx} | {word} | {phonetic} |  |  |")
    return "\n".join(lines) + "\n"


def generate_pos_meaning_markdown(entries: list[dict]) -> str:
    lines = _meta_lines(
        "·词义",
        "练习版：仅保留序号、词性、中文含义；英文单词、音标留空。",
        len(entries),
    )
    lines.extend(_table_header())
    for idx, _, _, pos, meaning in _entry_rows(entries):
        lines.append(f"| {idx} |  |  | {pos} | {meaning} |")
    return "\n".join(lines) + "\n"


def write_xls(path: Path, rows: list[tuple[int, str, str, str, str]]) -> None:
    workbook = xlwt.Workbook(encoding="utf-8")
    sheet = workbook.add_sheet("考纲词汇")

    header_style = xlwt.XFStyle()
    header_font = xlwt.Font()
    header_font.bold = True
    header_style.font = header_font

    col_widths = [5 * 256, 20 * 256, 20 * 256, 10 * 256, 40 * 256]
    for col, width in enumerate(col_widths):
        sheet.col(col).width = width

    for col, title in enumerate(HEADERS):
        sheet.write(0, col, title, header_style)

    for row_idx, (idx, word, phonetic, pos, meaning) in enumerate(rows, start=1):
        sheet.write(row_idx, 0, idx)
        sheet.write(row_idx, 1, word)
        sheet.write(row_idx, 2, phonetic)
        sheet.write(row_idx, 3, pos)
        sheet.write(row_idx, 4, meaning)

    workbook.save(str(path))


def write_csv(path: Path, rows: list[tuple[int, str, str, str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        for idx, word, phonetic, pos, meaning in rows:
            writer.writerow([idx, word, phonetic, pos, meaning])


def main():
    raw = SOURCE.read_text(encoding="utf-8")
    entries = parse_vocab(extract_vocab_text(raw))
    rows = _entry_rows(entries)

    OUTPUT.write_text(generate_full_markdown(entries), encoding="utf-8")
    OUTPUT_EN_PHONETIC.write_text(generate_en_phonetic_markdown(entries), encoding="utf-8")
    OUTPUT_POS_MEANING.write_text(generate_pos_meaning_markdown(entries), encoding="utf-8")

    write_xls(OUTPUT_XLS, rows)
    write_xls(
        OUTPUT_EN_PHONETIC_XLS,
        [(idx, word, phonetic, "", "") for idx, word, phonetic, _, _ in rows],
    )
    write_xls(
        OUTPUT_POS_MEANING_XLS,
        [(idx, "", "", pos, meaning) for idx, _, _, pos, meaning in rows],
    )

    write_csv(OUTPUT_CSV, rows)
    write_csv(
        OUTPUT_EN_PHONETIC_CSV,
        [(idx, word, phonetic, "", "") for idx, word, phonetic, _, _ in rows],
    )
    write_csv(
        OUTPUT_POS_MEANING_CSV,
        [(idx, "", "", pos, meaning) for idx, _, _, pos, meaning in rows],
    )

    print(f"Generated {len(entries)} entries:")
    print(f"  {OUTPUT.name}")
    print(f"  {OUTPUT_EN_PHONETIC.name}")
    print(f"  {OUTPUT_POS_MEANING.name}")
    print(f"  {OUTPUT_XLS.name}")
    print(f"  {OUTPUT_EN_PHONETIC_XLS.name}")
    print(f"  {OUTPUT_POS_MEANING_XLS.name}")
    print(f"  {OUTPUT_CSV.name}")
    print(f"  {OUTPUT_EN_PHONETIC_CSV.name}")
    print(f"  {OUTPUT_POS_MEANING_CSV.name}")


if __name__ == "__main__":
    main()
