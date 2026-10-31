"""Stage 1 of pipeline 1: get patent descriptions and find in-text citation windows.

Two sources are supported:
  (a) Google Patents pages (used for the pilot; fine for samples of hundreds of patents):
      --source google --assignee "Genentech" --n 25
  (b) PatentsView bulk 'g_detail_desc_text' files for the full build (tens of millions of
      paragraphs; run window_finder over the bulk CSV, no HTTP needed):
      --source patentsview --desc-file g_detail_desc_text.tsv --patent-ids ids.txt

Output: JSONL of citation windows, one row per candidate citation, with patent metadata.
The window finder is deliberately high-recall (it accepts 'et al.' in patent citations);
the cited-document-type classifier in the labeling stage removes non-paper citations.

Note on the pilot: the same logic was executed in the browser (JavaScript, see
pilot/README_pilot_method.md) because the pilot machine could not reach
patents.google.com directly. This file is the Python equivalent.
"""
import argparse, csv, json, re, sys, time
from html.parser import HTMLParser

CIT = re.compile(
    r"\bet al\b|\b(?:J\.|Journal of|Nature\b|Science\b|Cell\b|Proc\. Natl|PNAS|Lancet|N\.? Engl|Biochem|"
    r"Phys\. Rev\.|arXiv|doi:|Nucleic Acids|Cancer Res|Chem\. Soc|Angew|Adv\. Mater|Appl\. Phys)"
    r"[^.]{0,80}?\b(?:19|20)\d{2}\b")
PATENT_ONLY = re.compile(r"U\.?S\.? ?Pat(?:ent)?\.? ?(?:No\.?|Application|Publication|Pub\.)|WO\s?\d{2,4}/\d+|EP\s?\d{6,}|US\s?\d{4}/\d+", re.I)


def windows(paragraphs, max_per_patent=None, before=380, after=420):
    """Yield (para_idx, window_text, looks_patent_only) for paragraphs with a citation cue."""
    n = 0
    for i, t in enumerate(paragraphs):
        m = CIT.search(t)
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


def google_patents(assignee, n, session, after_priority="20170101", with_et_al=True):
    """Return granted US patent numbers for an assignee via the Google Patents XHR endpoint."""
    q = ("q%3D%22et+al%22%26" if with_et_al else "") + "assignee%3D" + assignee.replace(" ", "+") + \
        f"%26country%3DUS%26status%3DGRANT%26after%3Dpriority%3A{after_priority}%26type%3DPATENT%26num%3D{n}"
    r = session.get("https://patents.google.com/xhr/query?url=" + q + "&exp=", headers={"accept": "application/json"}, timeout=30)
    r.raise_for_status()
    out = []
    for c in r.json().get("results", {}).get("cluster", []):
        for x in c.get("result", []):
            pn = x["patent"]["publication_number"]
            if re.search(r"B[12]$", pn):
                out.append(pn)
    return out


def fetch_google(pns, session, max_per_patent=None):
    for pn in pns:
        r = session.get(f"https://patents.google.com/patent/{pn}/en", timeout=60)
        if r.status_code != 200:
            continue
        p = _Desc(); p.feed(r.text)
        for i, w, patent_only in windows(p.paras, max_per_patent):
            yield {"pn": pn, "title": p.meta.get("title", ""), "priority_date": p.meta.get("priorityDate", ""),
                   "grant_date": p.meta.get("publicationDate", ""), "n_desc_paras": len(p.paras), "para_idx": i,
                   "text": w, "regex_patent_only": patent_only}
        time.sleep(1.0)


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
    ap.add_argument("--assignee", action="append", default=[]); ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--per-assignee", type=int, default=2); ap.add_argument("--max-windows", type=int, default=0)
    ap.add_argument("--desc-file"); ap.add_argument("--patent-ids")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    k = 0
    with open(a.output, "w", encoding="utf-8") as out:
        if a.source == "google":
            import requests
            s = requests.Session(); s.headers["User-Agent"] = "corporate-science-strategy pilot (academic; contact in README)"
            for asg in a.assignee:
                pns = google_patents(asg, a.n, s)[: a.per_assignee]
                for row in fetch_google(pns, s, a.max_windows or None):
                    row["query_assignee"] = asg; k += 1
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
        else:
            ids = [l.strip() for l in open(a.patent_ids) if l.strip()]
            for row in fetch_patentsview(a.desc_file, ids, a.max_windows or None):
                k += 1; out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{k} windows -> {a.output}", file=sys.stderr)
