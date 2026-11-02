"""Stage 1 of the pipeline: get patent descriptions and find in-text citation windows.

Two sources are supported:
  (a) Google Patents pages (used for the pilots; fine for samples of hundreds of patents):
      --source google --assignee "Genentech" --n 25 --after-priority 20170101
      --source google --assignee "Eli Lilly~Lilly" --after-priority 19800101 --before-publication 19891231 \
          --tag sector=pharma --tag decade=1980s
      --source google --assignee "Du Pont~Du Pont|DuPont" --after-priority 19200101 --before-publication 19291231 \
          --query "" --require-paper-cue --cue-early --tag sector=chemicals --tag decade=1920s
          (pre-1976 OCR text: no full-text filter, walk the ranking and keep patents with a paper-looking
          citation; --cue-early also accepts "Journal ..., vol. 12, p. 34" without a year)
      An --assignee value is "search query~regex": the query goes to Google's fuzzy assignee search and the
      regex (case-insensitive; defaults to the query) must match the assignee printed in the search result,
      which keeps spin-offs and reassignments (Affymetrix for "General Electric") out of the sample.
  (b) PatentsView bulk 'g_detail_desc_text' files for the full build (tens of millions of
      paragraphs; run window_finder over the bulk CSV, no HTTP needed):
      --source patentsview --desc-file g_detail_desc_text.tsv --patent-ids ids.txt
  (c) Saved descriptions, one JSON object per line with pn, description and optional assignee, title,
      priority_date, grant_date, cell (e.g. Google Patents Public Data pulled from BigQuery, the route used for the
      pre-1976 decade cells after Google Patents blocked the scraper):
      --source textfile --desc-file descriptions.jsonl --cue-early --max-windows 3

Output: JSONL of citation windows, one row per candidate citation, with patent metadata (assignee, title,
priority and grant dates from the search result) and any --tag key=value pairs attached to every row.
The window finder is deliberately high-recall (it accepts 'et al.' in patent citations); the
cited-document-type label in the labeling stage removes non-paper citations.

Note on the first pilot: the same logic was executed in the browser (JavaScript, see
pilot/README_pilot_method.md) because the pilot machine could not reach patents.google.com
directly. The decade sample (pilot/decades/) was fetched with this file.
"""
import argparse, csv, html, json, re, sys, time
from html.parser import HTMLParser

CIT = re.compile(
    r"\bet al\b|\b(?:J\.|Journal of|Nature\b|Science\b|Cell\b|Proc\. Natl|PNAS|Lancet|N\.? Engl|Biochem|"
    r"Phys\. Rev\.|arXiv|doi:|Nucleic Acids|Cancer Res|Chem\. Soc|Angew|Adv\. Mater|Appl\. Phys)"
    r"[^.]{0,80}?\b(?:19|20)\d{2}\b")
CIT_IEEE = re.compile(r"\bIEEE\b|" + CIT.pattern)  # --cue-ieee: electronics venues are rarely "et al." in the text
CIT_EARLY = re.compile(  # --cue-early: pre-1976 citations often give journal, volume and page but no year
    r"(?:Journal|Journ\.|Jour\.|Berichte|Zeitschrift|Annalen|Transactions|Trans\.|Proceedings|Comptes|Bulletin|Bull\.|"
    r"Chemical Society|Chem\. Soc|Physical Review|Phys\. Rev|Philosophical Magazine|Phil\. Mag|Jahrbuch|Monatshefte)"
    r"[^.]{0,80}?\b(?:[Vv]ol\.?|[Vv]olume|[Pp]age|pp?\.|Bd\.|S\.)\s*\d|"
    r"\bpublished in\b[^.]{0,40}\b(?:18|19)\d{2}\b|\bVolume [IVXLC]+\b|" + CIT_IEEE.pattern)
