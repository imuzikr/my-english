#!/usr/bin/env python3
"""Render a daily parent-child English lesson text file into a standalone HTML page.

Input format is the Korean-friendly daily lesson text produced by the OpenClaw
cron job, for example:

오늘의 생활 영어
오늘의 상황: 방과 후 일정 미리 정하기

상황 1
- Parent: ... (...)
- Child: ... (...)

핵심 표현
...
"""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent.parent
DAILY_DIR = ROOT / "daily"

CSS = r"""
:root {
  --color-bg:#f5f2ed; --color-bg-alt:#eceae4; --color-bg-card:#ffffff;
  --color-bg-code:#1e1e1e;
  --color-text:#1a1a18; --color-text-muted:#6b6a63; --color-text-faint:#a09f97;
  --color-border:#dedad2; --color-border-strong:#b8b5ac;
  --color-accent:#d95f2b; --color-accent-hover:#c2521f; --color-accent-soft:#faeee7;
  --color-green:#3a6b4a; --color-green-soft:#e6f0e9;
  --color-blue:#2d5a8e; --color-blue-soft:#e5eef7;
  --color-yellow:#8a6a00; --color-yellow-soft:#fdf5d9;
  --font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  --text-xs:0.75rem; --text-sm:0.875rem; --text-base:1rem; --text-lg:1.125rem;
  --text-xl:1.25rem; --text-2xl:1.5rem; --text-3xl:1.875rem; --text-4xl:2.25rem;
  --weight-medium:500; --weight-semibold:600; --weight-bold:700;
  --leading-tight:1.25; --leading-normal:1.6;
  --space-1:0.25rem; --space-2:0.5rem; --space-3:0.75rem; --space-4:1rem;
  --space-5:1.25rem; --space-6:1.5rem; --space-8:2rem; --space-10:2.5rem;
  --space-12:3rem; --space-16:4rem;
  --radius-md:8px; --radius-lg:12px; --radius-xl:16px; --radius-full:9999px;
  --shadow-sm:0 1px 3px rgba(0,0,0,0.07),0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:0 4px 12px rgba(0,0,0,0.08),0 2px 4px rgba(0,0,0,0.04);
}
*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
html { font-size:16px; scroll-behavior:smooth; }
body { background:var(--color-bg); color:var(--color-text); font-family:var(--font-sans); font-size:var(--text-base); line-height:var(--leading-normal); -webkit-font-smoothing:antialiased; }
a { color:inherit; }
#progress { position:fixed; top:0; left:0; height:3px; background:var(--color-accent); width:0%; z-index:200; transition:width 80ms linear; }
.hero { background:linear-gradient(140deg,#2c2a26 0%,#3d3a33 100%); color:#f5f2ed; padding:var(--space-16) var(--space-6) var(--space-12); }
.hero-inner { max-width:900px; margin:0 auto; }
.hero-badge { display:inline-block; font-size:var(--text-xs); font-weight:var(--weight-semibold); text-transform:uppercase; letter-spacing:0.12em; color:var(--color-accent); background:rgba(217,95,43,0.16); padding:var(--space-1) var(--space-3); border-radius:var(--radius-full); margin-bottom:var(--space-5); }
.hero-title { font-size:var(--text-4xl); font-weight:var(--weight-bold); line-height:var(--leading-tight); letter-spacing:-0.02em; margin-bottom:var(--space-4); }
.hero-lead { font-size:var(--text-lg); color:#cfcbc2; max-width:680px; margin-bottom:var(--space-6); }
.hero-meta { display:flex; flex-wrap:wrap; gap:var(--space-2) var(--space-4); font-size:var(--text-sm); color:#a8a59d; }
.hero-meta span + span::before { content:""; display:inline-block; width:3px; height:3px; background:#6b6a63; border-radius:50%; margin:0 var(--space-4) 0 0; }
.toc { position:sticky; top:0; z-index:100; background:rgba(245,242,237,0.92); backdrop-filter:saturate(180%) blur(8px); border-bottom:1px solid var(--color-border); }
.toc-inner { max-width:900px; margin:0 auto; padding:var(--space-3) var(--space-6); display:flex; gap:var(--space-3); overflow-x:auto; }
.toc a { flex:0 0 auto; color:var(--color-text-muted); text-decoration:none; font-size:var(--text-sm); font-weight:var(--weight-medium); padding:var(--space-2) var(--space-3); border-radius:var(--radius-full); transition:background .15s,color .15s; }
.toc a:hover { color:var(--color-accent); background:var(--color-accent-soft); }
main { max-width:900px; margin:0 auto; padding:var(--space-10) var(--space-6) var(--space-16); }
section { margin-bottom:var(--space-10); }
.section-title { font-size:var(--text-2xl); font-weight:var(--weight-bold); letter-spacing:-0.01em; margin-bottom:var(--space-5); display:flex; align-items:center; gap:var(--space-3); }
.section-title::before { content:""; width:6px; height:1.35em; background:var(--color-accent); border-radius:var(--radius-full); }
.dialogue-card, .note-card { background:var(--color-bg-card); border:1px solid var(--color-border); border-radius:var(--radius-xl); padding:var(--space-6); box-shadow:var(--shadow-sm); margin-bottom:var(--space-5); }
.dialogue-card h3 { font-size:var(--text-xl); margin-bottom:var(--space-4); }
.dialogue { display:flex; flex-direction:column; gap:var(--space-4); }
.bubble-row { display:flex; }
.bubble-row.parent { justify-content:flex-start; }
.bubble-row.child { justify-content:flex-end; }
.dial-card { display:flex; align-items:center; gap:14px; max-width:min(88%,700px); background:var(--color-bg-card); border:1px solid var(--color-border); border-radius:20px; padding:13px 20px 13px 13px; box-shadow:var(--shadow-sm); transition:transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease; }
.dial-card:hover { transform:translateY(-2px); box-shadow:var(--shadow-md); border-color:var(--color-border-strong); }
.bubble-row.parent .dial-card { border-bottom-left-radius:var(--radius-md); }
.bubble-row.child .dial-card { border-bottom-right-radius:var(--radius-md); background:var(--color-accent-soft); border-color:#f4ddd0; }
.dial-icon { flex:0 0 auto; width:58px; height:58px; border-radius:15px; display:flex; align-items:center; justify-content:center; color:var(--color-blue); background:var(--color-blue-soft); }
.bubble-row.child .dial-icon { color:var(--color-accent); background:#fff7f2; }
.dial-icon svg { width:26px; height:26px; }
.dial-body { flex:1; min-width:0; }
.dial-speaker { font-size:var(--text-xs); font-weight:var(--weight-bold); text-transform:uppercase; letter-spacing:.08em; color:var(--color-text-muted); margin-bottom:var(--space-1); }
.dial-en { font-size:var(--text-lg); font-weight:var(--weight-semibold); color:var(--color-text); line-height:1.35; margin-bottom:var(--space-1); }
.dial-ko { color:var(--color-text-muted); }
.line { padding:var(--space-4); border-radius:var(--radius-lg); margin:var(--space-3) 0; border:1px solid var(--color-border); background:#fff; }
.speaker { display:inline-block; font-size:var(--text-xs); font-weight:var(--weight-bold); text-transform:uppercase; letter-spacing:.08em; padding:2px 8px; border-radius:var(--radius-full); margin-bottom:var(--space-2); }
.english { font-size:var(--text-lg); font-weight:var(--weight-semibold); margin-bottom:var(--space-1); }
.korean { color:var(--color-text-muted); }
ul { padding-left:1.25rem; }
li { margin:.45rem 0; }
.note-card { line-height:1.75; }
.note-card h3 { font-size:var(--text-xl); margin-bottom:var(--space-3); }
.raw-lines p { margin:.45rem 0; }
#back-to-index{position:fixed;bottom:1.5rem;left:1.5rem;width:44px;height:44px;background:#3b82f6;color:#fff;border-radius:9999px;display:flex;align-items:center;justify-content:center;text-decoration:none;box-shadow:0 4px 16px rgba(0,0,0,.18);transition:background .15s,transform .15s;z-index:800;}
#back-to-index:hover{background:#2563eb;transform:translateX(-2px);}
footer { color:var(--color-text-faint); text-align:center; padding:var(--space-8); border-top:1px solid var(--color-border); }
@media(max-width:640px){ .hero{padding:var(--space-12) var(--space-5) var(--space-8)} .hero-title{font-size:var(--text-3xl)} main{padding:var(--space-8) var(--space-4)} .dialogue-card,.note-card{padding:var(--space-5)} .dial-card{max-width:94%; gap:12px; padding:10px 14px 10px 10px; border-radius:16px;} .dial-icon{width:48px;height:48px;border-radius:12px;} .dial-icon svg{width:22px;height:22px;} #back-to-index{bottom:1rem;left:1rem;} }
"""

