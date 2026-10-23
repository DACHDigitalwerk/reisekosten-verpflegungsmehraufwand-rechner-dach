# -*- coding: utf-8 -*-
"""
CLI-Interface: dach-spesen
DACH Reisekosten-, Verpflegungsmehraufwand- & Pendlerpauschalen-Rechner 2026
"""

import argparse
import json
import sys
from datetime import date
from .rates import Country, VehicleType, DayType, get_rates, RATES_2026
from .models import TravelDay, ExpenseItem, TravelReport
from .calculator import ReisekostenCalculator, PendlerCalculator
from .validator import ReisekostenValidator


def format_currency(val: float, sym: str = "€") -> str:
    return f"{val:,.2f} {sym}".replace(",", "X").replace(".", ",").replace("X", ".")


def cmd_table(args):
    """Zeigt die amtlichen Spesensätze 2026 im DACH-Raum an."""
    countries = [Country(args.country.upper())] if args.country else [Country.DE, Country.AT, Country.CH]

    print("=" * 78)
    print("DACH DIGITALWERK • AMTLICHE SPESENSÄTZE & KILOMETERPAUSCHALEN 2026")
    print("=" * 78)

    names = {Country.DE: "Deutschland", Country.AT: "Österreich", Country.CH: "Schweiz"}
    for c in countries:
        r = get_rates(c)
        print(f"\n[{r.country.value}] {names.get(r.country, r.country.value)} • {r.currency} ({r.symbol})")
        print("-" * 50)
        print(f"  • Ganztagespauschale (>24h bzw. >11h):     {format_currency(r.full_day_per_diem, r.symbol)}")
        print(f"  • An-/Abreisetag & Abwesenheit >8h:       {format_currency(r.partial_day_per_diem, r.symbol)}")
        print(f"  • Mahlzeitenkürzung Frühstück:            -{format_currency(r.breakfast_cut, r.symbol)}")
        print(f"  • Mahlzeitenkürzung Mittagessen:          -{format_currency(r.lunch_cut, r.symbol)}")
        print(f"  • Mahlzeitenkürzung Abendessen:           -{format_currency(r.dinner_cut, r.symbol)}")
        print(f"  • Kilometerpauschale Pkw:                 {format_currency(r.car_km_rate, r.symbol)} / km")
        print(f"  • Kilometerpauschale Zweirad:             {format_currency(r.motorcycle_km_rate, r.symbol)} / km")
        if r.bicycle_km_rate > 0:
            print(f"  • Kilometerpauschale Fahrrad:             {format_currency(r.bicycle_km_rate, r.symbol)} / km")
        print(f"  • Übernachtungspauschale (ohne Beleg):    {format_currency(r.default_overnight_allowance, r.symbol)}")
        if r.pendler_step1_limit_km > 0:
            print(f"  • Pendlerpauschale (km 1 bis 20):         {format_currency(r.pendler_rate_step1, r.symbol)} / km")
            print(f"  • Pendlerpauschale (ab km 21):            {format_currency(r.pendler_rate_step2, r.symbol)} / km")
    print("\n" + "=" * 78)
    print("Web-Tool & DIN-A4 Generator: https://dach-digitalwerk.netlify.app/reisekosten-verpflegungsmehraufwand/\n")


def cmd_calc(args):
    """Berechnet einen einzelnen Reisetag."""
    country = Country(args.country.upper())
    rates = get_rates(country)

    day_type_map = {
        "full": DayType.FULL_DAY,
        "arrival": DayType.ARRIVAL,
        "departure": DayType.DEPARTURE,
        "over8h": DayType.SINGLE_OVER_8H,
        "under8h": DayType.SINGLE_UP_TO_8H,
    }
    dtype = day_type_map.get(args.type.lower(), DayType.FULL_DAY)

    day = TravelDay(
        trip_date=date.today(),
        day_type=dtype,
        hours_absent=args.hours,
        location=args.location or "Dienstreiseort",
        breakfast_provided=args.breakfast,
        lunch_provided=args.lunch,
        dinner_provided=args.dinner,
        km_driven=args.km or 0.0,
        vehicle=VehicleType(args.vehicle.lower()),
        overnight_allowance_claimed=args.overnight,
        overnight_receipt_amount=args.hotel_receipt or 0.0,
        expenses=[ExpenseItem("Nebenkosten", args.expenses)] if args.expenses else []
    )

    res = ReisekostenCalculator.calculate_day(day, country)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return

    sym = rates.symbol
    print("\n" + "=" * 60)
    print(f"BERECHNUNGSERGEBNIS REISETAG [{country.value}]")
    print("=" * 60)
    print(f"  Reiseart / Typ:            {day.day_type.value}")
    print(f"  Grundpauschale:            {format_currency(res.base_per_diem, sym)}")
    print(f"  Abzug Frühstück:          -{format_currency(res.breakfast_cut, sym)}")
    print(f"  Abzug Mittagessen:        -{format_currency(res.lunch_cut, sym)}")
    print(f"  Abzug Abendessen:         -{format_currency(res.dinner_cut, sym)}")
    print(f"  Effektives Tagegeld:       {format_currency(res.effective_per_diem, sym)}")
    print(f"  Fahrtkosten ({day.km_driven} km):     {format_currency(res.mileage_cost, sym)}")
    print(f"  Übernachtung:              {format_currency(res.overnight_cost, sym)}")
    print(f"  Reisenebenkosten:          {format_currency(res.expenses_cost, sym)}")
    print("-" * 60)
    print(f"  STEUERFREIER GESAMTBETRAG: {format_currency(res.total_reimbursement, sym)}")
    print("=" * 60 + "\n")


