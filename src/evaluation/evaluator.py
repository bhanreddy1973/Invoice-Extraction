"""Compare pipeline outputs to labelled ground truth."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.evaluation.metrics import accuracy
from src.evaluation.normalizer import (
    normalize_currency,
    normalize_date,
    normalize_string,
    numbers_equal,
)
from src.pipeline import InvoicePipeline, PipelineResult


FIELDS = [
    "is_invoice",
    "vendor",
    "invoice_number",
    "invoice_date",
    "currency",
    "line_items",
    "tax_total",
    "total",
]


@dataclass
class FieldScore:
    field: str
    correct: int = 0
    total: int = 0

    @property
    def acc(self) -> float:
        return accuracy(self.correct, self.total)


@dataclass
class DocumentEval:
    document: str
    field_matches: dict[str, bool]
    schema_valid: bool
    financial_valid: bool
    overall_exact: bool
    prediction: dict[str, Any] | None
    ground_truth: dict[str, Any]
    error_code: str | None = None


@dataclass
class EvaluationReport:
    documents: list[DocumentEval] = field(default_factory=list)
    field_scores: dict[str, FieldScore] = field(default_factory=dict)
    schema_success: float = 0.0
    financial_success: float = 0.0
    overall_accuracy: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents_evaluated": len(self.documents),
            "field_accuracy": {
                name: {"correct": s.correct, "total": s.total, "accuracy": s.acc}
                for name, s in self.field_scores.items()
            },
            "schema_success_rate": self.schema_success,
            "financial_success_rate": self.financial_success,
            "overall_accuracy": self.overall_accuracy,
            "documents": [
                {
                    "document": d.document,
                    "field_matches": d.field_matches,
                    "schema_valid": d.schema_valid,
                    "financial_valid": d.financial_valid,
                    "overall_exact": d.overall_exact,
                    "error_code": d.error_code,
                }
                for d in self.documents
            ],
        }


class Evaluator:
    def __init__(self, pipeline: InvoicePipeline | None = None) -> None:
        self.pipeline = pipeline or InvoicePipeline()

    def evaluate_labelled_dir(
        self,
        documents_dir: Path,
        ground_truth_dir: Path,
    ) -> EvaluationReport:
        docs = sorted(
            [
                p
                for p in documents_dir.iterdir()
                if p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
            ]
        )
        report = EvaluationReport(field_scores={f: FieldScore(field=f) for f in FIELDS})
        schema_ok = 0
        financial_ok = 0
        overall_ok = 0

        for doc_path in docs:
            gt_path = ground_truth_dir / f"{doc_path.stem}.json"
            gt = json.loads(gt_path.read_text(encoding="utf-8"))
            result = self.pipeline.process(doc_path)
            doc_eval = self._compare(doc_path.name, result, gt)
            report.documents.append(doc_eval)

            for field_name, matched in doc_eval.field_matches.items():
                score = report.field_scores[field_name]
                score.total += 1
                if matched:
                    score.correct += 1
            if doc_eval.schema_valid:
                schema_ok += 1
            if doc_eval.financial_valid:
                financial_ok += 1
            if doc_eval.overall_exact:
                overall_ok += 1

        n = len(report.documents) or 1
        report.schema_success = schema_ok / n
        report.financial_success = financial_ok / n
        report.overall_accuracy = overall_ok / n
        return report

    def _compare(self, name: str, result: PipelineResult, gt: dict[str, Any]) -> DocumentEval:
        pred = result.invoice
        matches: dict[str, bool] = {}
        if pred is None:
            matches = {f: False for f in FIELDS}
            return DocumentEval(
                document=name,
                field_matches=matches,
                schema_valid=False,
                financial_valid=False,
                overall_exact=False,
                prediction=None,
                ground_truth=gt,
                error_code=result.error_code,
            )

        matches["is_invoice"] = pred.get("is_invoice") == gt.get("is_invoice")
        matches["vendor"] = normalize_string(pred.get("vendor")) == normalize_string(gt.get("vendor"))
        matches["invoice_number"] = normalize_string(pred.get("invoice_number")) == normalize_string(
            gt.get("invoice_number")
        )
        matches["invoice_date"] = normalize_date(pred.get("invoice_date")) == normalize_date(
            gt.get("invoice_date")
        )
        matches["currency"] = normalize_currency(pred.get("currency")) == normalize_currency(
            gt.get("currency")
        )
        matches["tax_total"] = numbers_equal(pred.get("tax_total"), gt.get("tax_total"))
        matches["total"] = numbers_equal(pred.get("total"), gt.get("total"))
        matches["line_items"] = self._line_items_match(pred.get("line_items"), gt.get("line_items"))

        financial_valid = True
        if result.financial is not None:
            financial_valid = bool(result.financial.get("is_valid"))

        return DocumentEval(
            document=name,
            field_matches=matches,
            schema_valid=result.schema_valid,
            financial_valid=financial_valid,
            overall_exact=all(matches.values()),
            prediction=pred,
            ground_truth=gt,
            error_code=result.error_code,
        )

    def _line_items_match(self, pred: Any, gt: Any) -> bool:
        if pred is None and gt is None:
            return True
        if not isinstance(pred, list) or not isinstance(gt, list):
            return False
        if len(pred) != len(gt):
            return False
        # Order-sensitive exact match after normalization (assignment-friendly, no fuzzy awards)
        for p_item, g_item in zip(pred, gt, strict=True):
            if normalize_string(p_item.get("description")) != normalize_string(g_item.get("description")):
                return False
            if not numbers_equal(p_item.get("quantity"), g_item.get("quantity"), tol=Decimal("0.001")):
                # both null counts as equal via numbers_equal
                if not (p_item.get("quantity") is None and g_item.get("quantity") is None):
                    return False
            if not numbers_equal(p_item.get("amount"), g_item.get("amount")):
                return False
        return True


def format_report_table(report: EvaluationReport) -> str:
    lines = [
        "=========================================",
        "INVOICE EXTRACTION EVALUATION",
        "=========================================",
        "",
        f"Documents evaluated: {len(report.documents)}",
        "",
        "FIELD LEVEL ACCURACY",
        "",
        f"{'Field':<18}{'Correct':<12}{'Accuracy'}",
        "-----------------------------------------",
    ]
    for name in FIELDS:
        score = report.field_scores[name]
        lines.append(f"{name:<18}{score.correct:<12}{score.acc * 100:.1f}%")
    lines.extend(
        [
            "-----------------------------------------",
            f"Schema success rate: {report.schema_success * 100:.1f}%",
            f"Financial success rate: {report.financial_success * 100:.1f}%",
            f"Overall accuracy: {report.overall_accuracy * 100:.1f}%",
            "=========================================",
        ]
    )
    return "\n".join(lines)
