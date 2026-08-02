from decimal import ROUND_HALF_UP, Decimal

from app.domain.schemas import QuoteInput, QuoteResult

MAX_MINOR_UNITS = 9_000_000_000_000


def _apply_basis_points(value: int, basis_points: int) -> int:
    result = (Decimal(value) * Decimal(basis_points) / Decimal(10_000)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(result)


def calculate_quote(value: QuoteInput) -> QuoteResult:
    if not value.student_hours_low <= value.student_hours_base <= value.student_hours_high:
        raise ValueError("Effort estimates must be ordered low, base, high")
    if value.lead_hours > 0 and value.lead_rate_minor <= 0:
        raise ValueError("Lead work must use a positive compensation rate")

    student_low = value.student_hours_low * value.student_rate_minor
    student_base = value.student_hours_base * value.student_rate_minor
    student_high = value.student_hours_high * value.student_rate_minor
    lead = value.lead_hours * value.lead_rate_minor

    def total(student: int) -> int:
        labor = _apply_basis_points(student + lead, value.risk_multiplier_basis_points)
        fee = _apply_basis_points(labor, value.platform_fee_basis_points)
        tax = _apply_basis_points(labor + fee, value.tax_basis_points)
        amount = labor + fee + tax
        if amount < 0 or amount > MAX_MINOR_UNITS:
            raise ValueError("Quote exceeds supported money bounds")
        return amount

    base_labor = _apply_basis_points(student_base + lead, value.risk_multiplier_basis_points)
    platform_fee = _apply_basis_points(base_labor, value.platform_fee_basis_points)
    tax = _apply_basis_points(base_labor + platform_fee, value.tax_basis_points)
    return QuoteResult(
        low_minor=total(student_low),
        base_minor=total(student_base),
        high_minor=total(student_high),
        currency=value.currency,
        line_items={
            "student_compensation": student_base,
            "lead_compensation": lead,
            "risk_adjustment": base_labor - student_base - lead,
            "platform_fee": platform_fee,
            "tax": tax,
        },
        revision_rounds=value.revision_rounds,
        formula_version="pilot-2026-01",
    )
