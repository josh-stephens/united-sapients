#!/usr/bin/env python3
"""Build script for United Sapients Council Reader.

Reads markdown from archive/, personas/, and reports/, parses into structured
data, and generates a self-contained index.html with all content embedded.
"""

import json
import os
import re
from pathlib import Path

BASE = Path(__file__).parent
ARCHIVE = BASE / "sessions"
PERSONAS = BASE / "personas"
OUT = BASE / "index.html"

# --- Markdown to HTML ---

def md_to_html(text: str) -> str:
    if not text:
        return ""
    lines = text.split("\n")
    out = []
    in_list = False
    in_para = False
    buf = []

    def flush_para():
        nonlocal in_para, buf
        if buf:
            out.append("<p>" + inline(" ".join(buf)) + "</p>")
            buf = []
            in_para = False

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for line in lines:
        stripped = line.strip()

        # blank line
        if not stripped:
            flush_para()
            flush_list()
            continue

        # hr
        if re.match(r"^-{3,}$", stripped):
            flush_para()
            flush_list()
            out.append("<hr>")
            continue

        # headings
        m = re.match(r"^(#{1,6})\s+(.*)", stripped)
        if m:
            flush_para()
            flush_list()
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            continue

        # list items (- or * or numbered)
        m = re.match(r"^[-*]\s+(.*)", stripped) or re.match(r"^\d+\.\s+(.*)", stripped)
        if m:
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(m.group(1))}</li>")
            continue

        # continuation of paragraph
        flush_list()
        buf.append(stripped)
        in_para = True

    flush_para()
    flush_list()
    return "\n".join(out)


def inline(text: str) -> str:
    # bold + italic
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # bold
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    # italic
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    # inline code
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)
    # em dash
    text = text.replace(" — ", " &mdash; ")
    text = text.replace("—", "&mdash;")
    return text


# --- Content parsers ---

