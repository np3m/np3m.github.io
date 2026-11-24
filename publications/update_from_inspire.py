#!/usr/bin/env python3
"""Rebuild publications.html from INSPIRE-HEP.

Lists every INSPIRE record whose full text acknowledges one of the NP3M NSF
grants below. The page header and footer are copied from science.html, so the
page always matches the rest of the site.

Run from the repository root:

    python3 publications/update_from_inspire.py

then commit publications.html. Needs only the Python standard library.
"""
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

GRANTS = ["PHY-2116686", "PHY-2621752", "PHY-2623480"]
API = "https://inspirehep.net/api/literature"
FIELDS = ",".join([
    "control_number", "titles.title", "authors.full_name", "author_count", "collaborations.value",
    "publication_info", "arxiv_eprints.value", "dois.value", "earliest_date", "document_type",
])
MAX_AUTHORS = 6  # longer author lists are shortened to "First, Second, Third, et al."

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "science.html")
OUTPUT = os.path.join(ROOT, "publications.html")


def variants(grant):
    """Spellings of a grant number that appear in acknowledgements."""
    num = grant.split("-")[1]
    return [num, "PHY" + num, num[:2] + "-" + num[2:]]


def query_for(grants):
    return " or ".join(f'fulltext:"{v}"' for g in grants for v in variants(g))


def fetch(q, fields="control_number"):
    hits, page = [], 1
    while True:
        url = API + "?" + urllib.parse.urlencode(
            {"q": q, "size": 250, "page": page, "sort": "mostrecent", "fields": fields})
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "np3m-site-builder"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        batch = data["hits"]["hits"]
        hits += batch
        if len(hits) >= data["hits"]["total"] or not batch:
            return hits
        page += 1
        time.sleep(1)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def short_name(full):
    """'Radice, David' -> 'D. Radice'."""
    if "," not in full:
        return full
    last, first = [x.strip() for x in full.split(",", 1)]
    initials = " ".join(w[0] + "." for w in re.split(r"[\s]+", first) if w and w[0].isalpha())
    initials = re.sub(r"(\w\.)-?(\w)", r"\1", initials)
    return f"{initials} {last}".strip()


def authors_text(m):
    collab = [c["value"] for c in m.get("collaborations", [])]
    names = [short_name(a["full_name"]) for a in m.get("authors", [])]
    count = m.get("author_count", len(names))
    if collab and count > MAX_AUTHORS:
        return ", ".join(c + " Collaboration" for c in collab)
    if count > MAX_AUTHORS:
        return ", ".join(names[:3]) + ", et al."
    if len(names) > 1:
        return ", ".join(names[:-1]) + " and " + names[-1]
    return names[0] if names else ""


def journal_ref(m):
    for p in m.get("publication_info", []):
        if p.get("journal_title"):
            ref = p["journal_title"]
            if p.get("journal_volume"):
                ref += f" {p['journal_volume']}"
            if p.get("year"):
                ref += f" ({p['year']})"
            page = p.get("artid") or p.get("page_start")
            if page:
                ref += f" {page}"
            return ref, p.get("year")
    return "", None


def esc(s):
    return html.escape(s, quote=True)


def entry(m, grants):
    title = strip_tags(m["titles"][0]["title"])
    arxiv = (m.get("arxiv_eprints") or [{}])[0].get("value")
    doi = (m.get("dois") or [{}])[0].get("value")
    recid = m["control_number"]
    ref, pub_year = journal_ref(m)
    year = pub_year or int(m.get("earliest_date", "0000")[:4] or 0)
    href = f"https://doi.org/{doi}" if doi else (f"https://arxiv.org/abs/{arxiv}" if arxiv else f"https://inspirehep.net/literature/{recid}")
    links = []
    if doi:
        links.append(f'<a class="chip" href="https://doi.org/{esc(doi)}">DOI</a>')
    if arxiv:
        links.append(f'<a class="chip" href="https://arxiv.org/abs/{esc(arxiv)}">arXiv:{esc(arxiv)}</a>')
    links.append(f'<a class="chip" href="https://inspirehep.net/literature/{recid}">INSPIRE</a>')
    status = esc(ref) if ref else '<span class="preprint">Preprint</span>'
    tags = "".join(f'<span class="gtag">{g}</span>' for g in grants)
    search = esc(" ".join([title, authors_text(m), ref, arxiv or ""]).lower())
    return year, (
        f'<li class="pub" data-search="{search}" data-grants="{" ".join(grants)}">'
        f'<p class="pub-title"><a href="{esc(href)}">{esc(title)}</a></p>'
        f'<p class="pub-authors">{esc(authors_text(m))}</p>'
        f'<p class="pub-ref">{status}</p>'
        f'<div class="pub-foot"><div class="chips">{"".join(links)}</div><div class="gtags">{tags}</div></div></li>'
    )


