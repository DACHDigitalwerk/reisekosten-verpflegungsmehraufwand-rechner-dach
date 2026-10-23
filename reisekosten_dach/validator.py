# -*- coding: utf-8 -*-
"""
Prüfroutinen und Validierung von Reisekostenabrechnungen nach BMF- und GoBD-Standards.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional
from .models import TravelReport, TravelDay
from .rates import Country, DayType


@dataclass
class ValidationError:
    field: str
    message: str
    severity: str = "error"  # "error", "warning"
    day_index: Optional[int] = None


class ReisekostenValidator:
    """Validiert Reisekostenberichte auf formale, steuerliche und rechnerische Richtigkeit."""

    @classmethod
    def validate(cls, report: TravelReport) -> List[ValidationError]:
        errors: List[ValidationError] = []

        # 1. Stammdaten-Prüfung
        if not report.employee_name or not report.employee_name.strip():
            errors.append(ValidationError(
                field="employee_name",
                message="Der Name des Mitarbeiters ist ein zwingendes Pflichtfeld.",
                severity="error"
            ))

        if not report.project_or_purpose or not report.project_or_purpose.strip():
            errors.append(ValidationError(
                field="purpose",
                message="Reisezweck bzw. geschäftlicher Anlass muss konkret benannt sein (Finanzamtsprüfung).",
                severity="warning"
            ))

        if not report.days:
            errors.append(ValidationError(
                field="days",
                message="Eine Reisekostenabrechnung muss mindestens einen Reisetag enthalten.",
                severity="error"
            ))
            return errors

        # 2. Chronologie & Datumsprüfung
        sorted_days = sorted(report.days, key=lambda d: d.trip_date)
        if [d.trip_date for d in report.days] != [d.trip_date for d in sorted_days]:
            errors.append(ValidationError(
                field="days",
                message="Die Reisetage sind nicht chronologisch sortiert.",
                severity="warning"
            ))

        # Prüfung auf Mehrtägigkeit und An-/Abreisetage
        if len(report.days) > 1:
            first_day = sorted_days[0]
            last_day = sorted_days[-1]

            if first_day.day_type not in (DayType.ARRIVAL, DayType.FULL_DAY, DayType.SINGLE_OVER_8H):
                errors.append(ValidationError(
                    field="day_type",
                    message=f"Der erste Tag ({first_day.trip_date}) einer mehrtägigen Reise sollte als Anreisetag deklariert sein.",
                    severity="warning",
                    day_index=0
                ))

            if last_day.day_type not in (DayType.DEPARTURE, DayType.FULL_DAY):
                errors.append(ValidationError(
                    field="day_type",
                    message=f"Der letzte Tag ({last_day.trip_date}) einer mehrtägigen Reise sollte als Abreisetag deklariert sein.",
                    severity="warning",
                    day_index=len(report.days) - 1
                ))

        # 3. Dreimonatsfrist (§ 9 Abs. 4a Satz 6 EStG)
        if len(report.days) >= 2:
            span_days = (sorted_days[-1].trip_date - sorted_days[0].trip_date).days + 1
            if span_days > 90 and report.country == Country.DE:
                # Prüfe ob derselbe Einsatzort
                locations = {d.location.lower().strip() for d in report.days if d.location}
                if len(locations) <= 1:
                    errors.append(ValidationError(
                        field="dreimonatsfrist",
                        message="Dreimonatsfrist (§ 9 Abs. 4a Satz 6 EStG): Die Auswärtstätigkeit am selben Ort überschreitet 90 Tage. Steuerfreie Verpflegungspauschalen sind ab dem 4. Monat unzulässig, sofern keine 4-wöchige Unterbrechung vorlag.",
                        severity="warning"
                    ))

        # 4. Einzelprüfung der Reisetage
        for idx, day in enumerate(report.days):
            if day.km_driven < 0:
                errors.append(ValidationError(
                    field="km_driven",
                    message=f"Gefahrene Kilometer an Tag {idx+1} dürfen nicht negativ sein.",
                    severity="error",
                    day_index=idx
                ))

            if day.hours_absent is not None and (day.hours_absent < 0 or day.hours_absent > 24):
                errors.append(ValidationError(
                    field="hours_absent",
                    message=f"Abwesenheitsstunden an Tag {idx+1} müssen zwischen 0 und 24 liegen.",
                    severity="error",
                    day_index=idx
                ))

            # Mahlzeitenkürzung Check
            if day.breakfast_provided and day.lunch_provided and day.dinner_provided:
                if day.day_type in (DayType.ARRIVAL, DayType.DEPARTURE, DayType.SINGLE_OVER_8H) and report.country == Country.DE:
                    errors.append(ValidationError(
                        field="meals",
                        message=f"Tag {idx+1}: An einem An-/Abreisetag (14,00 €) führen 3 gestellte Mahlzeiten zu einem rechnerischen Abzug von 28,00 €, der Mehraufwand wird auf 0,00 € gekürzt.",
                        severity="warning",
                        day_index=idx
                    ))

            # Übernachtung ohne Anlass
            if day.overnight_allowance_claimed and day.day_type == DayType.SINGLE_UP_TO_8H:
                errors.append(ValidationError(
                    field="overnight",
                    message=f"Tag {idx+1}: Übernachtungspauschale bei Kurzeinsatz unter 8 Stunden ist steuerrechtlich unplausibel.",
                    severity="warning",
                    day_index=idx
                ))

        return errors
