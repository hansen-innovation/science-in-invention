"""Stage 1 of the pipeline: get patent descriptions and find in-text citation windows.

Two sources are supported:
  (a) Google Patents pages (used for the pilots; fine for samples of hundreds of patents):
      --source google --assignee "Genentech" --n 25 --after-priority 20170101
      --source google --assignee "Eli Lilly~Lilly" --after-priority 19800101 --before-publication 19891231 \
          --tag sector=pharma --tag decade=1980s
      An --assignee value is "search query~regex": the query goes to Google's fuzzy assignee search and the
      regex (case-insensitive; defaults to the query) must match the assignee printed in the search result,
      which keeps spin-offs and reassignments (Affymetrix for "General Electric") out of the sample.
  (b) PatentsView bulk 'g_detail_desc_text' files for the full build (tens of millions of
      paragraphs; run window_finder over the bulk CSV, no HTTP needed):
      --source patentsview --desc-file g_detail_desc_text.tsv --patent-ids ids.txt

Output: JSONL of citation windows, one row per candidate citation, with patent metadata (assignee, title,
priority and grant dates from the search result) and any --tag key=value pairs attached to every row.
The window finder is deliberately high-recall (it accepts 'et al.' in patent citations); the
cited-document-type label in the labeling stage removes non-paper citations.

Note on the first pilot: the same logic was executed in the browser (JavaScript, see
pilot/README_pilot_method.md) because the pilot machine could not reach patents.google.com
directly. The decade sample (pilot/decades/) was fetched with this file.
"""
import argparse, csv, json, re, sys, time
from html.parser import HTMLParser

CIT = re.compile(
    r"\bet al\b|\b(?:J\.|Journal of|Nature\b|Science\b|Cell\b|Proc\. Natl|PNAS|Lancet|N\.? Engl|Biochem|"
    r"Phys\. Rev\.|arXiv|doi:|Nucleic Acids|Cancer Res|Chem\. Soc|Angew|Adv\. Mater|Appl\. Phys)"
    r"[^.]{0,80}?\b(?:19|20)\d{2}\b")
CIT_IEEE = re.compile(r"\bIEEE\b|" + CIT.pattern)  # --cue-ieee: electronics venues are rarely "et al." in the text
PATENT_ONLY = re.compile(r"U\.?S\.? ?Pat(?:ent)?\.? ?(?:No\.?|Application|Publication|Pub\.)|WO\s?\d{2,4}/\d+|EP\s?\d{6,}|US\s?\d{4}/\d+", re.I)
PAPER_CUE = re.compile(r"IEEE|\bvol\.|\bpp\.|Journal|\bJ\. |Proc\.|Phys\.|Lett\.|Trans\.|Symp|Conf\.|arXiv|doi", re.I)
ASSIGNEE_RX = [re.compile(r'itemprop="assigneeOriginal"[^>]*>([^<]+)<'), re.compile(r'itemprop="assigneeCurrent"[^>]*>([^<]+)<')]
TAG_RX = re.compile(r"<[^>]+>")


def windows(paragraphs, max_per_patent=None, before=380, after=420, cit=CIT):
    """Yield (para_idx, window_text, looks_patent_only) for paragraphs with a citation cue."""
    n = 0
    for i, t in enumerate(paragraphs):
        m = cit.search(t)
        if not m:
            continue
        s, e = max(0, m.start() - before), min(len(t), m.start() + after)
        w = ("…" if s > 0 else "") + t[s:e] + ("…" if e < len(t) else "")
        yield i, w, bool(PATENT_ONLY.search(w)) and not re.search(r"\b(?:19|20)\d{2}\)|\d+:\d+", w)
        n += 1
        if max_per_patent and n >= max_per_patent:
            break


class _Desc(HTMLParser):
    """Collect description paragraphs from a Google Patents HTML page."""
    def __init__(self):
        super().__init__(); self.in_p = 0; self.buf = []; self.paras = []; self.meta = {}
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "description-paragraph" in (a.get("class") or ""):
            self.in_p += 1; self.buf = []
        if tag == "meta" and a.get("name") == "DC.title":
            self.meta["title"] = a.get("content", "").strip()
        if tag == "time" and a.get("itemprop") in ("priorityDate", "publicationDate"):
            self.meta[a["itemprop"]] = a.get("datetime", "")
    def handle_endtag(self, tag):
        if tag == "div" and self.in_p:
            self.in_p -= 1
            txt = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if len(txt) > 40:
                self.paras.append(txt)
    def handle_data(self, data):
        if self.in_p:
            self.buf.append(data)


def assignee_of(html):
    for rx in ASSIGNEE_RX:
        m = rx.search(html)
        if m:
            return " ".join(m.group(1).split())
    return ""


