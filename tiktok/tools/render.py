import json, base64, sys, os, subprocess, html
from playwright.sync_api import sync_playwright
S = os.path.dirname(os.path.abspath(__file__))
REELS, OUT = sys.argv[1], sys.argv[2]
only = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
def b64(n): return base64.b64encode(open(f"{S}/fonts/{n}", "rb").read()).decode()
FONTS = ("@font-face{font-family:F;src:url(data:font/ttf;base64," + b64("fraunces.ttf") + ");font-weight:100 900}"
         "@font-face{font-family:FI;src:url(data:font/ttf;base64," + b64("fraunces_it.ttf") + ");font-style:italic;font-weight:100 900}"
         "@font-face{font-family:I;src:url(data:font/ttf;base64," + b64("inter.ttf") + ");font-weight:100 900}")
CSS = """*{margin:0;box-sizing:border-box}body{width:1080px;height:1920px;background:#14110f;overflow:hidden}
.bg{position:absolute;inset:0;background:radial-gradient(circle at 85% 8%,#3a2a1a 0,rgba(58,42,26,.45) 30%,transparent 60%)}
.wrap{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:0 110px}
.kick{position:absolute;top:300px;left:110px;font:600 30px I;letter-spacing:.32em;color:#e8a04a}
.t{font-family:FI;font-style:italic;font-weight:420;font-size:84px;line-height:1.22;color:#f3ebdd;white-space:pre-line}
.hook .t{font-family:F;font-style:normal;font-weight:650;font-size:96px;line-height:1.12}
.last .t{color:#e8a04a}
.line{width:120px;height:4px;background:#e8a04a;margin-top:56px}
.foot{position:absolute;bottom:330px;left:0;right:0;text-align:center;font:500 32px I;color:rgba(243,235,221,.55);letter-spacing:.04em}
.dots{position:absolute;bottom:260px;left:0;right:0;display:flex;justify-content:center;gap:14px}
.dots i{width:12px;height:12px;border-radius:50%;background:rgba(243,235,221,.25)}.dots i.on{background:#e8a04a}"""
def page(text, i, n):
    cls = "hook" if i == 0 else ("last" if i == n - 1 else "")
    dots = "".join(f'<i class="{"on" if k == i else ""}"></i>' for k in range(n))
    line = '<div class="line"></div>' if i == 0 else ""
    return (f"<html><head><style>{FONTS}{CSS}</style></head><body class='{cls}'><div class='bg'></div>"
            f"<div class='kick'>GEDANKENTANKEN</div><div class='wrap'><div class='t'>{html.escape(text)}</div>{line}</div>"
            f"<div class='dots'>{dots}</div><div class='foot'>@gedankentanken39</div></body></html>")
reels = json.load(open(REELS))
SEC, X = 2.8, 0.4
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    for r in reels:
        if only and r["id"] != only: continue
        d = f"{OUT}/{r['id']}"; os.makedirs(d, exist_ok=True)
        n = len(r["screens"])
        for i, t in enumerate(r["screens"]):
            pg.set_content(page(t, i, n)); pg.evaluate("document.fonts.ready.then(()=>1)")
            ok = pg.evaluate("document.fonts.check('650 96px F')" if i == 0 else "document.fonts.check('italic 84px FI')")
            assert ok, pg.evaluate("[...document.fonts].map(f=>f.family+f.style+f.weight+f.status).join(',')")
            pg.screenshot(path=f"{d}/s{i}.png")
    b.close()
for idx, r in enumerate(reels):
    if only and r["id"] != only: continue
    d = f"{OUT}/{r['id']}"; n = len(r["screens"])
    fr = int(SEC * 30)
    ins, flt = [], []
    for i in range(n):
        ins += ["-loop", "1", "-t", str(SEC), "-i", f"{d}/s{i}.png"]
        flt.append(f"[{i}:v]scale=2160:3840,zoompan=z='1+0.0005*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s=1080x1920:fps=30,setsar=1,format=yuv420p[v{i}]")
    prev = "v0"
    for i in range(1, n):
        off = round(i * (SEC - X), 2)
        flt.append(f"[{prev}][v{i}]xfade=transition=fade:duration={X}:offset={off}[x{i}]"); prev = f"x{i}"
    dur = n * SEC - (n - 1) * X
    wav = f"{d}/music.wav"
    subprocess.run(["python3", "-I", f"{S}/music.py", wav, str(idx + int(os.environ.get("SEED_OFFSET", "0"))), str([0, 2, -3, 5, -2, 3, 0][(idx + int(os.environ.get("SEED_OFFSET", "0"))) % 7]), str(dur)], check=True)
    ins += ["-i", wav]
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ins, "-filter_complex", ";".join(flt),
                    "-map", f"[{prev}]", "-map", f"{n}:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"{OUT}/{r['id']}.mp4"], check=True)
    print("ok", r["id"], dur)
