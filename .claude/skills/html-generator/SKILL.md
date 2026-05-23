---
name: html-generator
description: >
  Generates polished, self-contained HTML files for articles, reports, slide decks,
  diagrams, specs, code reviews, interactive editors, prototypes, and more.
  Use this skill whenever the user asks to "make an HTML file", "create an article",
  "write a report", "build a slide deck", "make a diagram", "create a prototype",
  "make a spec", "create a review document", or any similar request that would
  benefit from rich visual structure, navigation, interactivity, or hierarchy —
  even if they don't explicitly say "HTML". Also trigger when the user says
  "정리해줘", "아티클 만들어줘", "슬라이드 만들어줘", "다이어그램 그려줘",
  "명세서 만들어줘", "리포트 써줘", or similar Korean requests for structured documents.
---

# HTML Generator

Generate a polished, self-contained HTML file. Every output must work offline — no CDN, no external scripts, no image URLs.

**Arguments passed:** {{arguments}}

Interpret the arguments to pick the right sub-command and topic. If arguments are empty, ask the user what they'd like to create.

---

## Sub-commands

Pick the best match. If none fits, default to `report`.

| Sub-command | Use for | Output folder |
|---|---|---|
| `article` | Long-form educational writing | `articles/` |
| `report` | Research, status, analysis | `articles/` |
| `explain` | Code or concept explainer | `articles/` |
| `spec` | Feature specification | `specs/` |
| `plan` | Phased implementation plan | `specs/` |
| `review` | Code review document | `reviews/` |
| `pr` | PR writeup with diffs | `reviews/` |
| `explore` | Side-by-side option comparison | `explore/` |
| `slide` | Scroll-snap presentation deck | `tools/` |
| `diagram` | SVG architecture/flow diagram | `articles/` |
| `editor` | Interactive editor with copy-as-prompt | `tools/` |
| `prototype` | Drag-and-drop UI prototype | `tools/` |

---

## 시작 전 필수 확인

구현을 시작하기 전, 반드시 아래 순서를 먼저 따른다:

1. **`design-system.html`을 읽는다** — 프로젝트 루트에 해당 파일이 있으면 구현 전 반드시 읽고, 정의된 CSS 변수·컴포넌트·스타일 규칙을 우선 적용한다. 아래 Design system 블록은 해당 파일이 없을 때의 기본값이다.
2. **기존 아티클 파일을 하나 읽는다** — `articles/` 디렉터리에 파일이 있으면 하나를 골라 읽고, 실제 적용 패턴을 파악한 뒤 일관성을 유지한다.

---

## Design system

Every file must open with this exact `:root` block — no exceptions:

```css
:root {
  --color-bg:#f5f2ed; --color-bg-alt:#eceae4; --color-bg-card:#ffffff;
  --color-text:#1a1a18; --color-text-muted:#6b6a63; --color-text-faint:#a09f97;
  --color-border:#dedad2; --color-accent:#d95f2b; --color-accent-hover:#c2521f;
  --color-accent-soft:#faeee7;
  --color-green:#3a6b4a; --color-green-soft:#e6f0e9;
  --color-blue:#2d5a8e; --color-blue-soft:#e5eef7;
  --color-yellow:#8a6a00; --color-yellow-soft:#fdf5d9;
  --color-red:#b03a2e; --color-red-soft:#fdecea;
  --font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  --font-mono:"SF Mono","Fira Code",Consolas,"Liberation Mono",monospace;
  --text-xs:0.75rem; --text-sm:0.875rem; --text-base:1rem; --text-lg:1.125rem;
  --text-xl:1.25rem; --text-2xl:1.5rem; --text-3xl:1.875rem;
  --weight-medium:500; --weight-semibold:600; --weight-bold:700;
  --leading-tight:1.25; --leading-normal:1.6; --leading-loose:1.8;
  --space-1:0.25rem; --space-2:0.5rem; --space-3:0.75rem; --space-4:1rem;
  --space-5:1.25rem; --space-6:1.5rem; --space-8:2rem; --space-12:3rem;
  --radius-md:8px; --radius-lg:12px; --radius-full:9999px;
  --shadow-sm:0 1px 3px rgba(0,0,0,0.07); --shadow-md:0 4px 12px rgba(0,0,0,0.08);
}
```

