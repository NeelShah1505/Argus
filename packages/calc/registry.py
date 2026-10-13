from decimal import Decimal
from typing import Callable, Dict, List, Optional
from packages.canonical import AccuracyTier, DerivedMetric, Fact

TIER_SEVERITY = {
    AccuracyTier.VERIFIED: 1,
    AccuracyTier.EXTRACTED: 2,
    AccuracyTier.ESTIMATED: 3,
    AccuracyTier.NEEDS_REVIEW: 4,
    AccuracyTier.FAILED: 5,
}


def get_lowest_tier(tiers: List[AccuracyTier]) -> AccuracyTier:
    if not tiers:
        return AccuracyTier.NEEDS_REVIEW
    sorted_tiers = sorted(tiers, key=lambda t: TIER_SEVERITY[t], reverse=True)
    return sorted_tiers[0]


class CalculationError(Exception):
    pass


class FormulaRegistry:
    def __init__(self):
        self._formulas: Dict[str, Dict] = {}
        self._register_default_formulas()

    def register_formula(
        self,
        formula_id: str,
        name: str,
        required_metrics: List[str],
        compute_fn: Callable[[List[Fact]], Decimal],
    ):
        self._formulas[formula_id] = {
            "id": formula_id,
            "name": name,
            "required_metrics": required_metrics,
            "compute_fn": compute_fn,
        }

    def _register_default_formulas(self):
        # Revenue Growth: (rev_curr - rev_prev) / rev_prev
        def compute_growth(facts: List[Fact]) -> Decimal:
            rev_curr, rev_prev = facts[0].value, facts[1].value
            if rev_prev == Decimal("0"):
                raise CalculationError("Cannot compute growth: prior period revenue is zero.")
            return ((rev_curr - rev_prev) / rev_prev).quantize(Decimal("0.0001"))

        self.register_formula("revenue_growth", "Revenue Growth", ["revenue_curr", "revenue_prev"], compute_growth)

        # Gross Margin: gross_profit / revenue
        def compute_gross_margin(facts: List[Fact]) -> Decimal:
            gp, rev = facts[0].value, facts[1].value
            if rev == Decimal("0"):
                raise CalculationError("Cannot compute margin: revenue is zero.")
            return (gp / rev).quantize(Decimal("0.0001"))

        self.register_formula("gross_margin", "Gross Margin", ["gross_profit", "revenue"], compute_gross_margin)

        # Operating Margin: operating_income / revenue
        def compute_op_margin(facts: List[Fact]) -> Decimal:
            oi, rev = facts[0].value, facts[1].value
            if rev == Decimal("0"):
                raise CalculationError("Cannot compute margin: revenue is zero.")
            return (oi / rev).quantize(Decimal("0.0001"))

        self.register_formula("operating_margin", "Operating Margin", ["operating_income", "revenue"], compute_op_margin)

        # Current Ratio: current_assets / current_liabilities
        def compute_curr_ratio(facts: List[Fact]) -> Decimal:
            ca, cl = facts[0].value, facts[1].value
            if cl == Decimal("0"):
                raise CalculationError("Cannot compute current ratio: liabilities are zero.")
            return (ca / cl).quantize(Decimal("0.01"))

        self.register_formula("current_ratio", "Current Ratio", ["current_assets", "current_liabilities"], compute_curr_ratio)

    def execute_calculation(
        self,
        formula_id: str,
        input_facts: List[Fact],
        tenant_id: str = "tenant_default",
    ) -> DerivedMetric:
        if formula_id not in self._formulas:
            raise CalculationError(f"Formula '{formula_id}' not found in registry.")

        form = self._formulas[formula_id]
        if len(input_facts) != len(form["required_metrics"]):
            raise CalculationError(
                f"Formula '{formula_id}' requires {len(form['required_metrics'])} facts, received {len(input_facts)}."
            )

        # 1. Guard against Needs Review or Failed facts
        for f in input_facts:
            if f.tier in [AccuracyTier.NEEDS_REVIEW, AccuracyTier.FAILED]:
                raise CalculationError(
                    f"Calculation blocked: input fact '{f.id}' ({f.metric}) has tier '{f.tier.value}'. Must be Verified or Extracted."
                )

        # 2. Currency compatibility guard
        currencies = {f.currency for f in input_facts if f.currency}
        if len(currencies) > 1:
            raise CalculationError(f"Currency mismatch among inputs: {currencies}. Calculations require matching currencies.")

        # 3. Compute
        result_value = form["compute_fn"](input_facts)

        # 4. Tier inheritance: lowest tier of inputs
        derived_tier = get_lowest_tier([f.tier for f in input_facts])

        # 5. Build lineage DAG
        lineage_dag = {
            "formula_id": formula_id,
            "formula_name": form["name"],
            "inputs": [
                {
                    "fact_id": f.id,
                    "metric": f.metric,
                    "period": f.period,
                    "value": str(f.value),
                    "currency": f.currency,
                    "tier": f.tier.value,
                    "evidence": f.evidence.model_dump(),
                }
                for f in input_facts
            ],
            "result": str(result_value),
        }

        return DerivedMetric(
            id=f"metric_{formula_id}_{input_facts[0].period}",
            tenant_id=tenant_id,
            formula_id=formula_id,
            formula_name=form["name"],
            input_fact_ids=[f.id for f in input_facts],
            calculated_value=result_value,
            tier=derived_tier,
            lineage_dag=lineage_dag,
        )


_registry_instance: Optional[FormulaRegistry] = None


def get_formula_registry() -> FormulaRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = FormulaRegistry()
    return _registry_instance
