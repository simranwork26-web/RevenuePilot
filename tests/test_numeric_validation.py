import tempfile
import unittest
from pathlib import Path

from src.ingest import validate_numeric_column


class TestNumericValidation(unittest.TestCase):
    def validate_csv(self, contents, **rules):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)

        path = Path(temporary_directory.name) / "sample.csv"
        path.write_text(contents, encoding="utf-8")

        return validate_numeric_column(path, "value", **rules)

    def test_accepts_positive_price(self):
        self.validate_csv(
            "value\n0.85\n100.00\n",
            minimum=0.01,
            allow_zero=False,
        )

    def test_allows_zero_freight(self):
        self.validate_csv(
            "value\n0.00\n12.50\n",
            minimum=0,
            allow_zero=True,
        )

    def test_rejects_blank_value(self):
        with self.assertRaisesRegex(ValueError, "Blank numeric value"):
            self.validate_csv("value\n \n")

    def test_rejects_non_numeric_value(self):
        with self.assertRaisesRegex(ValueError, "Non-numeric value"):
            self.validate_csv("value\nunknown\n")

    def test_rejects_negative_value(self):
        with self.assertRaisesRegex(ValueError, "below minimum"):
            self.validate_csv("value\n-1.00\n", minimum=0)

    def test_rejects_zero_when_disallowed(self):
        with self.assertRaisesRegex(ValueError, "Zero value"):
            self.validate_csv("value\n0\n", allow_zero=False)

    def test_accepts_positive_integer_installments(self):
        self.validate_csv(
            "value\n1\n12\n24\n",
            minimum=1,
            require_integer=True,
        )

    def test_rejects_zero_installments(self):
        with self.assertRaisesRegex(ValueError, "below minimum"):
            self.validate_csv(
                "value\n0\n",
                minimum=1,
                require_integer=True,
            )

    def test_rejects_fractional_installments(self):
        with self.assertRaisesRegex(ValueError, "Non-integer value"):
            self.validate_csv(
                "value\n1.5\n",
                minimum=1,
                require_integer=True,
            )

    def test_rejects_non_finite_values(self):
        with self.assertRaisesRegex(ValueError, "Non-finite numeric value"):
            self.validate_csv("value\nNaN\n")


if __name__ == "__main__":
    unittest.main()