def google_patents(query, n, session, after_priority="20170101", before_priority=None, before_publication=None,
                   match=None, text='"et al"'):
    """Granted US patents for an assignee query via the Google Patents XHR endpoint.

    Returns dicts {pn, assignee, title, priority_date, grant_date} in Google's ranking order, keeping only
    results whose assignee matches `match` (regex, case-insensitive) when given. `text` is the full-text
    query ('"et al"' by default; "IEEE" for the electronics top-up; None for no text filter). Pre-2001 grants
    carry kind code A (US4570623A), later grants B1/B2; status=GRANT keeps applications out.
    """
    from urllib.parse import quote
    q = (f"q%3D{quote(text, safe='')}%26" if text else "") + "assignee%3D" + query.replace(" ", "+") + \
        f"%26country%3DUS%26status%3DGRANT%26after%3Dpriority%3A{after_priority}" + \
        (f"%26before%3Dpriority%3A{before_priority}" if before_priority else "") + \
        (f"%26before%3Dpublication%3A{before_publication}" if before_publication else "") + \
        f"%26type%3DPATENT%26num%3D{n}"
    r = session.get("https://patents.google.com/xhr/query?url=" + q + "&exp=", headers={"accept": "application/json"}, timeout=30)
    r.raise_for_status()
    out = []
    for c in r.json().get("results", {}).get("cluster", []):
        for x in c.get("result", []):
            p = x["patent"]; pn = p["publication_number"]
            asg = " ".join(TAG_RX.sub("", p.get("assignee", "")).split())
            if not re.search(r"(?:A|B[12])$", pn):
                continue
            if match and not re.search(match, asg, re.I):
                continue
            out.append({"pn": pn, "assignee": asg, "title": " ".join(TAG_RX.sub("", p.get("title", "")).split()),
                        "priority_date": p.get("priority_date", ""), "grant_date": p.get("grant_date", "")})
    return out


def fetch_one(it, session, max_per_patent=None, cit=CIT):
    """Citation-window rows for one patent; `it` is a dict from google_patents() or {"pn": ...}
    (metadata missing there is read from the page). Returns [] on HTTP errors."""
    pn = it["pn"]
    r = session.get(f"https://patents.google.com/patent/{pn}/en", timeout=60)
    time.sleep(1.0)
    if r.status_code != 200:
        print(f"{pn}: HTTP {r.status_code}", file=sys.stderr); return []
    html = r.content.decode("utf-8", errors="replace")  # pages are UTF-8; requests may guess Latin-1
    p = _Desc(); p.feed(html)
    meta = {"pn": pn, "assignee": it.get("assignee") or assignee_of(html),
            "title": it.get("title") or " ".join(p.meta.get("title", "").split()),
            "priority_date": it.get("priority_date") or p.meta.get("priorityDate", ""),
            "grant_date": it.get("grant_date") or p.meta.get("publicationDate", ""), "n_desc_paras": len(p.paras)}
    return [dict(meta, para_idx=i, text=w, regex_patent_only=patent_only) for i, w, patent_only in windows(p.paras, max_per_patent, cit=cit)]


def fetch_google(items, session, max_per_patent=None, cit=CIT):
    for it in items:
        yield from fetch_one(it, session, max_per_patent, cit)


def fetch_patentsview(desc_file, patent_ids, max_per_patent=None):
    """PatentsView g_detail_desc_text.tsv: columns patent_id, description_text (one row per patent)."""
    want = set(patent_ids)
    with open(desc_file, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["patent_id"] not in want:
                continue
            paras = [p.strip() for p in re.split(r"\n\s*\n|(?<=\.)\s{2,}", row["description_text"]) if len(p.strip()) > 40]
            for i, w, patent_only in windows(paras, max_per_patent):
                yield {"pn": "US" + row["patent_id"], "para_idx": i, "text": w, "regex_patent_only": patent_only}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["google", "patentsview"], required=True)
    ap.add_argument("--assignee", action="append", default=[], help='"query" or "query~regex" (see module docstring)')
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--per-assignee", type=int, default=2); ap.add_argument("--max-windows", type=int, default=0)
    ap.add_argument("--after-priority", default="20170101"); ap.add_argument("--before-priority", default=None)
    ap.add_argument("--before-publication", default=None)
    ap.add_argument("--tag", action="append", default=[], help="key=value attached to every row (e.g. sector=pharma)")
    ap.add_argument("--query", default='"et al"', help="Google Patents full-text query (default '\"et al\"'; e.g. IEEE)")
    ap.add_argument("--cue-ieee", action="store_true", help="also treat 'IEEE' as a citation cue in the window finder")
    ap.add_argument("--require-paper-cue", action="store_true",
                    help="walk the ranking and keep only patents with at least one window that looks like a paper citation, until --per-assignee are kept")
    ap.add_argument("--desc-file"); ap.add_argument("--patent-ids")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    tags = dict(t.split("=", 1) for t in a.tag)
    cit = CIT_IEEE if a.cue_ieee else CIT
    k = 0
    with open(a.output, "w", encoding="utf-8") as out:
        if a.source == "google":
            import requests
            s = requests.Session(); s.headers["User-Agent"] = "science-in-invention (academic; see README)"
            for spec in a.assignee:
                query, _, match = spec.partition("~")
                items = google_patents(query, a.n, s, a.after_priority, a.before_priority, a.before_publication, match or re.escape(query), a.query)
                kept, span = 0, f"{a.after_priority}-{a.before_publication or a.before_priority or ''}"
                for it in items:
                    if kept >= a.per_assignee:
                        break
                    rows = fetch_one(it, s, a.max_windows or None, cit)
                    if a.require_paper_cue and not any(PAPER_CUE.search(r["text"]) and not r["regex_patent_only"] for r in rows):
                        print(f"{query} {span}: skip {it['pn']} ({len(rows)} windows, no paper cue)", file=sys.stderr); continue
                    kept += 1
                    print(f"{query} {span}: {it['pn']} ({it['assignee']}, {it['grant_date']}) {len(rows)} windows", file=sys.stderr)
                    for row in rows:
                        row["query_assignee"] = query; row.update(tags); k += 1
                        out.write(json.dumps(row, ensure_ascii=False) + "\n")
        else:
            ids = [l.strip() for l in open(a.patent_ids) if l.strip()]
            for row in fetch_patentsview(a.desc_file, ids, a.max_windows or None):
                row.update(tags); k += 1; out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{k} windows -> {a.output}", file=sys.stderr)
