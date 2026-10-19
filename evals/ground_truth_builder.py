"""
Automated Ground Truth Builder from SEC EDGAR XBRL.

Parses official SEC EDGAR companyfacts JSON into canonical GroundTruthFiling
records with certified decimal values, US-GAAP concept mappings, and sign conventions.
"""

from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Common US-GAAP concepts to extract for the benchmark
CRITICAL_GAAP_METRICS = {
    # Income statement
    "total_revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "Revenues",
    ],
    "cost_of_sales": [
        "CostOfGoodsAndServicesSold",
        "CostOfRevenue",
    ],
    "gross_profit": [
        "GrossProfit",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
    ],
    "net_income": [
        "NetIncomeLoss",
    ],
    # Balance sheet
    "total_assets": [
        "Assets",
    ],
    "total_liabilities": [
        "Liabilities",
    ],
    "stockholders_equity": [
        "StockholdersEquity",
    ],
    "cash_and_equivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
    ],
}


class GroundTruthField(BaseModel):
    metric: str
    gaap_concept: str
    expected_value: Decimal
    scale: Decimal = Decimal("1.0")
    currency: str = "USD"
    is_negative: bool = False
    source_form: str = "10-K"
    fiscal_year: int
    period: str


class GroundTruthFiling(BaseModel):
    ticker: str
    company_name: str
    cik: str
    fiscal_year: int
    period: str
    critical_fields: List[GroundTruthField]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "cik": self.cik,
            "fiscal_year": self.fiscal_year,
            "period": self.period,
            "critical_fields": [
                {
                    "metric": f.metric,
                    "gaap_concept": f.gaap_concept,
                    "expected_value": str(f.expected_value),
                    "scale": str(f.scale),
                    "currency": f.currency,
                    "is_negative": f.is_negative,
                    "source_form": f.source_form,
                    "fiscal_year": f.fiscal_year,
                    "period": f.period,
                }
                for f in self.critical_fields
            ],
        }


def _find_best_fact(units_list: List[Dict[str, Any]], fiscal_year: int) -> Optional[Dict[str, Any]]:
    """Select the 10-K full year filing fact for the given fiscal year."""
    candidates = []
    for item in units_list:
        if item.get("form") == "10-K" and item.get("fp") == "FY" and item.get("fy") == fiscal_year:
            candidates.append(item)
    if not candidates:
        # Fallback: look for item with matching fy and fp=="FY"
        for item in units_list:
            if item.get("fp") == "FY" and item.get("fy") == fiscal_year:
                candidates.append(item)
    if not candidates:
        return None
    # Prefer filed latest (highest filed date)
    candidates.sort(key=lambda x: str(x.get("filed", "")), reverse=True)
    return candidates[0]


def build_ground_truth_from_facts(
    facts_json: Dict[str, Any],
    ticker: str,
    fiscal_year: int = 2024,
) -> GroundTruthFiling:
    """
    Extracts standardized critical fields for the specified fiscal year
    from raw SEC EDGAR companyfacts JSON.
    """
    company_name = facts_json.get("entityName", ticker)
    cik = str(facts_json.get("cik", "")).zfill(10)
    us_gaap = facts_json.get("facts", {}).get("us-gaap", {})

    fields: List[GroundTruthField] = []

    for metric_name, concepts in CRITICAL_GAAP_METRICS.items():
        matched_concept = None
        matched_fact = None

        for concept in concepts:
            if concept in us_gaap:
                units = us_gaap[concept].get("units", {})
                usd_units = units.get("USD", [])
                best = _find_best_fact(usd_units, fiscal_year)
                if best is not None:
                    matched_concept = concept
                    matched_fact = best
                    break

        if matched_fact is not None and matched_concept is not None:
            raw_val = matched_fact.get("val")
            if raw_val is not None:
                val_dec = Decimal(str(raw_val))
                is_neg = val_dec < 0
                # Cost of sales is conventionally represented as negative in statements of operations
                if metric_name == "cost_of_sales" and val_dec > 0:
                    is_neg = True

                fields.append(
                    GroundTruthField(
                        metric=metric_name,
                        gaap_concept=matched_concept,
                        expected_value=val_dec,
                        scale=Decimal("1.0"),
                        currency="USD",
                        is_negative=is_neg,
                        source_form=matched_fact.get("form", "10-K"),
                        fiscal_year=fiscal_year,
                        period=f"FY{fiscal_year}",
                    )
                )

    return GroundTruthFiling(
        ticker=ticker,
        company_name=company_name,
        cik=cik,
        fiscal_year=fiscal_year,
        period=f"FY{fiscal_year}",
        critical_fields=fields,
    )


def save_ground_truth_filing(filing: GroundTruthFiling, output_dir: Optional[Path] = None) -> Path:
    out = output_dir or (Path(__file__).parent / "golden")
    out.mkdir(parents=True, exist_ok=True)
    file_path = out / f"{filing.ticker}_10K_FY{filing.fiscal_year}.json"
    file_path.write_text(json.dumps(filing.to_dict(), indent=2), encoding="utf-8")
    return file_path