PATENT_ONLY = re.compile(r"U\.?S\.? ?Pat(?:ent)?\.? ?(?:No\.?|Application|Publication|Pub\.)|WO\s?\d{2,4}/\d+|EP\s?\d{6,}|US\s?\d{4}/\d+", re.I)
PAPER_CUE = re.compile(r"IEEE|\bvol\.|\bpp\.|\bJournal\b|\bJ\. (?![A-Z]{3,})[A-Z]|Proc\.|Phys\.|Lett\.|Trans\.|Symp|Conf\.|arXiv|doi|Berichte|Zeitschrift|Annalen|Comptes|Bulletin|Volume [IVXLC]+\b|published in")
# Window choice for the long-run fill (Nov 2, 2026): among the 2,966 pre-1980 long-run windows labeled by
# claude-opus-5-5, a window with a SCIENCE_CUE and no PATENT_CUE cited science 95% of the time (1,916 of 2,022);
# with a patent number as well, 31%; with neither cue, 55%.
SCIENCE_CUE = re.compile(
    r"\bJournal\b|\bJ\. ?[A-Z][a-z]|\bProc\.|\bTrans\.|\bPhys\.|\bChem\.|\bBer\.|\bBerichte\b|\bAnn\.|\bAnnalen\b|\bZ\. ?[A-Z]|"
    r"\bZeitschrift\b|\bBull\.|\bBulletin\b|\bRev\.|\bSoc\.|\bComptes\b|\bAcad\b|\bMag\.|\bMagazine\b|\bReview\b|\bInd\. Eng\.|"
    r"\bSci\.|\bScience\b|\bNature\b|"
    r"\b[Vv]ol\. ?\d+|\b\d{1,3}, \d{1,4}(?:-\d+)? ?\((?:18|19)\d\d\)|\bpp?\. ?\d+|\bpage \d+|\bVolume [IVXLC\d]+|"
    r"\b(?:edition|[Ee]d\.|Handbook|[Tt]extbook|[Tt]reatise|[Mm]anual of|published by|Press\b|Publishing|McGraw|Wiley|Macmillan|Reinhold)")
PATENT_CUE = re.compile(r"\b[Pp]at(?:ent)?\.? ?No\.?|\bPatents? \d|\bSerial No\.|\b\d,\d{3},\d{3}\b|\bapplication Ser|"
                        r"\bBritish Patent|\bGerman Patent|\bFrench Patent")
# --cue-science (Nov 2, 2026): window anchor for pre-1980 science citations that give a venue or book but no volume or
# page ("Proceedings of the Institute of Radio Engineers, January 1925"; "Mellor's Treatise"). Case-sensitive words
# that rarely occur outside citations (the long-run fill draw prefiltered BigQuery text with the full words).
CIT_SCIENCE = re.compile(r"\b(?:Journal|Proceedings|Transactions|Berichte|Annalen|Zeitschrift|Bulletin|Comptes|Academy|Society|"
                         r"Handbook|Textbook|Treatise|edition|published by|University Press)\b|"
                         r"\b(?:Proc|Trans|Phys|Chem|Ber|Bull|Acad|Soc|Rev)\.|\bInd\. Eng\.")
# --cue-modern (Nov 2, 2026): extra anchors for in-text citations with no "et al." and no journal word, such as
# '"Generating viewsheds without using sightlines," Photogrammetric engineering and remote sensing, 66(1), 2000 pp 87-90'
# or 'OLE Controls Inside Out, by Adam Denning, Microsoft Press, 1995'. Used (firm sample) only for patents that Reliance on
# Science lists as citing a paper in the text but where the other anchors find no window.
CIT_MODERN = re.compile(r"[“\"][^”\"]{15,200}[”\"][^.]{0,120}?\b(?:19|20)\d{2}\b|\b\d{1,4} ?\(\d{1,3}\)[,:]? ?(?:pp?\.? ?)?\d|"
                        r"\bpp\.? ?\d+ ?[-–] ?\d+|\b(?:Press|Conference|Symposium|Workshop|Letters|arXiv|doi|ACM|SIAM)\b")
ASSIGNEE_RX = [re.compile(r'itemprop="assigneeOriginal"[^>]*>([^<]+)<'), re.compile(r'itemprop="assigneeCurrent"[^>]*>([^<]+)<')]
TAG_RX = re.compile(r"<[^>]+>")


FRONT_MATTER = re.compile(r"\bFiled\b[^.]{0,40}\b(?:18|19|20)\d{2}\b|Sheets?-Sheet|\bINVENTORS?\b|\bATTORNEYS?\b|\bPatented\b [A-Z][a-z]{2,8}\.? \d{1,2}, (?:18|19|20)\d{2}"
                          r"|\b[A-Z]\. [A-Z]{3,} ET AL\b")


