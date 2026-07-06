#!/usr/bin/env python3
"""
generate_builds.py
------------------
Fetches pinned repositories from GitHub's GraphQL API for Redooyyy
and renders a beautiful animated SVG card grid into assets/builds.svg.

Usage:
  GITHUB_TOKEN=<your_token> python scripts/generate_builds.py

The GITHUB_TOKEN only needs public read access (default Actions token works).
Pin repos on your GitHub profile to control which projects appear here.
"""

import os
import sys
import math
import textwrap
import requests

# ─────────────────────────────────────────────
USERNAME    = "Redooyyy"
OUTPUT_PATH = "assets/builds.svg"
MAX_REPOS   = 6   # GitHub allows up to 6 pinned repos
# ─────────────────────────────────────────────

# Language name → pill accent color (Monochrome / Slate / Subtle Blue)
LANG_COLORS = {
    "default":    "#64748B",
    "Java":       "#64748B",
    "CSS":        "#64748B",
    "Lua":        "#64748B",
    "Shell":      "#64748B",
    "TypeScript": "#64748B",
    "Dart":       "#64748B",
    "Flutter":    "#64748B",
    "Python":     "#64748B",
    "C":          "#64748B",
    "C++":        "#64748B",
}

GRAPHQL_QUERY = """
{
  user(login: "%s") {
    pinnedItems(first: %d, types: REPOSITORY) {
      nodes {
        ... on Repository {
          name
          description
          url
          stargazerCount
          languages(first: 3, orderBy: {field: SIZE, direction: DESC}) {
            nodes { name }
          }
        }
      }
    }
  }
}
""" % (USERNAME, MAX_REPOS)


def fetch_pinned_repos(token: str) -> list:
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": GRAPHQL_QUERY},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        print("GraphQL errors:", data["errors"], file=sys.stderr)
        sys.exit(1)
    return data["data"]["user"]["pinnedItems"]["nodes"]


def wrap_desc(text: str, width: int = 46) -> list[str]:
    if not text:
        return ["No description provided."]
    return textwrap.wrap(text, width)[:3]


def lang_color(name: str) -> str:
    return LANG_COLORS.get(name, LANG_COLORS["default"])


def pill(x: float, y: int, text: str, color: str) -> tuple[str, float]:
    """Return (svg_string, consumed_width) for one language pill."""
    w = len(text) * 7.0 + 18
    svg = (
        f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="20" rx="5" '
        f'fill="{color}" fill-opacity="0.15" '
        f'stroke="{color}" stroke-width="0.7" stroke-opacity="0.5"/>'
        f'<text x="{x + w/2:.1f}" y="{y + 14}" '
        f'font-family="\'JetBrains Mono\',monospace" font-size="11" '
        f'fill="{color}" text-anchor="middle">{text}</text>'
    )
    return svg, w + 6


def build_defs() -> str:
    return """<defs>
  <!-- Card border gradients (Monochrome/Slate) -->
  <linearGradient id="b0" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%"   stop-color="#64748B" stop-opacity="0.6"/>
    <stop offset="100%" stop-color="#334155" stop-opacity="0.6"/>
  </linearGradient>
  <linearGradient id="b1" x1="100%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%"   stop-color="#475569" stop-opacity="0.6"/>
    <stop offset="100%" stop-color="#1E293B" stop-opacity="0.6"/>
  </linearGradient>
  <linearGradient id="b2" x1="0%" y1="100%" x2="100%" y2="0%">
    <stop offset="0%"   stop-color="#334155" stop-opacity="0.6"/>
    <stop offset="100%" stop-color="#475569" stop-opacity="0.6"/>
  </linearGradient>
  <!-- Name gradients (Subtle blue & white) -->
  <linearGradient id="n0" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%"   stop-color="#E2E8F0"/>
    <stop offset="100%" stop-color="#94A3B8"/>
  </linearGradient>
  <linearGradient id="n1" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%"   stop-color="#F8FAFC"/>
    <stop offset="100%" stop-color="#E2E8F0"/>
  </linearGradient>
  <linearGradient id="n2" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%"   stop-color="#E2E8F0"/>
    <stop offset="100%" stop-color="#CBD5E1"/>
  </linearGradient>
  <!-- Card inner glow (Slate) -->
  <radialGradient id="g0" cx="20%" cy="20%" r="70%">
    <stop offset="0%"   stop-color="#64748B" stop-opacity="0.05"/>
    <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="g1" cx="80%" cy="20%" r="70%">
    <stop offset="0%"   stop-color="#475569" stop-opacity="0.05"/>
    <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="g2" cx="20%" cy="80%" r="70%">
    <stop offset="0%"   stop-color="#334155" stop-opacity="0.05"/>
    <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
  </radialGradient>
  <filter id="sg">
    <feGaussianBlur stdDeviation="1.5" result="b"/>
    <feComposite in="SourceGraphic" in2="b" operator="over"/>
  </filter>
  <style>
    @keyframes p0{0%,100%{opacity:.55}50%{opacity:1}}
    @keyframes p1{0%,100%{opacity:.45}50%{opacity:.85}}
    @keyframes p2{0%,100%{opacity:.5}50%{opacity:.9}}
    @keyframes sg{0%,100%{opacity:.5}50%{opacity:.8}}
    .p0{animation:p0 4s ease-in-out infinite}
    .p1{animation:p1 5s ease-in-out infinite}
    .p2{animation:p2 6s ease-in-out infinite}
    .sg{animation:sg 2.5s ease-in-out infinite}
  </style>
</defs>"""


