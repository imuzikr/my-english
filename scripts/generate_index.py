#!/usr/bin/env python3
"""Generates main index for daily English learning HTML files."""

import re
from html import escape
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
DAILY_DIR = ROOT / "daily"
SKIP = {"index.html"}

GRADIENTS = [
    ("3b82f6", "1d4ed8"),
    ("8b5cf6", "6d28d9"),
    ("10b981", "047857"),
    ("f59e0b", "b45309"),
    ("ef4444", "b91c1c"),
    ("06b6d4", "0e7490"),
    ("ec4899", "be185d"),
    ("84cc16", "4d7c0f"),
]

LEVEL_COLORS = {
    "beginner":     ("dcfce7", "16a34a"),
    "intermediate": ("dbeafe", "2563eb"),
    "advanced":     ("fae8ff", "9333ea"),
    "": ("f3f4f6", "6b7280"),
}

SHARED_CSS = """
:root {
  --bg:#f8fafc; --bg-card:#ffffff; --text:#0f172a; --text-muted:#64748b;
  --text-faint:#94a3b8; --border:#e2e8f0; --accent:#3b82f6;
  --accent-hover:#2563eb; --accent-soft:#eff6ff;
  --font:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --r-md:8px; --r-lg:14px;
  --sh-sm:0 1px 3px rgba(0,0,0,.06); --sh-md:0 4px 16px rgba(0,0,0,.1);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:var(--text);min-height:100vh}
a{text-decoration:none;color:inherit}
"""


def get_meta(path: Path, key: str, default: str = "") -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    key_pattern = re.escape(key)
    m = re.search(
        rf'<meta\s+name=["\']{key_pattern}["\']\s+content=["\'](.*?)["\']',
        text, re.IGNORECASE
    )
    if not m:
        m = re.search(
            rf'<meta\s+content=["\'](.*?)["\']\s+name=["\']{key_pattern}["\']',
            text, re.IGNORECASE
        )
    return m.group(1).strip() if m else default


def get_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else path.stem.replace("-", " ").title()


def get_date(path: Path) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", path.stem)
    return m.group(1) if m else ""


