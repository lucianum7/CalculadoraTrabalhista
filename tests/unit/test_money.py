from decimal import Decimal

import pytest

from calculadora_trabalhista.money import format_brl, percentage, quantize_money, to_decimal


def test_rounding_is_half_up() -> None:
    assert quantize_money("1.005") == Decimal("1.01")
    assert quantize_money("-1.005") == Decimal("-1.01")


def test_float_is_rejected() -> None:
    with pytest.raises(TypeError):
        to_decimal(1.2)


def test_percentage_and_format() -> None:
    assert percentage("100.00", "8") == Decimal("8.00")
    assert format_brl("1234.50") == "R$ 1.234,50"