def cmd_pendler(args):
    """Berechnet die Entfernungspauschale für Arbeitnehmer."""
    country = Country(args.country.upper())
    res = PendlerCalculator.calculate(
        one_way_km=args.km,
        workdays=args.days,
        vehicle=VehicleType(args.vehicle.lower()),
        country=country
    )

    if args.json:
        print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return

    sym = res.currency
    print("\n" + "=" * 65)
    print(f"PENDLERPAUSCHALEN-BERECHNUNG 2026 [{country.value}]")
    print("=" * 65)
    print(f"  Einfache Wegstrecke:         {res.one_way_distance_km} km")
    print(f"  Präsenztage im Betrieb:      {res.workdays_count} Tage")
    print(f"  Verkehrsmittel:              {res.vehicle.value}")
    print("-" * 65)
    print(f"  • Stufe 1 (km 1 bis 20):     {format_currency(res.step1_allowance, sym)} / Tag")
    print(f"  • Stufe 2 (ab km 21):        {format_currency(res.step2_allowance, sym)} / Tag")
    print(f"  • Tagesanspruch:             {format_currency(res.daily_allowance, sym)} / Tag")
    print("-" * 65)
    print(f"  JÄHRLICHER WERBUNGSKOSTENABZUG: {format_currency(res.total_yearly_allowance, sym)}")
    print(f"  Monatlicher Durchschnitt:       {format_currency(res.monthly_average_allowance, sym)} / Monat")
    if res.capped_at_max:
        print("  Hinweis: Gedeckelt auf den gesetzlichen Höchstbetrag von 4.500,00 € (Nicht-PKW).")
    print("=" * 65 + "\n")


