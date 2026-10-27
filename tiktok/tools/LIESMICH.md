# Gedankentanken TikTok – Werkzeuge
1. Schriften holen (in tiktok/tools/fonts/): fraunces.ttf, fraunces_it.ttf, inter.ttf von
   raw.githubusercontent.com/google/fonts/main/ofl/ (Fraunces[SOFT,WONK,opsz,wght].ttf, Fraunces-Italic[...].ttf, inter/Inter[opsz,wght].ttf)
2. Neue Woche als JSON (Format wie tiktok/gedankentanken/reels.json, 5 Bildschirme, Caption) anlegen.
3. `python3 tiktok/tools/render.py <reels.json> <ausgabeordner> [id]` → MP4 mit eigener Musik (render.py sucht fonts/ und music.py neben sich).
4. Buffer (Zapier, Verbindung 02ed0124-320f-8c80-812e-493c38a5016d): organizationId 6ae0eb26f7270bc85e2aa986,
   channelId 6ae0ed4d2f1f5ed648ee4d04 (TikTok @gedankentanken39, Anzeigename pinsel89), method schedule,
   dynamic_properties {attachment: video, video: raw-URL, text: caption, scheduling_type: direct, scheduled_at}.
   Buffer-Gratis: max. 10 Posts in der Warteschlange.
