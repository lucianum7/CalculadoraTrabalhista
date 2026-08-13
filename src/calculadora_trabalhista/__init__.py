"""CalculadoraTrabalhista: engine local para cálculos trabalhistas auditáveis."""

from .models import CalculationMode, CalculationResult, ProcessFacts

__all__ = ["CalculationMode", "CalculationResult", "ProcessFacts"]
__version__ = "0.1.0"
