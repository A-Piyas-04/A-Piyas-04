"""Generate an SVG heatmap using real GitHub GraphQL contribution-day counts."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

USER = "A-Piyas-04"
TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN is not set. Pass secrets.GITHUB_TOKEN in the workflow.")

query = '''query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}'''
request = Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "github-profile-calendar"},
    method="POST",
)
with urlopen(request, timeout=35) as response:
    payload = json.load(response)
if payload.get("errors"):
    raise RuntimeError("GitHub GraphQL error: " + str(payload["errors"]))
calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
if not weeks or sum(len(w["contributionDays"]) for w in weeks) < 300:
    raise RuntimeError("Received incomplete contribution data; refusing to publish.")

COLORS = {"NONE":"#26181F", "FIRST_QUARTILE":"#315C3B", "SECOND_QUARTILE":"#589D4E", "THIRD_QUARTILE":"#A9DE55", "FOURTH_QUARTILE":"#E8D94F"}
cell, gap = 12, 4
left, top = 14, 65
step = cell + gap
width, height = left * 2 + len(weeks) * step, 210
parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contribution calendar for {USER}">',
'<rect width="100%" height="100%" rx="15" fill="#10070C"/>',
'<text x="14" y="29" fill="#F8F0F3" font-size="18" font-family="Arial,sans-serif" font-weight="700">CONTRIBUTION SIGNAL</text>',
f'<text x="14" y="49" fill="#C77B9B" font-size="11" font-family="Arial,sans-serif">{calendar["totalContributions"]} reported contributions · rolling 12 months · LIVE DATA</text>']
for x, week in enumerate(weeks):
    for day in week["contributionDays"]:
        # ISO date weekday (Sun=0) without third-party libraries.
        from datetime import date
        weekday = (date.fromisoformat(day["date"]).weekday() + 1) % 7
        count = day["contributionCount"]
        color = COLORS.get(day["contributionLevel"], COLORS["NONE"])
        px, py = left + x * step, top + weekday * step
        parts.append(f'<rect x="{px}" y="{py}" width="{cell}" height="{cell}" rx="3" fill="{color}"><title>{escape(day["date"])}: {count} contributions</title></rect>')
parts.append(f'<text x="14" y="195" fill="#E5B5C7" font-size="11" font-family="Arial,sans-serif">LESS</text>')
for i, color in enumerate(COLORS.values()):
    parts.append(f'<rect x="52" y="184" width="12" height="12" rx="2" fill="{color}" transform="translate({i*17} 0)"/>')
parts.append('<text x="145" y="195" fill="#E5B5C7" font-size="11" font-family="Arial,sans-serif">MORE</text></svg>')
path = Path("assets/contributions.svg")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("\n".join(parts), encoding="utf-8")
print(f"Wrote {path}: {len(weeks)} weeks, {calendar['totalContributions']} contributions")
