# -*- coding: utf-8 -*-
"""
Berechnungslogik für Spesen, Mahlzeitenkürzungen, Fahrtkosten und Pendlerpauschalen.
"""

import math
from typing import Optional
from .rates import Country, VehicleType, DayType, get_rates
from .models import (
    TravelDay,
    DayCalculationResult,
    TravelReport,
    PendlerCalculation,
)


class ReisekostenCalculator:
    """Berechnet Reisekosten und Verpflegungsmehraufwand nach DACH-Rechtsnormen 2026."""

    def __init__(self, default_country: Country = Country.DE):
        self.default_country = default_country

    @staticmethod
    def calculate_day(day: TravelDay, country: Country = Country.DE) -> DayCalculationResult:
        rates = get_rates(country)
        base_per_diem = 0.0

        # Bestimmung des Grund-Tagessatzes
        if country == Country.DE:
            if day.hours_absent is not None:
                if day.hours_absent >= 24.0:
                    base_per_diem = rates.full_day_per_diem
                elif day.hours_absent > 8.0:
                    base_per_diem = rates.partial_day_per_diem
                else:
                    base_per_diem = 0.0
            else:
                if day.day_type == DayType.FULL_DAY:
                    base_per_diem = rates.full_day_per_diem
                elif day.day_type in (DayType.ARRIVAL, DayType.DEPARTURE, DayType.SINGLE_OVER_8H):
                    base_per_diem = rates.partial_day_per_diem
                else:
                    base_per_diem = 0.0

        elif country == Country.AT:
            # Österreich § 26 Z 4 EStG
            if day.hours_absent is not None:
                h = day.hours_absent
                if h > 11.0:
                    base_per_diem = rates.full_day_per_diem # 30 €
                elif h > 3.0:
                    hours_billed = math.ceil(h)
                    base_per_diem = min(rates.full_day_per_diem, hours_billed * 2.50)
                else:
                    base_per_diem = 0.0
            else:
                if day.day_type == DayType.FULL_DAY:
                    base_per_diem = rates.full_day_per_diem
                elif day.day_type in (DayType.ARRIVAL, DayType.DEPARTURE):
                    base_per_diem = rates.partial_day_per_diem
                elif day.day_type == DayType.SINGLE_OVER_8H:
                    base_per_diem = min(rates.full_day_per_diem, 8 * 2.50) # 20.00 €
                else:
                    base_per_diem = 0.0

        elif country == Country.CH:
            # Schweizer Spesenpraxis
            if day.day_type == DayType.FULL_DAY:
                base_per_diem = rates.full_day_per_diem # 70 CHF
            elif day.day_type in (DayType.ARRIVAL, DayType.DEPARTURE, DayType.SINGLE_OVER_8H):
                base_per_diem = rates.partial_day_per_diem # 35 CHF
            else:
                base_per_diem = 0.0

        # Mahlzeitenkürzungen
        bf_cut = 0.0
        lu_cut = 0.0
        di_cut = 0.0

        if country == Country.DE:
            if day.breakfast_provided:
                bf_cut = rates.breakfast_cut # 5.60 €
            if day.lunch_provided:
                lu_cut = rates.lunch_cut     # 11.20 €
            if day.dinner_provided:
                di_cut = rates.dinner_cut    # 11.20 €

        elif country == Country.AT:
            if day.breakfast_provided:
                bf_cut = base_per_diem * 0.15
            if day.lunch_provided:
                lu_cut = base_per_diem * 0.40
            if day.dinner_provided:
                di_cut = base_per_diem * 0.40

        elif country == Country.CH:
            if day.breakfast_provided:
                bf_cut = rates.breakfast_cut # 15 CHF
            if day.lunch_provided:
                lu_cut = rates.lunch_cut     # 35 CHF
            if day.dinner_provided:
                di_cut = rates.dinner_cut    # 35 CHF

        # Keine negativen Verpflegungsmehraufwendungen (Deckelung bei 0,00)
        total_cuts = round(bf_cut + lu_cut + di_cut, 2)
        effective_per_diem = round(max(0.0, base_per_diem - total_cuts), 2)

        # Kilometergeld
        mileage_cost = round(ReisekostenCalculator.calculate_mileage(day.km_driven, day.vehicle, country), 2)

        # Übernachtungskosten
        overnight_cost = 0.0
        if day.overnight_allowance_claimed:
            overnight_cost += rates.default_overnight_allowance
        if day.overnight_receipt_amount > 0:
            overnight_cost += day.overnight_receipt_amount
        overnight_cost = round(overnight_cost, 2)

        # Nebenkosten / Belege
        expenses_cost = round(sum(item.amount for item in day.expenses), 2)

        # Tagessumme
        day_total = round(effective_per_diem + mileage_cost + overnight_cost + expenses_cost, 2)

        return DayCalculationResult(
            trip_date=day.trip_date,
            base_per_diem=round(base_per_diem, 2),
            breakfast_cut=round(bf_cut, 2),
            lunch_cut=round(lu_cut, 2),
            dinner_cut=round(di_cut, 2),
            effective_per_diem=effective_per_diem,
            mileage_cost=mileage_cost,
            overnight_cost=overnight_cost,
            expenses_cost=expenses_cost,
            total_reimbursement=day_total
        )

    @staticmethod
    def calculate_mileage(km: float, vehicle: VehicleType = VehicleType.CAR, country: Country = Country.DE) -> float:
        if km <= 0:
            return 0.0
        rates = get_rates(country)
        if vehicle == VehicleType.CAR:
            return round(km * rates.car_km_rate, 2)
        elif vehicle == VehicleType.MOTORCYCLE:
            return round(km * rates.motorcycle_km_rate, 2)
        elif vehicle == VehicleType.BICYCLE:
            return round(km * rates.bicycle_km_rate, 2)
        return round(km * rates.car_km_rate, 2)

    @classmethod
    def calculate_report(cls, report: TravelReport) -> TravelReport:
        rates = get_rates(report.country)
        report.currency = rates.currency

        day_results = []
        tot_per_diem = 0.0
        tot_mileage = 0.0
        tot_overnight = 0.0
        tot_expenses = 0.0

        for day in report.days:
            res = cls.calculate_day(day, report.country)
            day_results.append(res)
            tot_per_diem += res.effective_per_diem
            tot_mileage += res.mileage_cost
            tot_overnight += res.overnight_cost
            tot_expenses += res.expenses_cost

        report.day_results = day_results
        report.total_per_diem = round(tot_per_diem, 2)
        report.total_mileage = round(tot_mileage, 2)
        report.total_overnight = round(tot_overnight, 2)
        report.total_expenses = round(tot_expenses, 2)
        report.total_reimbursement = round(tot_per_diem + tot_mileage + tot_overnight + tot_expenses, 2)

        return report


