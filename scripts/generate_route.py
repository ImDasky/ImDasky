#!/usr/bin/env python3
"""
Generate the 'THE ROUTE' timeline SVG dynamically from ImDasky's public GitHub repos.
Produces both light and dark versions in assets/ and assets/dark/.
"""

import json
import os
import urllib.request
from collections import defaultdict
from datetime import datetime

USERNAME = "ImDasky"
API_URL = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=created&direction=asc"

# ── Color palettes ──────────────────────────────────────────────────────────
LIGHT = {
    "bone": "#333333", "muted": "#888888", "dim": "#AAAAAA",
    "rule": "#C0C0C0", "accent": "#555555", "dot": "#555555",
    "ring": "#CCCCCC",
}
DARK = {
    "bone": "#DDDDDD", "muted": "#777777", "dim": "#666666",
    "rule": "#444444", "accent": "#AAAAAA", "dot": "#AAAAAA",
    "ring": "#555555",
}


def fetch_repos():
    """Fetch public repos from GitHub API."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(API_URL, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def group_by_year(repos):
    """Group repos by creation year, return sorted dict."""
    by_year = defaultdict(list)
    for r in repos:
        year = int(r["created_at"][:4])
        lang = r.get("language") or ""
        by_year[year].append({"name": r["name"], "language": lang})
    return dict(sorted(by_year.items()))


def generate_svg(years_data, palette, total_repos):
    """Build the timeline SVG string."""
    year_list = list(years_data.keys())
    if not year_list:
        return ""

    min_year = year_list[0]
    max_year = datetime.now().year

    # Layout constants
    svg_w = 1200
    pad_l, pad_r = 80, 140
    axis_y = 125
    usable_w = svg_w - pad_l - pad_r
    num_years = max_year - min_year
    if num_years == 0:
        num_years = 1
    step = usable_w / num_years

    # Calculate height based on max annotations
    max_items = max(len(v) for v in years_data.values()) if years_data else 1
    svg_h = max(250, 170 + max_items * 18)

    c = palette  # shorthand

    lines = []
    lines.append(f'<svg viewBox="0 0 {svg_w} {svg_h}" fill="none" '
                 f'xmlns="http://www.w3.org/2000/svg" role="img" '
                 f'aria-label="Timeline of {total_repos} public repositories">')
    lines.append("""  <style>
    .mono { font-family: ui-monospace, "SFMono-Regular", "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; }
    .axis { stroke-dasharray: 1110; stroke-dashoffset: 1110; animation: draw 2.4s cubic-bezier(.6,0,.2,1) forwards; }
    @keyframes draw { to { stroke-dashoffset: 0; } }
    .m { opacity: 0; animation: rise .7s cubic-bezier(.2,.7,.2,1) forwards; }
    @keyframes rise { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
    .pulse { animation: pulse 2.6s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }
    @media (prefers-reduced-motion: reduce) { .axis,.m,.pulse { animation: none; opacity: 1; } }
  </style>""")

    # Title
    lines.append(f'  <text x="{pad_l}" y="28" class="mono m" style="animation-delay:.1s" '
                 f'fill="{c["muted"]}" font-size="11" letter-spacing="2">'
                 f'THE ROUTE SO FAR</text>')
    lines.append(f'  <text x="{svg_w - 50}" y="28" class="mono m" style="animation-delay:.1s" '
                 f'fill="{c["dim"]}" font-size="10" text-anchor="end" letter-spacing="1">'
                 f'FIG. 02</text>')

    # Horizontal axis line
    now_x = pad_l + usable_w + 40
    lines.append(f'  <line x1="{pad_l}" y1="{axis_y}" x2="{now_x}" y2="{axis_y}" '
                 f'class="axis" stroke="{c["rule"]}" stroke-width="1"/>')

    # Year markers and repo annotations
    delay_idx = 1
    for year in range(min_year, max_year + 1):
        x = pad_l + (year - min_year) * step
        delay = 0.3 + delay_idx * 0.3
        delay_idx += 1

        # Year label below axis
        lines.append(f'  <text x="{x}" y="{axis_y + 24}" class="mono m" '
                     f'style="animation-delay:{delay}s" fill="{c["muted"]}" '
                     f'font-size="12" text-anchor="middle" font-weight="700">{year}</text>')

        if year in years_data:
            repos = years_data[year]
            # Tick mark
            lines.append(f'  <line x1="{x}" y1="{axis_y - 8}" x2="{x}" y2="{axis_y + 8}" '
                         f'stroke="{c["rule"]}" stroke-width="1"/>')
            # Dot on axis
            lines.append(f'  <circle cx="{x}" cy="{axis_y}" r="4" fill="{c["dot"]}" '
                         f'class="m" style="animation-delay:{delay}s"/>')

            # Repo count badge above
            count = len(repos)
            lines.append(f'  <text x="{x}" y="{axis_y - 20}" class="mono m" '
                         f'style="animation-delay:{delay}s" fill="{c["accent"]}" '
                         f'font-size="10" text-anchor="middle" letter-spacing="1">'
                         f'{count} repo{"s" if count != 1 else ""}</text>')

            # Repo names below year label
            for i, repo in enumerate(repos[:5]):  # max 5 per year to avoid overflow
                ry = axis_y + 42 + i * 16
                name_display = repo["name"]
                if len(name_display) > 18:
                    name_display = name_display[:16] + ".."
                lines.append(f'  <text x="{x}" y="{ry}" class="mono m" '
                             f'style="animation-delay:{delay + 0.05 * i}s" '
                             f'fill="{c["dim"]}" font-size="9" text-anchor="middle" '
                             f'letter-spacing="0.5">{name_display}</text>')
            if len(repos) > 5:
                ry = axis_y + 42 + 5 * 16
                lines.append(f'  <text x="{x}" y="{ry}" class="mono m" '
                             f'style="animation-delay:{delay + 0.3}s" '
                             f'fill="{c["dim"]}" font-size="9" text-anchor="middle">'
                             f'+{len(repos) - 5} more</text>')
        else:
            # Empty year — small tick
            lines.append(f'  <line x1="{x}" y1="{axis_y - 4}" x2="{x}" y2="{axis_y + 4}" '
                         f'stroke="{c["rule"]}" stroke-width="0.5"/>')

    # "NOW" pulsing dot at the end
    lines.append(f'  <circle cx="{now_x}" cy="{axis_y}" r="5" fill="{c["dot"]}" class="pulse"/>')
    lines.append(f'  <circle cx="{now_x}" cy="{axis_y}" r="5" fill="none" '
                 f'stroke="{c["ring"]}" stroke-width="1" opacity="0.5" class="pulse"/>')
    lines.append(f'  <text x="{now_x}" y="{axis_y + 24}" class="mono m pulse" '
                 f'fill="{c["muted"]}" font-size="11" text-anchor="middle" '
                 f'font-weight="700">NOW</text>')
    lines.append(f'  <text x="{now_x}" y="{axis_y - 16}" class="mono m" '
                 f'style="animation-delay:2.5s" fill="{c["accent"]}" font-size="10" '
                 f'text-anchor="middle">{total_repos} repos</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    repos = fetch_repos()
    # Exclude the profile repo itself
    repos = [r for r in repos if r["name"] != USERNAME]
    total = len(repos)
    years_data = group_by_year(repos)

    # Determine output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(script_dir)
    assets = os.path.join(root, "assets")
    assets_dark = os.path.join(assets, "dark")
    os.makedirs(assets_dark, exist_ok=True)

    # Generate light
    svg_light = generate_svg(years_data, LIGHT, total)
    with open(os.path.join(assets, "route.svg"), "w") as f:
        f.write(svg_light)

    # Generate dark
    svg_dark = generate_svg(years_data, DARK, total)
    with open(os.path.join(assets_dark, "route.svg"), "w") as f:
        f.write(svg_dark)

    print(f"✓ Generated route.svg ({total} repos across {len(years_data)} years)")


if __name__ == "__main__":
    main()
