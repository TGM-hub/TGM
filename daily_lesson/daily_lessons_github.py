"""
daily_lessons.py
----------------
Generates a deep daily learning lesson from a broad domain catalog,
saves it as Markdown + HTML, stores metadata in SQLite, and opens it
in the browser.

Run once a day via cron (Linux/macOS) or Task Scheduler (Windows).

SETUP
-----
1. Copy .env.example to .env and fill in your values:
       OPENROUTER_API_KEY=sk-or-v1-...
       LESSON_MODEL=deepseek/deepseek-chat        # or any OpenAI-compatible model
       LESSON_OUTPUT_DIR=/path/to/output/folder   # defaults to ~/knowledge_history

2. Install dependencies:
       pip install openai python-dotenv

3. Run manually to test:
       python daily_lessons.py

4. Schedule daily execution:
   - Linux/macOS cron:  0 7 * * * /usr/bin/python3 /path/to/daily_lessons.py
   - Windows Task Scheduler: create a Basic Task, trigger Daily, action = python daily_lessons.py

CONFIGURATION
-------------
All configuration is via environment variables (see .env.example).
The domain catalog is loaded from domain_catalog.json in the same directory —
edit that file freely to add, remove, or rebalance topics.

COMPATIBLE PROVIDERS
--------------------
Any OpenAI-compatible API endpoint works. Tested with:
  - OpenRouter  (https://openrouter.ai/api/v1)     — recommended, access to many models
  - OpenAI      (https://api.openai.com/v1)
  - Ollama      (http://localhost:11434/v1)         — local models, set API_KEY to "ollama"
"""

import os
import re
import json
import time
import sqlite3
import logging
import datetime
import sys
import urllib.parse
import webbrowser
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars can be set directly in the shell

from openai import OpenAI

# ============================================================
# CONFIG — all values from environment variables
# ============================================================
API_KEY   = os.environ.get("OPENROUTER_API_KEY", "")
BASE_URL  = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL     = os.environ.get("LESSON_MODEL", "deepseek/deepseek-chat")

BASE_PATH = Path(os.environ.get("LESSON_OUTPUT_DIR", Path.home() / "knowledge_history"))
DB_PATH   = BASE_PATH / "knowledge.db"
MD_DIR    = BASE_PATH / "lessons"
HTML_DIR  = BASE_PATH / "lessons"
LOG_PATH  = BASE_PATH / "logs" / "daily_lesson.log"

MAX_RETRIES = int(os.environ.get("LESSON_MAX_RETRIES", 3))
RETRY_DELAY = int(os.environ.get("LESSON_RETRY_DELAY", 5))

if not API_KEY:
    print("ERROR: OPENROUTER_API_KEY environment variable is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)
# ============================================================

# ---- Logging: UTF-8 safe on Windows stdout ----
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

class SafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            msg = self.format(record).encode("ascii", errors="replace").decode("ascii")
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

_file_handler   = logging.FileHandler(LOG_PATH, encoding="utf-8")
_stream_handler = SafeStreamHandler(sys.stdout)
_formatter      = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s")
_file_handler.setFormatter(_formatter)
_stream_handler.setFormatter(_formatter)
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _stream_handler])
log = logging.getLogger(__name__)

MD_DIR.mkdir(parents=True, exist_ok=True)
BASE_PATH.mkdir(parents=True, exist_ok=True)

REQUIRED_KEYS = {
    "title", "domain", "hook", "prerequisites",
    "part1_foundations", "part2_mechanisms", "part3_advanced",
    "key_takeaways", "related_concepts",
    "further_depth", "wikipedia_links", "youtube_links",
}