PWA_HEAD = """<link rel=\"manifest\" href=\"/my-english/manifest.json\">
<meta name=\"theme-color\" content=\"#3b82f6\">
<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">
<meta name=\"mobile-web-app-capable\" content=\"yes\">
<meta name=\"apple-mobile-web-app-status-bar-style\" content=\"default\">
<meta name=\"apple-mobile-web-app-title\" content=\"My English\">
<link rel=\"apple-touch-icon\" href=\"/my-english/icons/apple-touch-icon.png\">
<script>
(function(){
  if(!('serviceWorker' in navigator)) return;
  var refreshing = false;
  navigator.serviceWorker.addEventListener('controllerchange', function(){
    if(refreshing) return;
    refreshing = true;
    window.location.reload();
  });
  window.addEventListener('load', function(){
    navigator.serviceWorker.register('/my-english/sw.js', { updateViaCache: 'none' })
      .then(function(reg){
        if(reg.waiting) reg.waiting.postMessage({ type: 'SKIP_WAITING' });
        reg.addEventListener('updatefound', function(){
          var worker = reg.installing;
          if(!worker) return;
          worker.addEventListener('statechange', function(){
            if(worker.state === 'installed' && navigator.serviceWorker.controller){
              worker.postMessage({ type: 'SKIP_WAITING' });
            }
          });
        });
      })
      .catch(function(){});
  });
})();
</script>
"""