Use `var(--...)` everywhere. No magic numbers, no hard-coded colors.

---

## Mandatory rules

### Layout
- **Content width: `max-width: 900px`** on `main`, `.hero-inner`, `.nav-inner` — always.
- Collapse to single column below `768px`. Hide decorative sidebars below `880px`.
- Content + sidebar: `grid-template-columns: 1fr 320px`.
- Tap targets minimum 44px. Table wrappers: `overflow-x: auto`.

### Navigation
- 3+ major sections → use tabs (`.tab-btn` / `.tab-panel`, inline JS, first tab active by default).
- Long documents → sticky section nav or sidebar TOC.
- Collapsible content → native `<details>`/`<summary>`, no custom JS needed.

### SVG diagrams
- All diagrams inline `<svg>`. Never ASCII art.
- Define arrowheads in `<defs>` with `<marker>`; use `marker-end` on paths.
- Solid lines = sync/required. Dashed (`stroke-dasharray`) = async/optional.
- SVG can't inherit CSS variables — use hex values directly in `fill`/`stroke`.

### Code blocks
- Structure: `.code-block-header` + `<pre><code>` with language label and Copy button.
- Syntax tokens: `.tok-keyword`, `.tok-string`, `.tok-comment`, `.tok-number`, `.tok-function`.

### Animations
- Hover lift: `transition: all 180ms ease` + `transform: translateY(-2px)`.
- State changes (toggles, tabs): `transition: background 140ms ease`.
- Nothing longer than 400ms.

### Semantic HTML
- `<nav>` for TOC and tabs, `<article>` for content blocks, `<aside>` for sidebars.
- `aria-label` on interactive SVG elements.

### Clipboard
Always use `navigator.clipboard` with `execCommand` fallback — see T4 in `references/implementation-templates.md`.

---

## Sub-command details

### `article` / `report` / `explain`
Include: hero section (dark gradient, title, lead sentence), sticky progress bar, numbered sections, SVG diagrams, `<meta name="description">` for index previews.

### `spec` / `plan`
Include: status badge (Draft/In Review/Approved), executive summary card, tabs for Overview/Technical/Operations. For `plan`: milestone timeline (dot + connector line, filled=done/outlined=pending), slice cards with `<details>`, rollout steps timeline.

### `review` / `pr`
Include: severity badges (Error=red, Warning=yellow, Suggestion=blue, Praise=green), before/after code panels side by side (`grid 1fr 1fr`, green border on "after"). For `pr`: sticky sidebar TOC, `<details>` per changed file, `.badge.new/.mod/.del`.

### `explore`
Include: option cards (pros=green bullets, cons=red bullets, badge row), comparison table with colored cells (green/yellow/red), recommendation section, tabs for detail views.

### `slide`
Use T1 from `references/implementation-templates.md`. Mix slide types: title, content, diagram, quote, code.

### `diagram`
Use T2 from `references/implementation-templates.md`. Add Download SVG button using T7.

### `editor`
Include: sticky toolbar, "Copy as prompt" button (clipboard API), reset button. For prompt template editors use T6. For feature-flag editors use T5 (toggle switch). For live diff: sticky 320px sidebar with color-coded diff, "Copy diff" button.

### `prototype`
Use T3 from `references/implementation-templates.md`. Populate with realistic data. Include add/delete/move actions and "Copy as JSON" export button.

---

## Implementation templates

For the following patterns, read `references/implementation-templates.md` and copy the relevant template verbatim — do not rewrite from memory:

- **T1** — CSS scroll-snap slide deck with IntersectionObserver counter
- **T2** — SVG arrowhead marker definitions (solid + dashed)
- **T3** — HTML5 drag-and-drop Kanban columns
- **T4** — Clipboard copy with execCommand fallback
- **T5** — Animated CSS toggle switch
- **T6** — contenteditable prompt editor with slot highlighting
- **T7** — SVG download button

---

## Output

Generate the complete HTML and output it in a single `\`\`\`html` code block.
Above the block, suggest a filename: `파일명: YYYY-MM-DD-slug.html`
Below the block: `브라우저에서 직접 열어 확인하세요.`

Make it genuinely polished — hierarchy obvious at a glance, real content (not Lorem ipsum), interactive features that actually work.
