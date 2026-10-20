import json, os, re, urllib.request, urllib.parse
from datetime import datetime, timedelta

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

def vid(s):
    m = re.search(r"(?:v=|youtu\.be/|/live/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", s)
    if m:
        return m.group(1)
    s = s.strip()
    return s if re.fullmatch(r"[A-Za-z0-9_-]{11}", s) else None

def dur(s):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return 0
    d, h, mi, sec = [int(x or 0) for x in m.groups()]
    return d * 86400 + h * 3600 + mi * 60 + sec

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

extra = []
if os.path.exists("extra.json"):
    with open("extra.json", encoding="utf-8") as f:
        for x in json.load(f):
            v = vid(x)
            if v:
                extra.append(v)
guest = set(extra)
all_ids = list(dict.fromkeys(ids + extra))

new = {}
for n in range(0, len(all_ids), 50):
    d = api("videos", part="snippet,liveStreamingDetails,contentDetails",
            id=",".join(all_ids[n:n+50]))
    for v in d["items"]:
        L = v.get("liveStreamingDetails")
        if L:
            start = L.get("actualStartTime") or L.get("scheduledStartTime")
            end = L.get("actualEndTime")
            status = ("upcoming" if not L.get("actualStartTime")
                      else "live" if not end else "done")
        elif v["id"] in guest:
            start = v["snippet"]["publishedAt"]
            sec = dur(v.get("contentDetails", {}).get("duration"))
            end = (t(start) + timedelta(seconds=sec)).isoformat() if sec else None
            status = "done"
        else:
            continue
        if not start:
            continue
        hours = round((t(end) - t(start)).total_seconds() / 3600, 1) if end else 0
        new[v["id"]] = {
            "id": v["id"],
            "title": v["snippet"]["title"],
            "start": start,
            "end": end,
            "hours": hours,
            "status": status,
            "thumb": v["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
            "channel": v["snippet"].get("channelTitle", ""),
            "guest": v["id"] in guest,
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
