#!/usr/bin/env python3
"""데이터·문서 빠른 점검 (표준 라이브러리만 사용, 원본은 읽기만 함).

사용법:
    python3 profile_data.py <파일 또는 폴더> [...] [--max-rows N] [--top K]

표(CSV, TSV), 엑셀(XLSX, 첫 행이 헤더라고 가정), JSON 배열·JSONL, 문서(.md, .txt)를 요약한다.
폴더를 주면 안의 파일을 모두 본다(.git, .harness, .agents 같은 숨김 폴더는 건너뜀).
"""
import argparse
import csv
import io
import json
import os
import re
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

TABLE_EXT = {".csv", ".tsv"}
XLSX_EXT = {".xlsx", ".xlsm"}
JSON_EXT = {".json", ".jsonl"}
DOC_EXT = {".md", ".markdown", ".txt", ".rst"}
SKIP_DIRS = {".git", ".harness", ".agents", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache"}
MISSING = {"", "na", "n/a", "null", "none", "nan", "-", "?", "#n/a"}
MAX_COLS = 40
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))  # 아주 긴 칸이 있어도 읽는다
MAX_FILES = 200

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


# ---------- 읽기 ----------
def read_text(path):
    raw = open(path, "rb").read()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16"), "utf-16"
    for enc in ("utf-8-sig", "cp949", "latin-1"):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        if enc == "utf-8-sig":
            return text, "utf-8 (BOM 있음)" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
        return text, enc
    return raw.decode("latin-1"), "latin-1"


def read_table(path, ext, max_rows):
    text, enc = read_text(path)
    if ext == ".tsv":
        delim = "\t"
    else:
        try:
            delim = csv.Sniffer().sniff(text[:20000], delimiters=",\t;|").delimiter
        except csv.Error:
            delim = ","
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delim)
    header, rows, truncated, total = None, [], False, 0
    for row in reader:
        if header is None:
            if not any(c.strip() for c in row):
                continue
            header = row
            continue
        total += 1
        if len(rows) >= max_rows:
            truncated = True
            continue  # 분석은 앞부분만, 행 수는 끝까지 센다
        rows.append(row)
    meta = f"{enc}, 구분자 {delim!r}" + (f", 전체 {total}행 중" if truncated else "")
    return header or [], rows, meta, truncated


def _col_index(ref):
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def read_xlsx(path, max_rows):
    """시트마다 (이름, 헤더, 행 목록, 잘림 여부)를 돌려준다."""
    out = []
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(NS + "si"):
                shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
        rels = {}
        if "xl/_rels/workbook.xml.rels" in names:
            for rel in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")):
                rels[rel.get("Id")] = rel.get("Target", "")
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        for sheet in workbook.iter(NS + "sheet"):
            target = rels.get(sheet.get(RNS + "id"), "").lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            if target not in names:
                continue
            grid, truncated = [], False
            for r in ET.fromstring(z.read(target)).iter(NS + "row"):
                cells = {}
                for pos, c in enumerate(r.iter(NS + "c")):
                    idx = _col_index(c.get("r")) if c.get("r") else pos
                    kind, v = c.get("t"), c.find(NS + "v")
                    if kind == "s" and v is not None and v.text:
                        k = int(v.text)
                        val = shared[k] if k < len(shared) else ""
                    elif kind == "inlineStr":
                        val = "".join(t.text or "" for t in c.iter(NS + "t"))
                    else:
                        val = v.text if v is not None and v.text is not None else ""
                    cells[idx] = val
                grid.append([cells.get(i, "") for i in range(max(cells) + 1)] if cells else [])
                if len(grid) > max_rows:
                    truncated = True
                    break
            grid = [row for row in grid if any(str(c).strip() for c in row)]
            header = grid[0] if grid else []
            out.append((sheet.get("name"), header, grid[1:], truncated))
    return out


def read_json(path, ext, max_rows):
    text, enc = read_text(path)
    bad = 0
    if ext == ".jsonl":
        items = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except ValueError:
                bad += 1
    else:
        data = json.loads(text)
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list) and v and isinstance(v[0], dict)), [data])
        items = data if isinstance(data, list) else [data]
    if bad:
        enc += f", 깨진 줄 {bad}개 건너뜀"
    items = [x for x in items if isinstance(x, dict)][:max_rows]
    keys = []
    for x in items:
        for k in x:
            if k not in keys:
                keys.append(k)
    rows = [["" if x.get(k) is None else (json.dumps(x[k], ensure_ascii=False) if isinstance(x[k], (dict, list)) else str(x[k])) for k in keys] for x in items]
    return keys, rows, enc


