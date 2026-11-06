"""Render a Top Languages card (SVG) from the GitHub API, so the README does not depend on a shared public service.

Sums the language bytes of the user's own public repositories (forks and archived repos left out) and draws the
top N as one stacked bar with a legend. Usage: GH_TOKEN=... python top_langs.py <user> <out.svg> [count]
"""
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "C++": "#f34b7d", "C": "#555555",
    "Cuda": "#3A4E3A", "C#": "#178600", "HTML": "#e34c26", "CSS": "#663399", "Shell": "#89e051",
    "PowerShell": "#012456", "Batchfile": "#C1F12E", "CMake": "#DA3434", "Jupyter Notebook": "#DA5B0B",
    "Go": "#00ADD8", "Rust": "#dea584", "Java": "#b07219", "Kotlin": "#A97BFF", "Dart": "#00B4AB",
    "Vue": "#41b883", "Svelte": "#ff3e00", "SCSS": "#c6538c", "Dockerfile": "#384d54", "Lua": "#000080",
    "GLSL": "#5686a5", "HLSL": "#aace60", "ShaderLab": "#222c37", "Metal": "#8f14e9", "TeX": "#3D6117",
    "Assembly": "#6E4C13", "Makefile": "#427819", "Objective-C": "#438eff", "PHP": "#4F5D95", "Ruby": "#701516",
}
BG, TITLE, TEXT = "#1c1917", "#0891b2", "#ffffff"


def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "top-langs-card",
        **({"Authorization": "Bearer " + os.environ["GH_TOKEN"]} if os.environ.get("GH_TOKEN") else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def totals(user):
    langs, page = {}, 1
    while True:
        repos = api(f"/users/{user}/repos?type=owner&per_page=100&page={page}")
        for repo in repos:
            if repo["fork"] or repo["archived"] or repo["private"]:
                continue
            for name, size in api(f"/repos/{user}/{repo['name']}/languages").items():
                langs[name] = langs.get(name, 0) + size
        if len(repos) < 100:
            return langs
        page += 1


def render(langs, count):
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:count]
    whole = sum(v for _, v in top) or 1
    width, pad, bar_y, bar_w = 350, 25, 55, 300
    rows = (len(top) + 1) // 2
    height = bar_y + 30 + rows * 25 + 10
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
             f'role="img" aria-label="Top Languages">',
             f'<rect width="{width}" height="{height}" rx="4.5" fill="{BG}"/>',
             f'<text x="{pad}" y="35" fill="{TITLE}" font-family="Segoe UI,Ubuntu,sans-serif" font-size="18" '
             f'font-weight="600">Top Languages</text>',
             f'<clipPath id="bar"><rect x="{pad}" y="{bar_y}" width="{bar_w}" height="8" rx="5"/></clipPath>',
             '<g clip-path="url(#bar)">']
    x = float(pad)
    for name, size in top:
        w = bar_w * size / whole
        parts.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{w + 0.5:.2f}" height="8" fill="{COLORS.get(name, "#858585")}"/>')
        x += w
    parts.append("</g>")
    for i, (name, size) in enumerate(top):
        cx = pad + (i % 2) * 150
        cy = bar_y + 35 + (i // 2) * 25
        parts.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{COLORS.get(name, "#858585")}"/>')
        parts.append(f'<text x="{cx + 15}" y="{cy}" fill="{TEXT}" font-family="Segoe UI,Ubuntu,sans-serif" '
                     f'font-size="11">{escape(name)} {100 * size / whole:.2f}%</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    user, out = sys.argv[1], sys.argv[2]
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    langs = totals(user)
    if not langs:
        sys.exit("no language data; the card is left as it was")
    svg = render(langs, count)  # fetch and render first, so a failed API call never leaves an empty card
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
