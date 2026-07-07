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
  <!-- Card border gradients (Soft Glow - Brightened) -->
  <linearGradient id="b0" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%"   stop-color="#38BDF8" stop-opacity="0.8"/>
    <stop offset="100%" stop-color="#334155" stop-opacity="0.5"/>
  </linearGradient>
  <linearGradient id="b1" x1="100%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%"   stop-color="#818CF8" stop-opacity="0.8"/>
    <stop offset="100%" stop-color="#1E293B" stop-opacity="0.5"/>
  </linearGradient>
  <linearGradient id="b2" x1="0%" y1="100%" x2="100%" y2="0%">
    <stop offset="0%"   stop-color="#2DD4BF" stop-opacity="0.8"/>
    <stop offset="100%" stop-color="#475569" stop-opacity="0.5"/>
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
  <!-- Card inner glow (Soft Blue) -->
  <radialGradient id="g0" cx="20%" cy="20%" r="70%">
    <stop offset="0%"   stop-color="#38BDF8" stop-opacity="0.12"/>
    <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="g1" cx="80%" cy="20%" r="70%">
    <stop offset="0%"   stop-color="#818CF8" stop-opacity="0.12"/>
    <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="g2" cx="20%" cy="80%" r="70%">
    <stop offset="0%"   stop-color="#2DD4BF" stop-opacity="0.12"/>
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


def generate_individual_svgs(repos: list):
    import glob
    SVG_W = 440
    CARD_H = 168
    defs = build_defs()
    
    # Clean up old SVGs if any
    for old in glob.glob(os.path.join("assets", "build-*.svg")):
        os.remove(old)
        
    generated = []
    for idx, repo in enumerate(repos):
        svg_content = (
            f'<svg width="{SVG_W}" height="{CARD_H}" '
            f'viewBox="0 0 {SVG_W} {CARD_H}" '
            f'xmlns="http://www.w3.org/2000/svg">\n'
            f'{defs}\n\n'
            f'{render_card(repo, idx, 0, 0, SVG_W, CARD_H)}\n'
            f'</svg>\n'
        )
        path = os.path.join("assets", f"build-{idx}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        generated.append({
            "url": repo.get("url", ""),
            "path": f"assets/build-{idx}.svg"
        })
    return generated


def update_readme(generated: list):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return
        
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    start_marker = "<!-- BUILDS START -->"
    end_marker = "<!-- BUILDS END -->"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("Builds markers not found in README.md")
        return
        
    new_section = [start_marker, '<div align="center">']
    for idx, item in enumerate(generated):
        link = f'<a href="{item["url"]}"><img src="{item["path"]}" width="400" alt="Build {idx+1}"/></a>'
        new_section.append(link)
        if idx % 2 == 1:
            new_section.append('</div>\n<div align="center">')
        else:
            new_section.append('&nbsp;')
            
    # Clean up trailing div stuff if odd number of items
    if len(generated) % 2 != 0:
        new_section.append('</div>')
    else:
        # If even, the last thing added was the opening of a new div, so we pop it
        new_section.pop()
        new_section.append('</div>')
        
    new_section.append(end_marker)
    
    new_content = content[:start_idx] + "\n".join(new_section) + content[end_idx + len(end_marker):]
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    import glob
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

    os.makedirs("assets", exist_ok=True)
    generated = generate_individual_svgs(repos)
    update_readme(generated)

    print(f"Generated {len(generated)} SVGs and updated README.md")


if __name__ == "__main__":
    main()
