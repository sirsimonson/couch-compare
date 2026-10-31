#!/usr/bin/env python3
"""Export all validated couch results into app/data.json for the web UI."""
import json, os, csv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(BASE, "app")
os.makedirs(APP, exist_ok=True)
links = {x["id"]: x for x in json.load(open(os.path.join(BASE, "links.json"), encoding="utf-8"))}

KEYS = ["breite_265_285","tiefe_160_220","sitzhoehe_38_42","hoehe_68_75",
        "modultyp_longchair","platz_2_personen_110_130","ausstrecklaenge_140",
        "design_bodennah","unterfederung_nosag","polsterkern_hr","sitzgefuehl_weich",
        "farbe_salbei","bezug_weiche_haptik","budget_max_1500"]
LABEL = {
 "breite_265_285":"Breite 265–285 cm","tiefe_160_220":"Tiefe 160–220 cm",
 "sitzhoehe_38_42":"Sitzhöhe 38–42 cm","hoehe_68_75":"Höhe 68–75 cm",
 "modultyp_longchair":"Longchair XL","platz_2_personen_110_130":"Récamiere 110–130 cm",
 "ausstrecklaenge_140":"Ausstrecklänge ≥ 140 cm","design_bodennah":"Bodennahes Design",
 "unterfederung_nosag":"Wellen-/Nosagfederung","polsterkern_hr":"HR-Kaltschaum",
 "sitzgefuehl_weich":"Weiches Einsinken","farbe_salbei":"Salbeigrün",
 "bezug_weiche_haptik":"Weiche Haptik","budget_max_1500":"Budget ≤ 1.500 €"}
NONPRODUCT = {"015":"Polsterhocker – kein Sofa","023":"Bewertungsseite – kein Produkt","057":"Filter-Listing – kein Einzelprodukt"}
DUPLICATE = {"024":"018","045":"034","041":"037","049":"048"}

items = []
for lid, meta in links.items():
    p = os.path.join(BASE, "results", lid + ".json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    k = d["kriterien"]
    price = d.get("preis_eur")
    pts = sum(1.0 if k[x]=="erfüllt" else 0.5 if k[x]=="teilweise" else 0.0 for x in KEYS)
    score = round(pts/14*10, 1)
    if price is not None and price > 1500: score = min(score, 4.0)
    if k.get("modultyp_longchair") == "nicht": score = min(score, 3.0)
    if lid in NONPRODUCT: score = 0.0
    empfehlung = (score >= 6.5 and price is not None and price <= 1500
                  and k.get("farbe_salbei") in ("erfüllt","teilweise")
                  and k.get("breite_265_285") in ("erfüllt","teilweise")
                  and k.get("modultyp_longchair") in ("erfüllt","teilweise")
                  and lid not in NONPRODUCT)
    m = d.get("masse") or {}
    def num(v): return v if isinstance(v,(int,float)) else None
    items.append({
        "id": lid,
        "titel": d.get("titel") or meta["note"],
        "note": meta["note"],
        "preis": price,
        "segment": ("<1000" if price is not None and price < 1000 else
                    ">=1000<1500" if price is not None and price < 1500 else
                    ">1500" if price is not None else "unbekannt"),
        "link": d.get("link") or meta["url"],
        "haendler": d.get("haendler") or meta["retailer"],
        "hersteller": d.get("hersteller") or "unbekannt",
        "breite": num(m.get("breite_cm")), "tiefe": num(m.get("tiefe_cm")),
        "hoehe": num(m.get("hoehe_cm")), "sitzhoehe": num(m.get("sitzhoehe_cm")),
        "sitzflaeche": m.get("sitzflaeche") or "k. A.",
        "recamiere": num(m.get("recamiere_breite_cm")),
        "liegeflaeche": m.get("liegeflaeche") or "k. A.",
        "masse_text": d.get("masse_text") or "",
        "masse_korrekt": d.get("masse_korrekt") or "ungeprüft",
        "masse_begruendung": d.get("masse_begruendung") or "",
        "stoffe": d.get("stoffe_farben") or "k. A.",
        "salbei": bool(d.get("farbe_salbei_vorhanden")),
        "features": d.get("features") or [],
        "komfort": d.get("sitzkomfort_interpretation") or "k. A.",
        "feedback": d.get("kundenfeedback") or "keine Bewertungen gefunden",
        "kriterien": {x: k.get(x, "ungeprüft") for x in KEYS},
        "labels": LABEL,
        "erfuellt": [LABEL[x] for x in KEYS if k.get(x)=="erfüllt"],
        "teilweise": [LABEL[x] for x in KEYS if k.get(x)=="teilweise"],
        "nicht": [LABEL[x] for x in KEYS if k.get(x)=="nicht"],
        "ungeprueft": [LABEL[x] for x in KEYS if k.get(x)=="ungeprüft"],
        "score": score,
        "empfehlung": empfehlung,
        "nonproduct": NONPRODUCT.get(lid),
        "duplicate": DUPLICATE.get(lid),
        "fazit": d.get("fazit") or d.get("weitere_anmerkungen") or "",
        "anmerkungen": d.get("weitere_anmerkungen") or "",
        "quellen": d.get("quellen") or [meta["url"]],
    })

items.sort(key=lambda x: (-x["score"], x["preis"] if x["preis"] is not None else 1e9))
json.dump({"generated": "2026-10-31", "count": len(items), "items": items},
          open(os.path.join(APP, "data.json"), "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
print(f"exported {len(items)} items -> app/data.json")
