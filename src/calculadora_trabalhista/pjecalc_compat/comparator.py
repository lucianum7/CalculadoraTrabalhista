from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from ..models import CalculationResult
from ..money import quantize_money, to_decimal


class ComparisonRow(BaseModel):
    code: str
    expected: Decimal
    actual: Decimal
    absolute_difference: Decimal
    relative_difference: Decimal | None
    status: str


def compare_results(
    result: CalculationResult, expected: dict[str, Any], tolerance: str = "0.01"
) -> list[ComparisonRow]:
    actual_map = {line.code: line.amount for line in result.lines}
    rows: list[ComparisonRow] = []
    tolerance_decimal = to_decimal(tolerance)
    for code, raw_expected in expected.items():
        expected_value = quantize_money(raw_expected)
        actual_value = quantize_money(actual_map.get(code, "0"))
        difference = quantize_money(abs(expected_value - actual_value))
        relative = None if expected_value == 0 else difference / abs(expected_value)
        rows.append(
            ComparisonRow(
                code=code,
                expected=expected_value,
                actual=actual_value,
                absolute_difference=difference,
                relative_difference=relative,
                status="PASS" if difference <= tolerance_decimal else "FAIL",
            )
        )
    return rows