def windows(paragraphs, max_per_patent=None, before=380, after=420, cit=CIT):
    """Yield (para_idx, window_text, looks_patent_only) for paragraphs with a citation cue. Paragraphs that are OCR
    front matter or drawing-sheet headers ("J. RUSSELL ET AL ... Filed April 24, 1924 2 Sheets-Sheet 1") are skipped."""
    n = 0
    for i, t in enumerate(paragraphs):
        if FRONT_MATTER.search(t):
            continue
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
    r = get_with_backoff(session, "https://patents.google.com/xhr/query?url=" + q + "&exp=", headers={"accept": "application/json"}, timeout=30)
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


def get_with_backoff(session, url, waits=(60, 120, 240), **kw):
    """GET that waits out Google's automated-traffic block (HTTP 503/429) a few times instead of hammering it."""
    for i, w in enumerate(waits + (None,)):
        r = session.get(url, **kw)
        if r.status_code not in (429, 503) or w is None:
            return r
        print(f"HTTP {r.status_code} from patents.google.com; waiting {w}s (attempt {i + 1}/{len(waits)})", file=sys.stderr)
        time.sleep(w)
    return r


def fetch_one(it, session, max_per_patent=None, cit=CIT):
    """Citation-window rows for one patent; `it` is a dict from google_patents() or {"pn": ...}
    (metadata missing there is read from the page). Returns [] on HTTP errors."""
    pn = it["pn"]
    r = get_with_backoff(session, f"https://patents.google.com/patent/{pn}/en", timeout=60)
    time.sleep(1.0)
    if r.status_code != 200:
        print(f"{pn}: HTTP {r.status_code}", file=sys.stderr); return []
    html = r.content.decode("utf-8", errors="replace")  # pages are UTF-8; requests may guess Latin-1
    p = _Desc(); p.feed(html); p.paras = cut_references_cited(p.paras)
    meta = {"pn": pn, "assignee": it.get("assignee") or assignee_of(html),
            "title": it.get("title") or " ".join(p.meta.get("title", "").split()),
            "priority_date": it.get("priority_date") or p.meta.get("priorityDate", ""),
            "grant_date": it.get("grant_date") or p.meta.get("publicationDate", ""), "n_desc_paras": len(p.paras)}
    return [dict(meta, para_idx=i, text=w, regex_patent_only=patent_only) for i, w, patent_only in windows(p.paras, max_per_patent, cit=cit)]


def fetch_google(items, session, max_per_patent=None, cit=CIT):
    for it in items:
        yield from fetch_one(it, session, max_per_patent, cit)


REFERENCES_CITED = re.compile(r"[Rr]eferences? [Cc]ited|REFERENCES CITED|references are of record|of record in the file|OTHER REFERENCES"
                              r"|OTHER PUBLICATIONS|UNITED STATES PATENTS|FOREIGN PATENTS|\[56\]")
REFERENCE_ENTRY = re.compile(r"\bet al\b|\bvol\.|\bpp?\. ?\d|\(\d{4}\)|\b(?:19|20)\d{2}\b.{0,5}$|\bNo\. \d|\d{1,2}/\d{4}", re.S)


def cut_references_cited(paras):
    """Drop the front page's 'References Cited' list, which OCR text of patents granted 1947-1975 carries at the end of
    the specification and text of patents from the 1970s on carries at the start ([56] References Cited ... OTHER
    PUBLICATIONS ...). From a header paragraph on, drop paragraphs while they look like list entries (short, or
    with a citation shape); a header in the second half of the text ends the text."""
    out, i = [], 0
    while i < len(paras):
        p = paras[i]
        if REFERENCES_CITED.search(p):
            if i >= len(paras) // 2:
                break
            i += 1
            while i < len(paras) and (len(paras[i]) < 300 or REFERENCE_ENTRY.search(paras[i])) and not re.search(r"\b(?:invention|embodiment|claims?|comprises|wherein|according)\b", paras[i], re.I):
                i += 1
            continue
        out.append(p); i += 1
    return out


