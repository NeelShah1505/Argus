from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AnomalyRecord(BaseModel):
    rule_id: str
    rule_name: str
    severity: str  # Critical, High, Medium, Low
    affected_element_ids: List[str]
    description: str
    details: Dict[str, Any] = {}


def check_yoy_outlier(
    metric_name: str,
    val_prev: Decimal,
    val_curr: Decimal,
    threshold: Decimal = Decimal("0.40"),
    element_id: str = "",
) -> Optional[AnomalyRecord]:
    """
    Flags YoY swings exceeding 40% for review.
    """
    if val_prev == Decimal("0"):
        return None

    pct_change = abs((val_curr - val_prev) / val_prev)
    if pct_change > threshold:
        return AnomalyRecord(
            rule_id="ANOM-03",
            rule_name="YoY Variance Outlier",
            severity="Medium",
            affected_element_ids=[element_id] if element_id else [],
            description=f"{metric_name} experienced an abnormal YoY change of {pct_change * 100:.1f}%.",
            details={
                "metric": metric_name,
                "prev_val": str(val_prev),
                "curr_val": str(val_curr),
                "pct_change": str(pct_change),
            },
        )
    return None