def split_translation(text: str) -> tuple[str, str]:
    text = text.strip()
    m = re.match(r"^(.*?)\s*[（(](.+?)[）)]\s*$", text)
    if not m:
        return text, ""
    return m.group(1).strip(), m.group(2).strip()


def extract_title(raw: str, fallback: str) -> str:
    m = re.search(r"^오늘의 상황\s*[:：]\s*(.+)$", raw, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def parse_sections(raw: str) -> tuple[list[dict], dict[str, list[str]]]:
    lines = [line.rstrip() for line in raw.splitlines()]
    dialogues: list[dict] = []
    notes: dict[str, list[str]] = {"핵심 표현": [], "바꿔 말하기": [], "짧은 연습 포인트": []}
    current_dialogue: dict | None = None
    current_note: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped == "오늘의 생활 영어" or stripped.startswith("오늘의 상황"):
            continue
        if re.match(r"^상황\s*\d+", stripped):
            current_dialogue = {"title": stripped, "lines": []}
            dialogues.append(current_dialogue)
            current_note = None
            continue
        if stripped in notes:
            current_note = stripped
            current_dialogue = None
            continue

        speaker_match = re.match(r"^-\s*(Parent|Child)\s*[:：]\s*(.+)$", stripped, re.IGNORECASE)
        if speaker_match and current_dialogue is not None:
            speaker = speaker_match.group(1).capitalize()
            english, korean = split_translation(speaker_match.group(2))
            current_dialogue["lines"].append({"speaker": speaker, "english": english, "korean": korean})
            continue

        if current_note:
            notes[current_note].append(stripped.lstrip("- ").strip())
        elif current_dialogue is not None:
            current_dialogue["lines"].append({"speaker": "", "english": stripped.lstrip("- "), "korean": ""})

    return dialogues, notes


def render_note_items(items: list[str]) -> str:
    if not items:
        return "<p>오늘 대화에서 자연스럽게 한 번씩 소리 내어 말해 보세요.</p>"
    lis = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f"<ul>{lis}</ul>"


ICONS = {
    "bag": '<path d="M6 7h12l1 15H5L6 7z"/><path d="M9 7a3 3 0 0 1 6 0"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    "paper": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8M8 17h5"/>',
    "pen": '<path d="m18 2 4 4L8 20l-6 2 2-6L18 2z"/><path d="m14 6 4 4"/>',
    "shirt": '<path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46 2 9l4 1.5V22h12V10.5L22 9l-1.62-5.54z"/>',
    "water": '<path d="M12 2C8 7 6 10.5 6 14a6 6 0 0 0 12 0c0-3.5-2-7-6-12z"/><path d="M9 15a3 3 0 0 0 3 3"/>',
    "snack": '<path d="M3 11h18"/><path d="M5 11l2 10h10l2-10"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "wash": '<path d="M4 12h16"/><path d="M6 12v5a4 4 0 0 0 4 4h4a4 4 0 0 0 4-4v-5"/><path d="M8 8c0-2 1-4 4-4s4 2 4 4"/><path d="M9 15h.01M12 16h.01M15 15h.01"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>',
    "walk": '<path d="M13 4a2 2 0 1 0-2 2 2 2 0 0 0 2-2z"/><path d="M8 22l2-7-2-3 3-4 3 2 2 4"/><path d="M14 22l-2-5 2-5"/>',
    "home": '<path d="M3 12l9-9 9 9"/><path d="M9 21V12h6v9"/>',
    "read": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M8 7h8M8 11h8"/>',
    "homework": '<path d="M4 4h16v16H4z"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    "timer": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2"/><path d="M9 2h6"/>',
    "soccer": '<circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="M14.83 9.17 19.07 4.93"/><path d="m4.93 19.07 4.24-4.24"/><path d="M14.83 14.83l4.24 4.24"/><circle cx="12" cy="12" r="2.5" fill="currentColor" stroke="none"/>',
    "pickup": '<path d="M19 17H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h11l4 4v5a2 2 0 0 1-1 1.73"/><circle cx="7.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
    "gate": '<path d="M4 21V9l8-5 8 5v12"/><path d="M9 21v-8h6v8"/><path d="M12 13v8"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "rest": '<path d="M4 13h16"/><path d="M5 13v6M19 13v6"/><path d="M8 13V9a4 4 0 0 1 8 0v4"/>',
    "parent": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "child": '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.4 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/>',
}

ICON_RULES = [
    ("soccer", ("soccer", "practice")),
    ("pickup", ("pick you up", "five thirty")),
    ("gate", ("front gate",)),
    ("wash", ("wash", "hands")),
    ("snack", ("snack", "watermelon", "sandwich", "cut a few pieces")),
    ("sun", ("hot", "cold", "cool down", "cool off")),
    ("water", ("water bottle", "drink some water", "sweaty")),
    ("rest", ("break", "rest", "after snack")),
    ("bag", ("bag", "pack", "put them in")),
    ("book", ("math book", "planner")),
    ("paper", ("paper", "permission slip")),
    ("pen", ("signature", "sign it")),
    ("shirt", ("t-shirt", "shirt", "pe class", "sticky")),
    ("walk", ("walking", "walk")),
    ("read", ("read", "sofa")),
    ("homework", ("homework", "list")),
    ("timer", ("timer", "ten minutes", "10 minutes")),
    ("home", ("home",)),
    ("check", ("done", "deal", "sounds good", "okay")),
]


def dialogue_icon(speaker: str, english: str, context: str = "") -> str:
    """Pick a small inline icon from the dialogue context, with speaker fallback."""
    haystack = f"{english} {context}".lower()
    icon_name = ""
    for candidate, keywords in ICON_RULES:
        if any(keyword in haystack for keyword in keywords):
            icon_name = candidate
            break
    if not icon_name:
        icon_name = "child" if speaker.lower() == "child" else "parent"

    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f'{ICONS[icon_name]}'
        '</svg>'
    )


