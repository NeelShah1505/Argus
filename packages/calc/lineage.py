from typing import Dict, List, Optional
from packages.canonical import DerivedMetric


class LineageGraph:
    def __init__(self):
        self._metrics: Dict[str, DerivedMetric] = {}  # metric_id -> DerivedMetric
        self._fact_to_metrics: Dict[str, List[str]] = {}  # fact_id -> list of metric_ids

    def register_derived_metric(self, metric: DerivedMetric):
        self._metrics[metric.id] = metric
        for fact_id in metric.input_fact_ids:
            self._fact_to_metrics.setdefault(fact_id, []).append(metric.id)

    def get_metric(self, metric_id: str) -> Optional[DerivedMetric]:
        return self._metrics.get(metric_id)

    def get_lineage(self, metric_id: str) -> Optional[Dict]:
        metric = self.get_metric(metric_id)
        if not metric:
            return None
        return {
            "metric_id": metric.id,
            "formula_name": metric.formula_name,
            "calculated_value": str(metric.calculated_value),
            "tier": metric.tier.value,
            "lineage_dag": metric.lineage_dag,
        }

    def invalidate_fact(self, fact_id: str) -> List[str]:
        """
        Invalidates and returns all dependent derived metrics when a primary fact changes.
        """
        affected_ids = self._fact_to_metrics.pop(fact_id, [])
        for mid in affected_ids:
            self._metrics.pop(mid, None)
        return affected_ids


_lineage_graph: Optional[LineageGraph] = None


def get_lineage_graph() -> LineageGraph:
    global _lineage_graph
    if _lineage_graph is None:
        _lineage_graph = LineageGraph()
    return _lineage_graph