class PendlerCalculator:
    """Berechnet die Entfernungspauschale 2026 nach § 9 Abs. 1 Satz 3 Nr. 4 EStG."""

    @staticmethod
    def calculate(
        one_way_km: float,
        workdays: int,
        vehicle: VehicleType = VehicleType.CAR,
        country: Country = Country.DE
    ) -> PendlerCalculation:
        if one_way_km < 0:
            one_way_km = 0.0
        if workdays < 0:
            workdays = 0

        rates = get_rates(country)

        # Stufe 1: Bis 20 km
        step1_km = min(one_way_km, rates.pendler_step1_limit_km)
        step1_daily = step1_km * rates.pendler_rate_step1

        # Stufe 2: Ab dem 21. km
        step2_km = max(0.0, one_way_km - rates.pendler_step1_limit_km)
        step2_daily = step2_km * rates.pendler_rate_step2

        daily_total = step1_daily + step2_daily
        yearly_total = daily_total * workdays

        # Deckelung auf 4.500 € bei Nicht-PKW (DE)
        capped = False
        if country == Country.DE and vehicle != VehicleType.CAR:
            if yearly_total > 4500.0:
                yearly_total = 4500.0
                capped = True

        monthly_avg = yearly_total / 12.0

        return PendlerCalculation(
            country=country,
            one_way_distance_km=one_way_km,
            workdays_count=workdays,
            vehicle=vehicle,
            daily_allowance=daily_total,
            step1_allowance=step1_daily,
            step2_allowance=step2_daily,
            total_yearly_allowance=yearly_total,
            monthly_average_allowance=monthly_avg,
            capped_at_max=capped,
            currency=rates.currency
        )
