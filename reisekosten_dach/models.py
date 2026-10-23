# -*- coding: utf-8 -*-
"""
Datenmodelle für Reisetage, Spesenabrechnungen und Pendlerpauschalen.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any
from .rates import Country, VehicleType, DayType


@dataclass
class ExpenseItem:
    """Belegnachweis für Nebenkosten (z. B. Parken, Maut, Bahn)."""
    description: str
    amount: float
    receipt_number: Optional[str] = None
    category: str = "other"  # parking, toll, transit, hospitality, other


@dataclass
class TravelDay:
    """Repräsentiert einen einzelnen Kalendertag einer Dienstreise."""
    trip_date: date
    day_type: DayType = DayType.FULL_DAY
    hours_absent: Optional[float] = None
    location: str = ""
    purpose: str = ""
    breakfast_provided: bool = False
    lunch_provided: bool = False
    dinner_provided: bool = False
    km_driven: float = 0.0
    vehicle: VehicleType = VehicleType.CAR
    overnight_stay: bool = False
    overnight_allowance_claimed: bool = False
    overnight_receipt_amount: float = 0.0
    expenses: List[ExpenseItem] = field(default_factory=list)


@dataclass
class DayCalculationResult:
    """Berechnungsergebnis eines einzelnen Reisetags."""
    trip_date: date
    base_per_diem: float
    breakfast_cut: float
    lunch_cut: float
    dinner_cut: float
    effective_per_diem: float
    mileage_cost: float
    overnight_cost: float
    expenses_cost: float
    total_reimbursement: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.trip_date.isoformat(),
            "base_per_diem": round(self.base_per_diem, 2),
            "cuts": {
                "breakfast": round(self.breakfast_cut, 2),
                "lunch": round(self.lunch_cut, 2),
                "dinner": round(self.dinner_cut, 2),
            },
            "effective_per_diem": round(self.effective_per_diem, 2),
            "mileage_cost": round(self.mileage_cost, 2),
            "overnight_cost": round(self.overnight_cost, 2),
            "expenses_cost": round(self.expenses_cost, 2),
            "total_reimbursement": round(self.total_reimbursement, 2)
        }


@dataclass
class TravelReport:
    """Vollständige Reisekostenabrechnung mit mehreren Tagen und Stammdaten."""
    employee_name: str
    employee_id: str = ""
    department: str = ""
    project_or_purpose: str = ""
    country: Country = Country.DE
    days: List[TravelDay] = field(default_factory=list)
    day_results: List[DayCalculationResult] = field(default_factory=list)
    total_per_diem: float = 0.0
    total_mileage: float = 0.0
    total_overnight: float = 0.0
    total_expenses: float = 0.0
    total_reimbursement: float = 0.0
    currency: str = "EUR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_name": self.employee_name,
            "employee_id": self.employee_id,
            "department": self.department,
            "purpose": self.project_or_purpose,
            "country": self.country.value,
            "currency": self.currency,
            "summary": {
                "total_per_diem": round(self.total_per_diem, 2),
                "total_mileage": round(self.total_mileage, 2),
                "total_overnight": round(self.total_overnight, 2),
                "total_expenses": round(self.total_expenses, 2),
                "total_reimbursement": round(self.total_reimbursement, 2),
            },
            "days": [r.to_dict() for r in self.day_results]
        }


@dataclass
class PendlerCalculation:
    """Ergebnis der Pendlerpauschalen-Berechnung (Entfernungspauschale)."""
    country: Country
    one_way_distance_km: float
    workdays_count: int
    vehicle: VehicleType
    daily_allowance: float
    step1_allowance: float
    step2_allowance: float
    total_yearly_allowance: float
    monthly_average_allowance: float
    capped_at_max: bool = False
    currency: str = "EUR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "country": self.country.value,
            "one_way_distance_km": self.one_way_distance_km,
            "workdays_count": self.workdays_count,
            "daily_allowance": round(self.daily_allowance, 2),
            "step1_allowance": round(self.step1_allowance, 2),
            "step2_allowance": round(self.step2_allowance, 2),
            "total_yearly_allowance": round(self.total_yearly_allowance, 2),
            "monthly_average_allowance": round(self.monthly_average_allowance, 2),
            "capped_at_max": self.capped_at_max,
            "currency": self.currency
        }
