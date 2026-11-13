"""
Builds dark_mode.svg and light_mode.svg: a neofetch-style GitHub profile card.

Run locally:   ACCESS_TOKEN=ghp_xxx USER_NAME=hassanzubair1c python today.py
Preview only:  python today.py --demo        (sample numbers, no token needed)
The GitHub Action in .github/workflows/build.yaml runs this daily.
"""
import datetime as dt
import html
import json
import os
import sys
import time

import requests

# ───────────────────────────── EDIT ME ─────────────────────────────
USER = os.environ.get("USER_NAME", "hassanzubair1c")
HEADER = "hassan@zubair"
UPTIME_SINCE = dt.date(2016, 1, 1)  # career start (shows as "Uptime")

INFO = [  # (key, value) — None = blank line, ("—", "Title") = section header
    ("OS", "Linux, Windows 11, macOS"),
    ("Uptime", "{uptime}"),
    ("Host", "Freelance & direct client engagements"),
    ("Kernel", "AI Systems Architect"),
    ("IDE", "VS Code, Cursor, Claude Code"),
    None,
    ("Languages.Programming", "Python, TypeScript, Go, SQL"),
    ("Languages.Computer", "HTML, CSS, JSON, YAML"),
    ("Languages.Real", "English, Urdu"),
    None,
    ("Stack.AI", "LangChain, RAG, Multi-Agent, vLLM"),
    ("Stack.Backend", "FastAPI, Django, PostgreSQL, Redis"),
    ("Stack.Cloud", "Azure, AWS, GCP, Docker, K8s"),
    ("Certs", "AWS Solutions Architect, Python, Django"),
    ("—", "Contact"),
    ("Website", "hassanzubair.ai"),
    ("LinkedIn", "your-linkedin-handle"),
    ("Upwork", "your-upwork-profile"),
    ("—", "GitHub Stats"),
]
# ───────────────────────────────────────────────────────────────────

WIDTH_CH = 58          # characters in the right-hand panel
LINE_H = 20
FONT = 16
ART_X, TOP = 20, 30
ART_FONT, ART_LINE = 10, 12   # smaller font for the portrait = more detail
CHAR_W = FONT * 0.61  # approx monospace glyph width

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                 add="#3fb950", dele="#f85149", dots="#616e7f"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                  add="#1a7f37", dele="#cf222e", dots="#c2cfde"),
}

API = "https://api.github.com"
TOKEN = os.environ.get("ACCESS_TOKEN", "")
HEADERS = {"Authorization": f"bearer {TOKEN}"} if TOKEN else {}


