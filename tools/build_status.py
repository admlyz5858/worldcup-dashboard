#!/usr/bin/env python3
# GitHub Actions'ta çalışır — iki kanalın PUBLIC verisini tek OAuth token'la ID'den çeker,
# videos.json (yayınlanan video kaydı) + queue.json (sıradaki maç/kuyruk) okur, status.json yazar.
# Kullanım: python3 tools/build_status.py docs/status.json
import json, os, sys, datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

OUT = sys.argv[1] if len(sys.argv) > 1 else "docs/status.json"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHANNELS = [
    {"key": "tr", "name": "ThYsf", "id": "UCwuQBJAjSlE8BUxmbw8vzlA"},
    {"key": "en", "name": "World Cup HQ", "id": "UC3d2KK7-XRgDt-rM-G5LCMQ"},
]

now = datetime.datetime.now(datetime.timezone.utc)
videos = json.load(open(os.path.join(ROOT, "videos.json")))
qfile = os.path.join(ROOT, "queue.json")
qd = json.load(open(qfile)) if os.path.exists(qfile) else {}

healthy = True
yt = None
try:
    cr = Credentials(token=None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                     token_uri="https://oauth2.googleapis.com/token",
                     client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                     scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"])
    cr.refresh(Request())
    yt = build("youtube", "v3", credentials=cr)
except Exception as e:
    healthy = False
    print("AUTH FAIL:", str(e)[:120])

# kanal public istatistikleri (ID ile — tek token yeter)
channels = []
ch_stats = {}
if yt:
    try:
        r = yt.channels().list(part="snippet,statistics", id=",".join(c["id"] for c in CHANNELS)).execute()
        for it in r.get("items", []):
            ch_stats[it["id"]] = it
    except Exception as e:
        healthy = False; print("CHAN FAIL:", str(e)[:120])
for c in CHANNELS:
    it = ch_stats.get(c["id"])
    if it:
        channels.append({"key": c["key"], "name": it["snippet"]["title"], "id": c["id"],
                         "url": f"https://youtube.com/channel/{c['id']}",
                         "subs": int(it["statistics"].get("subscriberCount", 0)),
                         "videos": int(it["statistics"].get("videoCount", 0))})
    else:
        channels.append({"key": c["key"], "name": c["name"], "id": c["id"],
                         "url": f"https://youtube.com/channel/{c['id']}", "error": "veri yok"})

# video public istatistikleri
stats = {}
if yt:
    ids = [v["id"] for v in videos]
    for i in range(0, len(ids), 50):
        try:
            r = yt.videos().list(part="statistics,snippet", id=",".join(ids[i:i+50])).execute()
            for it in r.get("items", []):
                stats[it["id"]] = {"views": int(it["statistics"].get("viewCount", 0)),
                                   "likes": int(it["statistics"].get("likeCount", 0)),
                                   "published_at": it["snippet"]["publishedAt"]}
        except Exception as e:
            healthy = False; print("VID FAIL:", str(e)[:120])

published = []
for v in videos:
    s = stats.get(v["id"], {})
    published.append({**v, "url": f"https://youtu.be/{v['id']}",
                      "views": s.get("views", 0), "likes": s.get("likes", 0),
                      "published_at": s.get("published_at")})
published.sort(key=lambda x: x.get("published_at") or "", reverse=True)

total_views = sum(p["views"] for p in published)
today = now.date().isoformat()
today_count = sum(1 for p in published if (p.get("published_at") or "").startswith(today))

nxt = qd.get("next")
queue = qd.get("queue", [])
pipeline = qd.get("pipeline") or [
    {"key": "prepare", "label": "Veri", "state": "done", "detail": "web doğrulandı"},
    {"key": "render", "label": "Render", "state": "done", "detail": "Lambda"},
    {"key": "merge", "label": "QC", "state": "done", "detail": "kare montaj"},
    {"key": "publish", "label": "Yükle", "state": "done", "detail": "public"},
]

status = {
    "updated_at": now.isoformat(),
    "automation": {"healthy": healthy, "cron_label": "GitHub Actions · ~15 dk'da bir canlı tazeleme"},
    "channels": channels,
    "next": nxt,
    "queue": queue,
    "pipeline": pipeline,
    "stats": {"queue": len(queue), "today": today_count, "published": len(published),
              "total_views": total_views, "total_likes": sum(p["likes"] for p in published)},
    "published": published[:12],
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(status, open(OUT, "w"), ensure_ascii=False, indent=2)
print(f"OK {OUT} | healthy={healthy} | video={len(published)} | izlenme={total_views} | abone={[c.get('subs') for c in channels]}")