# ============================================================
# LOAD DOMAIN CATALOG FROM JSON
# ============================================================
def load_catalog(path: Path) -> str:
    """Load domain_catalog.json and format it as a readable string for the prompt."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        log.warning(f"domain_catalog.json not found at {path}. Using empty catalog.")
        return "(no catalog loaded — place domain_catalog.json next to this script)"
    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in domain_catalog.json: {e}")
        return "(catalog parse error)"

    lines = []
    for category, subcategories in data.items():
        lines.append(f"\n{category}")
        for subcat, topics in subcategories.items():
            topic_str = ", ".join(topics)
            lines.append(f"  - {subcat}: {topic_str}")
    return "\n".join(lines)

CATALOG_PATH   = Path(__file__).parent / "domain_catalog.json"
DOMAIN_CATALOG = load_catalog(CATALOG_PATH)


# ============================================================
# DB
# ============================================================
def init_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT UNIQUE,
            domain        TEXT,
            date_created  TEXT,
            content_json  TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS concept_edges (
            source  TEXT NOT NULL,
            target  TEXT NOT NULL,
            PRIMARY KEY (source, target)
        )
    """)
    conn.commit()
    return conn


def get_recent_lessons(conn: sqlite3.Connection, n: int = 60):
    rows = conn.execute(
        "SELECT title, domain FROM lessons ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def save_lesson(conn: sqlite3.Connection, lesson: dict, today: str):
    conn.execute("""
        INSERT INTO lessons (title, domain, date_created, content_json)
        VALUES (?, ?, ?, ?)
    """, (lesson["title"], lesson["domain"], today, json.dumps(lesson, ensure_ascii=False)))
    for target in lesson.get("related_concepts", []):
        conn.execute(
            "INSERT OR IGNORE INTO concept_edges (source, target) VALUES (?, ?)",
            (lesson["title"], target),
        )
    conn.commit()


# ============================================================
# PROMPT
# ============================================================
def build_prompt(recent_lessons: list) -> str:
    if recent_lessons:
        recent_str     = "\n".join(f"  - {t} ({d})" for t, d in recent_lessons[:30])
        recent_domains = list({d for _, d in recent_lessons[:15]})
    else:
        recent_str     = "  (none yet)"
        recent_domains = []

    return f"""You are writing one deeply educational daily learning module for a reader who has solid fundamentals across all scientific and humanistic disciplines and wants genuine depth — not introductory material. Longer is better. Do not summarize when you can explain. Do not explain when you can illustrate with a concrete example.

RECENT LESSONS (avoid duplicating titles or clustering in the same sub-domain):
{recent_str}

RECENT DOMAINS TO DEPRIORITIZE: {recent_domains}

DOMAIN CATALOG — pick ONE specific topic, ensuring variety across the week:
{DOMAIN_CATALOG}

STRUCTURAL PHILOSOPHY:
The lesson is a rigorous self-contained mini-lecture. Each part must build directly on the previous.
  Prerequisites → Part I: Foundations → Part II: Mechanisms → Part III: Advanced Territory → Key Takeaways → Further Depth
The reader knows fundamentals but needs the precise conceptual bridge to reach expert-level understanding.

EXAMPLE POLICY (critical):
Every Part (I, II, III) MUST contain at least one fully worked concrete example:
  - Name a specific real case (a molecule, experiment, theorem, author, event — never generic)
  - Walk through it step by step showing HOW the concept applies, not just THAT it applies
  - If numbers or equations are relevant, state them in plain language
  - Examples should feel like the best moment in a great lecture — when abstraction becomes real

SECTIONS — follow this order exactly:

1. hook — a striking fact, paradox, or collision that creates immediate intellectual tension. No definitions yet.
2. prerequisites — name the specific prior concepts the reader must hold. Frame the conceptual gap this lesson bridges.
3. part1_foundations — the core theoretical structure, built from prerequisites. At least one foundational example embedded.
4. part2_mechanisms — detailed step-by-step working: specific pathways, equations in words, edge cases. One detailed end-to-end worked example.
5. part3_advanced — current frontiers, open problems, cutting-edge extensions. One named frontier problem with enough detail to feel its difficulty.
6. key_takeaways — distilled insights worth carrying: not summaries but the things you'd write in a textbook margin.
7. further_depth — the harder generalization, the adjacent field this unlocks, a specific direction to pursue.
8. wikipedia_links — 5–7 specific Wikipedia article titles for direct navigation.
9. youtube_links — 3–5 YouTube search queries that will reliably surface excellent videos on this topic. Prefer known educators: 3Blue1Brown, Veritasium, Kurzgesagt, PBS Space Time, Numberphile, SciShow, Sean Carroll, MIT OpenCourseWare, CrashCourse, Sixty Symbols, Domain of Science, History of the Earth.
10. diagram_ascii — optional: a compact diagram (max 20 lines) if the concept has a spatial or sequential structure worth showing. Otherwise null.

REQUIREMENTS PER KEY:
- "hook": 2–3 sentences. Start with a surprising number, paradox, or named historical fact.
- "prerequisites": 4–5 sentences. Name specific concepts, not vague domains. Explain the gap.
- "part1_foundations": 12–16 sentences. Dense, rigorous. At least one worked example embedded in the prose.
- "part2_mechanisms": 14–18 sentences. Name the actual moving parts — receptors, coupling constants, lemmas. One end-to-end worked example.
- "part3_advanced": 10–13 sentences. One named frontier problem with context. Current research with specific names or years where possible.
- "key_takeaways": 5–7 items. Each a distilled insight — "X means Y, which is counterintuitive because Z."
- "related_concepts": 6–10 short concept names.
- "further_depth": 4–5 sentences. A specific direction to pursue.
- "wikipedia_links": list of 5–7 objects: {{"title": "exact Wikipedia article title", "description": "one sentence on relevance"}}.
- "youtube_links": list of 3–5 objects: {{"query": "specific YouTube search string", "description": "one sentence on what to look for and why it's worth watching"}}.
- "diagram_ascii": string or null.

Return STRICT raw JSON only — no markdown fences, no preamble, no commentary.

{{
  "title": "string",
  "domain": "string",
  "hook": "string",
  "prerequisites": "string",
  "part1_foundations": "string",
  "part2_mechanisms": "string",
  "part3_advanced": "string",
  "key_takeaways": ["string"],
  "related_concepts": ["string"],
  "further_depth": "string",
  "wikipedia_links": [{{"title": "string", "description": "string"}}],
  "youtube_links": [{{"query": "string", "description": "string"}}],
  "diagram_ascii": "string or null"
}}"""


# ============================================================
# MODEL CALL
# ============================================================
def clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def validate(lesson: dict):
    missing = REQUIRED_KEYS - lesson.keys()
    if missing:
        raise ValueError(f"Missing keys: {missing}")
    for key in ("key_takeaways", "related_concepts", "wikipedia_links", "youtube_links"):
        if not isinstance(lesson.get(key), list):
            raise TypeError(f"'{key}' must be a list")


def fetch_lesson(client: OpenAI, recent_lessons: list) -> dict:
    prompt = build_prompt(recent_lessons)
    for attempt in range(1, MAX_RETRIES + 1):
        log.info(f"Attempt {attempt}/{MAX_RETRIES} — calling model...")
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.85,
                max_tokens=8192,
            )
            raw    = clean_json(response.choices[0].message.content)
            lesson = json.loads(raw)
            validate(lesson)
            log.info(f"Lesson received: {lesson['title']} ({lesson['domain']})")
            return lesson
        except json.JSONDecodeError as e:
            log.warning(f"Invalid JSON (attempt {attempt}): {e}")
        except (ValueError, TypeError) as e:
            log.warning(f"Validation failed (attempt {attempt}): {e}")
        except Exception as e:
            log.error(f"Unexpected error (attempt {attempt}): {e}")
        if attempt < MAX_RETRIES:
            log.info(f"Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
    raise RuntimeError(f"Failed after {MAX_RETRIES} attempts.")


# ============================================================
# MARKDOWN RENDERER
# ============================================================
def render_markdown(lesson: dict, date: str) -> str:
    def bullets(items):
        return "\n".join(f"- {i}" for i in items) if items else "_None._"

    related = ", ".join(f"`{c}`" for c in lesson.get("related_concepts", []))

    wiki_md = ""
    for link in lesson.get("wikipedia_links", []):
        slug = link["title"].replace(" ", "_")
        wiki_md += f"- [{link['title']}](https://en.wikipedia.org/wiki/{slug}) — {link['description']}\n"

    yt_md = ""
    for link in lesson.get("youtube_links", []):
        q   = urllib.parse.quote_plus(link["query"])
        url = f"https://www.youtube.com/results?search_query={q}"
        yt_md += f"- [{link['query']}]({url}) — {link['description']}\n"

    diagram_section = ""
    if lesson.get("diagram_ascii"):
        diagram_section = f"\n## Diagram\n\n```\n{lesson['diagram_ascii']}\n```\n\n---\n"

    return "\n".join([
        f'---',
        f'title: "{lesson["title"]}"',
        f'domain: {lesson["domain"]}',
        f'date: {date}',
        f'related_concepts: {json.dumps(lesson.get("related_concepts", []))}',
        f'---', f'',
        f'# {lesson["title"]}',
        f'> **Domain:** {lesson["domain"]}  |  **Date:** {date}', f'', f'---', f'',
        f'## Hook', f'', lesson.get("hook", ""), f'', f'---', f'',
        f'## Prerequisites', f'', lesson.get("prerequisites", ""), f'', f'---', f'',
        f'## Part I — Foundations', f'', lesson.get("part1_foundations", ""), f'', f'---', f'',
        f'## Part II — Mechanisms', f'', lesson.get("part2_mechanisms", ""), f'',
        diagram_section,
        f'---', f'',
        f'## Part III — Advanced Territory', f'', lesson.get("part3_advanced", ""), f'', f'---', f'',
        f'## Key Takeaways', f'', bullets(lesson.get("key_takeaways", [])), f'', f'---', f'',
        f'## Related Concepts', f'', related, f'', f'---', f'',
        f'## Further Depth', f'', lesson.get("further_depth", ""), f'', f'---', f'',
        f'## Wikipedia', f'', wiki_md,
        f'## YouTube', f'', yt_md,
    ])


def save_markdown(lesson: dict, date: str) -> Path:
    slug     = re.sub(r"[^\w\-]", "_", lesson["title"].lower())[:60]
    filename = MD_DIR / f"{date}_{slug}.md"
    filename.write_text(render_markdown(lesson, date), encoding="utf-8")
    log.info(f"Markdown saved: {filename}")
    return filename


# ============================================================
# DOMAIN COLORS
# ============================================================
DOMAIN_COLORS = {
    "quantum":               "#22d3ee",
    "particle physics":      "#06b6d4",
    "nuclear":               "#0ea5e9",
    "cosmology":             "#38bdf8",
    "relativity":            "#7dd3fc",
    "astrophysics":          "#93c5fd",
    "physics":               "#60a5fa",
    "number theory":         "#818cf8",
    "topology":              "#6366f1",
    "analysis":              "#8b5cf6",
    "algebra":               "#a78bfa",
    "logic":                 "#c4b5fd",
    "game theory":           "#ddd6fe",
    "mathematics":           "#818cf8",
    "thermodynamics":        "#fb923c",
    "statistical mechanics": "#f97316",
    "materials science":     "#ea580c",
    "material science":      "#ea580c",
    "aerospace":             "#c2410c",
    "engineering":           "#fed7aa",
    "immunology":            "#f43f5e",
    "autoimmune":            "#fb7185",
    "neuroscience":          "#a78bfa",
    "microbiology":          "#34d399",
    "genetics":              "#10b981",
    "oncology":              "#d946ef",
    "evolutionary biology":  "#4ade80",
    "cell biology":          "#86efac",
    "medicine":              "#f43f5e",
    "biology":               "#4ade80",
    "molecular biology":     "#34d399",
    "organic chemistry":     "#fbbf24",
    "biochemistry":          "#f59e0b",
    "physical chemistry":    "#d97706",
    "electrochemistry":      "#b45309",
    "astrochemistry":        "#fde68a",
    "chemistry":             "#fbbf24",
    "stoicism":              "#c084fc",
    "epistemology":          "#d8b4fe",
    "ethics":                "#e9d5ff",
    "philosophy of mind":    "#c084fc",
    "political philosophy":  "#a855f7",
    "philosophy":            "#c084fc",
    "ancient history":       "#f472b6",
    "history of science":    "#ec4899",
    "history":               "#f472b6",
    "civilizations":         "#db2777",
    "linguistics":           "#e879f9",
    "phonology":             "#f0abfc",
    "semiotics":             "#d946ef",
    "plate tectonics":       "#a3e635",
    "oceanography":          "#4ade80",
    "climatology":           "#86efac",
    "geomorphology":         "#bef264",
    "geography":             "#a3e635",
    "earth sciences":        "#84cc16",
    "paleontology":          "#fb923c",
    "evolution":             "#4ade80",
    "paleobiology":          "#fdba74",
    "literature":            "#f472b6",
    "mythology":             "#fda4af",
    "cultural history":      "#fb7185",
    "humanities":            "#f9a8d4",
    "ecology":               "#86efac",
    "cognitive science":     "#c084fc",
    "computer science":      "#2dd4bf",
    "information theory":    "#67e8f9",
    "economic history":      "#f59e0b",
    "economics":             "#fbbf24",
}

def domain_color(domain: str) -> str:
    dl = domain.lower()
    for k, v in DOMAIN_COLORS.items():
        if k in dl:
            return v
    return "#94a3b8"


# ============================================================
# HTML RENDERER  (identical to personal version)
# ============================================================
def render_html(lesson: dict, date: str) -> str:
    color = domain_color(lesson["domain"])
    h     = color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def li_items(items):
        return "\n".join(f"      <li>{item}</li>" for item in items)

    def tag_items(items):
        return "\n".join(f'      <span class="tag">{item}</span>' for item in items)

    def wiki_items(links):
        out = []
        for link in links:
            slug = urllib.parse.quote(link["title"].replace(" ", "_"))
            url  = f"https://en.wikipedia.org/wiki/{slug}"
            out.append(
                f'      <a class="resource-link" href="{url}" target="_blank" rel="noopener">'
                f'<span class="resource-icon wiki-icon">W</span>'
                f'<span class="resource-content"><strong>{link["title"]}</strong>'
                f'<em>{link["description"]}</em></span>'
                f'<span class="resource-arrow">↗</span></a>'
            )
        return "\n".join(out)

    def yt_items(links):
        out = []
        for link in links:
            q   = urllib.parse.quote_plus(link["query"])
            url = f"https://www.youtube.com/results?search_query={q}"
            out.append(
                f'      <a class="resource-link" href="{url}" target="_blank" rel="noopener">'
                f'<span class="resource-icon yt-icon">▶</span>'
                f'<span class="resource-content"><strong>{link["query"]}</strong>'
                f'<em>{link["description"]}</em></span>'
                f'<span class="resource-arrow">↗</span></a>'
            )
        return "\n".join(out)

    diagram_html = ""
    if lesson.get("diagram_ascii"):
        diagram_html = f"""
  <div class="section">
    <div class="section-label">Diagram</div>
    <div class="diagram-block"><pre>{lesson['diagram_ascii']}</pre></div>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{lesson['title']}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,300&family=JetBrains+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg:       #0a0c10;
      --surface:  #10141c;
      --surface2: #161b26;
      --border:   #1e2535;
      --text:     #c9d1e0;
      --muted:    #4a5568;
      --accent:   {color};
    }}
    html {{ scroll-behavior: smooth; }}
    body {{
      background: var(--bg); color: var(--text);
      font-family: 'DM Sans', sans-serif; font-weight: 300;
      line-height: 1.75; min-height: 100vh; padding-bottom: 100px;
    }}
    .read-progress {{
      position: fixed; top: 0; left: 0; height: 3px;
      background: var(--accent); box-shadow: 0 0 12px rgba({r},{g},{b},.8);
      width: 0%; transition: width .1s linear; z-index: 100;
    }}
    .hero {{
      position: relative; padding: 90px 40px 70px;
      border-bottom: 1px solid var(--border); overflow: hidden;
    }}
    .hero::before {{
      content: ''; position: absolute; inset: 0;
      background:
        radial-gradient(ellipse 80% 70% at 10% 50%, rgba({r},{g},{b},.13) 0%, transparent 65%),
        radial-gradient(ellipse 40% 40% at 90% 20%, rgba({r},{g},{b},.06) 0%, transparent 60%);
      pointer-events: none;
    }}
    .hero-inner {{ max-width: 860px; margin: 0 auto; position: relative; }}
    .domain-badge {{
      display: inline-flex; align-items: center; gap: 8px;
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
      letter-spacing: .14em; text-transform: uppercase; color: var(--accent);
      border: 1px solid rgba({r},{g},{b},.35); background: rgba({r},{g},{b},.07);
      padding: 5px 14px; border-radius: 4px; margin-bottom: 30px;
    }}
    .domain-badge::before {{
      content: ''; width: 6px; height: 6px; border-radius: 50%;
      background: var(--accent); box-shadow: 0 0 8px var(--accent);
    }}
    h1 {{
      font-family: 'Fraunces', serif; font-size: clamp(2.2rem, 5vw, 3.6rem);
      font-weight: 600; line-height: 1.08; color: #edf2f9;
      letter-spacing: -.025em; margin-bottom: 24px;
    }}
    .hero-meta {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px; color: var(--muted); letter-spacing: .08em;
    }}
    .container {{ max-width: 860px; margin: 0 auto; padding: 0 40px; }}
    .section {{
      padding: 52px 0; border-bottom: 1px solid var(--border);
      animation: fadeUp .55s ease both;
    }}
    .section:nth-child(2)  {{ animation-delay: .04s; }}
    .section:nth-child(3)  {{ animation-delay: .08s; }}
    .section:nth-child(4)  {{ animation-delay: .12s; }}
    .section:nth-child(5)  {{ animation-delay: .16s; }}
    .section:nth-child(6)  {{ animation-delay: .20s; }}
    .section:nth-child(7)  {{ animation-delay: .24s; }}
    .section:nth-child(8)  {{ animation-delay: .28s; }}
    .section:nth-child(9)  {{ animation-delay: .32s; }}
    .section:nth-child(10) {{ animation-delay: .36s; }}
    .section:nth-child(11) {{ animation-delay: .40s; }}
    @keyframes fadeUp {{
      from {{ opacity:0; transform:translateY(20px); }}
      to   {{ opacity:1; transform:translateY(0); }}
    }}
    .section-label {{
      display: flex; align-items: center; gap: 10px;
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
      letter-spacing: .16em; text-transform: uppercase;
      color: var(--muted); margin-bottom: 22px;
    }}
    .section-label::after {{ content: ''; flex: 1; height: 1px; background: var(--border); }}
    .hook-block {{
      font-family: 'Fraunces', serif; font-size: clamp(1.15rem, 2.5vw, 1.35rem);
      font-weight: 300; font-style: italic; color: #e2e8f4;
      line-height: 1.65; padding-left: 22px; border-left: 3px solid var(--accent);
    }}
    .prereq-block {{
      background: rgba({r},{g},{b},.04); border: 1px solid rgba({r},{g},{b},.2);
      border-left: 3px solid rgba({r},{g},{b},.5); border-radius: 10px; padding: 20px 24px;
    }}
    .prereq-label {{
      font-family: 'JetBrains Mono', monospace; font-size: 10px;
      letter-spacing: .14em; text-transform: uppercase;
      color: rgba({r},{g},{b},.7); margin-bottom: 10px;
    }}
    .prereq-block p {{ font-size: .94rem; line-height: 1.78; color: var(--text); }}
    .part-indicator {{ display: inline-flex; align-items: center; gap: 10px; margin-bottom: 16px; }}
    .part-number {{
      font-family: 'JetBrains Mono', monospace; font-size: 10px;
      width: 26px; height: 26px; border-radius: 50%;
      background: rgba({r},{g},{b},.15); border: 1px solid rgba({r},{g},{b},.35);
      color: var(--accent); display: flex; align-items: center;
      justify-content: center; flex-shrink: 0;
    }}
    .part-title {{
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
      letter-spacing: .14em; text-transform: uppercase; color: var(--accent);
    }}
    .theory-block {{
      background: linear-gradient(135deg, rgba({r},{g},{b},.05) 0%, transparent 50%);
      border: 1px solid rgba({r},{g},{b},.18); border-radius: 14px; padding: 32px 36px;
    }}
    .theory-block.part2 {{
      background: linear-gradient(135deg, rgba({r},{g},{b},.08) 0%, transparent 60%);
      border-color: rgba({r},{g},{b},.25);
    }}
    .theory-block.part3 {{
      background: linear-gradient(135deg, rgba({r},{g},{b},.12) 0%, rgba({r},{g},{b},.02) 70%);
      border-color: rgba({r},{g},{b},.35);
    }}
    .theory-block p {{ font-size: .97rem; line-height: 1.85; color: var(--text); }}
    .diagram-block {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px; padding: 24px 28px; overflow-x: auto;
    }}
    .diagram-block pre {{
      font-family: 'JetBrains Mono', monospace; font-size: .82rem;
      line-height: 1.6; color: rgba({r},{g},{b},.9); white-space: pre;
    }}
    ul.styled {{ list-style: none; display: flex; flex-direction: column; gap: 10px; }}
    ul.styled li {{
      display: flex; gap: 14px; padding: 15px 20px;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 9px; font-size: .94rem; line-height: 1.68;
      transition: border-color .2s, background .2s;
    }}
    ul.styled li:hover {{ border-color: rgba({r},{g},{b},.4); background: var(--surface2); }}
    ul.styled li::before {{ content: '✓'; color: rgba({r},{g},{b},.8); font-size: .85rem; flex-shrink: 0; margin-top: 3px; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .tag {{
      font-family: 'JetBrains Mono', monospace; font-size: 12px;
      padding: 6px 15px; border-radius: 6px;
      background: var(--surface2); border: 1px solid var(--border);
      color: var(--accent); letter-spacing: .04em;
      transition: border-color .2s, background .2s;
    }}
    .tag:hover {{ background: rgba({r},{g},{b},.12); border-color: rgba({r},{g},{b},.5); }}
    .resource-tabs {{ display: flex; gap: 8px; margin-bottom: 18px; }}
    .resource-tab {{
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
      letter-spacing: .1em; text-transform: uppercase;
      padding: 6px 16px; border-radius: 6px; cursor: pointer;
      background: var(--surface2); border: 1px solid var(--border);
      color: var(--muted); transition: all .2s;
    }}
    .resource-tab.active {{
      background: rgba({r},{g},{b},.12); border-color: rgba({r},{g},{b},.4); color: var(--accent);
    }}
    .resource-panel {{ display: none; }}
    .resource-panel.active {{ display: flex; flex-direction: column; gap: 10px; }}
    .resource-link {{
      display: flex; align-items: center; gap: 14px; padding: 14px 18px;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 9px; text-decoration: none; color: inherit;
      transition: border-color .2s, background .2s;
    }}
    .resource-link:hover {{ border-color: rgba({r},{g},{b},.4); background: var(--surface2); }}
    .resource-icon {{
      width: 32px; height: 32px; border-radius: 7px; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center;
      font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600;
    }}
    .wiki-icon {{ background: rgba({r},{g},{b},.12); border: 1px solid rgba({r},{g},{b},.3); color: var(--accent); }}
    .yt-icon {{ background: rgba(255,0,0,.1); border: 1px solid rgba(255,0,0,.25); color: #f87171; font-size: 14px; }}
    .resource-content {{ flex: 1; }}
    .resource-content strong {{ display: block; font-size: .93rem; font-weight: 500; color: #e2e8f4; margin-bottom: 3px; }}
    .resource-content em {{ display: block; font-size: .84rem; font-style: normal; color: var(--muted); line-height: 1.5; }}
    .resource-arrow {{ color: var(--muted); font-size: .9rem; flex-shrink: 0; }}
    .depth-card {{
      background: linear-gradient(135deg, rgba({r},{g},{b},.09) 0%, var(--surface) 55%);
      border: 1px solid rgba({r},{g},{b},.32); border-radius: 14px; padding: 32px 36px;
    }}
    .depth-card .arrow {{ display: block; font-size: 1.5rem; color: var(--accent); margin-bottom: 14px; }}
    .depth-card p {{ font-size: .97rem; line-height: 1.82; color: var(--text); }}
    @media (max-width: 640px) {{
      .hero {{ padding: 55px 20px 45px; }}
      .container {{ padding: 0 20px; }}
      .theory-block, .depth-card {{ padding: 22px 20px; }}
    }}
  </style>
</head>
<body>
<div class="read-progress" id="progress"></div>
<div class="hero">
  <div class="hero-inner">
    <div class="domain-badge">{lesson['domain']}</div>
    <h1>{lesson['title']}</h1>
    <div class="hero-meta">knowledge_history &nbsp;·&nbsp; {date}</div>
  </div>
</div>
<div class="container">
  <div class="section">
    <div class="section-label">Hook</div>
    <div class="hook-block">{lesson.get('hook', '')}</div>
  </div>
  <div class="section">
    <div class="section-label">Prerequisites</div>
    <div class="prereq-block">
      <div class="prereq-label">What you need to know first</div>
      <p>{lesson.get('prerequisites', '')}</p>
    </div>
  </div>
  <div class="section">
    <div class="section-label">Part I</div>
    <div class="part-indicator">
      <div class="part-number">I</div>
      <div class="part-title">Foundations</div>
    </div>
    <div class="theory-block"><p>{lesson.get('part1_foundations', '')}</p></div>
  </div>
  <div class="section">
    <div class="section-label">Part II</div>
    <div class="part-indicator">
      <div class="part-number">II</div>
      <div class="part-title">Mechanisms</div>
    </div>
    <div class="theory-block part2"><p>{lesson.get('part2_mechanisms', '')}</p></div>
  </div>
{diagram_html}
  <div class="section">
    <div class="section-label">Part III</div>
    <div class="part-indicator">
      <div class="part-number">III</div>
      <div class="part-title">Advanced Territory</div>
    </div>
    <div class="theory-block part3"><p>{lesson.get('part3_advanced', '')}</p></div>
  </div>
  <div class="section">
    <div class="section-label">Key Takeaways</div>
    <ul class="styled">
{li_items(lesson.get('key_takeaways', []))}
    </ul>
  </div>
  <div class="section">
    <div class="section-label">Related Concepts</div>
    <div class="tags">
{tag_items(lesson.get('related_concepts', []))}
    </div>
  </div>
  <div class="section">
    <div class="section-label">Further Depth</div>
    <div class="depth-card">
      <span class="arrow">&#8594;</span>
      <p>{lesson.get('further_depth', '')}</p>
    </div>
  </div>
  <div class="section" style="border-bottom:none;">
    <div class="section-label">Resources</div>
    <div class="resource-tabs">
      <button class="resource-tab active" onclick="switchTab(this,'wiki')">Wikipedia</button>
      <button class="resource-tab" onclick="switchTab(this,'yt')">YouTube</button>
    </div>
    <div id="wiki" class="resource-panel active">
{wiki_items(lesson.get('wikipedia_links', []))}
    </div>
    <div id="yt" class="resource-panel">
{yt_items(lesson.get('youtube_links', []))}
    </div>
  </div>
</div>
<script>
  window.addEventListener('scroll', () => {{
    const pct = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight) * 100;
    document.getElementById('progress').style.width = Math.min(pct, 100) + '%';
  }});
  function switchTab(btn, panelId) {{
    document.querySelectorAll('.resource-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.resource-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(panelId).classList.add('active');
  }}
</script>
</body>
</html>"""


def save_html(lesson: dict, date: str) -> Path:
    slug     = re.sub(r"[^\w\-]", "_", lesson["title"].lower())[:60]
    filename = HTML_DIR / f"{date}_{slug}.html"
    filename.write_text(render_html(lesson, date), encoding="utf-8")
    log.info(f"HTML saved: {filename}")
    return filename


# ============================================================
# OPEN IN BROWSER
# ============================================================
def open_in_browser(path: Path):
    try:
        webbrowser.open(path.as_uri())
        log.info(f"Opened in browser: {path}")
    except Exception as e:
        log.warning(f"Could not open browser: {e}")


# ============================================================
# MAIN
# ============================================================
def main():
    today = datetime.date.today().isoformat()
    log.info(f"=== daily_lessons.py — {today} ===")

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    conn   = init_db(DB_PATH)

    try:
        recent    = get_recent_lessons(conn, n=60)
        lesson    = fetch_lesson(client, recent)
        save_lesson(conn, lesson, today)
        save_markdown(lesson, today)
        html_path = save_html(lesson, today)
        log.info(f"Lesson saved: {lesson['title']}")
        open_in_browser(html_path)

    except RuntimeError as e:
        log.error(f"FAILED: {e}")
        sys.exit(1)
    except sqlite3.IntegrityError:
        log.warning("Lesson already in DB (duplicate title). Nothing written.")
        sys.exit(0)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
