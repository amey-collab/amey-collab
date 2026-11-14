"""Generates assets/3d-skyline.svg: an isometric 3D "contribution city".

Every day of the last year is a building; taller + brighter = more contributions.
Run locally for a preview without a token:  DEMO=1 python scripts/gen_3d_skyline.py
"""
import os, json, math, random, urllib.request
from datetime import date, timedelta

USER = os.environ.get("GH_USER", "amey-collab")

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{date weekday contributionCount}}}}}}"""


def load():
    if os.environ.get("DEMO"):
        random.seed(7)
        today = date.today()
        d = today - timedelta(days=364)
        d -= timedelta(days=(d.weekday() + 1) % 7)          # back to Sunday
        weeks, total = [], 0
        while d <= today:
            days = []
            for wd in range(7):
                day = d + timedelta(days=wd)
                if day > today:
                    break
                c = 0 if random.random() < 0.45 else random.randint(1, 12)
                total += c
                days.append({"date": str(day), "weekday": wd, "contributionCount": c})
            weeks.append({"contributionDays": days})
            d += timedelta(days=7)
        return weeks, total
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["weeks"], cal["totalContributions"]


def shade(hexc, f):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


weeks, total = load()
nw = len(weeks)
grid = {(i, d["weekday"]): d["contributionCount"] for i, w in enumerate(weeks) for d in w["contributionDays"]}
maxc = max(1, max(grid.values()))

COLORS = ["#2a1a55", "#0097b8", "#00f5ff", "#b967ff", "#ff00ff"]   # level 0..4
S, MAXH, PAD, TOP = 13, 90, 34, 80
K, HALF = S * 0.866, S * 0.5
ox, oy = 7 * K + PAD, TOP + MAXH
W = int((nw + 7) * K + 2 * PAD)
H = int(oy + (nw + 7) * HALF + PAD + 10)


def P(i, j, z=0):
    return f"{ox + (i - j) * K:.1f},{oy + (i + j) * HALF - z:.1f}"


out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<style>.b{animation:rise .7s ease-out backwards}'
       '@keyframes rise{from{opacity:0;transform:translateY(-16px)}}</style>',
       '<defs><radialGradient id="bg" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="#1a0533"/>'
       '<stop offset="1" stop-color="#05030f"/></radialGradient>'
       '<filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
       '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
       f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)" stroke="#00f5ff" stroke-width="1.5"/>',
       f'<text x="{PAD}" y="42" fill="#00f5ff" font-family="monospace" font-size="20" font-weight="bold">'
       f'3D CONTRIBUTION CITY</text>',
       f'<text x="{PAD}" y="64" fill="#ff00ff" font-family="monospace" font-size="13">'
       f'{total} contributions in the last year  |  peak day: {maxc}</text>']

for s in range(nw + 7):                       # painter's algorithm: back -> front
    for i in range(max(0, s - 6), min(nw - 1, s) + 1):
        j = s - i
        if (i, j) not in grid:
            continue
        c = grid[(i, j)]
        lvl = 0 if c == 0 else max(1, min(4, math.ceil(4 * c / maxc)))
        h = 2 if c == 0 else 8 + (c / maxc) * (MAXH - 8)
        base = COLORS[lvl]
        top = f'<polygon points="{P(i, j, h)} {P(i + 1, j, h)} {P(i + 1, j + 1, h)} {P(i, j + 1, h)}" fill="{base}"'
        if lvl >= 4:
            top += ' filter="url(#glow)"'
        top += "/>"
        left = f'<polygon points="{P(i, j + 1, 0)} {P(i + 1, j + 1, 0)} {P(i + 1, j + 1, h)} {P(i, j + 1, h)}" fill="{shade(base, .5)}"/>'
        right = f'<polygon points="{P(i + 1, j, 0)} {P(i + 1, j + 1, 0)} {P(i + 1, j + 1, h)} {P(i + 1, j, h)}" fill="{shade(base, .72)}"/>'
        out.append(f'<g class="b" style="animation-delay:{i * 20}ms" stroke="#0d0221" stroke-width=".4">{left}{right}{top}</g>')

# legend
lx = W - PAD - 5 * 16 - 70
out.append(f'<text x="{lx}" y="42" fill="#8888aa" font-family="monospace" font-size="11">Less</text>')
for k, col in enumerate(COLORS):
    out.append(f'<rect x="{lx + 32 + k * 16}" y="32" width="12" height="12" rx="2" fill="{col}"/>')
out.append(f'<text x="{lx + 32 + 5 * 16 + 4}" y="42" fill="#8888aa" font-family="monospace" font-size="11">More</text>')
out.append("</svg>")

os.makedirs("assets", exist_ok=True)
with open("assets/3d-skyline.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("3d skyline ok", W, H, total)
