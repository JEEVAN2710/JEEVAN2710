#!/usr/bin/env python3
"""
Regenerates stats.svg, langs.svg and trophies.svg directly from the GitHub REST API,
so the profile README never depends on a rate-limited third-party card service.

Run in CI (see .github/workflows/update-stats.yml) with GITHUB_TOKEN available,
or locally with a personal access token exported as GITHUB_TOKEN.
"""
import os
import math
import requests

USERNAME = os.environ.get("GH_USERNAME", "JEEVAN2710")
TOKEN = os.environ.get("GITHUB_TOKEN")
API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

DARK = dict(
    bg0="#020f09", bg1="#041b12", card_border="#1c4a30",
    text_main="#eafff2", text_dim="#8fd9b5",
    ring_track="#123322", accent="#39ff9d", accent2="#ff6ec7", accent3="#7b5cff",
)

LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Java": "#b07219",
    "Python": "#3572A5", "HTML": "#e34c26", "CSS": "#563d7c",
    "Kotlin": "#A97BFF", "C++": "#f34b7d", "C": "#555555", "Shell": "#89e051",
}

COMMON_DEFS = f'''
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{DARK['bg0']}"/>
      <stop offset="100%" stop-color="{DARK['bg1']}"/>
    </linearGradient>
    <linearGradient id="ringGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{DARK['accent']}"/>
      <stop offset="50%" stop-color="{DARK['accent3']}"/>
      <stop offset="100%" stop-color="{DARK['accent2']}"/>
    </linearGradient>
    <filter id="softGlow2" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3.4"/>
    </filter>
    <linearGradient id="shine2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="30%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="48%" stop-color="#ffffff" stop-opacity="0.5"/>
      <stop offset="60%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
'''

def wrapper(w, h, body):
    return f'''<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs>
    <clipPath id="rc"><rect x="0" y="0" width="{w}" height="{h}" rx="18"/></clipPath>
    {COMMON_DEFS}
  </defs>
  <g clip-path="url(#rc)">
    <rect x="0" y="0" width="{w}" height="{h}" fill="url(#bgGrad)"/>
    <rect x="0" y="0" width="{w}" height="{h}" fill="none" stroke="{DARK['card_border']}" stroke-width="1.4"/>
    {body}
  </g>
</svg>'''

