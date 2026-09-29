#!/usr/bin/env python3
"""Build index.html from notes.md + recordings.js.  Usage: python3 build.py"""
import re, json, html, os
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
md = open(os.path.join(HERE, "notes.md"), encoding="utf-8").read()

# --- trim doc title/byline; the page has its own header ---
md = re.sub(r"\A# .*?\n\n.*?\n\n", "", md, count=1, flags=re.S)
md = md.replace(
    "so you can go back and listen.",
    "so you can go back and listen. Tap a recording label to play it (audio is hosted in a shared Google Drive folder).",
)

body = markdown.markdown(md, extensions=["toc", "sane_lists"], extension_configs={"toc": {"toc_depth": "2-4"}})

# --- recording chips ---
def chips(m):
    labels = [s.strip() for s in m.group(1).split(",")]
    btns = "".join(
        f'<button class="rec" type="button" data-label="{html.escape(l)}"><span class="rec-icon" aria-hidden="true"></span>{html.escape(l)}</button>'
        for l in labels
    )
    return f'<div class="recs"><span class="recs-label">Listen</span>{btns}</div>'

body = re.sub(r"<p><em>Recordings?: ([^<]+)</em></p>", chips, body)

# --- wrap each day (h2) in a section ---
parts = re.split(r'(?=<h2 id=")', body)
intro = parts[0] + "".join(p for p in parts[1:] if not p.startswith('<h2 id="day-'))
days = [p for p in parts[1:] if p.startswith('<h2 id="day-')]

# --- table of contents from h2/h3 ---
toc = []
for d in days:
    m = re.match(r'<h2 id="([^"]+)">(.*?)</h2>', d)
    did, dtitle = m.group(1), m.group(2)
    dm = re.match(r"(Day \d+) — ([^:]+): (.*)", html.unescape(dtitle))
    stops = re.findall(r'<h3 id="([^"]+)">(.*?)</h3>', d)
    toc.append((did, dm.group(1), dm.group(2), dm.group(3), stops))

def toc_html():
    out = []
    for did, day, date, places, stops in toc:
        items = "".join(
            f'<li><a href="#{sid}"{" class=bus" if "On the bus" in st else ""}>{st}</a></li>' for sid, st in stops
        )
        out.append(
            f'<li class="toc-day"><a class="toc-daylink" href="#{did}"><span class="toc-dayname">{day}</span>'
            f'<span class="toc-date">{html.escape(date)}</span></a><ul>{items}</ul></li>'
        )
    return "<ul class=\"toc\">" + "".join(out) + "</ul>"

cards = "".join(
    f'<a class="daycard" href="#{did}"><span class="dc-day">{day}</span><span class="dc-date">{html.escape(date)}</span>'
    f'<span class="dc-places">{html.escape(places)}</span><span class="dc-count">{sum(1 for _, s in stops if "On the bus" not in s)} stops</span></a>'
    for did, day, date, places, stops in toc
)

# --- link Bible references to BibleGateway (NIV) ---
import urllib.parse
BOOKS = (r"(?:(?:[123] )(?:Samuel|Kings|Chronicles|Corinthians|Thessalonians|Timothy|Peter|John)"
         r"|Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs"
         r"|Ecclesiastes|Song of Songs|Song of Solomon|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah"
         r"|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Galatians"
         r"|Ephesians|Philippians|Colossians|Titus|Philemon|Hebrews|James|Jude|Revelation"
         r"|Gen|Exod|Lev|Deut|Isa|Jer|Ezek|Matt|Rom|Gal|Eph|Phil|Col|Heb|Rev|Ps)")
VERSES = r"\d+(?:[–-]\d+)?(?:, ?\d+(?:[–-]\d+)?)*"
REF = re.compile(r"\b(" + BOOKS + r") (\d+)(?::(" + VERSES + r"))?(?:[–-](\d+)(?::\d+)?)?(?!\d)(?!:\d)")
CONT = re.compile(r"(; ?)(\d+):(" + VERSES + r")")

def bg(q):
    return "https://www.biblegateway.com/passage/?search=" + urllib.parse.quote_plus(q.replace("–", "-")) + "&version=NIV"

def link_text(t):
    out, pos = [], 0
    for m in REF.finditer(t):
        book = m.group(1)
        if m.group(3) is None and book in ("Numbers", "Job", "Mark", "James", "Acts", "Jude", "Titus") and not re.search(r"[(]\s*$", t[max(0,m.start()-2):m.start()]):
            # chapter-only refs of name-like books: only link when inside parentheses
            if book in ("Job", "Mark", "James", "Jude", "Titus"):
                continue
        out.append(t[pos:m.start()])
        txt = m.group(0)
        out.append(f'<a class="vref" href="{bg(txt)}" target="_blank" rel="noopener">{txt}</a>')
        pos = m.end()
        # continuation like "; 3:9"
        while True:
            c = CONT.match(t, pos)
            if not c: break
            q = f"{book} {c.group(2)}:{c.group(3)}"
            out.append(c.group(1) + f'<a class="vref" href="{bg(q)}" target="_blank" rel="noopener">{c.group(2)}:{c.group(3)}</a>')
            pos = c.end()
    out.append(t[pos:])
    return "".join(out)

def link_refs(h):
    toks = re.split(r"(<[^>]+>)", h)
    skip = 0
    for i, tk in enumerate(toks):
        if tk.startswith("<"):
            tag = re.match(r"</?(\w+)", tk)
            if tag and tag.group(1) in ("h2", "h3", "a", "button"):
                skip += -1 if tk.startswith("</") else 1
        elif skip == 0 and tk.strip():
            toks[i] = link_text(tk)
    return "".join(toks)

days = [link_refs(d) for d in days]
intro = link_refs(intro)

sections = "".join(f'<section class="day">{d}</section>' for d in days)

# --- all-recordings appendix (filled client-side from recordings.js) ---
appendix = (
    '<section class="day" id="all-recordings-section"><h2 id="all-recordings">All recordings</h2>'
    '<p>Every recording from the trip, in order. Recordings marked <em>no content</em> were accidental.</p>'
    '<div id="rec-table"></div></section>'
)

tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
page = (
    tpl.replace("{{TOC}}", toc_html())
    .replace("{{CARDS}}", cards)
    .replace("{{INTRO}}", intro)
    .replace("{{SECTIONS}}", sections + appendix)
)
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(page)
print("wrote index.html", len(page) // 1024, "KB;", len(toc), "days;", sum(len(t[4]) for t in toc), "stops")