CSS = """
<style>
.pub-tools { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-bottom: 28px; }
.pub-tools input { flex: 1 1 280px; font: inherit; font-size: 16px; padding: 11px 14px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
.pub-tools input:focus { outline: 3px solid var(--amber); outline-offset: 1px; }
.pub-tools select { font: inherit; font-size: 15px; padding: 10px 12px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
.pub-count { color: var(--muted); font-size: 15px; margin: 0; }
.pub-year + .pub-year { margin-top: 44px; }
.pubs { list-style: none; margin: 0; padding: 0; }
.pub { padding: 16px 0; border-bottom: 1px solid var(--line); }
.pub-title { font-weight: 600; margin: 0 0 4px; font-size: 17px; }
.pub-title a { color: var(--ink); text-decoration: none; }
.pub-title a:hover { color: var(--link); text-decoration: underline; }
.pub-authors { margin: 0; color: var(--ink-2); font-size: 15px; }
.pub-ref { margin: 2px 0 10px; font-size: 15px; font-style: italic; color: var(--ink-2); }
.preprint { font-style: normal; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; color: var(--orange); }
.pub-foot { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; align-items: center; }
.pub .chip { font-size: 13px; padding: 3px 11px; }
.gtags { display: flex; gap: 6px; flex-wrap: wrap; }
.gtag { font-size: 12px; color: var(--muted); background: var(--sand); border-radius: 4px; padding: 2px 8px; }
.no-results { display: none; color: var(--muted); padding: 24px 0; }
</style>"""

JS = """
<script>
(function () {
  var q = document.getElementById('pub-q'), g = document.getElementById('pub-g'), c = document.getElementById('pub-n');
  var items = [].slice.call(document.querySelectorAll('.pub')), years = [].slice.call(document.querySelectorAll('.pub-year'));
  function run() {
    var terms = q.value.toLowerCase().split(/\\s+/).filter(Boolean), grant = g.value, n = 0;
    items.forEach(function (li) {
      var ok = terms.every(function (t) { return li.dataset.search.indexOf(t) > -1; }) && (!grant || li.dataset.grants.indexOf(grant) > -1);
      li.hidden = !ok; if (ok) n++;
    });
    years.forEach(function (y) { y.hidden = !y.querySelector('.pub:not([hidden])'); });
    c.textContent = n + (n === 1 ? ' publication' : ' publications');
    document.getElementById('pub-none').style.display = n ? 'none' : 'block';
  }
  q.addEventListener('input', run); g.addEventListener('change', run);
})();
</script>"""


def build():
    # which records acknowledge which grant
    by_grant = {}
    for g in GRANTS:
        by_grant[g] = {h["metadata"]["control_number"] for h in fetch(query_for([g]))}
        time.sleep(1)
    records = [h["metadata"] for h in fetch(query_for(GRANTS), FIELDS)]
    if not records:
        sys.exit("INSPIRE returned no records; publications.html left unchanged.")

    groups = {}
    for m in records:
        grants = [g for g in GRANTS if m["control_number"] in by_grant[g]]
        year, li = entry(m, grants)
        groups.setdefault(year, []).append(li)

    sections = "".join(
        f'<section class="pub-year" id="y{y}"><h2 class="col-title">{y} <span class="count">{len(groups[y])}</span></h2>'
        f'<ol class="pubs">{"".join(groups[y])}</ol></section>'
        for y in sorted(groups, reverse=True)
    )
    year_pills = "".join(f'<a href="#y{y}">{y}</a>' for y in sorted(groups, reverse=True))
    options = "".join(f'<option value="{g}">{g}</option>' for g in GRANTS)
    grant_list = ", ".join(GRANTS[:-1]) + " or " + GRANTS[-1]
    today = datetime.date.today().strftime("%B %-d, %Y")

    main = f"""
<section class="page-head"><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a><span>/</span><a href="science.html">Science</a><span>/</span>Publications</nav><p class="kicker">Science</p><h1>NP3M Publications</h1><p class="page-lead">Papers that acknowledge NSF grant {grant_list}, as listed on INSPIRE-HEP. Last updated {today}.</p></div></section>
<div class="pillbar"><div class="wrap pills">{year_pills}</div></div>
<section class="band"><div class="wrap">
  <div class="pub-tools">
    <input id="pub-q" type="search" placeholder="Search titles, authors, journals&hellip;" aria-label="Search publications">
    <select id="pub-g" aria-label="Filter by grant"><option value="">All grants</option>{options}</select>
    <p class="pub-count" id="pub-n" aria-live="polite">{len(records)} publications</p>
  </div>
  <p class="no-results" id="pub-none">No publications match your search.</p>
  {sections}
</div></section>
{JS}
"""
    tpl = open(TEMPLATE, encoding="utf-8").read()
    out = re.sub(r"<main id=\"main\">.*?</main>", lambda _: f'<main id="main">{main}</main>', tpl, count=1, flags=re.S)
    out = re.sub(r"<title>.*?</title>", "<title>Publications | NP3M</title>", out, count=1)
    out = re.sub(r'<meta name="description" content="[^"]*">',
                 '<meta name="description" content="Publications that acknowledge the NP3M NSF grants.">', out, count=1)
    out = out.replace("</head>", CSS + "\n</head>", 1)
    # mark the current page in the navigation
    out = out.replace('<li class="has-menu is-active">', '<li class="has-menu">')
    out = out.replace(' aria-current="page"', "")
    out = out.replace('<li class="has-menu"><button class="top" aria-expanded="false">Science',
                      '<li class="has-menu is-active"><button class="top" aria-expanded="false">Science', 1)
    out = out.replace('<li><a href="publications.html">Publications</a></li></ul></li>',
                      '<li><a href="publications.html" aria-current="page">Publications</a></li></ul></li>', 1)
    open(OUTPUT, "w", encoding="utf-8").write(out)
    print(f"Wrote {OUTPUT}: {len(records)} publications "
          + ", ".join(f"{g}: {len(by_grant[g])}" for g in GRANTS))


if __name__ == "__main__":
    build()
