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
# TikTok: 4 Videos pro Tag, Buffer-Gratis max. 10 pro Kanal -> nur 2 Tage im Voraus (max. 8)
TIKTOK_WINDOW_DAYS = min(WINDOW_DAYS, int(os.environ.get("TIKTOK_WINDOW_DAYS", "2")))
# Plan-Datei -> Umgebungsvariable mit der Buffer-Kanal-ID
PLANS = {
    "tiktok/gedankentanken/plan_tiktok.json": os.environ.get("BUFFER_TIKTOK_CHANNEL", "6ae0ed4d2f1f5ed648ee4d04"),  # TikTok @pinsel89
    "plan.json": os.environ.get("BUFFER_IG_CHANNEL", "6ae0fd9d2f1f5ed648efa671"),  # Instagram @klarverbunden
}


def build_input(e, channel):
    """TikTok-Plan: Feld "video". Instagram-Plan: "type" carousel/reel und Liste "media"."""
    inp = {"text": e["caption"], "channelId": channel, "schedulingType": "automatic", "mode": "customScheduled"}
    if "video" in e:
        inp["assets"] = [{"video": {"url": e["video"], "metadata": {"thumbnailOffset": 500}}}]
    elif e.get("type") == "reel":
        inp["assets"] = [{"video": {"url": e["media"][0], "metadata": {"thumbnailOffset": 500}}}]
        inp["metadata"] = {"instagram": {"type": "reel", "shouldShareToFeed": True}}
    else:
        inp["assets"] = [{"image": {"url": u}} for u in e["media"]]
        inp["metadata"] = {"instagram": {"type": "post", "shouldShareToFeed": True}}
    return inp


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


def queue(only=None):
    now = datetime.now(timezone.utc)
    failed = 0
    for path, channel in PLANS.items():
        changed = False
        if not os.path.exists(path):
            continue
        plan = json.load(open(path, encoding="utf-8"))
        for e in plan:
            if only and e["id"] != only:
                continue
            if e.get("status") != "geplant" or not e.get("when_zurich"):
                continue
            due = datetime.fromisoformat(e["when_zurich"]).replace(tzinfo=ZH).astimezone(timezone.utc)
            if due <= now:
                print(f"übersprungen (Zeit vorbei): {e['id']}")
                continue
            window = TIKTOK_WINDOW_DAYS if "tiktok" in path else WINDOW_DAYS
            if due > now + timedelta(days=window):
                continue  # später einplanen (Buffer-Gratis: max. 10 in der Warteschlange)
            inp = build_input(e, channel)
            inp["dueAt"] = due.strftime("%Y-%m-%dT%H:%M:%S.000Z")
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


TIKTOK_CH = PLANS["tiktok/gedankentanken/plan_tiktok.json"]


def _type(name):
    q = """query($n: String!) { __type(name: $n) { fields { name args { name type { name kind ofType { name kind ofType { name } } } }
      type { name kind ofType { name kind ofType { name kind } } } } inputFields { name type { name kind ofType { name } } } } }"""
    return gql(q, {"n": name})["__type"]


def diagnose():
    """Zeigt, mit welchem Profil der TikTok-Kanal verbunden ist (nur Namensfelder)."""
    ch = _type("Channel") or {}
    keep = [f["name"] for f in ch.get("fields", []) if not f["args"]
            and any(k in f["name"].lower() for k in ("name", "service", "handle", "user", "type", "locked", "disconnected"))
            and (f["type"]["kind"] == "SCALAR" or (f["type"].get("ofType") or {}).get("kind") in ("SCALAR", "ENUM") or f["type"]["kind"] == "ENUM")]
    print("Channel-Felder:", keep)
    d = gql("query($i: ChannelId!) { channel(input: {id: $i}) { %s } }" % " ".join(keep), {"i": TIKTOK_CH})
    print(json.dumps(d, indent=1, ensure_ascii=False))


def tiktok_stop():
    """Löscht künftige, schon in Buffer eingeplante TikTok-Beiträge und setzt sie auf vorrat."""
    m = next(f for f in _type("Mutation")["fields"] if f["name"] == "deletePost")
    arg = m["args"][0]
    tname = arg["type"].get("name") or (arg["type"].get("ofType") or {}).get("name")
    print("deletePost-Argument:", arg["name"], tname)
    if arg["name"] == "input":
        fields = [x["name"] for x in (_type(tname).get("inputFields") or [])]
        print("Input-Felder:", fields)
        mk = lambda pid: {"input": {"id": pid}}
        sig = "mutation($input: %s!) { deletePost(input: $input) { __typename ... on MutationError { message } } }" % tname
    else:
        mk = lambda pid: {"id": pid}
        sig = "mutation($id: %s!) { deletePost(id: $id) { __typename ... on MutationError { message } } }" % tname
    path = "tiktok/gedankentanken/plan_tiktok.json"
    plan = json.load(open(path, encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for e in plan:
        if e.get("status") != "in_buffer" or not e.get("buffer_post_id"):
            continue
        due = datetime.fromisoformat(e["when_zurich"]).replace(tzinfo=ZH).astimezone(timezone.utc)
        if due <= now:
            continue
        try:
            r = gql(sig, mk(e["buffer_post_id"]))["deletePost"]
        except RuntimeError as err:
            print("FEHLER", e["id"], err); continue
        print("aus Buffer entfernt:", e["id"], r)
        if "message" not in r:
            e["status"] = "vorrat"; e.pop("buffer_post_id", None)
    json.dump(plan, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if not KEY:
        raise SystemExit("Secret BUFFER_API_KEY fehlt")
    mode = sys.argv[1] if len(sys.argv) > 1 else "queue"
    if mode == "check":
        check()
    elif mode == "diagnose":
        diagnose()
    elif mode == "tiktok_stop":
        tiktok_stop()
    else:
        queue(os.environ.get("NUR_ID") or None)
