from .calc import router as calc_router
from .documents import router as documents_router
from .insights import router as insights_router
from .queries import router as queries_router

__all__ = ["calc_router", "documents_router", "insights_router", "queries_router"]
