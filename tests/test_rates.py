# -*- coding: utf-8 -*-
import unittest
from reisekosten_dach.rates import Country, VehicleType, DayType, get_rates, CountryRates


class TestRates(unittest.TestCase):

    def test_germany_rates_bmf_2026(self):
        r = get_rates(Country.DE)
        self.assertEqual(r.currency, "EUR")
        self.assertEqual(r.symbol, "€")
        self.assertEqual(r.full_day_per_diem, 28.00)
        self.assertEqual(r.partial_day_per_diem, 14.00)
        self.assertEqual(r.breakfast_cut, 5.60)
        self.assertEqual(r.lunch_cut, 11.20)
        self.assertEqual(r.dinner_cut, 11.20)
        self.assertEqual(r.car_km_rate, 0.30)
        self.assertEqual(r.motorcycle_km_rate, 0.20)
        self.assertEqual(r.pendler_rate_step1, 0.30)
        self.assertEqual(r.pendler_rate_step2, 0.38)
        self.assertEqual(r.default_overnight_allowance, 20.00)

    def test_austria_rates_estg_26(self):
        r = get_rates(Country.AT)
        self.assertEqual(r.currency, "EUR")
        self.assertEqual(r.full_day_per_diem, 30.00)
        self.assertEqual(r.car_km_rate, 0.42)
        self.assertEqual(r.motorcycle_km_rate, 0.24)
        self.assertEqual(r.bicycle_km_rate, 0.38)
        self.assertEqual(r.default_overnight_allowance, 17.00)

    def test_switzerland_rates(self):
        r = get_rates(Country.CH)
        self.assertEqual(r.currency, "CHF")
        self.assertEqual(r.full_day_per_diem, 70.00)
        self.assertEqual(r.partial_day_per_diem, 35.00)
        self.assertEqual(r.breakfast_cut, 15.00)
        self.assertEqual(r.car_km_rate, 0.70)
        self.assertEqual(r.default_overnight_allowance, 100.00)

    def test_get_rates_string_and_case_insensitive(self):
        r1 = get_rates("de")
        r2 = get_rates("AT")
        r3 = get_rates("ch")
        self.assertEqual(r1.country, Country.DE)
        self.assertEqual(r2.country, Country.AT)
        self.assertEqual(r3.country, Country.CH)

    def test_invalid_country_raises_error(self):
        with self.assertRaises(ValueError):
            get_rates("FR")


if __name__ == "__main__":
    unittest.main()