def render(raw: str, lesson_date: str, title: str) -> str:
    dialogues, notes = parse_sections(raw)
    page_title = f"{lesson_date} · 오늘의 생활 영어 — {title}"
    description = f"부모와 아이의 짧은 대화 3가지 — {title}. 핵심 표현·바꿔 말하기·연습 포인트까지."
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    dialogue_html = []
    for idx, dialogue in enumerate(dialogues, start=1):
        line_html = []
        for item in dialogue["lines"]:
            cls = item["speaker"].lower()
            speaker = escape(item["speaker"] or "Line")
            english = escape(item["english"])
            korean = escape(item["korean"])
            if cls in {"parent", "child"}:
                line_html.append(
                    f'<div class="bubble-row {cls}"><div class="dial-card">'
                    f'<div class="dial-icon">{dialogue_icon(item["speaker"], item["english"], dialogue["title"])}</div>'
                    f'<div class="dial-body"><div class="dial-speaker">{speaker}</div>'
                    f'<div class="dial-en">{english}</div>'
                    f'{f"<div class=\"dial-ko\">{korean}</div>" if korean else ""}'
                    f'</div></div></div>'
                )
            else:
                line_html.append(
                    f'<div class="line"><span class="speaker">{speaker}</span>'
                    f'<p class="english">{english}</p>'
                    f'{f"<p class=\"korean\">{korean}</p>" if korean else ""}</div>'
                )
        dialogue_html.append(
            f'<section id="situation-{idx}"><h2 class="section-title">{escape(dialogue["title"])}</h2>'
            f'<div class="dialogue-card"><div class="dialogue">{"".join(line_html)}</div></div></section>'
        )

    if not dialogue_html:
        paragraphs = "".join(f"<p>{escape(line)}</p>" for line in raw.splitlines() if line.strip())
        dialogue_html.append(f'<section><div class="note-card raw-lines">{paragraphs}</div></section>')

    notes_html = "".join(
        f'<section id="note-{idx}"><h2 class="section-title">{escape(name)}</h2>'
        f'<div class="note-card">{render_note_items(items)}</div></section>'
        for idx, (name, items) in enumerate(notes.items(), start=1)
    )

    toc_links = "".join(f'<a href="#situation-{i}">상황 {i}</a>' for i in range(1, len(dialogues) + 1))
    toc_links += '<a href="#note-1">핵심 표현</a><a href="#note-2">바꿔 말하기</a><a href="#note-3">연습 포인트</a>'

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(page_title)}</title>
<meta name="description" content="{escape(description, quote=True)}">
<meta name="english-level" content="beginner">
<meta name="english-topic" content="Daily Conversation">
{PWA_HEAD}<style>{CSS}</style>
</head>
<body>
<div id="progress"></div>
<header class="hero">
  <div class="hero-inner">
    <span class="hero-badge">Daily Conversation</span>
    <h1 class="hero-title">{escape(page_title)}</h1>
    <p class="hero-lead">{escape(description)}</p>
    <div class="hero-meta"><span>{escape(lesson_date)}</span><span>Beginner</span><span>Parent & Child</span><span>Generated {generated}</span></div>
  </div>
