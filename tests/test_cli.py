# -*- coding: utf-8 -*-
import unittest
import io
import json
import os
import tempfile
from contextlib import redirect_stdout
from reisekosten_dach.cli import build_parser, main


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.parser = build_parser()

    def test_cli_table_germany(self):
        f = io.StringIO()
        with redirect_stdout(f):
            args = self.parser.parse_args(["table", "--country", "DE"])
            args.func(args)
        out = f.getvalue()
        self.assertIn("DEUTSCHLAND", out.upper())
        self.assertIn("28,00", out)
        self.assertIn("14,00", out)

    def test_cli_calc_json(self):
        f = io.StringIO()
        with redirect_stdout(f):
            args = self.parser.parse_args(["calc", "--country", "DE", "--type", "full", "--km", "100", "--breakfast", "--json"])
            args.func(args)
        out = f.getvalue()
        data = json.loads(out)
        self.assertEqual(data["base_per_diem"], 28.00)
        self.assertEqual(data["cuts"]["breakfast"], 5.60)
        self.assertEqual(data["effective_per_diem"], 22.40)
        self.assertEqual(data["mileage_cost"], 30.00)
        self.assertEqual(data["total_reimbursement"], 52.40)

    def test_cli_pendler_json(self):
        f = io.StringIO()
        with redirect_stdout(f):
            args = self.parser.parse_args(["pendler", "--km", "35", "--days", "200", "--json"])
            args.func(args)
        out = f.getvalue()
        data = json.loads(out)
        self.assertEqual(data["one_way_distance_km"], 35.0)
        self.assertEqual(data["daily_allowance"], 11.70)
        self.assertEqual(data["total_yearly_allowance"], 2340.0)

    def test_cli_report_file(self):
        sample = {
            "employee_name": "Test Person",
            "country": "DE",
            "purpose": "Mandantentermin",
            "days": [
                {
                    "date": "2026-03-01",
                    "day_type": "arrival",
                    "km_driven": 80
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as tmp:
            json.dump(sample, tmp)
            tmp_path = tmp.name

        try:
            f = io.StringIO()
            with redirect_stdout(f):
                args = self.parser.parse_args(["report", tmp_path, "--json"])
                args.func(args)
            out = f.getvalue()
            res = json.loads(out)
            self.assertEqual(res["employee_name"], "Test Person")
            self.assertEqual(res["summary"]["total_per_diem"], 14.00)
            self.assertEqual(res["summary"]["total_mileage"], 24.00)
            self.assertEqual(res["summary"]["total_reimbursement"], 38.00)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
