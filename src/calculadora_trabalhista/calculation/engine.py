"""Orquestração determinística do cálculo por competência."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from .. import __version__
from ..hashing import sha256_json
from ..models import (
    CalculationLine,
    CalculationManifest,
    CalculationMode,
    CalculationResult,
    CalculationStatus,
    Claim,
    ProcessFacts,
    Provenance,
)
from ..money import quantize_money, to_decimal
from .audit import audit_result
from .reflections import ReflectionGraph


class CalculationEngine:
    """Motor puro: entrada estruturada, saída estruturada, sem chamadas a LLM."""

    def calculate(
        self, facts: ProcessFacts, mode: CalculationMode = CalculationMode.SIMULATION
    ) -> CalculationResult:
        facts = ProcessFacts.model_validate(facts)
        params = facts.calculation_parameters
        lines: list[CalculationLine] = []
        missing: list[str] = list(facts.missing_information)
        warnings: list[str] = []
        claims = {claim.code: claim for claim in facts.claims if claim.requested}
        salaries = {entry.competence: entry for entry in facts.salary_history}
        contract = facts.contracts[0] if facts.contracts else None
        divisor = params.get("divisor") or (contract.divisor if contract else None)
        if divisor is not None:
            divisor = to_decimal(divisor, field="divisor")

        graph_config = params.get("reflection_graph", [])
        graph = ReflectionGraph.from_config(graph_config)
        context: dict[str, Any] = {
            "fgts_rate": params.get("fgts_rate", "0.08"),
            "fgts_fine_rate": params.get("fgts_fine_rate", "0.40"),
            "notice_days": params.get("notice_days")
            or (contract.notice_days if contract else None),
        }
        source_amounts: dict[str, Decimal] = {}
        line_counter = 1

        def add_line(
            code: str,
            label: str,
            category: str,
            amount: Decimal,
            formula: str,
            source_chain: list[str],
            *,
            competence: str | None = None,
            legal_basis: str | None = None,
            parent_code: str | None = None,
            provenance: list[Provenance] | None = None,
        ) -> CalculationLine:
            nonlocal line_counter
            line = CalculationLine(
                order=line_counter,
                code=code,
                label=label,
                category=category,
                competence=competence,
                amount=amount,
                formula=formula,
                source_chain=source_chain,
                legal_basis=legal_basis,
                parent_code=parent_code,
                provenance=provenance or [],
            )
            line_counter += 1
            lines.append(line)
            return line

        overtime_source = self._calculate_overtime(
            claims.get("overtime"),
            params,
            salaries,
            divisor,
            add_line,
            missing,
        )
        if overtime_source:
            source_amounts["overtime"] = quantize_money(sum(overtime_source, Decimal("0")))

        variable_source = self._calculate_variable(
            claims.get("variable_integration"),
            salaries,
            add_line,
        )
        if variable_source:
            source_amounts["variable_integration"] = quantize_money(
                sum(variable_source, Decimal("0"))
            )

        termination_sources = self._calculate_termination(
            claims,
            params,
            salaries,
            contract,
            add_line,
            missing,
        )
        source_amounts.update(termination_sources)

        self._calculate_fgts(
            claims.get("fgts"),
            salaries,
            params,
            add_line,
            source_amounts,
        )

        self._calculate_reflections(
            graph,
            source_amounts,
            context,
            add_line,
            claims,
        )

        audit = audit_result(facts, lines, graph, missing)
        has_error = any(item.status.value == "ERROR" for item in audit)
        has_warning = any(item.status.value == "WARNING" for item in audit) or bool(warnings)
        if has_error:
            status = CalculationStatus.BLOCKED if not lines else CalculationStatus.PARTIAL
        elif missing:
            status = CalculationStatus.PARTIAL
        elif has_warning:
            status = CalculationStatus.AUDITED_WITH_WARNINGS
        else:
            status = CalculationStatus.AUDITED

        totals = {
            "principal": quantize_money(
                sum(
                    (
                        line.amount
                        for line in lines
                        if line.category in {"principal", "termination"}
                    ),
                    Decimal("0"),
                )
            ),
            "reflections": quantize_money(
                sum((line.amount for line in lines if line.category == "reflection"), Decimal("0"))
            ),
            "total_economic": quantize_money(sum((line.amount for line in lines), Decimal("0"))),
        }
        provisional = CalculationResult(
            mode=mode,
            status=status,
            lines=lines,
            audit=audit,
            totals=totals,
            missing_information=missing,
            warnings=warnings,
        )
        result_hash = sha256_json(provisional.as_dict())
        manifest = CalculationManifest(
            engine_version=__version__,
            execution_time=datetime.now(UTC),
            facts_hash=sha256_json(facts.as_dict()),
            rules_hash=sha256_json(params.get("rules", {})),
            official_tables_hash=sha256_json(params.get("official_tables", {})),
            configuration_hash=sha256_json(params),
            result_hash=result_hash,
        )
        provisional.manifest = manifest
        return provisional

    def _calculate_overtime(
        self,
        claim: Claim | None,
        params: dict[str, Any],
        salaries: dict[str, Any],
        divisor: Decimal | None,
        add_line: Any,
        missing: list[str],
    ) -> list[Decimal]:
        if claim is None:
            return []
        if divisor is None:
            missing.append("divisor: necessário para calcular horas extras")
            return []
        hours_by_comp = params.get("overtime_hours_by_competence", {})
        if not hours_by_comp:
            missing.append("overtime_hours_by_competence: quantidade de horas não informada")
            return []
        rate = to_decimal(
            params.get("overtime_rate", claim.parameters.get("rate", "0.50")), field="overtime_rate"
        )
        results: list[Decimal] = []
        for comp, raw_hours in sorted(hours_by_comp.items()):
            salary = salaries.get(comp)
            if salary is None:
                missing.append(f"salary_history[{comp}]")
                continue
            hours = to_decimal(raw_hours, field=f"overtime_hours[{comp}]")
            paid_raw = params.get("overtime_paid_by_competence", {}).get(comp, salary.paid_overtime)
            if paid_raw is None:
                missing.append(f"overtime_paid[{comp}]: pagamento não informado")
                continue
            paid = quantize_money(paid_raw)
            hourly = salary.remuneration / divisor
            due = quantize_money(hourly * (Decimal("1") + rate) * hours)
            difference = quantize_money(due - paid)
            if difference < 0:
                difference = Decimal("0.00")
            code = f"overtime_{comp}"
            add_line(
                code,
                f"Horas extras {int(rate * 100)}%",
                "principal",
                difference,
                f"({salary.remuneration} / {divisor}) × (1 + {rate}) × {hours} - {paid}",
                [
                    f"salary_history:{comp}",
                    f"calculation_parameters:overtime_hours_by_competence.{comp}",
                ],
                competence=comp,
                legal_basis=claim.legal_basis,
                provenance=claim.provenance + salary.provenance,
            )
            results.append(difference)
        return results

    def _calculate_variable(
        self, claim: Claim | None, salaries: dict[str, Any], add_line: Any
    ) -> list[Decimal]:
        if claim is None:
            return []
        values: list[Decimal] = []
        for comp, salary in sorted(salaries.items()):
            if salary.variable is None:
                continue
            amount = quantize_money(salary.variable)
            add_line(
                f"variable_integration_{comp}",
                "Integração de verba variável",
                "principal",
                amount,
                f"variável informada na competência {comp}",
                [f"salary_history:{comp}.variable"],
                competence=comp,
                legal_basis=claim.legal_basis,
                provenance=claim.provenance + salary.provenance,
            )
            values.append(amount)
        return values

    def _calculate_termination(
        self,
        claims: dict[str, Claim],
        params: dict[str, Any],
        salaries: dict[str, Any],
        contract: Any,
        add_line: Any,
        missing: list[str],
    ) -> dict[str, Decimal]:
        claim = claims.get("termination")
        if claim is None:
            return {}
        if contract is None or contract.termination is None:
            missing.append("termination: data de desligamento não informada")
            return {}
        termination_params = params.get("termination", {})
        last_comp = max(salaries) if salaries else None
        last_salary = salaries[last_comp].remuneration if last_comp else None
        if last_salary is None:
            missing.append("salary_history: salário para verbas rescisórias")
            return {}
        result: dict[str, Decimal] = {}
        balance_days = termination_params.get("salary_balance_days")
        if balance_days is None:
            balance_days = contract.termination.day
        balance = quantize_money(last_salary * to_decimal(balance_days) / Decimal("30"))
        add_line(
            "termination_salary_balance",
            "Saldo salarial",
            "termination",
            balance,
            f"{last_salary} × {balance_days} / 30",
            [f"salary_history:{last_comp}", "termination.salary_balance_days"],
            competence=last_comp,
            legal_basis=claim.legal_basis,
            provenance=claim.provenance + contract.provenance,
        )
        result["termination_salary_balance"] = balance

        notice_days = (
            termination_params.get("notice_days")
            or params.get("notice_days")
            or contract.notice_days
        )
        if termination_params.get("notice_indemnified", False):
            if notice_days is None:
                missing.append("notice_days: dias do aviso indenizado não informados")
            else:
                notice = quantize_money(last_salary * to_decimal(notice_days) / Decimal("30"))
                add_line(
                    "termination_notice",
                    "Aviso-prévio indenizado",
                    "termination",
                    notice,
                    f"{last_salary} × {notice_days} / 30",
                    [f"salary_history:{last_comp}", "termination.notice_days"],
                    competence=last_comp,
                    legal_basis=claim.legal_basis,
                    provenance=claim.provenance + contract.provenance,
                )
                result["termination_notice"] = notice

        vac_avos = termination_params.get("vacation_proportional_avos")
        if vac_avos is not None:
            vacation = quantize_money(last_salary * to_decimal(vac_avos) / Decimal("12"))
            one_third = quantize_money(vacation / Decimal("3"))
            add_line(
                "termination_vacation_proportional",
                "Férias proporcionais",
                "termination",
                vacation,
                f"{last_salary} × {vac_avos} / 12",
                [f"salary_history:{last_comp}", "termination.vacation_proportional_avos"],
                competence=last_comp,
                legal_basis=claim.legal_basis,
                provenance=claim.provenance,
            )
            add_line(
                "termination_vacation_one_third",
                "1/3 constitucional sobre férias proporcionais",
                "termination",
                one_third,
                f"{vacation} / 3",
                ["termination_vacation_proportional"],
                competence=last_comp,
                legal_basis=claim.legal_basis,
                parent_code="termination_vacation_proportional",
                provenance=claim.provenance,
            )
            result["termination_vacation_proportional"] = vacation
            result["termination_vacation_one_third"] = one_third

        thirteenth_avos = termination_params.get("thirteenth_proportional_avos")
        if thirteenth_avos is not None:
            thirteenth = quantize_money(last_salary * to_decimal(thirteenth_avos) / Decimal("12"))
            add_line(
                "termination_thirteenth_proportional",
                "13º salário proporcional",
                "termination",
                thirteenth,
                f"{last_salary} × {thirteenth_avos} / 12",
                [f"salary_history:{last_comp}", "termination.thirteenth_proportional_avos"],
                competence=last_comp,
                legal_basis=claim.legal_basis,
                provenance=claim.provenance,
            )
            result["termination_thirteenth_proportional"] = thirteenth
        return result

    def _calculate_fgts(
        self,
        claim: Claim | None,
        salaries: dict[str, Any],
        params: dict[str, Any],
        add_line: Any,
        source_amounts: dict[str, Decimal],
    ) -> None:
        if claim is None:
            return
        rate = to_decimal(params.get("fgts_rate", "0.08"), field="fgts_rate")
        paid_map = params.get("fgts_paid_by_competence", {})
        total = Decimal("0")
        for comp, salary in sorted(salaries.items()):
            base = salary.remuneration
            due = quantize_money(base * rate)
            paid = quantize_money(paid_map.get(comp, salary.paid_fgts or "0"))
            difference = max(Decimal("0.00"), quantize_money(due - paid))
            add_line(
                f"fgts_{comp}",
                "Diferença de FGTS",
                "principal",
                difference,
                f"({base} × {rate}) - {paid}",
                [f"salary_history:{comp}", "calculation_parameters:fgts_rate"],
                competence=comp,
                legal_basis=claim.legal_basis,
                provenance=claim.provenance + salary.provenance,
            )
            total += difference
        source_amounts["fgts"] = quantize_money(total)

    def _calculate_reflections(
        self,
        graph: ReflectionGraph,
        source_amounts: dict[str, Decimal],
        context: dict[str, Any],
        add_line: Any,
        claims: dict[str, Claim],
    ) -> None:
        for edge in graph.edges:
            if not edge.enabled or edge.source not in source_amounts:
                continue
            source_amount = source_amounts[edge.source]
            amount = graph.calculate(source_amount, edge, context)
            code = f"reflection_{edge.source}_{edge.target}"
            add_line(
                code,
                self._reflection_label(edge.target),
                "reflection",
                amount,
                f"{source_amount} → {edge.target} ({edge.calculation_method})",
                [f"source:{edge.source}", f"reflection_graph:{edge.source}->{edge.target}"],
                legal_basis=edge.legal_basis,
                parent_code=edge.source,
                provenance=claims.get(
                    edge.source, Claim(code=edge.source, label=edge.source)
                ).provenance,
            )

    @staticmethod
    def _reflection_label(target: str) -> str:
        labels = {
            "vacations": "Ref. em férias",
            "vacation_1_3": "Ref. em 1/3 de férias",
            "thirteenth": "Ref. em 13º salário",
            "fgts": "Ref. em FGTS",
            "fgts_fine_40": "Ref. em multa de 40% do FGTS",
            "notice": "Ref. em aviso-prévio indenizado",
            "dsr": "Ref. em DSR",
        }
        return labels.get(target, f"Reflexo em {target}")
