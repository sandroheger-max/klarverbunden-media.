"""Karussell-Folien 1080x1350 im Klarverbunden-Look rendern.
python carousel.py <inhalt.json> <ausgabeordner>   (TOOLS_DIR = Ordner mit fonts/)"""
import json, base64, sys, os, html
from playwright.sync_api import sync_playwright
T = os.environ.get("TOOLS_DIR", os.path.dirname(os.path.abspath(__file__)))
SRC, OUT = sys.argv[1], sys.argv[2]
HANDLE = os.environ.get("HANDLE", "@klarverbunden")
os.makedirs(OUT, exist_ok=True)
def b64(n): return base64.b64encode(open(f"{T}/fonts/{n}", "rb").read()).decode()
FONTS = ("@font-face{font-family:F;src:url(data:font/ttf;base64," + b64("fraunces.ttf") + ");font-weight:100 900}"
         "@font-face{font-family:FI;src:url(data:font/ttf;base64," + b64("fraunces_it.ttf") + ");font-style:italic;font-weight:100 900}"
         "@font-face{font-family:I;src:url(data:font/ttf;base64," + b64("inter.ttf") + ");font-weight:100 900}")
CSS = """*{margin:0;box-sizing:border-box}body{width:1080px;height:1350px;background:#14110f;overflow:hidden;position:relative}
.bg{position:absolute;inset:0;background:radial-gradient(circle at 85% 6%,#3a2a1a 0,rgba(58,42,26,.45) 28%,transparent 58%)}
.wrap{position:absolute;left:96px;right:96px;top:0;bottom:120px;display:flex;flex-direction:column;justify-content:center}
.kick{font:600 30px I;letter-spacing:.16em;color:#e8a04a;margin-bottom:34px}
h1{font:650 92px/1.08 F;color:#f3ebdd}
h2{font:600 70px/1.12 F;color:#f3ebdd}
.num{font:italic 400 170px/1 FI;color:#e8a04a;margin-bottom:26px}
.line{width:110px;height:4px;background:#e8a04a;margin:44px 0 40px}
p{font:400 38px/1.5 I;color:rgba(243,235,221,.82)}
.acc{color:#e8a04a;margin-top:36px}
.foot{position:absolute;left:96px;right:96px;bottom:64px;display:flex;justify-content:space-between;font:500 28px I;color:rgba(243,235,221,.5)}
.foot b{font-weight:600;color:#e8a04a}"""
def doc(inner, foot_r):
    return (f"<html><head><style>{FONTS}{CSS}</style></head><body><div class='bg'></div><div class='wrap'>{inner}</div>"
            f"<div class='foot'><span>{HANDLE}</span>{foot_r}</div></body></html>")
e = html.escape
data = json.load(open(SRC))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1350})
    for c in data["carousels"]:
        n = len(c["slides"]) + 2
        pages = [doc(f"<div class='kick'>{e(c['kicker'])}</div><h1>{e(c['title'])}</h1><div class='line'></div><p>{e(c['sub'])}</p>",
                     "<b>wischen →</b>")]
        for i, (h, t) in enumerate(c["slides"], 1):
            pages.append(doc(f"<div class='num'>{i}</div><h2>{e(h)}</h2><div class='line' style='margin:36px 0 34px'></div><p>{e(t)}</p>", f"<span>{i+1}/{n}</span>"))
        pages.append(doc(f"<div class='kick'>{e(HANDLE.lstrip('@').upper())}</div><h1>{e(c['cta'][0])}</h1><div class='line'></div><p>{e(c['cta'][1])}</p>"
                         f"<p class='acc'>Folge {e(HANDLE)} für mehr.</p>", f"<span>{n}/{n}</span>"))
        for k, h in enumerate(pages, 1):
            pg.set_content(h); pg.evaluate("document.fonts.ready.then(()=>1)")
            assert pg.evaluate("document.fonts.check('650 92px F')"), "Fraunces nicht geladen"
            pg.screenshot(path=f"{OUT}/{c['id']}_{k:02d}.jpg", type="jpeg", quality=92)
        print("ok", c["id"], n)
    b.close()