def parse_meta(path: Path) -> dict:
    text = path.read_text()
    meta = {}
    # title from h1
    m = re.search(r"^#\s+(.*)", text, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()
    # key-value fields
    for m in re.finditer(r"\*\*(.*?)\*\*:\s*(.*)", text):
        key = m.group(1).strip().lower()
        val = m.group(2).strip()
        if key == "date":
            meta["date"] = val
        elif key == "status":
            meta["status"] = val
        elif key == "rounds completed":
            meta["rounds_completed"] = int(val)
        elif key == "topic":
            meta["topic"] = val
    # round titles from numbered list
    rounds_info = []
    for m in re.finditer(r"^\s+\d+\.\s+(.*?)(?:\s*[✓✗])?\s*$", text, re.MULTILINE):
        rounds_info.append(m.group(1).strip())
    if rounds_info:
        meta["round_titles"] = rounds_info
    # outcome
    m = re.search(r"\*\*Outcome:\*\*\s*(.*)", text)
    if m:
        meta["outcome"] = m.group(1).strip()
    return meta


CURATOR_MAP = {
    "george carlin": "george-carlin",
    "carl sagan": "carl-sagan",
    "christopher hitchens": "christopher-hitchens",
}

CURATOR_COLORS = {
    "george-carlin": "#C4813D",
    "carl-sagan": "#5B8A72",
    "christopher-hitchens": "#8B6F5C",
}

CURATOR_NAMES = {
    "george-carlin": "George Carlin",
    "carl-sagan": "Carl Sagan",
    "christopher-hitchens": "Christopher Hitchens",
}


def parse_round(path: Path, round_titles=None) -> dict:
    text = path.read_text()
    num = int(re.search(r"round-(\d+)", path.name).group(1))

    # extract title from h1
    m = re.match(r"^#\s+(.*)", text, re.MULTILINE)
    title = m.group(1).strip() if m else f"Round {num}"

    # check for round format in title (e.g. "Round 2: Fireside — Core Values")
    fmt = ""
    m2 = re.search(r":\s*(\w+)\s*[—\-]", title)
    if m2:
        fmt = m2.group(1).strip()
    elif round_titles and num <= len(round_titles):
        rt = round_titles[num - 1]
        m3 = re.match(r"(.*?)\s*\((.*?)\)", rt)
        if m3:
            fmt = m3.group(2).strip()

    # split by curator h2 sections
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
    preamble = ""
    contributions = []

    for i, sec in enumerate(sections):
        if i == 0:
            lines = sec.strip().split("\n")
            rest = [l for l in lines if not l.strip().startswith("# ")]
            preamble_text = "\n".join(rest).strip()
            if preamble_text:
                preamble = md_to_html(preamble_text)
            continue

        heading_line, _, body = sec.partition("\n")
        heading = heading_line.strip()

        slug = None
        for name, s in CURATOR_MAP.items():
            if name in heading.lower():
                slug = s
                break

        if slug:
            contributions.append({
                "curatorSlug": slug,
                "html": md_to_html(body.strip()),
            })

    return {
        "number": num,
        "title": title,
        "format": fmt,
        "preambleHtml": preamble,
        "contributions": contributions,
    }


def parse_persona(path: Path) -> dict:
    text = path.read_text()
    slug = path.stem
    name = CURATOR_NAMES.get(slug, slug.replace("-", " ").title())
    return {
        "name": name,
        "slug": slug,
        "color": CURATOR_COLORS.get(slug, "#c9943e"),
        "profileHtml": md_to_html(text),
    }


def build_data() -> dict:
    curators = {}
    for p in sorted(PERSONAS.glob("*.md")):
        persona = parse_persona(p)
        curators[persona["slug"]] = persona

    sessions = []
    for session_dir in sorted(ARCHIVE.iterdir()):
        if not session_dir.is_dir():
            continue
        meta_path = session_dir / "meta.md"
        if not meta_path.exists():
            continue

        meta = parse_meta(meta_path)
        slug = session_dir.name
        sid = slug.split("-")[0]

        briefing_html = ""
        bp = session_dir / "briefing.md"
        if bp.exists():
            briefing_html = md_to_html(bp.read_text())

        report_html = ""
        rp = session_dir / "report.md"
        if rp.exists():
            report_html = md_to_html(rp.read_text())

        round_titles = meta.get("round_titles", [])
        rounds = []
        for rp in sorted(session_dir.glob("round-*.md")):
            rounds.append(parse_round(rp, round_titles))

        sessions.append({
            "id": sid,
            "slug": slug,
            "title": meta.get("title", slug),
            "date": meta.get("date", ""),
            "status": meta.get("status", ""),
            "topic": meta.get("topic", ""),
            "briefingHtml": briefing_html,
            "reportHtml": report_html,
            "rounds": rounds,
        })

    return {"curators": curators, "sessions": sessions}


# --- HTML template ---

def get_html_template():
    return r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>United Sapients Council</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg-deep: #1a1714;
  --bg-mid: #211e1a;
  --bg-surface: #2a2520;
  --bg-raised: #332e28;
  --text-primary: #e8e0d4;
  --text-secondary: #b8ad9e;
  --text-muted: #8a7e70;
  --accent: #c9943e;
  --accent-dim: #a07830;
  --border: #3d3630;
  --carlin: #C4813D;
  --sagan: #5B8A72;
  --hitchens: #8B6F5C;
  --sidebar-w: 260px;
  --reading-max: 72ch;
  --font-serif: 'Cormorant Garamond', Georgia, serif;
  --font-sans: 'Inter', -apple-system, sans-serif;
}

html { font-size: 17px; }

body {
  background: var(--bg-deep);
  color: var(--text-primary);
  font-family: var(--font-serif);
  line-height: 1.7;
  min-height: 100vh;
  overflow: hidden;
}