def render_card(repo: dict, index: int, x: float, y: float, w: float, h: float) -> str:
    i = index % 3
    name  = repo["name"]
    desc  = repo.get("description") or ""
    stars = repo.get("stargazerCount", 0)
    langs = [n["name"] for n in (repo.get("languages") or {}).get("nodes", [])]

    # Truncate long names
    display_name = name if len(name) <= 24 else name[:23] + "…"

    lines = []

    # Base card
    lines.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="13" '
        f'fill="#0d1117" fill-opacity="0.65"/>'
    )
    lines.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="13" '
        f'fill="url(#g{i})"/>'
    )
    lines.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="13" '
        f'fill="none" stroke="url(#b{i})" stroke-width="1.4" '
        f'class="p{i}" filter="url(#sg)"/>'
    )

    # Subtle header separator line
    lines.append(
        f'<line x1="{x:.1f}" y1="{y+30:.1f}" x2="{x+w:.1f}" y2="{y+30:.1f}" '
        f'stroke="#64748B" stroke-width="0.5" opacity="0.3"/>'
    )

    # Project name
    lines.append(
        f'<text x="{x+18:.1f}" y="{y+23:.1f}" '
        f'font-family="\'JetBrains Mono\',\'Courier New\',monospace" '
        f'font-size="14" font-weight="700" fill="url(#n{i})" filter="url(#sg)">'
        f'{display_name}</text>'
    )

    # Stars
    if stars > 0:
        lines.append(
            f'<text x="{x + w - 46:.1f}" y="{y+23:.1f}" '
            f'font-family="\'JetBrains Mono\',monospace" font-size="11" '
            f'fill="#F59E0B" class="sg">* {stars}</text>'
        )

    # Description lines
    desc_lines = wrap_desc(desc)
    for li, line in enumerate(desc_lines):
        dy = y + 52 + li * 17
        color = "#94A3B8" if li < 2 else "#64748B"
        lines.append(
            f'<text x="{x+18:.1f}" y="{dy:.1f}" '
            f'font-family="\'Segoe UI\',Arial,sans-serif" font-size="12" '
            f'fill="{color}">{line}</text>'
        )

    # Language pills
    px = x + 18
    py = int(y + h - 32)
    for lang in langs[:4]:
        svg_pill, pw = pill(px, py, lang, lang_color(lang))
        lines.append(svg_pill)
        px += pw

    return "\n".join(lines)


def generate_svg(repos: list) -> str:
    SVG_W   = 900
    CARD_H  = 168
    CARD_GAP = 10
    PAD     = 8
    COLS    = 2
    CARD_W  = (SVG_W - PAD * (COLS + 1)) / COLS   # ~440

    rows   = math.ceil(len(repos) / COLS)
    SVG_H  = PAD + rows * (CARD_H + CARD_GAP) - CARD_GAP + PAD

    cards = []
    for idx, repo in enumerate(repos):
        col = idx % COLS
        row = idx // COLS
        x   = PAD + col * (CARD_W + PAD)
        y   = PAD + row * (CARD_H + CARD_GAP)
        cards.append(render_card(repo, idx, x, y, CARD_W, CARD_H))

    defs = build_defs()
    body = "\n\n".join(cards)

    return (
        f'<svg width="{SVG_W}" height="{int(SVG_H)}" '
        f'viewBox="0 0 {SVG_W} {int(SVG_H)}" '
        f'xmlns="http://www.w3.org/2000/svg">\n'
        f'{defs}\n\n'
        f'{body}\n'
        f'</svg>\n'
    )


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: set the GITHUB_TOKEN environment variable.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching pinned repos for @{USERNAME} ...")
    repos = fetch_pinned_repos(token)

    if not repos:
        print(
            "No pinned repos found.\n"
            "Go to github.com/Redooyyy → 'Customize your pins' and pick up to 6 repos.",
            file=sys.stderr,
        )
        sys.exit(0)

    print(f"Found {len(repos)} pinned repo(s): {[r['name'] for r in repos]}")

    svg = generate_svg(repos)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"SVG written to {OUTPUT_PATH}  ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