# ---------- 요약 ----------
def _num(s):
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _fmt(x):
    return f"{x:.4g}" if isinstance(x, float) else str(x)


def _shape(v):
    s = re.sub(r"[0-9]", "9", v)
    s = re.sub(r"[A-Za-z]+", "a", s)
    return re.sub(r"[가-힣]+", "가", s)


def _short(v, n=24):
    return v if len(v) <= n else v[: n - 1] + "…"


DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
    "%Y/%m/%d", "%Y%m%d %H%M%S", "%Y%m%d", "%Y.%m.%d", "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%m/%d/%Y",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M",
)


def _parse_date(v):
    from datetime import datetime
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    if len(v) >= 10 and v[:4].isdigit() and v[4] == "-":
        try:  # 2026-10-31T09:00:00+09:00 같은 ISO 형식 (시간대는 떼고 비교)
            return datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def profile_column(values, top):
    lines = []
    present = [v for v in values if v.strip().lower() not in MISSING]
    miss = Counter(v.strip() if v.strip() else "(빈칸)" for v in values if v.strip().lower() in MISSING)
    ws = sum(1 for v in values if v != v.strip() and v.strip())  # 공백만 있는 값은 결측(빈칸)으로 센다
    uniq = Counter(values)
    head = [f"고유 {len(uniq)}"]
    if miss:
        head.append("결측 " + ", ".join(f"{k} {c}" for k, c in miss.most_common(4)))
    if ws:
        head.append(f"앞뒤에 공백이 붙은 값 {ws}(빈칸 아님, 정리 필요)")
    nums = [x for x in (_num(v.strip()) for v in present) if x is not None]
    numeric = bool(present) and len(nums) >= 0.95 * len(present)
    if numeric:
        q = sorted(nums)
        head.append(f"숫자 최소 {_fmt(q[0])} · 중앙 {_fmt(statistics.median(q))} · 평균 {_fmt(statistics.fmean(q))} · 최대 {_fmt(q[-1])}")
        if len(q) >= 8:
            q1, q3 = q[len(q) // 4], q[(3 * len(q)) // 4]
            iqr = max(q3 - q1, 1e-9)
            fence, low_fence = q3 + 3 * iqr, q1 - 3 * iqr
            far = [x for x in q if x > fence]
            low = [x for x in q if x < low_fence]
            if far:
                head.append(f"큰 값 {len(far)}개(>{_fmt(fence)}, 최대 {_fmt(far[-1])})")
            if low:
                head.append(f"작은 값 {len(low)}개(<{_fmt(low_fence)}, 최소 {_fmt(low[0])})")
        lead0 = sum(1 for v in present if re.fullmatch(r"0\d+", v.strip()))
        if lead0:
            head.append(f"앞자리가 0인 값 {lead0}개(코드일 수 있음, 숫자로 바꾸면 0이 사라짐)")
        bad = Counter(v for v in present if _num(v.strip()) is None)
        if bad:
            head.append("숫자 아님 " + ", ".join(f"{_short(k)!r} {c}" for k, c in bad.most_common(3)))
    lines.append(" · ".join(head))
    if not numeric and present:
        lines.append("상위: " + ", ".join(f"{_short(v)!r} {c}" for v, c in Counter(present).most_common(top)))
        groups = defaultdict(Counter)
        for v, c in uniq.items():
            if v.strip().lower() not in MISSING:
                groups[re.sub(r"[\s\-_.]", "", v.lower())][v] += c
        multi = sorted((g for g in groups.values() if len(g) > 1), key=lambda g: -sum(g.values()))
        if multi:
            shown = " ; ".join("/".join(f"{_short(v)!r}×{c}" for v, c in g.most_common(4)) for g in multi[:4])
            lines.append(f"표기만 다른 값 {len(multi)}묶음: {shown}")
        shapes = Counter(_shape(v.strip()) for v in present)
        if 2 <= len(shapes) <= 8 and any(ch == "9" for s in shapes for ch in s):
            lines.append("형태: " + ", ".join(f"{s!r} {c}" for s, c in shapes.most_common(5)))
        sample = present[:2000]
        if sample and sum(_parse_date(v.strip()) is not None for v in sample) >= 0.8 * len(sample):
            parsed = [(v.strip(), _parse_date(v.strip())) for v in present]
            ok = [d for _, d in parsed if d is not None]
            bad = Counter(v for v, d in parsed if d is None)
            span = f"날짜 {min(ok):%Y-%m-%d %H:%M} ~ {max(ok):%Y-%m-%d %H:%M}"
            if bad:
                span += f" · 날짜로 못 읽는 값 {sum(bad.values())}: " + ", ".join(f"{_short(k)!r}" for k, _ in bad.most_common(3))
            lines.append(span)
    return lines


def profile_table(title, header, rows, meta, truncated, top):
    width = len(header)
    print(f"\n== {title}  ({meta}, {len(rows)}행 × {width}열{', 앞부분만 읽음' if truncated else ''})")
    if not header:
        print("  (빈 표)")
        return
    ragged = sum(1 for r in rows if len(r) != width)
    dup = sum(c - 1 for c in Counter(tuple(r) for r in rows).values() if c > 1)
    notes = [f"완전 중복 행 {dup}"]
    if ragged:
        notes.append(f"열 개수가 다른 행 {ragged}")
    print("  " + " · ".join(notes))
    for i, name in enumerate(header[:MAX_COLS]):
        values = [r[i] if i < len(r) else "" for r in rows]
        col_lines = profile_column(values, top)
        print(f"  [{name}] {col_lines[0]}")
        for extra in col_lines[1:]:
            print(f"      {extra}")
    if width > MAX_COLS:
        print(f"  … 열 {width - MAX_COLS}개 더 있음")


def profile_docs(docs):
    print(f"\n== 문서 {len(docs)}개 (이름, 글자 수, 앞부분)")
    for path in docs:
        text, _ = read_text(path)
        head = [ln.strip() for ln in text.splitlines() if ln.strip()][:6]
        print(f"  - {path} ({len(text)}자): " + " | ".join(_short(h, 40) for h in head))


# ---------- 실행 ----------
def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
                files.extend(os.path.join(root, n) for n in sorted(names) if not n.startswith("."))
        elif os.path.exists(p):
            files.append(p)
        else:
            print(f"(없는 경로: {p})")
    return files[:MAX_FILES], len(files) > MAX_FILES


def main(argv=None):
    ap = argparse.ArgumentParser(description="데이터·문서 빠른 점검")
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--max-rows", type=int, default=200000)
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)

    files, more = collect(args.paths)
    headers, docs, others = {}, [], []
    for path in files:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in TABLE_EXT:
                header, rows, meta, trunc = read_table(path, ext, args.max_rows)
                profile_table(path, header, rows, meta, trunc, args.top)
                headers[path] = header
            elif ext in XLSX_EXT:
                for name, header, rows, trunc in read_xlsx(path, args.max_rows):
                    profile_table(f"{path} [시트 {name}]", header, rows, "xlsx, 날짜는 일련번호일 수 있음", trunc, args.top)
                    headers[f"{path} [{name}]"] = header
            elif ext in JSON_EXT:
                keys, rows, enc = read_json(path, ext, args.max_rows)
                profile_table(path, keys, rows, f"{enc}, JSON", False, args.top)
            elif ext in DOC_EXT:
                docs.append(path)
            else:
                others.append(path)
        except BrokenPipeError:
            raise
        except Exception as exc:  # 한 파일이 깨져도 나머지는 계속 본다
            print(f"\n== {path}\n  읽지 못함: {type(exc).__name__}: {exc}")
    if docs:
        profile_docs(docs)
    names = list(headers)
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            sa, sb = set(headers[a]), set(headers[b])
            if sa != sb and len(sa & sb) >= max(2, 0.5 * min(len(sa), len(sb))):
                pairs.append((a, b, sorted(sa - sb), sorted(sb - sa)))
    if pairs:
        print("\n== 비슷한 표인데 열이 다른 곳 (열 이름 변경·추가 의심)")
        for a, b, only_a, only_b in pairs[:10]:
            print(f"  {a} ↔ {b}: 앞에만 {only_a or '-'} · 뒤에만 {only_b or '-'}")
    if others:
        print(f"\n== 그 밖의 파일 {len(others)}개: " + ", ".join(f"{p} ({os.path.getsize(p)}B)" for p in others[:20]))
    if more:
        print(f"\n(파일이 많아 앞의 {MAX_FILES}개만 봄)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # | head 처럼 출력이 중간에 끊겨도 조용히 끝낸다
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
