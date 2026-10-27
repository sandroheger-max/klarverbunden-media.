"""Plant Einträge mit status "geplant" aus den Plan-Dateien in Buffer ein (Buffer GraphQL API).
Ohne Zapier. Läuft in GitHub Actions mit dem Secret BUFFER_API_KEY.
Modus: python buffer_queue.py check   -> zeigt Konto, Organisationen und Kanäle (Test)
       python buffer_queue.py queue   -> plant ein und markiert die Einträge mit "in_buffer"
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

API = "https://api.buffer.com"
KEY = os.environ.get("BUFFER_API_KEY", "")
ZH = ZoneInfo("Europe/Zurich")
WINDOW_DAYS = int(os.environ.get("WINDOW_DAYS", "5"))
# Plan-Datei -> Umgebungsvariable mit der Buffer-Kanal-ID
PLANS = {
    "tiktok/gedankentanken/plan_tiktok.json": os.environ.get("BUFFER_TIKTOK_CHANNEL", "6ae0ed4d2f1f5ed648ee4d04"),
}


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:800]}")
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False)[:1500])
    return data["data"]


def check():
    d = gql("query { account { id organizations { id name } } }")
    print("Verbindung ok, Organisationen:", len(d["account"]["organizations"]))
    for org in d["account"]["organizations"]:
        c = gql("query($o: OrganizationId!) { channels(input: {organizationId: $o}) { id name service } }", {"o": org["id"]})
        print(json.dumps(c, indent=1, ensure_ascii=False))


MUT = """mutation($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id dueAt } }
    ... on MutationError { message }
  }
}"""


def queue():
    now = datetime.now(timezone.utc)
    changed, failed = False, 0
    for path, channel in PLANS.items():
        if not os.path.exists(path):
            continue
        plan = json.load(open(path, encoding="utf-8"))
        for e in plan:
            if e.get("status") != "geplant" or not e.get("when_zurich"):
                continue
            due = datetime.fromisoformat(e["when_zurich"]).replace(tzinfo=ZH).astimezone(timezone.utc)
            if due <= now:
                print(f"übersprungen (Zeit vorbei): {e['id']}")
                continue
            if due > now + timedelta(days=WINDOW_DAYS):
                continue  # später einplanen (Buffer-Gratis: max. 10 in der Warteschlange)
            inp = {"text": e["caption"], "channelId": channel, "schedulingType": "automatic",
                   "mode": "customScheduled", "dueAt": due.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                   "assets": [{"video": {"url": e["video"], "metadata": {"thumbnailOffset": 500}}}]}
            try:
                res = gql(MUT, {"input": inp})["createPost"]
            except RuntimeError as err:
                print(f"FEHLER {e['id']}: {err}"); failed += 1; continue
            if "post" in res and res["post"]:
                e["status"], e["buffer_post_id"] = "in_buffer", res["post"]["id"]
                changed = True
                print(f"eingeplant: {e['id']} -> {res['post']['dueAt']}")
            else:
                print(f"FEHLER {e['id']}: {res.get('message')}"); failed += 1
        if changed:
            json.dump(plan, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    if not KEY:
        raise SystemExit("Secret BUFFER_API_KEY fehlt")
    {"check": check, "queue": queue}[sys.argv[1] if len(sys.argv) > 1 else "queue"]()
