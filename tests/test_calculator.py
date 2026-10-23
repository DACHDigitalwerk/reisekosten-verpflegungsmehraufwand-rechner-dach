# -*- coding: utf-8 -*-
import unittest
from datetime import date
from reisekosten_dach.rates import Country, VehicleType, DayType
from reisekosten_dach.models import TravelDay, ExpenseItem, TravelReport
from reisekosten_dach.calculator import ReisekostenCalculator, PendlerCalculator


class TestCalculator(unittest.TestCase):

    def test_germany_full_day_no_meals(self):
        day = TravelDay(trip_date=date(2026, 1, 15), day_type=DayType.FULL_DAY)
        res = ReisekostenCalculator.calculate_day(day, Country.DE)
        self.assertEqual(res.base_per_diem, 28.00)
        self.assertEqual(res.effective_per_diem, 28.00)
        self.assertEqual(res.total_reimbursement, 28.00)

    def test_germany_arrival_day(self):
        day = TravelDay(trip_date=date(2026, 1, 14), day_type=DayType.ARRIVAL)
        res = ReisekostenCalculator.calculate_day(day, Country.DE)
        self.assertEqual(res.base_per_diem, 14.00)
        self.assertEqual(res.effective_per_diem, 14.00)

    def test_germany_single_day_under_8h(self):
        day = TravelDay(trip_date=date(2026, 1, 14), day_type=DayType.SINGLE_UP_TO_8H, hours_absent=6.5)
        res = ReisekostenCalculator.calculate_day(day, Country.DE)
        self.assertEqual(res.base_per_diem, 0.0)
        self.assertEqual(res.effective_per_diem, 0.0)

    def test_germany_breakfast_cut(self):
        # 28.00 - 5.60 = 22.40 €
        day = TravelDay(trip_date=date(2026, 1, 15), day_type=DayType.FULL_DAY, breakfast_provided=True)
        res = ReisekostenCalculator.calculate_day(day, Country.DE)
        self.assertEqual(res.breakfast_cut, 5.60)
        self.assertEqual(res.effective_per_diem, 22.40)

    def test_germany_lunch_and_dinner_cut(self):
        # 28.00 - 11.20 - 11.20 = 5.60 €
        day = TravelDay(trip_date=date(2026, 1, 15), day_type=DayType.FULL_DAY, lunch_provided=True, dinner_provided=True)
        res = ReisekostenCalculator.calculate_day(day, Country.DE)
        self.assertEqual(res.lunch_cut, 11.20)
        self.assertEqual(res.dinner_cut, 11.20)
        self.assertEqual(res.effective_per_diem, 5.60)

    def test_germany_meal_cut_clamped_to_zero(self):
        # Anreisetag 14.00 €; alle 3 Mahlzeiten: 5.60 + 11.20 + 11.20 = 28.00 € Abzug
        # Darf nicht negativ werden!
        day = TravelDay(
            trip_date=date(2026, 1, 14),
            day_type=DayType.ARRIVAL,
            breakfast_provided=True,
            lunch_provided=True,
            dinner_provided=True
        )
        res = ReisekostenCalculator.calculate_day(day, Country.DE)
        self.assertEqual(res.effective_per_diem, 0.0)
        self.assertGreaterEqual(res.total_reimbursement, 0.0)

    def test_mileage_calculation_car_and_motorcycle(self):
        km_car = ReisekostenCalculator.calculate_mileage(100.0, VehicleType.CAR, Country.DE)
        km_moto = ReisekostenCalculator.calculate_mileage(100.0, VehicleType.MOTORCYCLE, Country.DE)
        self.assertEqual(km_car, 30.00)
        self.assertEqual(km_moto, 20.00)

    def test_overnight_allowance_and_receipt(self):
        day = TravelDay(
            trip_date=date(2026, 1, 15),
            day_type=DayType.FULL_DAY,
            overnight_allowance_claimed=True,
            overnight_receipt_amount=85.50
        )
        res = ReisekostenCalculator.calculate_day(day, Country.DE)
        # 20.00 Pauschale + 85.50 Beleg = 105.50
        self.assertEqual(res.overnight_cost, 105.50)

    def test_austria_hourly_aliquotierung(self):
        # > 11h = 30.00 €
        d1 = TravelDay(trip_date=date(2026, 1, 15), hours_absent=12.0)
        r1 = ReisekostenCalculator.calculate_day(d1, Country.AT)
        self.assertEqual(r1.base_per_diem, 30.00)

        # 5h = 5 * 2.50 = 12.50 €
        d2 = TravelDay(trip_date=date(2026, 1, 15), hours_absent=5.0)
        r2 = ReisekostenCalculator.calculate_day(d2, Country.AT)
        self.assertEqual(r2.base_per_diem, 12.50)

        # 2h = <= 3h = 0.00 €
        d3 = TravelDay(trip_date=date(2026, 1, 15), hours_absent=2.0)
        r3 = ReisekostenCalculator.calculate_day(d3, Country.AT)
        self.assertEqual(r3.base_per_diem, 0.0)

    def test_austria_mileage_bike_and_car(self):
        car = ReisekostenCalculator.calculate_mileage(50.0, VehicleType.CAR, Country.AT)
        bike = ReisekostenCalculator.calculate_mileage(20.0, VehicleType.BICYCLE, Country.AT)
        self.assertEqual(car, 21.00)  # 50 * 0.42
        self.assertEqual(bike, 7.60)  # 20 * 0.38

    def test_switzerland_full_day_and_lunch_cut(self):
        day = TravelDay(trip_date=date(2026, 1, 15), day_type=DayType.FULL_DAY, lunch_provided=True)
        res = ReisekostenCalculator.calculate_day(day, Country.CH)
        self.assertEqual(res.base_per_diem, 70.00)
        self.assertEqual(res.lunch_cut, 35.00)
        self.assertEqual(res.effective_per_diem, 35.00)

    def test_full_travel_report_multi_day(self):
        report = TravelReport(
            employee_name="Max Mustermann",
            project_or_purpose="Workshop",
            country=Country.DE,
            days=[
                TravelDay(date(2026, 1, 14), day_type=DayType.ARRIVAL, km_driven=100.0),
                TravelDay(date(2026, 1, 15), day_type=DayType.FULL_DAY, breakfast_provided=True),
                TravelDay(date(2026, 1, 16), day_type=DayType.DEPARTURE, km_driven=100.0)
            ]
        )
        calc = ReisekostenCalculator.calculate_report(report)
        # Day 1: 14.00 per diem + 30.00 km = 44.00
        # Day 2: 28.00 - 5.60 = 22.40 per diem
        # Day 3: 14.00 per diem + 30.00 km = 44.00
        # Total per diem: 14 + 22.40 + 14 = 50.40 €
        # Total km: 30 + 30 = 60.00 €
        # Grand total: 110.40 €
        self.assertEqual(calc.total_per_diem, 50.40)
        self.assertEqual(calc.total_mileage, 60.00)
        self.assertEqual(calc.total_reimbursement, 110.40)

    def test_pendler_calculator_german_steps_and_cap(self):
        # 35 km einfache Wegstrecke:
        # km 1-20: 20 * 0.30 = 6.00 €
        # km 21-35: 15 * 0.38 = 5.70 €
        # Daily: 11.70 €
        # 210 days: 11.70 * 210 = 2457.00 €
        calc_car = PendlerCalculator.calculate(35.0, 210, VehicleType.CAR, Country.DE)
        self.assertEqual(calc_car.daily_allowance, 11.70)
        self.assertEqual(calc_car.total_yearly_allowance, 2457.00)
        self.assertFalse(calc_car.capped_at_max)

        # High distance with public transit or bicycle (capped at 4500 €)
        calc_bike = PendlerCalculator.calculate(100.0, 230, VehicleType.BICYCLE, Country.DE)
        # Without cap: (6.00 + 80*0.38 = 36.40) * 230 = 8372 € -> capped at 4500 €
        self.assertEqual(calc_bike.total_yearly_allowance, 4500.00)
        self.assertTrue(calc_bike.capped_at_max)


if __name__ == "__main__":
    unittest.main()
