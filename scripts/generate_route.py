#!/usr/bin/env python3
"""
Generate the 'THE ROUTE' timeline SVG dynamically from ImDasky's public GitHub repos.
Produces both light and dark versions in assets/ and assets/dark/.
Organized by Year + Quarter / Month to spread out repositories evenly along the timeline.
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


def generate_svg(repos, palette):
    """Build a spread-out timeline SVG string based on repo creation dates."""
    if not repos:
        return ""

    # Parse dates
    parsed_repos = []
    for r in repos:
        dt = datetime.strptime(r["created_at"][:10], "%Y-%m-%d")
        parsed_repos.append({
            "name": r["name"],
            "date": dt,
            "year": dt.year,
            "month": dt.strftime("%b"),
            "language": r.get("language") or ""
        })

    # Sort chronologically
    parsed_repos.sort(key=lambda x: x["date"])

    min_date = parsed_repos[0]["date"]
    max_date = datetime.now()

    total_days = max(1, (max_date - min_date).days)

    # Layout constants
    svg_w = 1000
    pad_l, pad_r = 60, 80
    axis_y = 120
    usable_w = svg_w - pad_l - pad_r

    c = palette  # shorthand

    lines = []
    # Height is fixed and clean
    svg_h = 320

    lines.append(f'<svg viewBox="0 0 {svg_w} {svg_h}" fill="none" '
                 f'xmlns="http://www.w3.org/2000/svg" role="img" '
                 f'aria-label="Timeline of {len(repos)} public repositories">')
    lines.append("""  <style>
    .mono { font-family: ui-monospace, "SFMono-Regular", "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; }
    .pulse { animation: pulse 2.6s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }
    @media (prefers-reduced-motion: reduce) { .pulse { animation: none; opacity: 1; } }
  </style>""")

    # Title
    lines.append(f'  <text x="{pad_l}" y="28" class="mono" '
                 f'fill="{c["muted"]}" font-size="11" letter-spacing="2">'
                 f'THE ROUTE SO FAR — SHIPPING CHRONOLOGY</text>')
    lines.append(f'  <text x="{svg_w - 30}" y="28" class="mono" '
                 f'fill="{c["dim"]}" font-size="10" text-anchor="end" letter-spacing="1">'
                 f'FIG. 03</text>')

    # Horizontal axis line
    lines.append(f'  <line x1="{pad_l}" y1="{axis_y}" x2="{pad_l + usable_w}" y2="{axis_y}" '
                 f'stroke="{c["rule"]}" stroke-width="1"/>')

    # Year markers along the axis
    min_year = min_date.year
    max_year = max_date.year

    for y in range(min_year, max_year + 1):
        year_dt = datetime(y, 1, 1)
        if year_dt < min_date:
            year_dt = min_date
        days_from_start = (year_dt - min_date).days
        x = pad_l + (days_from_start / total_days) * usable_w

        lines.append(f'  <line x1="{x}" y1="{axis_y - 6}" x2="{x}" y2="{axis_y + 6}" '
                     f'stroke="{c["rule"]}" stroke-width="1"/>')
        lines.append(f'  <text x="{x}" y="{axis_y + 22}" class="mono" fill="{c["muted"]}" '
                     f'font-size="11" font-weight="700" text-anchor="middle">{y}</text>')

    # Spread out repos alternately ABOVE and BELOW the axis line
    # To prevent text collision between nearby repos, we calculate x for each repo
    for i, item in enumerate(parsed_repos):
        days_from_start = (item["date"] - min_date).days
        x = pad_l + (days_from_start / total_days) * usable_w

        # Alternate above and below
        is_above = (i % 2 == 0)

        # Dot on line
        lines.append(f'  <circle cx="{x}" cy="{axis_y}" r="3.5" fill="{c["dot"]}"/>')

        name_display = item["name"]
        if len(name_display) > 16:
            name_display = name_display[:14] + ".."

        if is_above:
            # Stem line extending UP
            stem_y = axis_y - 25 - (i % 3) * 15
            lines.append(f'  <line x1="{x}" y1="{axis_y - 3.5}" x2="{x}" y2="{stem_y}" '
                         f'stroke="{c["rule"]}" stroke-width="0.75" stroke-dasharray="2 2"/>')
            lines.append(f'  <text x="{x}" y="{stem_y - 6}" class="mono" fill="{c["bone"]}" '
                         f'font-size="9.5" font-weight="700" text-anchor="middle">{name_display}</text>')
            lines.append(f'  <text x="{x}" y="{stem_y - 18}" class="mono" fill="{c["dim"]}" '
                         f'font-size="8.5" text-anchor="middle">{item["month"]} {item["year"]}</text>')
        else:
            # Stem line extending DOWN below year labels
            stem_y = axis_y + 45 + (i % 3) * 15
            lines.append(f'  <line x1="{x}" y1="{axis_y + 26}" x2="{x}" y2="{stem_y}" '
                         f'stroke="{c["rule"]}" stroke-width="0.75" stroke-dasharray="2 2"/>')
            lines.append(f'  <text x="{x}" y="{stem_y + 12}" class="mono" fill="{c["bone"]}" '
                         f'font-size="9.5" font-weight="700" text-anchor="middle">{name_display}</text>')
            lines.append(f'  <text x="{x}" y="{stem_y + 24}" class="mono" fill="{c["dim"]}" '
                         f'font-size="8.5" text-anchor="middle">{item["month"]} {item["year"]}</text>')

    # "NOW" marker at the end
    now_x = pad_l + usable_w
    lines.append(f'  <circle cx="{now_x}" cy="{axis_y}" r="5" fill="{c["dot"]}" class="pulse"/>')
    lines.append(f'  <text x="{now_x}" y="{axis_y - 12}" class="mono pulse" '
                 f'fill="{c["muted"]}" font-size="10" text-anchor="middle" '
                 f'font-weight="700">NOW</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    repos = fetch_repos()
    # Exclude profile repo
    repos = [r for r in repos if r["name"] != USERNAME]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(script_dir)
    assets = os.path.join(root, "assets")
    assets_dark = os.path.join(assets, "dark")
    os.makedirs(assets_dark, exist_ok=True)

    # Generate light
    svg_light = generate_svg(repos, LIGHT)
    with open(os.path.join(assets, "route.svg"), "w") as f:
        f.write(svg_light)

    # Generate dark
    svg_dark = generate_svg(repos, DARK)
    with open(os.path.join(assets_dark, "route.svg"), "w") as f:
        f.write(svg_dark)

    print(f"✓ Generated spread-out route.svg ({len(repos)} repos)")


if __name__ == "__main__":
    main()