# ───────────────────────────── stats ─────────────────────────────
def gql(query, variables=None):
    r = requests.post(f"{API}/graphql", json={"query": query, "variables": variables or {}},
                      headers=HEADERS, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def uptime(since):
    today = dt.date.today()
    y = today.year - since.year
    m = today.month - since.month
    d = today.day - since.day
    if d < 0:
        m -= 1
        prev = (today.replace(day=1) - dt.timedelta(days=1))
        d += prev.day
    if m < 0:
        y -= 1
        m += 12
    s = lambda n: "" if n == 1 else "s"
    return f"{y} year{s(y)}, {m} month{s(m)}, {d} day{s(d)}"


def owned_repos():
    repos, cursor = [], None
    q = """query($login:String!,$cursor:String){ user(login:$login){
      repositories(first:100, after:$cursor, ownerAffiliations:[OWNER], isFork:false){
        pageInfo{hasNextPage endCursor}
        nodes{ nameWithOwner stargazerCount pushedAt } } } }"""
    while True:
        r = gql(q, {"login": USER, "cursor": cursor})["user"]["repositories"]
        repos += r["nodes"]
        if not r["pageInfo"]["hasNextPage"]:
            return repos
        cursor = r["pageInfo"]["endCursor"]


def account_stats():
    q = """query($login:String!){ user(login:$login){
      createdAt followers{totalCount}
      contributed: repositories(ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]){totalCount}
      owned: repositories(ownerAffiliations:[OWNER]){totalCount} } }"""
    return gql(q, {"login": USER})["user"]


def total_commits(created_at):
    start = int(created_at[:4])
    total = 0
    for year in range(start, dt.date.today().year + 1):
        q = """query($login:String!,$from:DateTime!,$to:DateTime!){ user(login:$login){
          contributionsCollection(from:$from,to:$to){ totalCommitContributions restrictedContributionsCount } } }"""
        c = gql(q, {"login": USER, "from": f"{year}-01-01T00:00:00Z",
                    "to": f"{year}-12-31T23:59:59Z"})["user"]["contributionsCollection"]
        total += c["totalCommitContributions"] + c["restrictedContributionsCount"]
    return total


def lines_of_code(repos):
    """Additions/deletions you authored, per repo, cached by last push time."""
    path = "cache/loc.json"
    try:
        cache = json.load(open(path))
    except (OSError, ValueError):
        cache = {}
    add = dele = 0
    for repo in repos:
        name, pushed = repo["nameWithOwner"], repo["pushedAt"]
        hit = cache.get(name)
        if not hit or hit["pushed"] != pushed:
            a = d = 0
            for _ in range(6):  # GitHub returns 202 while it computes stats
                r = requests.get(f"{API}/repos/{name}/stats/contributors", headers=HEADERS, timeout=60)
                if r.status_code == 202:
                    time.sleep(3)
                    continue
                if r.status_code == 200 and r.text.strip():
                    for c in r.json() or []:
                        if c.get("author") and c["author"]["login"].lower() == USER.lower():
                            a = sum(w["a"] for w in c["weeks"])
                            d = sum(w["d"] for w in c["weeks"])
                break
            hit = cache[name] = {"pushed": pushed, "add": a, "del": d}
        add += hit["add"]
        dele += hit["del"]
    os.makedirs("cache", exist_ok=True)
    json.dump(cache, open(path, "w"), indent=1)
    return add, dele


def collect():
    acct = account_stats()
    repos = owned_repos()
    add, dele = lines_of_code(repos)
    return dict(
        repos=acct["owned"]["totalCount"],
        contributed=acct["contributed"]["totalCount"],
        stars=sum(r["stargazerCount"] for r in repos),
        commits=total_commits(acct["createdAt"]),
        followers=acct["followers"]["totalCount"],
        loc_add=add, loc_del=dele,
    )


DEMO = dict(repos=48, contributed=112, stars=96, commits=3412, followers=57,
            loc_add=812_455, loc_del=301_928)


# ───────────────────────────── SVG ─────────────────────────────
def esc(s):
    return html.escape(str(s), quote=False)


def kv_line(key, value, width=WIDTH_CH):
    """'. Key: ........ value' -> list of (text, class) spans."""
    left = f"{key}:"
    dots = width - 2 - len(left) - len(value) - 2
    dots = max(dots, 1)
    return [(". ", "cc"), (left, "key"), (" " + "." * dots + " ", "cc"), (value, "value")]


def section(title, width=WIDTH_CH):
    head = f"- {title} "
    return [(head, "text"), ("—" * (width - len(head)), "text")]


def fmt(n):
    return f"{n:,}"


def build_info_lines(stats):
    out = [[(HEADER, "text"), (" " + "—" * (WIDTH_CH - len(HEADER) - 1), "text")]]
    for item in INFO:
        if item is None:
            out.append([])
        elif item[0] == "—":
            out.append([])
            out.append(section(item[1]))
        else:
            out.append(kv_line(item[0], item[1].format(uptime=uptime(UPTIME_SINCE))))
    # stats rows (two per line, like the original)
    def pair(k1, v1, k2, v2, w1=26):
        a = kv_line(k1, v1, w1)
        b = kv_line(k2, v2, WIDTH_CH - w1 - 1)
        return a + [(" | ", "cc")] + b[1:]

    out.append(pair("Repos", fmt(stats["repos"]),
                    "Contributed", fmt(stats["contributed"])))
    out.append(pair("Commits", fmt(stats["commits"]),
                    "Stars", fmt(stats["stars"])))
    total = stats["loc_add"] - stats["loc_del"]
    tail = f"( {fmt(stats['loc_add'])}++, {fmt(stats['loc_del'])}-- )"
    loc = kv_line("Lines of Code", fmt(total) + " " + tail)
    loc = loc[:-1] + [(fmt(total) + " ", "value"), ("( ", "text"),
                      (fmt(stats["loc_add"]) + "++", "add"), (", ", "text"),
                      (fmt(stats["loc_del"]) + "--", "del"), (" )", "text")]
    out.append(kv_line("Followers", fmt(stats["followers"])))
    out.append(loc)
    return out


def render(theme, art_lines, info_lines):
    t = THEMES[theme]
    INFO_X = int(ART_X + max(map(len, art_lines)) * ART_FONT * 0.61 + 30)
    height = max(TOP + len(info_lines) * LINE_H, TOP + len(art_lines) * ART_LINE) + 10
    width = INFO_X + int(WIDTH_CH * CHAR_W) + 25
    parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'DejaVu Sans Mono\',monospace" '
        f'width="{width}px" height="{height}px" font-size="{FONT}px">',
        "<style>",
        "@font-face{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';"
        "font-display:swap;-webkit-size-adjust:109%;size-adjust:109%;}",
        f".key{{fill:{t['key']};}} .value{{fill:{t['value']};}} .add{{fill:{t['add']};}} "
        f".del{{fill:{t['dele']};}} .cc{{fill:{t['dots']};}} text,tspan{{white-space:pre;}}",
        "</style>",
        f'<rect width="{width}px" height="{height}px" fill="{t["bg"]}" rx="15"/>',
        f'<text xml:space="preserve" x="{ART_X}" y="{TOP}" fill="{t["text"]}" font-size="{ART_FONT}px">',
    ]
    for i, line in enumerate(art_lines):
        parts.append(f'<tspan x="{ART_X}" y="{TOP + i * ART_LINE}">{esc(line)}</tspan>')
    parts.append("</text>")
    parts.append(f'<text xml:space="preserve" x="{INFO_X}" y="{TOP}" fill="{t["text"]}">')
    for i, spans in enumerate(info_lines):
        if not spans:
            continue
        parts.append(f'<tspan x="{INFO_X}" y="{TOP + i * LINE_H}">' +
                     "".join(f'<tspan class="{c}">{esc(s)}</tspan>' if c != "text" else esc(s)
                             for s, c in spans) + "</tspan>")
    parts.append("</text></svg>")
    return "\n".join(parts)


def main():
    demo = "--demo" in sys.argv or not TOKEN
    if demo:
        print("No ACCESS_TOKEN (or --demo): using sample stats")
    stats = DEMO if demo else collect()
    print(stats)
    art = open("ascii.txt", encoding="utf-8").read().rstrip("\n").split("\n")
    info = build_info_lines(stats)
    # vertically centre the art against the info panel
    pad = max(0, (len(info) * LINE_H - len(art) * ART_LINE) // 2 // ART_LINE)
    art = [""] * pad + art
    for theme in THEMES:
        with open(f"{theme}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(theme, art, info))
    print("wrote dark_mode.svg, light_mode.svg")


if __name__ == "__main__":
    main()
