import requests, json, re
from datetime import datetime, timezone
from bs4 import BeautifulSoup

BASE = "https://wahlergebnisse.komm.one/24/produktion/8425020/999-1337/20301224/buergermeisterwahl_gemeinde/"

BEZIRKE = [
    {"url": "ergebnisse_stimmbezirk_08425020-001.html", "name": "001 Rathaus, Karlstraße 2",            "nr": "001", "ort": "Blaubeuren", "adresse": "Karlstraße 2"},
    {"url": "ergebnisse_stimmbezirk_08425020-002.html", "name": "002 Johannes-Montini-Haus, Karlstraße 53", "nr": "002", "ort": "Blaubeuren", "adresse": "Karlstraße 53"},
    {"url": "ergebnisse_stimmbezirk_08425020-003.html", "name": "003 Johannes-Montini-Haus ZVU, Karlstraße 53", "nr": "003", "ort": "Blaubeuren", "adresse": "Karlstraße 53"},
    {"url": "ergebnisse_stimmbezirk_08425020-004.html", "name": "004 Gemeindehaus Gerhausen, Schulstraße 26", "nr": "004", "ort": "Gerhausen",  "adresse": "Schulstraße 26"},
    {"url": "ergebnisse_stimmbezirk_08425020-005.html", "name": "005 Karl-Spohn-Realschule, Helfensteinerstrasse 12", "nr": "005", "ort": "Blaubeuren", "adresse": "Helfensteinerstrasse 12"},
    {"url": "ergebnisse_stimmbezirk_08425020-006.html", "name": "006 Rathaus Asch, Bei der Hüle 1",       "nr": "006", "ort": "Asch",       "adresse": "Bei der Hüle 1"},
    {"url": "ergebnisse_stimmbezirk_08425020-007.html", "name": "007 Proberaum Musikverein Beiningen, Im Eichert 3", "nr": "007", "ort": "Beiningen",  "adresse": "Im Eichert 3"},
    {"url": "ergebnisse_stimmbezirk_08425020-008.html", "name": "008 Feuerwehrgerätehaus Pappelau, Ehemalige Molke, Römerstraße 22", "nr": "008", "ort": "Pappelau",   "adresse": "Römerstraße 22"},
    {"url": "ergebnisse_stimmbezirk_08425020-009.html", "name": "009 Fr. Schulhaus Erstetten, Schleichtalstraße 32", "nr": "009", "ort": "Erstetten",  "adresse": "Schleichtalstraße 32"},
    {"url": "ergebnisse_stimmbezirk_08425020-010.html", "name": "010 Zehntscheuer Seißen, Albstraße 74", "nr": "010", "ort": "Seißen",     "adresse": "Albstraße 74"},
    {"url": "ergebnisse_stimmbezirk_08425020-011.html", "name": "011 Dorfgemeinschaftshaus Sonderbuch, Blaubeurer Str. 12", "nr": "011", "ort": "Sonderbuch", "adresse": "Blaubeurer Str. 12"},
    {"url": "ergebnisse_stimmbezirk_08425020-012.html", "name": "012 altes Schulhaus Weiler, Siedlungsstraße 1", "nr": "012", "ort": "Weiler",     "adresse": "Siedlungsstraße 1"},
    {"url": "ergebnisse_stimmbezirk_08425020-013.html", "name": "013 Grundschule Blaubeuren, Alberstraße 3", "nr": "013", "ort": "Blaubeuren", "adresse": "Alberstraße 3"},
    {"url": "ergebnisse_stimmbezirk_08425020-014.html", "name": "014 Mehrzweckhalle Seißen, Flurstraße 55", "nr": "014", "ort": "Seißen",     "adresse": "Flurstraße 55"},
    {"url": "ergebnisse_briefwahlbezirk_08425020-999-1.html", "name": "Briefwahl 1", "nr": "BW1", "ort": "Briefwahl", "adresse": "-"},
    {"url": "ergebnisse_briefwahlbezirk_08425020-999-2.html", "name": "Briefwahl 2", "nr": "BW2", "ort": "Briefwahl", "adresse": "-"},
    {"url": "ergebnisse_briefwahlbezirk_08425020-999-3.html", "name": "Briefwahl 3", "nr": "BW3", "ort": "Briefwahl", "adresse": "-"},
    {"url": "ergebnisse_briefwahlbezirk_08425020-999-4.html", "name": "Briefwahl 4", "nr": "BW4", "ort": "Briefwahl", "adresse": "-"},
]

# Erlaubte Bezirknamen – verhindert dass "Blaubeuren, Stadt" als Bezirk erkannt wird
BEZIRK_NAMEN = {bk["name"] for bk in BEZIRKE}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; WahlBot/1.0)"}

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text

