"""Modelos de entrada e saída com validação explícita de proveniência."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .money import quantize_money, to_decimal


class FactStatus(StrEnum):
    CONFIRMADO_DOCUMENTO = "CONFIRMADO_DOCUMENTO"
    CONFIRMADO_DECISAO = "CONFIRMADO_DECISAO"
    CONFIRMADO_PETICAO = "CONFIRMADO_PETICAO"
    CONFIRMADO_USUARIO = "CONFIRMADO_USUARIO"
    CALCULADO = "CALCULADO"
    DERIVADO = "DERIVADO"
    ESTIMADO_AUTORIZADO = "ESTIMADO_AUTORIZADO"
    CONFLITANTE = "CONFLITANTE"
    AUSENTE = "AUSENTE"
    NAO_APLICAVEL = "NAO_APLICAVEL"


class CalculationMode(StrEnum):
    INITIAL_CLAIM = "INITIAL_CLAIM"
    LIQUIDATION = "LIQUIDATION"
    EXECUTION = "EXECUTION"
    AUDIT = "AUDIT"
    SIMULATION = "SIMULATION"


class AuditStatus(StrEnum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


class CalculationStatus(StrEnum):
    AUDITED = "AUDITED"
    AUDITED_WITH_WARNINGS = "AUDITED_WITH_WARNINGS"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class Provenance(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: FactStatus
    document: str | None = None
    page: int | None = Field(default=None, ge=1)
    source_excerpt: str | None = None
    decision: str | None = None
    source_url: str | None = None
    confidence: Decimal | None = Field(default=None, ge=0, le=1)

    @field_validator("confidence", mode="before")
    @classmethod
    def validate_confidence(cls, value: Any) -> Decimal | None:
        return None if value is None else to_decimal(value, field="confidence")


class MoneyValue(BaseModel):
    value: Decimal
    provenance: list[Provenance] = Field(default_factory=list)

    @field_validator("value", mode="before")
    @classmethod
    def validate_value(cls, value: Any) -> Decimal:
        return quantize_money(value)


class SalaryEntry(BaseModel):
    competence: str = Field(pattern=r"^\d{4}-\d{2}$")
    base_salary: Decimal
    variable: Decimal | None = None
    additional: Decimal | None = None
    paid_overtime: Decimal | None = None
    paid_fgts: Decimal | None = None
    provenance: list[Provenance] = Field(default_factory=list)

    @field_validator(
        "base_salary", "variable", "additional", "paid_overtime", "paid_fgts", mode="before"
    )
    @classmethod
    def validate_money(cls, value: Any) -> Decimal | None:
        return None if value is None else quantize_money(value)

    @property
    def remuneration(self) -> Decimal:
        """Soma apenas parcelas informadas; ausência permanece auditável."""

        return quantize_money(
            self.base_salary + (self.variable or Decimal("0")) + (self.additional or Decimal("0"))
        )


class WorkSegment(BaseModel):
    start: time
    end: time
    break_minutes: int = Field(default=0, ge=0)


class Timecard(BaseModel):
    date: date
    segments: list[WorkSegment] = Field(min_length=1)
    holiday: bool | None = None
    absence: bool = False
    provenance: list[Provenance] = Field(default_factory=list)


class Contract(BaseModel):
    admission: date
    termination: date | None = None
    termination_reason: str | None = None
    role: str | None = None
    work_schedule: str | None = None
    weekly_hours: Decimal | None = None
    divisor: Decimal | None = None
    notice_days: Decimal | None = None
    notice_type: Literal["TRABALHADO", "INDENIZADO"] | None = None
    salary_history: list[SalaryEntry] = Field(default_factory=list)
    provenance: list[Provenance] = Field(default_factory=list)

    @field_validator("weekly_hours", "divisor", "notice_days", mode="before")
    @classmethod
    def validate_decimal(cls, value: Any) -> Decimal | None:
        return None if value is None else to_decimal(value)

    @model_validator(mode="after")
    def validate_dates(self) -> Contract:
        if self.termination is not None and self.termination < self.admission:
            raise ValueError("termination não pode ser anterior à admission")
        return self


class Claim(BaseModel):
    code: str
    label: str
    requested: bool = True
    legal_basis: str | None = None
    provenance: list[Provenance] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    id: str
    document_type: str
    filename: str | None = None
    pages: int | None = Field(default=None, ge=1)
    source_url: str | None = None
    sha256: str | None = None


class ProcessFacts(BaseModel):
    """Schema de `process_facts.json`; campos extras são preservados."""

    model_config = ConfigDict(extra="allow")

    metadata: dict[str, Any] = Field(default_factory=dict)
    process: dict[str, Any] = Field(default_factory=dict)
    parties: dict[str, Any] = Field(default_factory=dict)
    contracts: list[Contract] = Field(default_factory=list)
    functions: list[dict[str, Any]] = Field(default_factory=list)
    salary_history: list[SalaryEntry] = Field(default_factory=list)
    remuneration_items: list[dict[str, Any]] = Field(default_factory=list)
    work_schedules: list[dict[str, Any]] = Field(default_factory=list)
    timecards: list[Timecard] = Field(default_factory=list)
    vacations: list[dict[str, Any]] = Field(default_factory=list)
    absences: list[dict[str, Any]] = Field(default_factory=list)
    leaves: list[dict[str, Any]] = Field(default_factory=list)
    collective_agreements: list[dict[str, Any]] = Field(default_factory=list)
    payments: list[dict[str, Any]] = Field(default_factory=list)
    fgts: list[dict[str, Any]] = Field(default_factory=list)
    termination: dict[str, Any] = Field(default_factory=dict)
    claims: list[Claim] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    executive_title: dict[str, Any] = Field(default_factory=dict)
    calculation_parameters: dict[str, Any] = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_salary_source(self) -> ProcessFacts:
        if not self.salary_history:
            for contract in self.contracts:
                self.salary_history.extend(contract.salary_history)
        return self

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=False)


class CalculationLine(BaseModel):
    order: int
    code: str
    label: str
    category: str
    competence: str | None = None
    amount: Decimal
    formula: str
    source_chain: list[str] = Field(default_factory=list)
    legal_basis: str | None = None
    parent_code: str | None = None
    provenance: list[Provenance] = Field(default_factory=list)

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: Any) -> Decimal:
        return quantize_money(value)


class AuditCheck(BaseModel):
    name: str
    status: AuditStatus
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class CalculationManifest(BaseModel):
    engine_version: str
    execution_time: datetime
    facts_hash: str
    rules_hash: str
    official_tables_hash: str
    configuration_hash: str
    result_hash: str


class CalculationResult(BaseModel):
    mode: CalculationMode
    status: CalculationStatus
    lines: list[CalculationLine]
    audit: list[AuditCheck]
    totals: dict[str, Decimal]
    missing_information: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    manifest: CalculationManifest | None = None

    @property
    def total(self) -> Decimal:
        return self.totals.get("total_economic", Decimal("0.00"))

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=False)