def split_paragraphs(text):
    """Description text -> paragraphs: blank lines or newlines when the text has them (PatentsView, Google Patents
    Public Data), otherwise sentence-boundary chunks of about 800 characters (single-block OCR text)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n|(?<=\.)\s{2,}", text) if len(p.strip()) > 40]
    if len(paras) >= 3 or len(text) < 1200:
        return cut_references_cited(paras)
    out, cur = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        cur = (cur + " " + sent).strip()
        if len(cur) >= 800:
            out.append(cur); cur = ""
    if len(cur) > 40:
        out.append(cur)
    return cut_references_cited(out)


def fetch_patentsview(desc_file, patent_ids, max_per_patent=None):
    """PatentsView g_detail_desc_text.tsv: columns patent_id, description_text (one row per patent)."""
    want = set(patent_ids)
    with open(desc_file, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["patent_id"] not in want:
                continue
            for i, w, patent_only in windows(split_paragraphs(row["description_text"]), max_per_patent):
                yield {"pn": "US" + row["patent_id"], "para_idx": i, "text": w, "regex_patent_only": patent_only}


def fetch_textfile(desc_file, max_per_patent=None, cit=CIT):
    """JSONL with one patent per line: pn (US1633096A or US-1633096-A), description, and optionally assignee, title,
    priority_date, grant_date (e.g. saved from Google Patents Public Data on BigQuery). Same rows as fetch_one()."""
    with open(desc_file, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            pn = (r.get("pn") or r["publication_number"]).replace("-", "").upper()
            paras = split_paragraphs(html.unescape(r.get("description") or ""))
            meta = {"pn": pn, "assignee": r.get("assignee", ""), "title": html.unescape(r.get("title") or ""),
                    "priority_date": str(r.get("priority_date", "")), "grant_date": str(r.get("grant_date", "")), "n_desc_paras": len(paras)}
            for k in ("cell",):
                if r.get(k):
                    meta[k] = r[k]
            for i, w, patent_only in windows(paras, max_per_patent, cit=cit):
                yield dict(meta, para_idx=i, text=w, regex_patent_only=patent_only)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["google", "patentsview", "textfile"], required=True)
    ap.add_argument("--assignee", action="append", default=[], help='"query" or "query~regex" (see module docstring)')
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--per-assignee", type=int, default=2); ap.add_argument("--max-windows", type=int, default=0)
    ap.add_argument("--after-priority", default="20170101"); ap.add_argument("--before-priority", default=None)
    ap.add_argument("--before-publication", default=None)
    ap.add_argument("--tag", action="append", default=[], help="key=value attached to every row (e.g. sector=pharma)")
    ap.add_argument("--query", default='"et al"', help="Google Patents full-text query (default '\"et al\"'; e.g. IEEE)")
    ap.add_argument("--cue-ieee", action="store_true", help="also treat 'IEEE' as a citation cue in the window finder")
    ap.add_argument("--cue-early", action="store_true", help="also accept journal title + volume/page without a year as a cue (pre-1976 text)")
    ap.add_argument("--cue-science", action="store_true",
                    help="with --cue-early: also anchor windows on a journal, society, bulletin or book word without volume or page (CIT_SCIENCE)")
    ap.add_argument("--cue-modern", action="store_true",
                    help="also anchor on a quoted title with a year, volume(issue), a page range, or Press/Conference/Symposium... (CIT_MODERN)")
    ap.add_argument("--require-paper-cue", action="store_true",
                    help="walk the ranking and keep only patents with at least one window that looks like a paper citation, until --per-assignee are kept")
    ap.add_argument("--desc-file"); ap.add_argument("--patent-ids")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    tags = dict(t.split("=", 1) for t in a.tag)
    cit = CIT_EARLY if a.cue_early else CIT_IEEE if a.cue_ieee else CIT
    if a.cue_science:
        cit = re.compile(CIT_EARLY.pattern + "|" + CIT_SCIENCE.pattern)
    if a.cue_modern:
        cit = re.compile(cit.pattern + "|" + CIT_MODERN.pattern)
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
        elif a.source == "textfile":
            for row in fetch_textfile(a.desc_file, a.max_windows or None, cit):
                row.update(tags); k += 1; out.write(json.dumps(row, ensure_ascii=False) + "\n")
        else:
            ids = [l.strip() for l in open(a.patent_ids) if l.strip()]
            for row in fetch_patentsview(a.desc_file, ids, a.max_windows or None):
                row.update(tags); k += 1; out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{k} windows -> {a.output}", file=sys.stderr)
