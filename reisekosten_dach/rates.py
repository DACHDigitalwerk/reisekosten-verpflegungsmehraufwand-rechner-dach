# -*- coding: utf-8 -*-
"""
Amtliche Spesensätze und Kilometerpauschalen 2026 für Deutschland, Österreich und Schweiz.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict


class Country(str, Enum):
    DE = "DE"
    AT = "AT"
    CH = "CH"


class VehicleType(str, Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"


class DayType(str, Enum):
    FULL_DAY = "full_day"              # Ganzer Tag / 24h Abwesenheit
    ARRIVAL = "arrival"                # Anreisetag bei mehrtägiger Reise
    DEPARTURE = "departure"            # Abreisetag bei mehrtägiger Reise
    SINGLE_OVER_8H = "single_over_8h"  # Eintägig > 8 Stunden
    SINGLE_UP_TO_8H = "single_up_to_8h"# Eintägig <= 8 Stunden (0 EUR)
    CUSTOM_HOURS = "custom_hours"      # Für Österreich (Aliquotierung nach Stunden)


@dataclass(frozen=True)
class CountryRates:
    country: Country
    currency: str
    symbol: str
    full_day_per_diem: float
    partial_day_per_diem: float
    breakfast_cut: float
    lunch_cut: float
    dinner_cut: float
    car_km_rate: float
    motorcycle_km_rate: float
    bicycle_km_rate: float
    default_overnight_allowance: float
    pendler_rate_step1: float
    pendler_rate_step2: float
    pendler_step1_limit_km: float


RATES_2026: Dict[Country, CountryRates] = {
    Country.DE: CountryRates(
        country=Country.DE,
        currency="EUR",
        symbol="€",
        full_day_per_diem=28.00,        # § 9 Abs. 4a EStG BMF 2026
        partial_day_per_diem=14.00,     # An-/Abreisetag & > 8h
        breakfast_cut=5.60,             # 20% von 28,00 €
        lunch_cut=11.20,                # 40% von 28,00 €
        dinner_cut=11.20,               # 40% von 28,00 €
        car_km_rate=0.30,               # § 9 EStG / BRKG
        motorcycle_km_rate=0.20,
        bicycle_km_rate=0.00,
        default_overnight_allowance=20.00,
        pendler_rate_step1=0.30,        # km 1-20
        pendler_rate_step2=0.38,        # ab km 21
        pendler_step1_limit_km=20.0
    ),
    Country.AT: CountryRates(
        country=Country.AT,
        currency="EUR",
        symbol="€",
        full_day_per_diem=30.00,        # § 26 Z 4 EStG (>11h)
        partial_day_per_diem=15.00,     # Richtwert Anreise
        breakfast_cut=4.50,             # 15%
        lunch_cut=12.00,                # 40%
        dinner_cut=12.00,               # 40%
        car_km_rate=0.42,               # Amtliches Kilometergeld PKW
        motorcycle_km_rate=0.24,        # Amtliches Kilometergeld Motorrad
        bicycle_km_rate=0.38,           # Amtliches Kilometergeld Fahrrad
        default_overnight_allowance=17.00, # Pauschales Nächtigungsgeld Inland
        pendler_rate_step1=0.30,
        pendler_rate_step2=0.38,
        pendler_step1_limit_km=20.0
    ),
    Country.CH: CountryRates(
        country=Country.CH,
        currency="CHF",
        symbol="CHF",
        full_day_per_diem=70.00,        # 35 CHF Mittag + 35 CHF Abend
        partial_day_per_diem=35.00,     # Einzelne Hauptmahlzeit
        breakfast_cut=15.00,            # Hotelabzug
        lunch_cut=35.00,                # Hauptmahlzeit Mittag
        dinner_cut=35.00,               # Hauptmahlzeit Abend
        car_km_rate=0.70,               # CHF je km
        motorcycle_km_rate=0.40,
        bicycle_km_rate=0.00,
        default_overnight_allowance=100.00,
        pendler_rate_step1=0.70,
        pendler_rate_step2=0.70,
        pendler_step1_limit_km=0.0
    )
}


def get_rates(country: Country) -> CountryRates:
    if isinstance(country, str):
        country = Country(country.upper())
    if country not in RATES_2026:
        raise ValueError(f"Ungültiges Land: {country}. Unterstützt werden: DE, AT, CH.")
    return RATES_2026[country]