</header>
<nav class="toc"><div class="toc-inner">{toc_links}</div></nav>
<main>
  {''.join(dialogue_html)}
  {notes_html}
</main>
<a id="back-to-index" href="../index.html" aria-label="목록으로" title="목록으로">
<svg viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18"><path d="M8.5 15L3 10l5.5-5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M3 10h14" stroke="white" stroke-width="2" stroke-linecap="round"/></svg></a>
<footer>My English Daily · Parent-child practical English</footer>
<script>
window.addEventListener('scroll',function(){{
  const h=document.documentElement;
  const p=h.scrollTop/(h.scrollHeight-h.clientHeight)*100;
  document.getElementById('progress').style.width=(isFinite(p)?p:0)+'%';
}});
</script>
</body>
</html>
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to lesson text file")
    parser.add_argument("--date", default=date.today().isoformat(), help="Lesson date, YYYY-MM-DD")
    parser.add_argument("--title", default="", help="Optional situation title override")
    parser.add_argument("--output", default="", help="Optional output HTML path")
    args = parser.parse_args()

    raw = Path(args.input).read_text(encoding="utf-8").strip()
    title = args.title.strip() or extract_title(raw, "오늘의 생활 영어")
    out = Path(args.output) if args.output else DAILY_DIR / f"{args.date}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(raw, args.date, title), encoding="utf-8")
    print(f"Rendered {out}")


if __name__ == "__main__":
    main()