body::before {
  content: '';
  position: fixed;
  top: -20%; left: 30%;
  width: 60vw; height: 60vh;
  background: radial-gradient(ellipse, rgba(201,148,62,0.04) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.app { display: flex; height: 100vh; position: relative; z-index: 1; }

.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  background: var(--bg-mid);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 1.5rem 1.2rem 1rem;
  border-bottom: 1px solid var(--border);
}

.sidebar-header h1 {
  font-family: var(--font-serif);
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.02em;
}

.sidebar-header .subtitle {
  font-family: var(--font-sans);
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 0.2rem;
}

.sidebar-section {
  padding: 1rem 0;
  border-bottom: 1px solid var(--border);
}

.sidebar-section-title {
  font-family: var(--font-sans);
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  padding: 0 1.2rem;
  margin-bottom: 0.5rem;
}

.sidebar-item {
  display: block;
  padding: 0.5rem 1.2rem;
  font-family: var(--font-serif);
  font-size: 0.95rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  border-left: 3px solid transparent;
  text-decoration: none;
}

.sidebar-item:hover {
  color: var(--text-primary);
  background: rgba(201,148,62,0.06);
}

.sidebar-item.active {
  color: var(--accent);
  border-left-color: var(--accent);
  background: rgba(201,148,62,0.08);
}

.sidebar-item .session-id {
  font-family: var(--font-sans);
  font-size: 0.65rem;
  color: var(--text-muted);
  margin-right: 0.4rem;
}

.curator-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 0.5rem;
  vertical-align: middle;
}

