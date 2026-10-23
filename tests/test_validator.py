# -*- coding: utf-8 -*-
import unittest
from datetime import date, timedelta
from reisekosten_dach.rates import Country, DayType
from reisekosten_dach.models import TravelDay, TravelReport
from reisekosten_dach.validator import ReisekostenValidator


class TestValidator(unittest.TestCase):

    def test_valid_report_no_errors(self):
        report = TravelReport(
            employee_name="Erika Musterfrau",
            project_or_purpose="Systemprüfung",
            country=Country.DE,
            days=[
                TravelDay(date(2026, 2, 1), day_type=DayType.ARRIVAL, km_driven=120.0),
                TravelDay(date(2026, 2, 2), day_type=DayType.DEPARTURE, km_driven=120.0)
            ]
        )
        errors = ReisekostenValidator.validate(report)
        err_levels = [e.severity for e in errors]
        self.assertNotIn("error", err_levels)

    def test_missing_employee_name_triggers_error(self):
        report = TravelReport(
            employee_name="",
            project_or_purpose="Audit",
            days=[TravelDay(date(2026, 2, 1))]
        )
        errors = ReisekostenValidator.validate(report)
        self.assertTrue(any(e.field == "employee_name" and e.severity == "error" for e in errors))

    def test_empty_days_triggers_error(self):
        report = TravelReport(employee_name="Max", days=[])
        errors = ReisekostenValidator.validate(report)
        self.assertTrue(any(e.field == "days" and e.severity == "error" for e in errors))

    def test_negative_km_triggers_error(self):
        report = TravelReport(
            employee_name="Max",
            project_or_purpose="Audit",
            days=[TravelDay(date(2026, 2, 1), km_driven=-50.0)]
        )
        errors = ReisekostenValidator.validate(report)
        self.assertTrue(any(e.field == "km_driven" and e.severity == "error" for e in errors))

    def test_dreimonatsfrist_warning(self):
        start = date(2026, 1, 1)
        end = start + timedelta(days=95)
        report = TravelReport(
            employee_name="Langzeit-Consultant",
            project_or_purpose="Dauerprojekt",
            days=[
                TravelDay(start, day_type=DayType.ARRIVAL, location="Projektstandort Berlin"),
                TravelDay(end, day_type=DayType.DEPARTURE, location="Projektstandort Berlin")
            ]
        )
        errors = ReisekostenValidator.validate(report)
        self.assertTrue(any(e.field == "dreimonatsfrist" and e.severity == "warning" for e in errors))


if __name__ == "__main__":
    unittest.main()
