#!/usr/bin/env python3
'''Generate assets/github-stats.svg for the GitHub profile README.

Uses GitHub GraphQL for the contribution calendar and GitHub REST for
repositories, followers, stars, and repository language bytes.
No third-party Python packages are required.
'''

from __future__ import annotations

import datetime as dt
import html
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

USERNAME = os.environ.get("PROFILE_USERNAME", "poezi123")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = Path("assets/github-stats.svg")

BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#f0f6fc"
MUTED = "#8b949e"
CYAN = "#22d3ee"
BLUE = "#2f81f7"
GREEN = "#3fb950"
GREEN2 = "#56d364"
YELLOW = "#f2cc60"
ORANGE = "#f0883e"
PURPLE = "#a371f7"

LANG_COLORS = [BLUE, CYAN, ORANGE, YELLOW, PURPLE, GREEN, GREEN2, "#db61a2"]


def request_json(url: str, *, data=None, headers=None):
    headers = dict(headers or {})
    headers.setdefault("Accept", "application/vnd.github+json")
    headers.setdefault("User-Agent", "poezi123-profile-stats")
    if TOKEN:
        headers.setdefault("Authorization", f"Bearer {TOKEN}")

    payload = None
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"GitHub API error {e.code}: {body}") from e


def graphql(query: str, variables: dict):
    if not TOKEN:
        raise RuntimeError("GH_TOKEN/GITHUB_TOKEN is required for GraphQL.")
    result = request_json(
        "https://api.github.com/graphql",
        data={"query": query, "variables": variables},
    )
    if result.get("errors"):
        raise RuntimeError(str(result["errors"]))
    return result["data"]


def fetch_contributions():
    query = '''
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
                weekday
              }
            }
          }
        }
      }
    }
    '''
    data = graphql(query, {"login": USERNAME})
    user = data.get("user")
    if not user:
        raise RuntimeError(f"GitHub user {USERNAME!r} not found.")
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days


def fetch_repos_and_languages():
    repos = []
    page = 1
    while True:
        batch = request_json(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&sort=updated&type=owner"
        )
        if not batch:
            break
        repos.extend(r for r in batch if not r.get("fork"))
        if len(batch) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    lang_bytes = Counter()

    for repo in repos[:60]:
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        try:
            langs = request_json(lang_url)
            lang_bytes.update(langs)
        except Exception as exc:
            print(f"warning: languages for {repo.get('name')}: {exc}", file=sys.stderr)

    return repos, total_stars, lang_bytes


def fetch_followers():
    user = request_json(f"https://api.github.com/users/{USERNAME}")
    return int(user.get("followers", 0))


def streaks(days):
    ordered = sorted(
        ((dt.date.fromisoformat(d["date"]), int(d["contributionCount"])) for d in days),
        key=lambda x: x[0],
    )
    by_date = dict(ordered)
    if not ordered:
        return 0, 0

    first, last = ordered[0][0], ordered[-1][0]

    longest = current_run = 0
    cur = first
    while cur <= last:
        if by_date.get(cur, 0) > 0:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 0
        cur += dt.timedelta(days=1)

    anchor = last
    if by_date.get(anchor, 0) == 0:
        anchor -= dt.timedelta(days=1)

    current = 0
    cur = anchor
    while cur >= first and by_date.get(cur, 0) > 0:
        current += 1
        cur -= dt.timedelta(days=1)

    return current, longest


def esc(value):
    return html.escape(str(value), quote=True)