def get_og_image(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', text, re.IGNORECASE)
    if not m:
        m = re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:image["\']', text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def collect_files():
    if not DAILY_DIR.exists():
        return []
    files = []
    for html in sorted(DAILY_DIR.glob("*.html"), reverse=True):
        if html.name in SKIP:
            continue
        if not re.match(r"\d{4}-\d{2}-\d{2}\.html$", html.name):
            continue
        level = get_meta(html, "english-level").lower()
        topic = get_meta(html, "english-topic")
        files.append({
            "name": html.name,
            "path": f"daily/{html.name}",
            "title": get_title(html),
            "description": get_meta(html, "description"),
            "date": get_date(html),
            "og_image": get_og_image(html),
            "level": level,
            "topic": topic,
        })
    return files


BACK_BUTTON_MARKER = 'id="back-to-index"'

PWA_MARKER = 'rel="manifest"'
PWA_HEAD_SNIPPET = """<link rel="manifest" href="/my-english/manifest.json">
<meta name="theme-color" content="#3b82f6">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="My English">
<link rel="apple-touch-icon" href="/my-english/icons/apple-touch-icon.png">
<script>
if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('/my-english/sw.js',{updateViaCache:'none'}).catch(function(){});});}
</script>
"""


def inject_pwa_meta(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if PWA_MARKER in text:
        return False
    if "</head>" not in text:
        return False
    path.write_text(text.replace("</head>", PWA_HEAD_SNIPPET + "</head>", 1), encoding="utf-8")
    return True


def inject_back_button(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if BACK_BUTTON_MARKER in text:
        return False
    if "</body>" not in text:
        return False
    snippet = (
        '\n'
        '<a id="back-to-index" href="../index.html" aria-label="목록으로" title="목록으로">'
        '<svg viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18">'
        '<path d="M8.5 15L3 10l5.5-5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M3 10h14" stroke="white" stroke-width="2" stroke-linecap="round"/>'
        '</svg></a>\n'
        '<style>\n'
        '#back-to-index{position:fixed;bottom:1.5rem;left:1.5rem;width:44px;height:44px;'
        'background:#3b82f6;color:#fff;border-radius:9999px;display:flex;'
        'align-items:center;justify-content:center;text-decoration:none;'
        'box-shadow:0 4px 16px rgba(0,0,0,.18);transition:background .15s,transform .15s;z-index:800;}\n'
        '#back-to-index:hover{background:#2563eb;transform:translateX(-2px);}\n'
        '@media(max-width:600px){#back-to-index{bottom:1rem;left:1rem;}}\n'
        '</style>\n'
    )
    path.write_text(text.replace("</body>", snippet + "</body>", 1), encoding="utf-8")
    return True


def level_badge(level: str) -> str:
    bg, fg = LEVEL_COLORS.get(level, LEVEL_COLORS[""])
    if not level:
        return ""
    label = level.capitalize()
    return f"<span style='background:#{bg};color:#{fg};font-size:.75rem;font-weight:600;padding:2px 10px;border-radius:999px'>{label}</span>"


def render_card(f: dict, idx: int) -> str:
    c1, c2 = GRADIENTS[idx % len(GRADIENTS)]
    title = escape(f["title"])
    data_title = escape(f["title"].lower(), quote=True)
    date = escape(f["date"])
    description = escape(f["description"])
    level = escape(f["level"], quote=True)
    topic = escape(f["topic"])
    data_topic = escape(f["topic"].lower(), quote=True)
    path = escape(f["path"], quote=True)

    date_str = f"<span style='font-size:.8rem;color:var(--text-faint)'>{date}</span>" if date else ""
    desc_str = f"<p style='font-size:.85rem;color:var(--text-muted);line-height:1.6;margin-top:.25rem'>{description}</p>" if description else ""
    badge = level_badge(f["level"])
    topic_str = f"<span style='font-size:.75rem;color:var(--accent);background:var(--accent-soft);padding:2px 8px;border-radius:6px'>{topic}</span>" if topic else ""

    if f["og_image"]:
        og_img = escape(f["og_image"], quote=True)
        thumb = (
            f"<div style='width:100%;height:160px;overflow:hidden;flex-shrink:0;position:relative'>"
            f"<img src='../{og_img}' alt='' loading='lazy' style='position:absolute;inset:0;width:100%;height:100%;object-fit:cover'>"
            f"<div style='position:absolute;inset:0;background:rgba(0,0,0,.28)'></div></div>"
        )
    else:
        thumb = (
            f"<div style='width:100%;height:160px;flex-shrink:0;"
            f"background:linear-gradient(135deg,#{c1},#{c2});display:flex;align-items:center;justify-content:center'>"
            f"<span style='font-size:2.5rem'>📖</span></div>"
        )

    return f"""
<div class="card-wrap" data-title="{data_title}" data-level="{level}" data-topic="{data_topic}">
  <a class="card" href="{path}">
    {thumb}
    <div style='padding:1rem 1.25rem;display:flex;flex-direction:column;gap:.5rem'>
      <div style='display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.25rem'>
        {date_str}
        <div style='display:flex;gap:.4rem;flex-wrap:wrap'>{topic_str}{badge}</div>
      </div>
      <h3 style='font-size:1rem;font-weight:600;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden'>{title}</h3>
    </div>
  </a>
  {desc_str}
</div>"""


def build_main_index(files: list) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(files)
    cards_html = "".join(render_card(f, i) for i, f in enumerate(files))

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My English — 매일 영어 학습</title>
<meta name="description" content="부모와 아이의 짧은 대화로 매일 익히는 생활 영어">
<link rel="manifest" href="/my-english/manifest.json">
<meta name="theme-color" content="#3b82f6">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="My English">
<link rel="apple-touch-icon" href="/my-english/icons/apple-touch-icon.png">
<script>
if('serviceWorker' in navigator){{window.addEventListener('load',function(){{navigator.serviceWorker.register('/my-english/sw.js',{{updateViaCache:'none'}}).catch(function(){{}});}});}}
</script>
<style>
{SHARED_CSS}
header{{background:var(--bg-card);border-bottom:1px solid var(--border);padding:1.25rem 2rem;display:flex;align-items:center;gap:1rem}}
header h1{{font-size:1.4rem;font-weight:700;letter-spacing:-.02em}}
header h1 span{{color:var(--accent)}}
.meta{{font-size:.8rem;color:var(--text-faint);margin-left:auto}}
.container{{max-width:1100px;margin:0 auto;padding:2rem}}
.toolbar{{display:flex;align-items:center;gap:.75rem;margin-bottom:1.5rem;flex-wrap:wrap}}
.toolbar input{{padding:.45rem .9rem;border:1px solid var(--border);border-radius:var(--r-md);font-size:.875rem;background:var(--bg-card);color:var(--text);outline:none;width:220px}}
.toolbar input:focus{{border-color:var(--accent)}}
.toolbar select{{padding:.45rem .75rem;border:1px solid var(--border);border-radius:var(--r-md);font-size:.875rem;background:var(--bg-card);color:var(--text);outline:none;cursor:pointer}}
.toolbar select:focus{{border-color:var(--accent)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:1.5rem}}
.card-wrap{{display:flex;flex-direction:column;gap:.4rem}}
.card{{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--r-lg);overflow:hidden;display:flex;flex-direction:column;box-shadow:var(--sh-sm);transition:all 160ms ease}}
.card:hover{{box-shadow:var(--sh-md);border-color:var(--accent);transform:translateY(-2px)}}
.empty{{text-align:center;color:var(--text-faint);padding:4rem;font-size:1.1rem;display:none}}
footer{{text-align:center;padding:2rem;color:var(--text-faint);font-size:.8rem;border-top:1px solid var(--border);margin-top:3rem}}
@media(max-width:600px){{header{{padding:1rem}}.container{{padding:1rem}}.toolbar input{{width:100%}}.toolbar{{flex-direction:column;align-items:stretch}}}}
</style>
</head>
<body>
<header>
  <h1>My <span>English</span></h1>
  <span class="meta">{total}개 레슨 · {generated}</span>
</header>
<div class="container">
  <div class="toolbar">
    <input type="text" placeholder="검색..." oninput="applyFilter()" id="search">
    <select onchange="applyFilter()" id="levelFilter">
      <option value="">모든 레벨</option>
      <option value="beginner">Beginner</option>
      <option value="intermediate">Intermediate</option>
      <option value="advanced">Advanced</option>
    </select>
  </div>
  <div class="grid" id="grid">
    {cards_html}
  </div>
  <div class="empty" id="empty">검색 결과가 없습니다.</div>
</div>
<footer>Generated by GitHub Actions · My English Daily</footer>
<script>
function applyFilter() {{
  const q = document.getElementById('search').value.toLowerCase();
  const lv = document.getElementById('levelFilter').value;
  let visible = 0;
  document.querySelectorAll('.card-wrap').forEach(w => {{
    const matchQ = !q || w.dataset.title.includes(q) || w.textContent.toLowerCase().includes(q);
    const matchL = !lv || w.dataset.level === lv;
    const show = matchQ && matchL;
    w.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('empty').style.display = visible === 0 ? 'block' : 'none';
}}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    injected = 0
    pwa_injected = 0
    if DAILY_DIR.exists():
        for html in DAILY_DIR.glob("*.html"):
            if html.name in SKIP:
                continue
            if inject_back_button(html):
                injected += 1
            if inject_pwa_meta(html):
                pwa_injected += 1
    if injected:
        print(f"Injected back button into {injected} file(s)")
    if pwa_injected:
        print(f"Injected PWA meta into {pwa_injected} file(s)")

    files = collect_files()

    main_out = ROOT / "index.html"
    main_out.write_text(build_main_index(files), encoding="utf-8")
    print(f"Generated index.html - {len(files)} lessons")
