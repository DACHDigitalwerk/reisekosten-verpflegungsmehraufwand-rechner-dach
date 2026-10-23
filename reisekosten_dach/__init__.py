# -*- coding: utf-8 -*-
"""
DACH Reisekosten- & Verpflegungsmehraufwand-Rechner 2026 (DE, AT, CH)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Bibliothek zur normkonformen Berechnung von Verpflegungspauschalen (BMF 2026),
Mahlzeitenkürzungen, amtlichem Kilometergeld und Pendlerpauschalen.

Website: https://dach-digitalwerk.netlify.app/reisekosten-verpflegungsmehraufwand/
Lizenz: MIT
"""

__version__ = "2026.1.0"
__author__ = "DACH Digitalwerk"
__license__ = "MIT"

from .rates import Country, VehicleType, DayType, get_rates
from .models import TravelDay, ExpenseItem, TravelReport, PendlerCalculation
from .calculator import ReisekostenCalculator, PendlerCalculator
from .validator import ReisekostenValidator, ValidationError

__all__ = [
    "Country",
    "VehicleType",
    "DayType",
    "get_rates",
    "TravelDay",
    "ExpenseItem",
    "TravelReport",
    "PendlerCalculation",
    "ReisekostenCalculator",
    "PendlerCalculator",
    "ReisekostenValidator",
    "ValidationError",
]