def fmt_num(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def build_svg(total, current, longest, followers, repos, stars, lang_bytes, days):
    width, height = 960, 570
    total_lang = sum(lang_bytes.values()) or 1
    top_langs = lang_bytes.most_common(6)

    day_map = {d["date"]: d for d in days}
    dates = sorted(dt.date.fromisoformat(d["date"]) for d in days)
    end = dates[-1] if dates else dt.date.today()
    start = end - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)

    level_color = {
        "NONE": "#21262d",
        "FIRST_QUARTILE": "#0e4429",
        "SECOND_QUARTILE": "#006d32",
        "THIRD_QUARTILE": "#26a641",
        "FOURTH_QUARTILE": "#39d353",
    }

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )
    parts.append(
        f'''<style>
        .title {{ font: 700 22px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:{TEXT}; }}
        .h2 {{ font: 700 15px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:{TEXT}; }}
        .num {{ font: 700 26px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:{TEXT}; }}
        .label {{ font: 500 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:{MUTED}; }}
        .small {{ font: 500 11px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:{MUTED}; }}
        </style>'''
    )
    parts.append(f'<rect width="100%" height="100%" rx="12" fill="{BG}" stroke="{BORDER}"/>')
    parts.append('<text x="28" y="42" class="title">📊 GitHub Engineering Stats</text>')
    parts.append(f'<line x1="28" y1="58" x2="932" y2="58" stroke="{BORDER}"/>')

    cards = [
        ("Contributions", fmt_num(total), 28),
        ("Current Streak", str(current), 198),
        ("Longest Streak", str(longest), 368),
        ("Followers", fmt_num(followers), 538),
        ("Public Repos", str(len(repos)), 708),
    ]
    for label, value, x in cards:
        parts.append(
            f'<rect x="{x}" y="82" width="146" height="96" rx="8" fill="{PANEL}" stroke="{BORDER}"/>'
        )
        parts.append(f'<text x="{x+73}" y="122" text-anchor="middle" class="num">{esc(value)}</text>')
        parts.append(f'<text x="{x+73}" y="149" text-anchor="middle" class="label">{esc(label)}</text>')

    parts.append(f'<rect x="28" y="198" width="904" height="126" rx="8" fill="{PANEL}" stroke="{BORDER}"/>')
    parts.append('<text x="48" y="225" class="h2">Technology Footprint</text>')

    bar_x, bar_y, bar_w, bar_h = 48, 243, 864, 10
    cursor = bar_x
    for i, (lang, b) in enumerate(top_langs):
        pct = b / total_lang
        seg = bar_w * pct
        if seg >= 1:
            parts.append(f'<rect x="{cursor:.1f}" y="{bar_y}" width="{seg:.1f}" height="{bar_h}" fill="{LANG_COLORS[i]}"/>')
        cursor += seg

    col_x = [48, 300, 552]
    for i, (lang, b) in enumerate(top_langs):
        pct = b / total_lang * 100
        x = col_x[i % 3]
        y = 282 + (i // 3) * 22
        parts.append(f'<circle cx="{x+5}" cy="{y-4}" r="5" fill="{LANG_COLORS[i]}"/>')
        parts.append(f'<text x="{x+17}" y="{y}" class="small">{esc(lang)} {pct:.1f}%</text>')

    parts.append('<text x="28" y="359" class="h2">Contribution Activity</text>')
    cell, gap = 11, 3
    grid_x, grid_y = 92, 380

    last_month = None
    for week in range(53):
        d = start + dt.timedelta(days=week*7)
        if d.month != last_month:
            parts.append(f'<text x="{grid_x + week*(cell+gap)}" y="376" class="small">{d.strftime("%b")}</text>')
            last_month = d.month

    for week in range(53):
        for weekday in range(7):
            d = start + dt.timedelta(days=week*7 + weekday)
            data = day_map.get(d.isoformat())
            level = data["contributionLevel"] if data else "NONE"
            fill = level_color.get(level, "#21262d")
            x = grid_x + week*(cell+gap)
            y = grid_y + weekday*(cell+gap)
            parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fill}"/>')

    for text, idx in [("Mon",1),("Wed",3),("Fri",5)]:
        y = grid_y + idx*(cell+gap) + 9
        parts.append(f'<text x="48" y="{y}" class="small">{text}</text>')

    parts.append(f'<line x1="28" y1="500" x2="932" y2="500" stroke="{BORDER}"/>')
    parts.append(f'<text x="28" y="530" class="small">★ {stars} stars across public non-fork repositories</text>')
    parts.append(f'<text x="932" y="530" text-anchor="end" class="small">auto-generated • @{esc(USERNAME)}</text>')
    parts.append('</svg>')
    return "".join(parts)


def main():
    total, days = fetch_contributions()
    repos, stars, langs = fetch_repos_and_languages()
    followers = fetch_followers()
    current, longest = streaks(days)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        build_svg(total, current, longest, followers, repos, stars, langs, days),
        encoding="utf-8",
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