def cmd_report(args):
    """Lädt einen vollständigen Reisekostenbericht aus einer JSON-Datei."""
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Fehler beim Lesen von {args.file}: {e}", file=sys.stderr)
        sys.exit(1)

    country = Country(data.get("country", "DE").upper())
    days = []
    for d in data.get("days", []):
        trip_date = date.fromisoformat(d.get("date", str(date.today())))
        expenses = [ExpenseItem(exp.get("description", "Auslage"), float(exp.get("amount", 0))) for exp in d.get("expenses", [])]
        days.append(TravelDay(
            trip_date=trip_date,
            day_type=DayType(d.get("day_type", "full_day")),
            hours_absent=d.get("hours_absent"),
            location=d.get("location", ""),
            purpose=d.get("purpose", ""),
            breakfast_provided=bool(d.get("breakfast_provided", False)),
            lunch_provided=bool(d.get("lunch_provided", False)),
            dinner_provided=bool(d.get("dinner_provided", False)),
            km_driven=float(d.get("km_driven", 0)),
            vehicle=VehicleType(d.get("vehicle", "car")),
            overnight_allowance_claimed=bool(d.get("overnight_allowance_claimed", False)),
            overnight_receipt_amount=float(d.get("overnight_receipt_amount", 0)),
            expenses=expenses
        ))

    report = TravelReport(
        employee_name=data.get("employee_name", "Unbekannt"),
        employee_id=data.get("employee_id", ""),
        department=data.get("department", ""),
        project_or_purpose=data.get("purpose", ""),
        country=country,
        days=days
    )

    # Validierung
    errors = ReisekostenValidator.validate(report)
    if errors and not args.ignore_errors:
        print(f"\n⚠️ {len(errors)} Validierungs-Hinweise gefunden:")
        for err in errors:
            prefix = "[ERROR]" if err.severity == "error" else "[WARN]"
            print(f"  {prefix} {err.field}: {err.message}")
        if any(e.severity == "error" for e in errors):
            print("\nAbbruch wegen kritischer Validierungsfehler.", file=sys.stderr)
            sys.exit(1)

    # Berechnung
    calculated = ReisekostenCalculator.calculate_report(report)

    if args.json:
        print(json.dumps(calculated.to_dict(), indent=2, ensure_ascii=False))
        return

    sym = calculated.currency
    print("\n" + "=" * 70)
    print("REISEKOSTENABRECHNUNG 2026 • DACH DIGITALWERK")
    print("=" * 70)
    print(f"Mitarbeiter: {calculated.employee_name} ({calculated.employee_id})")
    print(f"Abteilung:   {calculated.department} | Land: {calculated.country.value}")
    print(f"Anlass:      {calculated.project_or_purpose}")
    print("-" * 70)
    print("Tagesübersicht:")
    for r in calculated.day_results:
        print(f"  • {r.trip_date}: Tagegeld {format_currency(r.effective_per_diem, sym)} | "
              f"Fahrt {format_currency(r.mileage_cost, sym)} | "
              f"Hotel {format_currency(r.overnight_cost, sym)} | "
              f"Summe: {format_currency(r.total_reimbursement, sym)}")
    print("-" * 70)
    print(f"GESAMTER VERPFLEGUNGSMEHRAUFWAND: {format_currency(calculated.total_per_diem, sym)}")
    print(f"GESAMTE FAHRTKOSTEN:              {format_currency(calculated.total_mileage, sym)}")
    print(f"GESAMTE HOTEL- & NÄCHTIGUNGSKOST: {format_currency(calculated.total_overnight, sym)}")
    print(f"GESAMTE REISENEBENKOSTEN:         {format_currency(calculated.total_expenses, sym)}")
    print("=" * 70)
    print(f"STEUERFREIER ERSTATTUNGSBETRAG:   {format_currency(calculated.total_reimbursement, sym)}")
    print("=" * 70 + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dach-spesen",
        description="DACH Reisekosten-, Verpflegungsmehraufwand- & Pendlerpauschalen-Rechner 2026 (DE, AT, CH)"
    )
    parser.add_argument("--version", action="version", version="dach-spesen 2026.1.0")

    subparsers = parser.add_subparsers(dest="subcommand", help="Verfügbare Befehle")

    # Subcommand: table
    p_table = subparsers.add_parser("table", help="Amtliche Spesensätze 2026 anzeigen")
    p_table.add_argument("--country", "-c", choices=["DE", "AT", "CH", "de", "at", "ch"], help="Land filtern")
    p_table.set_defaults(func=cmd_table)

    # Subcommand: calc
    p_calc = subparsers.add_parser("calc", help="Einzelnen Reisetag berechnen")
    p_calc.add_argument("--country", "-c", default="DE", choices=["DE", "AT", "CH", "de", "at", "ch"], help="Land")
    p_calc.add_argument("--type", "-t", default="full", choices=["full", "arrival", "departure", "over8h", "under8h"], help="Reisetyp")
    p_calc.add_argument("--hours", type=float, help="Genaue Abwesenheitsstunden")
    p_calc.add_argument("--location", "-l", help="Zielort")
    p_calc.add_argument("--breakfast", "-b", action="store_true", help="Frühstück gestellt")
    p_calc.add_argument("--lunch", "-m", action="store_true", help="Mittagessen gestellt")
    p_calc.add_argument("--dinner", "-d", action="store_true", help="Abendessen gestellt")
    p_calc.add_argument("--km", type=float, default=0.0, help="Gefahrene Kilometer mit Privat-KFZ")
    p_calc.add_argument("--vehicle", default="car", choices=["car", "motorcycle", "bicycle"], help="Fahrzeugart")
    p_calc.add_argument("--overnight", action="store_true", help="Übernachtungspauschale beanspruchen")
    p_calc.add_argument("--hotel-receipt", type=float, default=0.0, help="Hotel-Belegbetrag")
    p_calc.add_argument("--expenses", type=float, default=0.0, help="Nebenkosten (Parken, Maut)")
    p_calc.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    p_calc.set_defaults(func=cmd_calc)

    # Subcommand: pendler
    p_pendler = subparsers.add_parser("pendler", help="Pendlerpauschale (Entfernungspauschale) berechnen")
    p_pendler.add_argument("--km", "-k", type=float, required=True, help="Einfache Wegstrecke in km")
    p_pendler.add_argument("--days", "-d", type=int, default=220, help="Präsenztage im Betrieb pro Jahr")
    p_pendler.add_argument("--vehicle", "-v", default="car", choices=["car", "motorcycle", "bicycle"], help="Fahrzeugart")
    p_pendler.add_argument("--country", "-c", default="DE", choices=["DE", "AT", "CH", "de", "at", "ch"], help="Land")
    p_pendler.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    p_pendler.set_defaults(func=cmd_pendler)

    # Subcommand: report
    p_report = subparsers.add_parser("report", help="JSON-Reisekostenbericht berechnen und prüfen")
    p_report.add_argument("file", help="Pfad zur JSON-Datei")
    p_report.add_argument("--ignore-errors", action="store_true", help="Warnungen/Fehler ignorieren")
    p_report.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    p_report.set_defaults(func=cmd_report)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
