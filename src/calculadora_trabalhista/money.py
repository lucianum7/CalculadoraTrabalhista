"""Operações monetárias determinísticas.

Nenhuma função deste módulo aceita `float` silenciosamente. Valores externos
devem chegar como strings ou inteiros para manter precisão reprodutível.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, getcontext
from typing import Any

getcontext().prec = 40
CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def to_decimal(value: Any, *, field: str = "valor") -> Decimal:
    """Converte um valor de entrada para Decimal sem passar por float."""

    if isinstance(value, bool):
        raise TypeError(f"{field} não aceita booleano como valor monetário")
    if isinstance(value, float):
        raise TypeError(f"{field} não aceita float; use string ou Decimal")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} inválido: {value!r}") from exc


def quantize_money(value: Any) -> Decimal:
    """Arredonda para centavos com ROUND_HALF_UP."""

    return to_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def add_money(*values: Any) -> Decimal:
    return quantize_money(sum((to_decimal(v) for v in values), ZERO))


def percentage(base: Any, rate: Any) -> Decimal:
    """Aplica uma taxa expressa como 0.08 ou como Decimal("8")."""

    rate_decimal = to_decimal(rate, field="taxa")
    if rate_decimal > 1:
        rate_decimal /= Decimal("100")
    return quantize_money(to_decimal(base) * rate_decimal)


def format_brl(value: Any) -> str:
    """Formata valor para exibição brasileira sem alterar o valor calculado."""

    amount = quantize_money(value)
    sign = "-" if amount < 0 else ""
    integer, cents = f"{abs(amount):.2f}".split(".")
    integer = f"{int(integer):,}".replace(",", ".")
    return f"{sign}R$ {integer},{cents}"
