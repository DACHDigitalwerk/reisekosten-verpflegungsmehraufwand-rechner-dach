# DACH Reisekosten-, Verpflegungsmehraufwand- & Pendlerpauschalen-Rechner 2026 (DE, AT, CH)

[![Python Tests](https://github.com/DACHDigitalwerk/reisekosten-verpflegungsmehraufwand-rechner-dach/actions/workflows/python-tests.yml/badge.svg)](https://github.com/DACHDigitalwerk/reisekosten-verpflegungsmehraufwand-rechner-dach/actions)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rechtsstand](https://img.shields.io/badge/Rechtsstand-BMF%202026%20%7C%20EStG-emerald.svg)](https://dach-digitalwerk.netlify.app/reisekosten-verpflegungsmehraufwand/)

> **Online-Rechner & DIN-A4 Abrechnungs-Generator:**  
> Nutzen Sie unser kostenloses, 100 % client-side Browser-Tool zur sofortigen Erstellung prüffähiger Reisekostenabrechnungen:  
> 👉 **[DACH Reisekosten- & Spesenrechner 2026 starten](https://dach-digitalwerk.netlify.app/reisekosten-verpflegungsmehraufwand/)**

---

## 📌 Übersicht & Features

Dieses Repository bietet eine Python-Bibliothek und das CLI-Tool `dach-spesen` zur standardisierten Berechnung von:
- **Verpflegungsmehraufwendungen 2026** nach BMF-Schreiben & § 9 Abs. 4a EStG (Deutschland).
- **Mahlzeitenkürzungen** (Frühstück -20 %, Mittag- & Abendessen je -40 %) mit gesetzlicher Null-Euro-Deckelung.
- **Tagesgeldern & Nächtigungsgeldern** nach § 26 Z 4 EStG (Österreich) mit Stunden-Aliquotierung (2,50 €/h).
- **Spesenansätzen & Mahlzeitenpauschalen** nach eidgenössischer und kantonaler Spesenpraxis (Schweiz: 35 / 70 CHF).
- **Amtlichem Kilometergeld** für Pkw, Motorrad und Fahrrad.
- **Pendlerpauschalen (Entfernungspauschale 2026)** mit zweistufiger Staffel (0,30 € bis 20 km, 0,38 € ab km 21) und Obergrenzenprüfung.
- **GoBD- & steuerlichen Prüfroutinen** (inkl. Dreimonatsfrist nach § 9 Abs. 4a Satz 6 EStG).

---

## 📊 Amtliche Spesensätze 2026 im DACH-Vergleich

| Land / Norm | Ganztag (>24h / >11h) | An-/Abreisetag & >8h | Mahlzeitenkürzung | Pkw-km | Motorrad-km | Fahrrad-km |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **🇩🇪 Deutschland** (BMF / § 9 Abs. 4a EStG) | **28,00 €** | **14,00 €** | F: -5,60 € (-20%)<br>M: -11,20 € (-40%)<br>A: -11,20 € (-40%) | **0,30 €** | **0,20 €** | - |
| **🇦🇹 Österreich** (§ 26 Z 4 EStG) | **30,00 €** | **15,00 €** *(bzw. 2,50 €/h ab 3h)* | F: -15% (4,50 €)<br>M: -40% (12,00 €)<br>A: -40% (12,00 €) | **0,42 €** | **0,24 €** | **0,38 €** |
| **🇨🇭 Schweiz** (Spesenreglemente) | **70,00 CHF** | **35,00 CHF** | F: -15,00 CHF<br>M: -35,00 CHF<br>A: -35,00 CHF | **0,70 CHF** | **0,40 CHF** | - |

---

## 🚀 Installation

```bash
git clone https://github.com/DACHDigitalwerk/reisekosten-verpflegungsmehraufwand-rechner-dach.git
cd reisekosten-verpflegungsmehraufwand-rechner-dach
pip install .
```

---

## 💻 CLI-Tool: `dach-spesen`

Das Paket enthält das befehlszeilenbasierte Dienstprogramm `dach-spesen`:

### 1. Amtliche Tabelle 2026 anzeigen
```bash
dach-spesen table --country DE
```

### 2. Einzelnen Reisetag ad-hoc berechnen
```bash
# Voller Reisetag in Deutschland, Hotel mit Frühstück gestellt, 140 km gefahren:
dach-spesen calc --country DE --type full --km 140 --breakfast --vehicle car

# Ausgabe als maschinenlesbares JSON:
dach-spesen calc --country DE --type full --km 140 --breakfast --json
```

### 3. Pendlerpauschale (Entfernungspauschale 2026) berechnen
```bash
# 35 km einfache Wegstrecke, 210 Präsenztage im Betrieb:
dach-spesen pendler --km 35 --days 210 --vehicle car
```
*Berechnung: (20 km × 0,30 €) + (15 km × 0,38 €) = 11,70 € / Tag × 210 Tage = **2.457,00 € / Jahr**.*

### 4. Mehrtägige Reisekostenabrechnung aus JSON berechnen & prüfen
```bash
dach-spesen report examples/three_day_trip.json
```

---

## 🐍 Python API Verwendungsbeispiel

```python
from datetime import date
from reisekosten_dach import (
    ReisekostenCalculator,
    PendlerCalculator,
    TravelReport,
    TravelDay,
    Country,
    DayType,
    VehicleType
)

# 1. Mehrtägigen Bericht anlegen
report = TravelReport(
    employee_name="Maximilian Mustermann",
    employee_id="PA-84920",
    project_or_purpose="Kundenworkshop Frankfurt",
    country=Country.DE,
    days=[
        TravelDay(
            trip_date=date(2026, 1, 14),
            day_type=DayType.ARRIVAL,
            km_driven=180.0,
            dinner_provided=True  # Abendessen vom Kunden bezahlt (-11,20 €)
        ),
        TravelDay(
            trip_date=date(2026, 1, 15),
            day_type=DayType.FULL_DAY,
            breakfast_provided=True, # Frühstück im Hotel (-5,60 €)
            lunch_provided=True      # Mittagessen beim Kunden (-11,20 €)
        ),
        TravelDay(
            trip_date=date(2026, 1, 16),
            day_type=DayType.DEPARTURE,
            km_driven=180.0,
            breakfast_provided=True  # Frühstück im Hotel (-5,60 €)
        )
    ]
)

# 2. Abrechnung berechnen
result = ReisekostenCalculator.calculate_report(report)

print(f"Verpflegungsmehraufwand: {result.total_per_diem:.2f} €")
print(f"Fahrtkosten:             {result.total_mileage:.2f} €")
print(f"Gesamterstattungsbetrag: {result.total_reimbursement:.2f} €")

# 3. Pendlerpauschale berechnen (Entfernungspauschale § 9 EStG)
pendler = PendlerCalculator.calculate(
    one_way_km=40.0,
    workdays=220,
    vehicle=VehicleType.CAR,
    country=Country.DE
)
print(f"Jahresabzug Pendler:     {pendler.total_yearly_allowance:.2f} €")
```

---

## 🧪 Tests ausführen

Das Projekt wird mit einer vollständigen Unit-Test-Suite ausgeliefert:

```bash
python -m unittest discover -s tests
```

---

## 🔗 Weiterführende Fachratgeber & Ressourcen

Vertiefende Praxishilfen und gesetzliche Erläuterungen finden Sie im DACH Digitalwerk Hub:
- 📖 [Verpflegungsmehraufwand 2026 Tabelle & Pauschalen](https://dach-digitalwerk.netlify.app/verpflegungsmehraufwand-2026-tabelle-pauschalen.html)
- 📝 [Reisekostenabrechnung Muster & Excel-Vorlage kostenlos](https://dach-digitalwerk.netlify.app/reisekostenabrechnung-muster-excel-vorlage-kostenlos.html)
- 🚗 [Pendlerpauschale berechnen & Kilometergeld DACH](https://dach-digitalwerk.netlify.app/pendlerpauschale-berechnen-kilometergeld-dach.html)
- 💼 [DACH Digitalwerk B2B-Paket auf Gumroad](https://dachdigital.gumroad.com/l/gthgwc)

---

## ⚖️ Rechtlicher Hinweis & Haftungsausschluss

Dieses Repository und das enthaltene CLI-Tool stellen reine mathematische und programmtechnische Hilfswerkzeuge nach den amtlichen Tabellenwerten des Bundesministeriums der Finanzen (BMF 2026) und den jeweiligen Steuergesetzen dar. Es wird ausdrücklich **keine Steuer- oder Rechtsberatung** gemäß § 2 RDG bzw. § 5 StBerG erbracht. Für verbindliche lohnsteuerliche Prüfungen wenden Sie sich bitte an eine Steuerberaterin oder einen Steuerberater.

---

## 📄 Lizenz

Veröffentlicht unter der [MIT Lizenz](LICENSE).  
Copyright © 2026 [DACH Digitalwerk](https://dach-digitalwerk.netlify.app/).
