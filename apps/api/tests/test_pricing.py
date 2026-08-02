import pytest

from app.domain.pricing import calculate_quote
from app.domain.schemas import QuoteInput


def test_quote_uses_integer_minor_units_and_itemizes_lead_pay() -> None:
    result = calculate_quote(
        QuoteInput(
            student_hours_low=10,
            student_hours_base=20,
            student_hours_high=30,
            student_rate_minor=5000,
            lead_hours=4,
            lead_rate_minor=10000,
            platform_fee_basis_points=1500,
            risk_multiplier_basis_points=11000,
            tax_basis_points=0,
            currency="USD",
            revision_rounds=2,
        )
    )
    assert result.low_minor < result.base_minor < result.high_minor
    assert result.line_items["student_compensation"] == 100_000
    assert result.line_items["lead_compensation"] == 40_000
    assert result.line_items["platform_fee"] > 0
    assert result.revision_rounds == 2


def test_quote_rejects_unordered_estimates() -> None:
    with pytest.raises(ValueError, match="ordered"):
        calculate_quote(
            QuoteInput(
                student_hours_low=20,
                student_hours_base=10,
                student_hours_high=30,
                student_rate_minor=5000,
                lead_hours=0,
                lead_rate_minor=0,
                platform_fee_basis_points=0,
                risk_multiplier_basis_points=10000,
                tax_basis_points=0,
                currency="USD",
                revision_rounds=2,
            )
        )


def test_quote_rejects_unpaid_lead_work() -> None:
    with pytest.raises(ValueError, match="positive compensation"):
        calculate_quote(
            QuoteInput(
                student_hours_low=10,
                student_hours_base=20,
                student_hours_high=30,
                student_rate_minor=5000,
                lead_hours=2,
                lead_rate_minor=0,
                platform_fee_basis_points=0,
                risk_multiplier_basis_points=10000,
                tax_basis_points=0,
                currency="USD",
                revision_rounds=2,
            )
        )