def fetch_user():
    r = requests.get(f"{API}/users/{USERNAME}", headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_repos():
    repos, page = [], 1
    while True:
        r = requests.get(f"{API}/users/{USERNAME}/repos",
                          params={"per_page": 100, "page": page, "type": "owner"},
                          headers=HEADERS, timeout=20)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos

def fetch_languages(repos):
    totals = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        url = repo.get("languages_url")
        if not url:
            continue
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            for lang, bytes_ in r.json().items():
                totals[lang] = totals.get(lang, 0) + bytes_
        except requests.RequestException:
            continue
    return totals

def build_stats(user, total_stars):
    public_repos = user.get("public_repos", 0)
    followers = user.get("followers", 0)
    following = user.get("following", 0)

    # simple heuristic "rank" score just to size the ring (purely cosmetic)
    score = min(1.0, (public_repos * 2 + followers * 3 + total_stars * 4) / 300)
    if score > 0.85:
        rank = "S"
    elif score > 0.65:
        rank = "A+"
    elif score > 0.45:
        rank = "A"
    elif score > 0.25:
        rank = "B"
    else:
        rank = "C"

    W, H = 480, 260
    cx, cy, r = 92, 130, 62
    circumference = 2 * math.pi * r
    dash = circumference * score

    rows = [
        ("\U0001F4E6", "Public Repositories", str(public_repos)),
        ("\U0001F465", "Followers", str(followers)),
        ("\U0001F517", "Following", str(following)),
        ("\u2B50", "Total Stars", str(total_stars)),
    ]
    row_x, row_y0, row_h = 200, 58, 46
    rows_svg = []
    for i, (icon, label, val) in enumerate(rows):
        y = row_y0 + i * row_h
        b = 0.5 + i * 0.18
        rows_svg.append(f'''
      <g opacity="0">
        <animate attributeName="opacity" begin="{b:.2f}s" dur="0.5s" values="0;1" fill="freeze"/>
        <text x="{row_x}" y="{y}" font-family="Poppins, Verdana, sans-serif" font-size="16" fill="{DARK['text_main']}">{icon}  {label}</text>
        <text x="{W-30}" y="{y}" text-anchor="end" font-family="'JetBrains Mono', Consolas, monospace" font-size="16" font-weight="700" fill="{DARK['accent']}">{val}</text>
        <line x1="{row_x}" y1="{y+14}" x2="{W-30}" y2="{y+14}" stroke="{DARK['card_border']}" stroke-width="1"/>
      </g>''')

    body = f'''
    <text x="24" y="34" font-family="Poppins, Verdana, sans-serif" font-size="17" font-weight="700" fill="{DARK['text_main']}">Jeevan's GitHub Stats</text>
    <g transform="translate({cx},{cy})">
      <circle r="{r}" fill="none" stroke="{DARK['ring_track']}" stroke-width="12"/>
      <circle r="{r}" fill="none" stroke="url(#ringGrad2)" stroke-width="12" stroke-linecap="round"
        transform="rotate(-90)" stroke-dasharray="0 {circumference:.1f}">
        <animate attributeName="stroke-dasharray" begin="0.3s" dur="1.6s" fill="freeze"
          values="0 {circumference:.1f};{dash:.1f} {circumference:.1f}" calcMode="spline" keySplines="0.2 0 0.2 1"/>
      </circle>
      <text x="0" y="-2" text-anchor="middle" font-family="Poppins, Verdana, sans-serif" font-size="30" font-weight="800" fill="{DARK['text_main']}">{rank}</text>
      <text x="0" y="20" text-anchor="middle" font-family="Poppins, Verdana, sans-serif" font-size="11" fill="{DARK['text_dim']}">RANK</text>
    </g>
    {"".join(rows_svg)}
    '''
    return wrapper(W, H, body)

def build_langs(lang_totals):
    W, H = 480, 260
    total = sum(lang_totals.values()) or 1
    top = sorted(lang_totals.items(), key=lambda kv: kv[1], reverse=True)[:5]
    body = [f'<text x="24" y="34" font-family="Poppins, Verdana, sans-serif" font-size="17" font-weight="700" fill="{DARK["text_main"]}">Most Used Languages</text>']
    bar_x, bar_w = 24, W - 48
    y = 62
    row_h = 40
    for i, (name, bytes_) in enumerate(top):
        pct = round(bytes_ / total * 100, 1)
        col = LANG_COLORS.get(name, "#8fd9b5")
        b = 0.4 + i * 0.18
        w = bar_w * pct / 100
        body.append(f'''
      <g>
        <text x="{bar_x}" y="{y}" font-family="Poppins, Verdana, sans-serif" font-size="13.5" fill="{DARK['text_dim']}">{name}</text>
        <text x="{bar_x+bar_w}" y="{y}" text-anchor="end" font-family="'JetBrains Mono', Consolas, monospace" font-size="12.5" fill="{DARK['text_dim']}">{pct}%</text>
        <rect x="{bar_x}" y="{y+8}" width="{bar_w}" height="10" rx="5" fill="{DARK['ring_track']}"/>
        <rect x="{bar_x}" y="{y+8}" width="0" height="10" rx="5" fill="{col}">
          <animate attributeName="width" begin="{b:.2f}s" dur="1.1s" fill="freeze" values="0;{w:.1f}" calcMode="spline" keySplines="0.2 0 0.2 1"/>
        </rect>
      </g>''')
        y += row_h
    return wrapper(W, H, "".join(body))

def main():
    user = fetch_user()
    repos = fetch_repos()
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    lang_totals = fetch_languages(repos)

    out_dir = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(out_dir, "stats.svg"), "w") as f:
        f.write(build_stats(user, total_stars))
    if lang_totals:
        with open(os.path.join(out_dir, "langs.svg"), "w") as f:
            f.write(build_langs(lang_totals))
    print(f"Updated stats.svg (repos={user.get('public_repos')}, followers={user.get('followers')}, stars={total_stars})")
    if lang_totals:
        print("Updated langs.svg with", len(lang_totals), "languages")

if __name__ == "__main__":
    main()
