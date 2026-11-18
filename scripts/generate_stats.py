import datetime
import json
import os
import pathlib
import urllib.request

TOKEN = os.environ["STATS_TOKEN"]
LOGIN = "irfanjat"
ROOT = pathlib.Path(__file__).resolve().parent.parent

today = datetime.date.today()
start = today - datetime.timedelta(days=364)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {
        "login": LOGIN,
        "from": start.isoformat() + "T00:00:00Z",
        "to": today.isoformat() + "T23:59:59Z",
    },
}).encode()

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    },
)

with urllib.request.urlopen(request) as response:
    result = json.load(response)

calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
days.sort(key=lambda day: day["date"])

total = calendar["totalContributions"]

active = [day for day in days if day["contributionCount"] > 0]
end = len(days) - 1
if days and days[-1]["contributionCount"] == 0:
    end -= 1
current = 0
while end >= 0 and days[end]["contributionCount"] > 0:
    current += 1
    end -= 1

longest = 0
run = 0
for day in days:
    if day["contributionCount"] > 0:
        run += 1
        longest = max(longest, run)
    else:
        run = 0

colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

def level(count):
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 10:
        return 3
    return 4

cell = 11
gap = 3
step = cell + gap
grid_x = 20
grid_y = 112

parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="716" height="222" viewBox="0 0 716 222" font-family="Segoe UI, Ubuntu, sans-serif">',
    '<rect width="716" height="222" rx="8" fill="#0f172a"/>',
    '<text x="20" y="30" fill="#60a5fa" font-size="16" font-weight="700">Contribution Activity</text>',
    f'<text x="696" y="30" fill="#94a3b8" font-size="12" text-anchor="end">{start.strftime("%b %d, %Y")} - {today.strftime("%b %d, %Y")}</text>',
]

stats = [
    ("Total contributions", f"{total:,}", 20),
    ("Current streak", f"{current}", 250),
    ("Longest streak", f"{longest}", 480),
]
for label, value, x in stats:
    parts.append(f'<text x="{x}" y="68" fill="#e2e8f0" font-size="26" font-weight="700">{value}</text>')
    parts.append(f'<text x="{x}" y="88" fill="#94a3b8" font-size="12">{label}</text>')

for week_index, week in enumerate(calendar["weeks"]):
    for day in week["contributionDays"]:
        day_index = datetime.date.fromisoformat(day["date"]).weekday()
        x = grid_x + week_index * step
        y = grid_y + day_index * step
        fill = colors[level(day["contributionCount"])]
        parts.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fill}">'
            f'<title>{day["date"]}: {day["contributionCount"]} contributions</title></rect>'
        )

parts.append('</svg>')

output = ROOT / "assets" / "github-stats.svg"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("\n".join(parts) + "\n")
print(f"wrote {output} (total={total}, current={current}, longest={longest})")
