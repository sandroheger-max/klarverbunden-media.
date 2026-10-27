# Gedankentanken TikTok – Werkzeuge
1. Schriften holen (in tiktok/tools/fonts/): fraunces.ttf, fraunces_it.ttf, inter.ttf von
   raw.githubusercontent.com/google/fonts/main/ofl/ (Fraunces[SOFT,WONK,opsz,wght].ttf, Fraunces-Italic[...].ttf, inter/Inter[opsz,wght].ttf)
2. Neue Woche als JSON (Format wie tiktok/gedankentanken/reels.json, 5 Bildschirme, Caption) anlegen.
3. `python3 tiktok/tools/render.py <reels.json> <ausgabeordner> [id]` → MP4 mit eigener Musik (render.py sucht fonts/ und music.py neben sich).
4. Buffer (Zapier, Verbindung 02ed0124-320f-8c80-812e-493c38a5016d): organizationId 6ae0eb26f7270bc85e2aa986,
   channelId 6ae0ed4d2f1f5ed648ee4d04 (TikTok @gedankentanken39, Anzeigename pinsel89), method schedule,
   dynamic_properties {attachment: video, video: raw-URL, text: caption, scheduling_type: direct, scheduled_at}.
   Buffer-Gratis: max. 10 Posts in der Warteschlange.

## Neu (27.10.2026)
- Posten läuft ohne Zapier: `.github/workflows/buffer.yml` + `.github/scripts/buffer_queue.py` (Secret BUFFER_API_KEY in GitHub).
  Täglich 06:23 UTC und bei jedem Push von plan.json / plan_tiktok.json: alle "geplant"-Einträge bis 5 Tage im Voraus → Buffer → status "in_buffer".
  Kanäle: TikTok @gedankentanken39 6ae0ed4d2f1f5ed648ee4d04, Instagram @klarverbunden 6ae0fd9d2f1f5ed648efa671.
  Manuell: Actions → «Buffer einplanen» → modus check/queue, tage, nur_id.
- Karussells: `TOOLS_DIR=tiktok/tools python3 tiktok/tools/carousel.py w2/inhalt.json w2` (HANDLE=@klarverbunden Standard).
- Reels: `HANDLE=@klarverbunden KICK=KLARVERBUNDEN SEED_OFFSET=20 python3 tiktok/tools/render.py w2/inhalt.json <ordner>` (TikTok: ohne HANDLE/KICK).
- WOCHENAUFGABE.md ist veraltet: die Wochenaufgabe «Klarverbunden + Gedankentanken Wochen-Inhalte» (So 16:43) macht beides.
