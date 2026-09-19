"""
SilentReach Knowledge Graph Services.

Exports for marketing intelligence:
- KGService: bridges scrapers → knowledge graph
- MarketingReportGenerator: creates human/agent-ready reports
"""

from .kg_service import KGService, KGConfig, Entity, Conflict
from .report_generator import MarketingReportGenerator

__all__ = [
    "KGService",
    "KGConfig",
    "Entity",
    "Conflict",
    "MarketingReportGenerator",
]
