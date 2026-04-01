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

def debug_html(html, label):
    """Gibt die ersten 3000 Zeichen des reinen Texts und alle Tabellen-Inhalte aus."""
    soup = BeautifulSoup(html, "lxml")
    print(f"\n=== DEBUG {label} ===")
    print("--- Rohtext (erste 2000 Zeichen) ---")
    print(soup.get_text(" ", strip=True)[:2000])
    print(f"\n--- Anzahl Tabellen: {len(soup.find_all('table'))} ---")
    for i, tbl in enumerate(soup.find_all("table")):
        rows = tbl.find_all("tr")
        print(f"\nTabelle {i+1} ({len(rows)} Zeilen):")
        for row in rows[:10]:  # max 10 Zeilen pro Tabelle
            cells = [td.get_text(strip=True) for td in row.find_all(["td","th"])]
            if any(cells):
                print(f"  {cells}")
    print("=== ENDE DEBUG ===\n")

# Hauptseite laden und debuggen
print("Lade index.html...")
html = fetch(BASE + "index.html")
debug_html(html, "index.html")
