import json, os, urllib.request, urllib.parse
from datetime import datetime

KEY = os.environ["YT_API_KEY"]
CHANNEL = "UCgmFrRcyH7d1zR9sIVQhFow"
UPLOADS = "UU" + CHANNEL[2:]

def api(path, **params):
    params["key"] = KEY
    url = ("https://www.googleapis.com/youtube/v3/" + path
           + "?" + urllib.parse.urlencode(params))
    with urllib.request.urlopen(url) as r:
        return json.load(r)

def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

ids, token = [], None
for _ in range(2):
    p = dict(part="contentDetails", playlistId=UPLOADS, maxResults=50)
    if token:
        p["pageToken"] = token
    d = api("playlistItems", **p)
    ids += [i["contentDetails"]["videoId"] for i in d["items"]]
    token = d.get("nextPageToken")
    if not token:
        break

new = {}
for n in range(0, len(ids), 50):
    d = api("videos", part="snippet,liveStreamingDetails",
            id=",".join(ids[n:n+50]))
    for v in d["items"]:
        L = v.get("liveStreamingDetails")
        if not L:
            continue
        start = L.get("actualStartTime") or L.get("scheduledStartTime")
        if not start:
            continue
        end = L.get("actualEndTime")
        hours = round((t(end) - t(start)).total_seconds() / 3600, 1) if end else 0
        status = ("upcoming" if not L.get("actualStartTime")
                  else "live" if not end else "done")
        new[v["id"]] = {
            "id": v["id"],
            "title": v["snippet"]["title"],
            "start": start,
            "end": end,
            "hours": hours,
            "status": status,
            "thumb": v["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
        }

old = {}
if os.path.exists("data.json"):
    with open("data.json", encoding="utf-8") as f:
        old = {e["id"]: e for e in json.load(f)}
old.update(new)
out = sorted(old.values(), key=lambda e: e["start"])
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(len(out), "streams saved")
