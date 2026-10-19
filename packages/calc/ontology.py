"""
Canonical Financial Metric Ontology & Synonym Tables.

Provides standardized US-GAAP and IFRS financial metric classifications
and resolves multi-variant corporate filing labels (e.g., "Net Sales",
"Revenues from external customers", "Turnover") into canonical keys.
"""

import re
from typing import Dict, List, Optional, Set

# Standardized financial concepts and their empirical corporate filing aliases
CANONICAL_SYNONYM_MAP: Dict[str, List[str]] = {
    # Income Statement
    "revenue": [
        "revenue", "revenues", "total revenue", "total revenues",
        "net sales", "sales", "sales revenue", "net revenue", "net revenues",
        "turnover", "operating revenue", "operating revenues",
        "revenue from contracts with customers", "product sales", "total net sales",
    ],
    "cost_of_sales": [
        "cost of sales", "cost of goods sold", "cogs", "cost of products sold",
        "cost of revenue", "cost of revenues", "operating costs of sales",
        "cost of services", "costs and expenses of goods sold",
    ],
    "gross_profit": [
        "gross profit", "gross margin", "gross income", "gross operating profit",
    ],
    "operating_expenses": [
        "operating expenses", "total operating expenses", "opex",
        "operating costs", "selling, general and administrative expenses",
        "sg&a", "sga",
    ],
    "research_and_development": [
        "research and development", "r&d", "r and d", "research & development",
    ],
    "operating_income": [
        "operating income", "operating profit", "operating earnings",
        "income from operations", "operating profit (loss)", "operating income (loss)",
        "operating result",
    ],
    "net_income": [
        "net income", "net earnings", "net profit", "net income (loss)",
        "net earnings (loss)", "profit for the year", "profit for the period",
        "net profit attributable to shareholders",
    ],
    "ebitda": [
        "ebitda", "adjusted ebitda", "operating profit before depreciation",
    ],
    # Balance Sheet
    "cash_and_equivalents": [
        "cash and cash equivalents", "cash & cash equivalents", "cash and equivalents",
        "cash", "cash and short-term investments", "cash, cash equivalents and restricted cash",
    ],
    "accounts_receivable": [
        "accounts receivable", "trade receivables", "accounts and notes receivable",
        "receivables", "trade accounts receivable",
    ],
    "inventory": [
        "inventory", "inventories", "merchandise inventories", "finished goods",
    ],
    "current_assets": [
        "current assets", "total current assets",
    ],
    "total_assets": [
        "total assets", "assets",
    ],
    "accounts_payable": [
        "accounts payable", "trade payables", "accounts payable and accrued liabilities",
    ],
    "total_debt": [
        "total debt", "debt", "total borrowings", "borrowings", "aggregate debt",
        "funded debt", "long-term debt and short-term debt",
    ],
    "short_term_debt": [
        "short term debt", "short-term debt", "current portion of long-term debt",
        "current debt", "commercial paper",
    ],
    "current_liabilities": [
        "current liabilities", "total current liabilities",
    ],
    "long_term_debt": [
        "long term debt", "long-term debt", "non-current debt", "term debt",
    ],
    "total_liabilities": [
        "total liabilities", "liabilities",
    ],
    "stockholders_equity": [
        "stockholders equity", "stockholders' equity", "shareholders equity",
        "shareholders' equity", "total equity", "total stockholders' equity",
        "total shareholders' equity",
    ],
    # Cash Flow Statement
    "operating_cash_flow": [
        "operating cash flow", "cash flows from operating activities",
        "cash provided by operating activities", "net cash from operations",
        "net cash provided by (used in) operating activities",
    ],
    "capex": [
        "capex", "capital expenditures", "payments for property, plant and equipment",
        "additions to property, plant and equipment", "capital additions",
    ],
    "free_cash_flow": [
        "free cash flow", "fcf",
    ],
    "dividends_paid": [
        "dividends paid", "cash dividends paid", "payments of dividends",
    ],
}

# Reverse lookup dictionary for O(1) resolution
_REVERSE_SYNONYM_LOOKUP: Dict[str, str] = {}
for canonical_key, aliases in CANONICAL_SYNONYM_MAP.items():
    _REVERSE_SYNONYM_LOOKUP[canonical_key] = canonical_key
    for alias in aliases:
        _REVERSE_SYNONYM_LOOKUP[alias.lower().strip()] = canonical_key


def clean_metric_label(raw_label: str) -> str:
    """Cleans punctuation, footnote markers (e.g. '(Note 3)'), and extra whitespace."""
    text = raw_label.lower().strip()
    # Strip footnote notes: "(note 4)", "(note 3a)", "[1]", "(1)"
    text = re.sub(r"[\(\[]\s*(?:note(?:\s+\w+)?|\d+)\s*[\)\]]", "", text, flags=re.IGNORECASE)
    # Strip trailing punctuation, colons, asterisks, footnote symbols
    text = re.sub(r"[:*†‡,\.\-]+$", "", text)
    # Strip commas and hyphens inside words
    text = re.sub(r"[,\-_]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def resolve_canonical_metric(raw_label: str) -> str:
    """
    Deterministically maps any corporate filing metric string into its canonical key.
    If no alias is matched, returns the cleaned label string.
    """
    cleaned = clean_metric_label(raw_label)

    # 1. Direct O(1) dictionary match
    if cleaned in _REVERSE_SYNONYM_LOOKUP:
        return _REVERSE_SYNONYM_LOOKUP[cleaned]

    # 2. Tokenized substring matching with negative guardrails
    # Revenue checks (guard against deferred/unearned)
    if ("revenue" in cleaned or "sales" in cleaned or "turnover" in cleaned) and not (
        "deferred" in cleaned or "unearned" in cleaned or "cost" in cleaned or "margin" in cleaned
    ):
        return "revenue"

    # Cost of sales checks
    if ("cost of goods" in cleaned or "cogs" in cleaned or "cost of sales" in cleaned or "cost of revenue" in cleaned):
        return "cost_of_sales"

    # Operating income checks
    if ("operating income" in cleaned or "operating profit" in cleaned or "income from operations" in cleaned):
        return "operating_income"

    # Net income checks
    if ("net income" in cleaned or "net earnings" in cleaned or "net profit" in cleaned):
        return "net_income"

    # Cash checks
    if ("cash and cash" in cleaned or "cash and cash equivalents" in cleaned):
        return "cash_and_equivalents"

    # Assets checks
    if cleaned in ["total assets", "assets"]:
        return "total_assets"
    if cleaned in ["total liabilities", "liabilities"]:
        return "total_liabilities"
    if cleaned in ["total equity", "equity", "shareholders equity", "stockholders equity"]:
        return "stockholders_equity"

    return cleaned