.sidebar-toggle {
  display: none;
  position: fixed;
  top: 0.8rem; left: 0.8rem;
  z-index: 100;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  color: var(--accent);
  width: 40px; height: 40px;
  border-radius: 8px;
  font-size: 1.2rem;
  cursor: pointer;
  align-items: center;
  justify-content: center;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.content-header {
  padding: 1.5rem 2rem 0;
  flex-shrink: 0;
}

.content-header h2 {
  font-family: var(--font-serif);
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}

.content-header .meta {
  font-family: var(--font-sans);
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 0.3rem;
  display: flex;
  gap: 1rem;
}

.tab-bar {
  display: flex;
  gap: 0;
  padding: 0 2rem;
  margin-top: 1rem;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  overflow-x: auto;
}

.tab {
  font-family: var(--font-sans);
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--text-muted);
  padding: 0.6rem 1rem;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tab:hover { color: var(--text-secondary); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }

.reading-pane {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.reading-content {
  max-width: var(--reading-max);
  margin: 0 auto;
}

.filter-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  align-items: center;
}

.filter-label {
  font-family: var(--font-sans);
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  margin-right: 0.3rem;
}

.chip {
  font-family: var(--font-sans);
  font-size: 0.7rem;
  font-weight: 500;
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  background: transparent;
}

.chip:hover { border-color: var(--text-muted); }
.chip.active { color: #fff; border-color: transparent; }
.chip[data-curator="george-carlin"].active { background: var(--carlin); }
.chip[data-curator="carl-sagan"].active { background: var(--sagan); }
.chip[data-curator="christopher-hitchens"].active { background: var(--hitchens); }

.chip-compare {
  font-family: var(--font-sans);
  font-size: 0.65rem;
  font-weight: 500;
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid var(--accent-dim);
  color: var(--accent);
  background: transparent;
  margin-left: auto;
}

.chip-compare:hover { background: rgba(201,148,62,0.1); }
.chip-compare.active { background: var(--accent); color: var(--bg-deep); border-color: var(--accent); }

.curator-section {
  margin-bottom: 2.5rem;
  border-left: 3px solid var(--border);
  padding-left: 1.5rem;
  transition: opacity 0.2s;
}

.curator-section[data-curator="george-carlin"] { border-left-color: var(--carlin); }
.curator-section[data-curator="carl-sagan"] { border-left-color: var(--sagan); }
.curator-section[data-curator="christopher-hitchens"] { border-left-color: var(--hitchens); }
.curator-section.hidden { display: none; }

.curator-name {
  font-family: var(--font-sans);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.curator-section[data-curator="george-carlin"] .curator-name { color: var(--carlin); }
.curator-section[data-curator="carl-sagan"] .curator-name { color: var(--sagan); }
.curator-section[data-curator="christopher-hitchens"] .curator-name { color: var(--hitchens); }

.compare-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  max-width: none;
}

.compare-grid .curator-section {
  border-left: none;
  border-top: 3px solid var(--border);
  padding-left: 0;
  padding-top: 1rem;
}

.compare-grid .curator-section[data-curator="george-carlin"] { border-top-color: var(--carlin); }
.compare-grid .curator-section[data-curator="carl-sagan"] { border-top-color: var(--sagan); }
.compare-grid .curator-section[data-curator="christopher-hitchens"] { border-top-color: var(--hitchens); }

.reading-content h1 { font-size: 1.6rem; font-weight: 700; margin: 2rem 0 1rem; color: var(--text-primary); }
.reading-content h2 { font-size: 1.3rem; font-weight: 700; margin: 1.8rem 0 0.8rem; color: var(--text-primary); }
.reading-content h3 { font-size: 1.1rem; font-weight: 600; margin: 1.5rem 0 0.6rem; color: var(--text-primary); }
.reading-content h4 { font-size: 1rem; font-weight: 600; margin: 1.2rem 0 0.5rem; color: var(--accent); }
.reading-content p { margin-bottom: 1rem; color: var(--text-primary); }
.reading-content strong { font-weight: 700; color: var(--text-primary); }
.reading-content em { font-style: italic; }
.reading-content ul { margin: 0.5rem 0 1rem 1.5rem; }
.reading-content li { margin-bottom: 0.4rem; color: var(--text-primary); }
.reading-content hr { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }
.reading-content code { font-size: 0.9em; background: var(--bg-raised); padding: 0.1em 0.4em; border-radius: 3px; }

.overview-topic {
  font-size: 1.05rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 2rem;
  font-style: italic;
}

.round-cards { display: flex; flex-direction: column; gap: 0.8rem; margin: 1.5rem 0; }

.round-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.2rem;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.round-card:hover {
  border-color: var(--accent-dim);
  background: var(--bg-raised);
}

.round-num {
  font-family: var(--font-sans);
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--accent);
  background: rgba(201,148,62,0.12);
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  white-space: nowrap;
}

.round-card-title {
  font-family: var(--font-serif);
  font-size: 1rem;
  color: var(--text-primary);
}

.round-card-format {
  font-family: var(--font-sans);
  font-size: 0.6rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-left: auto;
}

.section-label {
  font-family: var(--font-sans);
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  margin: 2rem 0 0.8rem;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.profile-swatch {
  width: 48px; height: 48px;
  border-radius: 50%;
  flex-shrink: 0;
}

.profile-header h2 { margin: 0; }

.profile-links {
  margin-top: 2rem;
  border-top: 1px solid var(--border);
  padding-top: 1.5rem;
}

.profile-link {
  display: block;
  padding: 0.4rem 0;
  color: var(--accent);
  font-family: var(--font-sans);
  font-size: 0.8rem;
  cursor: pointer;
  text-decoration: none;
}

.profile-link:hover { text-decoration: underline; }

.welcome { text-align: center; padding: 4rem 2rem; }
.welcome h2 { font-size: 2rem; color: var(--accent); margin-bottom: 1rem; }
.welcome p { color: var(--text-secondary); max-width: 50ch; margin: 0 auto 0.5rem; }

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0; top: 0; bottom: 0;
    z-index: 50;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
  }
  .sidebar.open { transform: translateX(0); }
  .sidebar-toggle { display: flex; }
  .content-header { padding-left: 3.5rem; }
  .tab-bar { padding-left: 1rem; }
  .reading-pane { padding: 1.5rem 1rem; }
  .compare-grid { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
  html { font-size: 15px; }
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

.sidebar-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 40;
}
.sidebar-backdrop.open { display: block; }
</style>
</head>
<body>
<div class="app">
  <button class="sidebar-toggle" id="sidebarToggle">&#9776;</button>
  <div class="sidebar-backdrop" id="backdrop"></div>

  <nav class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <h1>United Sapients</h1>
      <div class="subtitle">Council Proceedings</div>
    </div>
    <div class="sidebar-section" id="sessionNav"></div>
    <div class="sidebar-section" id="curatorNav"></div>
  </nav>

  <main class="main">
    <div class="content-header" id="contentHeader"></div>
    <div class="tab-bar" id="tabBar"></div>
    <div class="reading-pane" id="readingPane">
      <div class="reading-content" id="readingContent"></div>
    </div>
  </main>
</div>

<script>
window.COUNCIL_DATA = __COUNCIL_DATA__;

(function() {
  var D = window.COUNCIL_DATA;
  function $(s) { return document.querySelector(s); }
  function $$(s) { return document.querySelectorAll(s); }

  var curatorNames = {};
  var curatorColors = {};
  Object.keys(D.curators).forEach(function(slug) {
    curatorNames[slug] = D.curators[slug].name;
    curatorColors[slug] = D.curators[slug].color;
  });

  var state = { view: 'welcome', sessionIdx: null, tab: 'overview', filter: null, compare: false, curatorSlug: null };

  /* --- Safe DOM helpers --- */
  function txt(parent, tag, text, cls) {
    var el = document.createElement(tag);
    el.textContent = text;
    if (cls) el.className = cls;
    parent.appendChild(el);
    return el;
  }

  /* Set trusted HTML from build-time generated content (not user input) */
  function setTrustedHTML(el, html) {
    el.innerHTML = html;
  }

  /* --- Sidebar --- */
  function buildSidebar() {
    var sessionNav = $('#sessionNav');
    sessionNav.textContent = '';
    txt(sessionNav, 'div', 'Sessions', 'sidebar-section-title');
    D.sessions.forEach(function(s, i) {
      var el = document.createElement('a');
      el.className = 'sidebar-item';
      el.dataset.session = i;
      var idSpan = document.createElement('span');
      idSpan.className = 'session-id';
      idSpan.textContent = s.id;
      el.appendChild(idSpan);
      el.appendChild(document.createTextNode(' ' + s.title.replace(/^Session \d+:\s*/, '')));
      el.addEventListener('click', function() { navigate('session', i, 'overview'); });
      sessionNav.appendChild(el);
    });

    var curatorNav = $('#curatorNav');
    curatorNav.textContent = '';
    txt(curatorNav, 'div', 'Curators', 'sidebar-section-title');
    Object.keys(D.curators).forEach(function(slug) {
      var c = D.curators[slug];
      var el = document.createElement('a');
      el.className = 'sidebar-item';
      el.dataset.curator = slug;
      var dot = document.createElement('span');
      dot.className = 'curator-dot';
      dot.style.background = c.color;
      el.appendChild(dot);
      el.appendChild(document.createTextNode(c.name));
      el.addEventListener('click', function() { navigate('curator', slug); });
      curatorNav.appendChild(el);
    });
  }

  function updateSidebarActive() {
    $$('.sidebar-item').forEach(function(el) { el.classList.remove('active'); });
    if (state.view === 'session' && state.sessionIdx !== null) {
      var el = $('.sidebar-item[data-session="' + state.sessionIdx + '"]');
      if (el) el.classList.add('active');
    } else if (state.view === 'curator') {
      var el = $('.sidebar-item[data-curator="' + state.curatorSlug + '"]');
      if (el) el.classList.add('active');
    }
  }

  /* --- Navigation --- */
  function navigate(view, id, tab) {
    if (view === 'session') {
      state = { view: 'session', sessionIdx: id, tab: tab || 'overview', filter: null, compare: false, curatorSlug: null };
    } else if (view === 'curator') {
      state = { view: 'curator', curatorSlug: id, tab: null, filter: null, compare: false, sessionIdx: null };
    }
    pushHash();
    render();
    closeSidebar();
  }

  /* --- Hash routing --- */
  function pushHash() {
    var hash = '#/';
    if (state.view === 'session' && state.sessionIdx !== null) {
      var s = D.sessions[state.sessionIdx];
      hash = '#/session/' + s.id;
      if (state.tab === 'overview') hash += '/overview';
      else if (state.tab === 'briefing') hash += '/briefing';
      else if (state.tab === 'report') hash += '/report';
      else if (state.tab && state.tab.indexOf('round-') === 0) {
        hash += '/round/' + state.tab.split('-')[1];
        if (state.compare) hash += '/compare';
      }
    } else if (state.view === 'curator') {
      hash = '#/curator/' + state.curatorSlug;
    }
    history.replaceState(null, '', hash);
  }

  function parseHash() {
    var h = location.hash.replace('#/', '').split('/');
    if (h[0] === 'session') {
      var idx = -1;
      D.sessions.forEach(function(s, i) { if (s.id === h[1]) idx = i; });
      if (idx >= 0) {
        state.view = 'session';
        state.sessionIdx = idx;
        state.filter = null;
        state.compare = false;
        if (h[2] === 'round' && h[3]) {
          state.tab = 'round-' + h[3];
          if (h[4] === 'compare') state.compare = true;
        } else if (h[2] === 'briefing') state.tab = 'briefing';
        else if (h[2] === 'report') state.tab = 'report';
        else state.tab = 'overview';
      }
    } else if (h[0] === 'curator') {
      state.view = 'curator';
      state.curatorSlug = h[1];
    }
  }

  /* --- Render --- */
  function render() {
    updateSidebarActive();
    if (state.view === 'session') renderSession();
    else if (state.view === 'curator') renderCurator();
    else renderWelcome();
  }

  function renderWelcome() {
    $('#contentHeader').textContent = '';
    $('#tabBar').textContent = '';
    var rc = $('#readingContent');
    rc.textContent = '';
    rc.style.maxWidth = '';
    var w = document.createElement('div');
    w.className = 'welcome';
    txt(w, 'h2', 'Council Proceedings');
    txt(w, 'p', 'Select a session from the sidebar to begin reading deliberations of the United Sapients council.');
    rc.appendChild(w);
  }

  function renderSession() {
    var s = D.sessions[state.sessionIdx];

    var header = $('#contentHeader');
    header.textContent = '';
    txt(header, 'h2', s.title);
    var meta = document.createElement('div');
    meta.className = 'meta';
    txt(meta, 'span', s.date);
    txt(meta, 'span', s.rounds.length + ' rounds');
    txt(meta, 'span', s.status);
    header.appendChild(meta);

    /* Tabs */
    var tabBar = $('#tabBar');
    tabBar.textContent = '';
    function addTab(label, key) {
      var t = document.createElement('div');
      t.className = 'tab' + (state.tab === key ? ' active' : '');
      t.textContent = label;
      t.addEventListener('click', function() {
        state.tab = key;
        state.filter = null;
        state.compare = false;
        pushHash();
        render();
      });
      tabBar.appendChild(t);
    }
    addTab('Overview', 'overview');
    if (s.briefingHtml) addTab('Briefing', 'briefing');
    s.rounds.forEach(function(r) { addTab('R' + r.number, 'round-' + r.number); });
    if (s.reportHtml) addTab('Report', 'report');

    if (state.tab === 'overview') renderOverview(s);
    else if (state.tab === 'briefing') renderBriefing(s);
    else if (state.tab === 'report') renderReport(s);
    else if (state.tab.indexOf('round-') === 0) renderRound(s);
  }

  function renderOverview(s) {
    var rc = $('#readingContent');
    rc.textContent = '';
    rc.style.maxWidth = '';

    if (s.topic) {
      var tp = document.createElement('div');
      tp.className = 'overview-topic';
      tp.textContent = s.topic;
      rc.appendChild(tp);
    }

    txt(rc, 'div', 'Rounds', 'section-label');
    var cards = document.createElement('div');
    cards.className = 'round-cards';
    s.rounds.forEach(function(r) {
      var card = document.createElement('div');
      card.className = 'round-card';
      txt(card, 'span', 'R' + r.number, 'round-num');
      txt(card, 'span', r.title, 'round-card-title');
      if (r.format) txt(card, 'span', r.format, 'round-card-format');
      card.addEventListener('click', function() {
        state.tab = 'round-' + r.number;
        state.filter = null;
        state.compare = false;
        pushHash();
        render();
      });
      cards.appendChild(card);
    });
    rc.appendChild(cards);

    if (s.briefingHtml) {
      var bl = document.createElement('div');
      bl.className = 'section-label';
      bl.style.marginTop = '2.5rem';
      bl.textContent = 'Briefing';
      rc.appendChild(bl);
      var bc = document.createElement('div');
      bc.className = 'round-card';
      txt(bc, 'span', 'Session briefing document', 'round-card-title');
      bc.addEventListener('click', function() { state.tab = 'briefing'; pushHash(); render(); });
      rc.appendChild(bc);
    }

    if (s.reportHtml) {
      var rl = document.createElement('div');
      rl.className = 'section-label';
      rl.style.marginTop = '1.5rem';
      rl.textContent = 'Report';
      rc.appendChild(rl);
      var rcard = document.createElement('div');
      rcard.className = 'round-card';
      txt(rcard, 'span', 'Final council report', 'round-card-title');
      rcard.addEventListener('click', function() { state.tab = 'report'; pushHash(); render(); });
      rc.appendChild(rcard);
    }

    $('#readingPane').scrollTop = 0;
  }

  function renderBriefing(s) {
    setContent(s.briefingHtml, false);
  }

  function renderReport(s) {
    setContent(s.reportHtml, false);
  }

  function renderRound(s) {
    var num = parseInt(state.tab.split('-')[1]);
    var r = null;
    s.rounds.forEach(function(x) { if (x.number === num) r = x; });
    if (!r) return;

    var rc = $('#readingContent');
    rc.textContent = '';
    rc.style.maxWidth = state.compare ? 'none' : '';

    /* Filter bar */
    var fb = document.createElement('div');
    fb.className = 'filter-bar';
    txt(fb, 'span', 'Filter', 'filter-label');

    r.contributions.forEach(function(c) {
      var chip = document.createElement('button');
      chip.className = 'chip' + (state.filter === c.curatorSlug ? ' active' : '');
      chip.dataset.curator = c.curatorSlug;
      chip.textContent = curatorNames[c.curatorSlug];
      chip.addEventListener('click', function() {
        state.filter = state.filter === c.curatorSlug ? null : c.curatorSlug;
        state.compare = false;
        pushHash();
        render();
      });
      fb.appendChild(chip);
    });

    var cmpBtn = document.createElement('button');
    cmpBtn.className = 'chip-compare' + (state.compare ? ' active' : '');
    cmpBtn.textContent = 'Compare';
    cmpBtn.addEventListener('click', function() {
      state.compare = !state.compare;
      state.filter = null;
      pushHash();
      render();
    });
    fb.appendChild(cmpBtn);
    rc.appendChild(fb);

    if (r.preambleHtml && !state.compare) {
      var pre = document.createElement('div');
      pre.style.marginBottom = '2rem';
      setTrustedHTML(pre, r.preambleHtml);
      rc.appendChild(pre);
    }

    var container = state.compare ? document.createElement('div') : rc;
    if (state.compare) {
      container.className = 'compare-grid';
      rc.appendChild(container);
    }

    r.contributions.forEach(function(c) {
      var hidden = state.filter && state.filter !== c.curatorSlug;
      var sec = document.createElement('div');
      sec.className = 'curator-section' + (hidden ? ' hidden' : '');
      sec.dataset.curator = c.curatorSlug;

      var nameDiv = document.createElement('div');
      nameDiv.className = 'curator-name';
      var dot = document.createElement('span');
      dot.className = 'curator-dot';
      dot.style.background = curatorColors[c.curatorSlug];
      nameDiv.appendChild(dot);
      nameDiv.appendChild(document.createTextNode(curatorNames[c.curatorSlug]));
      sec.appendChild(nameDiv);

      var body = document.createElement('div');
      setTrustedHTML(body, c.html);
      sec.appendChild(body);

      container.appendChild(sec);
    });

    $('#readingPane').scrollTop = 0;
  }

  function renderCurator() {
    var c = D.curators[state.curatorSlug];
    if (!c) return;

    $('#contentHeader').textContent = '';
    $('#tabBar').textContent = '';

    var rc = $('#readingContent');
    rc.textContent = '';
    rc.style.maxWidth = '';

    var ph = document.createElement('div');
    ph.className = 'profile-header';
    var swatch = document.createElement('div');
    swatch.className = 'profile-swatch';
    swatch.style.background = c.color;
    ph.appendChild(swatch);
    txt(ph, 'h2', c.name);
    rc.appendChild(ph);

    var profileBody = document.createElement('div');
    setTrustedHTML(profileBody, c.profileHtml);
    rc.appendChild(profileBody);

    var links = document.createElement('div');
    links.className = 'profile-links';
    txt(links, 'div', 'Appearances', 'section-label');
    D.sessions.forEach(function(s, si) {
      s.rounds.forEach(function(r) {
        var has = r.contributions.some(function(co) { return co.curatorSlug === state.curatorSlug; });
        if (has) {
          var a = document.createElement('a');
          a.className = 'profile-link';
          a.textContent = s.id + ' \u2014 ' + r.title;
          a.addEventListener('click', function() {
            state = { view: 'session', sessionIdx: si, tab: 'round-' + r.number, filter: state.curatorSlug, compare: false, curatorSlug: null };
            pushHash();
            render();
          });
          links.appendChild(a);
        }
      });
    });
    rc.appendChild(links);

    $('#readingPane').scrollTop = 0;
  }

  function setContent(html, wide) {
    var el = $('#readingContent');
    el.textContent = '';
    el.style.maxWidth = wide ? 'none' : '';
    var wrapper = document.createElement('div');
    setTrustedHTML(wrapper, html);
    el.appendChild(wrapper);
    $('#readingPane').scrollTop = 0;
  }

  /* --- Mobile sidebar --- */
  function closeSidebar() {
    $('#sidebar').classList.remove('open');
    $('#backdrop').classList.remove('open');
  }

  $('#sidebarToggle').addEventListener('click', function() {
    $('#sidebar').classList.toggle('open');
    $('#backdrop').classList.toggle('open');
  });

  $('#backdrop').addEventListener('click', closeSidebar);

  /* --- Init --- */
  buildSidebar();
  if (location.hash.length > 2) parseHash();
  render();
  window.addEventListener('hashchange', function() { parseHash(); render(); });
})();
</script>
</body>
</html>'''


def main():
    data = build_data()
    data_json = json.dumps(data, ensure_ascii=False)
    html = get_html_template().replace("__COUNCIL_DATA__", data_json)
    OUT.write_text(html)
    print(f"Built {OUT} ({len(html):,} bytes)")
    print(f"  {len(data['sessions'])} sessions, {len(data['curators'])} curators")
    for s in data["sessions"]:
        print(f"  Session {s['id']}: {len(s['rounds'])} rounds")


if __name__ == "__main__":
    main()
