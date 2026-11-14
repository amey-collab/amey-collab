"""Generates assets/activity-graph.svg: a neon daily-commit line graph.

Flat line = no commits that day. The line rises with the day's contribution count.
Run locally for a preview without a token:  DEMO=1 python scripts/gen_activity_graph.py
"""
import os, json, random, urllib.request
from datetime import datetime, timedelta, timezone

USER = os.environ.get("GH_USER", "amey-collab")
DAYS = 31

QUERY = """query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){contributionsCollection(from:$from,to:$to){
    contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""


def load(start, end):
    if os.environ.get("DEMO"):
        random.seed(3)
        return {(start + timedelta(days=i)).strftime("%Y-%m-%d"): random.choice([0, 0, 1, 2, 3, 5, 8])
                for i in range(DAYS)}
    body = json.dumps({"query": QUERY, "variables": {
        "login": USER,
        "from": start.strftime("%Y-%m-%dT00:00:00Z"),
        "to": end.strftime("%Y-%m-%dT%H:%M:%SZ")}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def current_streak(v):
    i = len(v) - 1
    if v[i] == 0:          # today may not have a commit yet; don't break the streak
        i -= 1
    n = 0
    while i >= 0 and v[i] > 0:
        n += 1
        i -= 1
    return n


def longest_streak(v):
    best = run = 0
    for x in v:
        run = run + 1 if x > 0 else 0
        best = max(best, run)
    return best


end = datetime.now(timezone.utc)
start = end - timedelta(days=DAYS - 1)
counts = load(start, end)
days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(DAYS)]
vals = [counts.get(d, 0) for d in days]

W, H = 900, 320
L, R, T, B = 55, 35, 95, 50
ymax = max(max(vals), 4)
cw, ch = W - L - R, H - T - B
xs = [L + i * cw / (DAYS - 1) for i in range(DAYS)]
ys = [T + ch - (v / ymax) * ch for v in vals]
line = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
area = f"{L},{T + ch} {line} {xs[-1]:.1f},{T + ch}"

streak, best, total, active = current_streak(vals), longest_streak(vals), sum(vals), sum(1 for v in vals if v)

s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
     '<style>'
     '.ln{stroke-dasharray:1;animation:draw 2.6s ease-out backwards}'
     '.ar{animation:fade 1.6s ease-out .9s backwards}'
     '.pt{animation:pulse 2.2s ease-in-out infinite}'
     '@keyframes draw{from{stroke-dashoffset:1}}'
     '@keyframes fade{from{opacity:0}}'
     '@keyframes pulse{50%{r:6;opacity:.7}}'
     '</style>',
     '<defs>'
     '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d0221"/><stop offset="1" stop-color="#050a1f"/></linearGradient>'
     '<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff00ff" stop-opacity=".5"/><stop offset="1" stop-color="#ff00ff" stop-opacity="0"/></linearGradient>'
     '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="b"/>'
     '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
     '</defs>',
     f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)" stroke="#00f5ff" stroke-width="1.5"/>',
     f'<text x="{W / 2}" y="34" text-anchor="middle" fill="#00f5ff" font-family="monospace" font-size="19" font-weight="bold">'
     f'DAILY COMMIT ACTIVITY // LAST {DAYS} DAYS</text>',
     f'<text x="{W / 2}" y="62" text-anchor="middle" fill="#ff00ff" font-family="monospace" font-size="14">'
     f'streak {streak}d  |  longest {best}d  |  {total} contributions  |  {active} active days</text>']

for i in range(5):
    gy = T + ch - i * ch / 4
    s.append(f'<line x1="{L}" y1="{gy:.1f}" x2="{W - R}" y2="{gy:.1f}" stroke="#fff" stroke-opacity=".08"/>')
    s.append(f'<text x="{L - 8}" y="{gy + 4:.1f}" text-anchor="end" fill="#8888aa" font-family="monospace" font-size="11">{round(i * ymax / 4)}</text>')

s.append(f'<polygon class="ar" points="{area}" fill="url(#g)"/>')
s.append(f'<polyline class="ln" pathLength="1" points="{line}" fill="none" stroke="#ff00ff" stroke-width="3" '
         f'stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)"/>')

for i, (x, y, v) in enumerate(zip(xs, ys, vals)):
    if v > 0:
        s.append(f'<circle class="pt" cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#00f5ff" stroke="#fff" stroke-width="1" filter="url(#glow)"/>')
        s.append(f'<text x="{x:.1f}" y="{y - 11:.1f}" text-anchor="middle" fill="#00f5ff" font-family="monospace" font-size="11">{v}</text>')
    if i % 5 == 0 or i == DAYS - 1:
        label = datetime.strptime(days[i], "%Y-%m-%d").strftime("%d %b")
        s.append(f'<text x="{x:.1f}" y="{H - 18}" text-anchor="middle" fill="#8888aa" font-family="monospace" font-size="11">{label}</text>')

s.append('</svg>')
os.makedirs("assets", exist_ok=True)
with open("assets/activity-graph.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(s))
print("activity graph ok", vals)