def parse_kandidaten(html):
    """Kandidaten, Statistik und ausgezaehlte Bezirke aus einer Seite lesen."""
    soup = BeautifulSoup(html, "lxml")
    full = soup.get_text(" ", strip=True)

    # Beteiligung aus Fliesstext
    m = re.search(r"Wahlbeteiligung[^\d]*([\d,]+)\s*%", full)
    beteiligung = m.group(1).replace(",", ".") + " %" if m else "-"

    stats = {"beteiligung": beteiligung, "berechtigt": 0, "waehler": 0, "ungueltig": 0}
    candidates = []
    counted_map = {}

    SKIP_NAMES = {"Direktkandidat/in", "Stichwahlteilnehmer/in", "Gültige Stimmen", ""}

    for table in soup.find_all("table"):
        cands_in_table = []
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue

            # Auszählungsstand: Link + letzte Zelle = Uhrzeit?
            link = tds[0].find("a")
            if link:
                bname = link.get_text(strip=True)
                last  = tds[-1].get_text(strip=True)
                # Nur echte Bezirke aufnehmen (nicht "Blaubeuren, Stadt")
                if re.match(r"^\d{2}:\d{2}$", last) and bname in BEZIRK_NAMEN:
                    counted_map[bname] = last
                    print(f"    Erkannt als ausgezaehlt: {bname} um {last}")

            name = tds[0].get_text(strip=True)
            if not name or name in SKIP_NAMES:
                continue

            raw = re.sub(r"\D", "", tds[1].get_text(strip=True))
            if not raw:
                continue
            val = int(raw)

            if name == "Wahlberechtigte":   stats["berechtigt"] = val; continue
            if name == "Wählende":          stats["waehler"]    = val; continue
            if name == "Ungültige Stimmen": stats["ungueltig"]  = val; continue

            if len(tds) < 3:
                continue
            m2 = re.search(r"([\d]+[,.][\d]+)", tds[2].get_text(strip=True))
            if not m2:
                continue
            try:
                pct = round(float(m2.group(1).replace(",", ".")), 1)
            except:
                continue
            if pct <= 0:
                continue

            parts = name.split(",", 1)
            cands_in_table.append({
                "name":    parts[0].strip(),
                "vorname": parts[1].strip() if len(parts) > 1 else "",
                "stimmen": val,
                "anteil":  pct
            })

        if len(cands_in_table) > len(candidates):
            candidates = cands_in_table

    return sorted(candidates, key=lambda x: -x["anteil"]), stats, counted_map


# ── Hauptseite laden (index.html hat alle Daten statisch) ──
print("Lade index.html...")
html = fetch(BASE + "index.html")

soup_main = BeautifulSoup(html, "lxml")
full_text = soup_main.get_text(" ", strip=True)

# Datum
datum = ""
m = re.search(r"(\d{1,2}\.\s+\w+\s+\d{4})", full_text)
if m:
    datum = m.group(1)

# Ausgezaehlt / Gesamt
ausgezaehlt, gesamt = 0, 18
m = re.search(r"Ausgez[^:]*:\s*(\d+)\s+von\s+(\d+)", full_text)
if m:
    ausgezaehlt, gesamt = int(m.group(1)), int(m.group(2))

print(f"  Datum:      {datum}")
print(f"  Ausgezählt: {ausgezaehlt}/{gesamt}")

# Kandidaten + Stats + counted aus index.html
global_cands, global_stats, counted_map = parse_kandidaten(html)

print(f"  Kandidaten: {[c['name'] for c in global_cands]}")
print(f"  Beteiligung:{global_stats['beteiligung']}")
print(f"  Berechtigt: {global_stats['berechtigt']}")
print(f"  Counted:    {list(counted_map.keys())}")

# Falls index.html keine Kandidaten liefert, ergebnisse.html versuchen
if not global_cands:
    print("  -> Keine Kandidaten in index.html, versuche ergebnisse.html...")
    html2 = fetch(BASE + "ergebnisse.html")
    global_cands, global_stats2, counted_map2 = parse_kandidaten(html2)
    # Stats und counted_map zusammenfuehren
    for k, v in counted_map2.items():
        counted_map[k] = v
    if not global_stats["berechtigt"] and global_stats2["berechtigt"]:
        global_stats = global_stats2
    print(f"  Kandidaten nach Fallback: {[c['name'] for c in global_cands]}")

# ── Einzelne Bezirke laden ──────────────────────────────────
result_bezirke = []
for bk in BEZIRKE:
    is_counted = bk["name"] in counted_map
    entry = {
        **bk,
        "counted":    is_counted,
        "time":       counted_map.get(bk["name"]),
        "candidates": [],
        "beteiligung": "-",
        "waehler":    0,
        "berechtigt": 0,
        "ungueltig":  0,
    }
    if is_counted:
        print(f"  Lade Bezirk: {bk['name']}")
        try:
            bk_html = fetch(BASE + bk["url"])
            cands, bk_stats, _ = parse_kandidaten(bk_html)
            entry.update({
                "candidates":  cands,
                "beteiligung": bk_stats["beteiligung"],
                "waehler":     bk_stats["waehler"],
                "berechtigt":  bk_stats["berechtigt"],
                "ungueltig":   bk_stats["ungueltig"],
            })
            print(f"    OK: {len(cands)} Kandidaten, Beteiligung {bk_stats['beteiligung']}")
        except Exception as e:
            print(f"    FEHLER: {e}")
    result_bezirke.append(entry)

# ── JSON schreiben ──────────────────────────────────────────
output = {
    "datum":            datum,
    "ausgezaehlt":      ausgezaehlt,
    "gesamt":           gesamt,
    "globalCandidates": global_cands,
    "globalStats":      global_stats,
    "bezirke":          result_bezirke,
    "fetchedAt":        datetime.now(timezone.utc).isoformat()
}

with open("daten.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nFertig! {ausgezaehlt}/{gesamt} Bezirke, {len(global_cands)} Kandidaten.")
