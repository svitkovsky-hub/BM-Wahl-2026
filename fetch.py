import requests, json, re
from datetime import datetime, timezone
from bs4 import BeautifulSoup

BASE = "https://wahlergebnisse.komm.one/24/produktion/8425020/999-1337/20301224/buergermeisterwahl_gemeinde/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; WahlBot/1.0)"}

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
BEZIRK_NAMEN = {bk["name"] for bk in BEZIRKE}

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text

def clean(s):
    return s.replace("\xa0", " ").strip()

def parse_zahl(s):
    raw = re.sub(r"\D", "", clean(s))
    return int(raw) if raw else None

def parse_pct(s):
    m = re.search(r"(\d+[,.]?\d*)", clean(s))
    if not m:
        return None
    try:
        return round(float(m.group(1).replace(",", ".")), 1)
    except:
        return None

def parse_seite(html, label=""):
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")

    print(f"\n  [DEBUG {label}] {len(tables)} Tabellen gefunden")
    for i, tbl in enumerate(tables):
        rows = tbl.find_all("tr")
        header = [clean(td.get_text()) for td in rows[0].find_all(["th","td"])] if rows else []
        print(f"  Tabelle {i+1} Header: {header}")
        for row in rows[1:6]:
            cells = [clean(td.get_text()) for td in row.find_all("td")]
            if any(cells):
                print(f"    Zeile: {cells}")

    stats = {"beteiligung": "-", "berechtigt": 0, "waehler": 0, "ungueltig": 0}
    candidates = []
    counted_map = {}

    for tbl in tables:
        rows = tbl.find_all("tr")
        if not rows:
            continue
        header = [clean(td.get_text()) for td in rows[0].find_all(["th","td"])]

        # Ergebnistabelle
        if header and header[0] in ("Direktkandidat/in", "Stichwahlteilnehmer/in"):
            print(f"  -> Ergebnistabelle erkannt (Header[0]='{header[0]}')")
            for row in rows[1:]:
                tds = row.find_all("td")
                if len(tds) < 2:
                    continue
                name = clean(tds[0].get_text())
                val  = parse_zahl(tds[1].get_text())
                if val is None:
                    continue
                if name == "Wahlberechtigte":
                    stats["berechtigt"] = val
                elif name == "Wählende":
                    stats["waehler"] = val
                    pct = parse_pct(tds[2].get_text()) if len(tds) >= 3 else None
                    if pct:
                        stats["beteiligung"] = str(pct).replace(".", ",") + " %"
                elif name == "Ungültige Stimmen":
                    stats["ungueltig"] = val
                elif name and name not in ("Gültige Stimmen", ""):
                    pct = parse_pct(tds[2].get_text()) if len(tds) >= 3 else None
                    if pct and pct > 0:
                        parts = name.split(",", 1)
                        candidates.append({
                            "name":    parts[0].strip(),
                            "vorname": parts[1].strip() if len(parts) > 1 else "",
                            "stimmen": val,
                            "anteil":  pct
                        })
                        print(f"    Kandidat: {parts[0].strip()} {val} St. {pct}%")

        # Auszählungsstand-Tabelle
        elif len(header) >= 3 and "Auszählungsstand" in (header[1] if len(header) > 1 else ""):
            print(f"  -> Auszählungstabelle erkannt")
            for row in rows[1:]:
                tds = row.find_all("td")
                if len(tds) < 3:
                    continue
                link = tds[0].find("a")
                name  = clean(link.get_text() if link else tds[0].get_text())
                stand = clean(tds[1].get_text())
                zeit  = clean(tds[2].get_text())
                if name in BEZIRK_NAMEN and stand.startswith("1 von"):
                    counted_map[name] = zeit if zeit else "?"
                    print(f"    Ausgezählt: {name} um {zeit or '?'}")

    candidates.sort(key=lambda x: -x["anteil"])
    return candidates, stats, counted_map


# ── Hauptseite ──────────────────────────────────────────────
print("Lade index.html...")
html = fetch(BASE + "index.html")
soup = BeautifulSoup(html, "lxml")
full = soup.get_text(" ", strip=True)

datum = ""
m = re.search(r"(\d{1,2}\.\s+\w+\s+\d{4})", full)
if m:
    datum = m.group(1)

ausgezaehlt, gesamt = 0, 18
m = re.search(r"Ausgez[^:]*:\s*(\d+)\s+von\s+(\d+)", full)
if m:
    ausgezaehlt, gesamt = int(m.group(1)), int(m.group(2))

global_cands, global_stats, counted_map = parse_seite(html, "index.html")

print(f"\n  Datum:      {datum}")
print(f"  Ausgezählt: {ausgezaehlt}/{gesamt}")
print(f"  Kandidaten: {[c['name'] for c in global_cands]}")
print(f"  Beteiligung:{global_stats['beteiligung']}")
print(f"  Berechtigt: {global_stats['berechtigt']}")
print(f"  Counted:    {list(counted_map.keys())}")

# ── Einzelne Bezirke ────────────────────────────────────────
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
        print(f"\n  Lade Bezirk: {bk['name']}")
        try:
            bk_html = fetch(BASE + bk["url"])
            cands, bk_stats, _ = parse_seite(bk_html, bk["nr"])
            entry.update({
                "candidates":  cands,
                "beteiligung": bk_stats["beteiligung"],
                "waehler":     bk_stats["waehler"],
                "berechtigt":  bk_stats["berechtigt"],
                "ungueltig":   bk_stats["ungueltig"],
            })
            print(f"  -> OK: {len(cands)} Kandidaten, Beteiligung {bk_stats['beteiligung']}")
        except Exception as e:
            print(f"  -> FEHLER: {e}")
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
