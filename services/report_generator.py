"""
Marketing Intelligence Report Generator
Creates human-readable reports and agent-ready data from KG data.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class MarketingReportGenerator:
    """
    Generates marketing intelligence reports from knowledge graph data.
    
    Outputs:
    - Human-readable markdown reports for marketing teams
    - Structured JSON for AI marketing agents
    - Executive summaries for quick decision-making
    """
    
    def __init__(self, kg_service):
        self.kg = kg_service
    
    def generate_executive_summary(self, topic: str) -> dict:
        """Generate executive summary for marketing leadership."""
        conflicts = self.kg.detect_conflicts()
        entities = list(self.kg._entities.values())
        
        # Categorize entities
        companies = [e for e in entities if e.type == "Company"]
        products = [e for e in entities if e.type == "Product"]
        trends = [e for e in entities if e.type == "Trend"]
        strategies = [e for e in entities if e.type == "Concept" and "strategy" in " ".join(f[0] for f in e.facts).lower()]
        
        # Confidence scoring
        high_confidence = [e for e in entities if e.confidence >= 0.7]
        medium_confidence = [e for e in entities if 0.5 <= e.confidence < 0.7]
        low_confidence = [e for e in entities if e.confidence < 0.5]
        
        summary = {
            "topic": topic,
            "generated_at": datetime.utcnow().isoformat(),
            "overall_confidence": self._calculate_overall_confidence(entities),
            "entity_count": len(entities),
            "key_findings": {
                "companies_mentioned": len(companies),
                "products_mentioned": len(products),
                "trends_identified": len(trends),
                "active_strategies": len(strategies),
            },
            "data_quality": {
                "high_confidence": len(high_confidence),
                "medium_confidence": len(medium_confidence),
                "low_confidence": len(low_confidence),
            },
            "risk_factors": {
                "conflicts_detected": len(conflicts),
                "low_credibility_sources": len([e for e in entities if any(
                    self.kg.PLATFORM_CREDIBILITY.get(s, 0.5) < 0.5 for s in e.sources
                )]),
            },
            "recommendations": self._generate_recommendations(entities, conflicts),
        }
        
        return summary
    
    def generate_agent_bundle(self, topic: str, include_raw: bool = True) -> dict:
        """
        Generate agent-ready bundle with structured data.
        
        This is what marketing AI agents consume for their workflows.
        """
        bundle = {
            "version": "1.0",
            "topic": topic,
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": self.generate_executive_summary(topic),
            "entities": self.kg.query_entities(),
            "relations": self.kg._relations[-50:],  # Recent relations
            "conflicts": [c.to_dict() for c in self.kg.detect_conflicts()],
        }
        
        if include_raw:
            bundle["raw_kg_json"] = self.kg.to_agent_json()
        
        return bundle
    
    def generate_campaign_brief(self, topic: str, target_audience: Optional[str] = None) -> str:
        """
        Generate a campaign brief based on gathered intelligence.
        
        Useful for marketing teams to plan campaigns.
        """
        entities = self.kg.query_entities()
        conflicts = self.kg.detect_conflicts()
        
        lines = [
            f"# Campaign Intelligence Brief: {topic}",
            f"",
            f"**Prepared:** {datetime.utcnow().strftime('%B %d, %Y')}",
            f"**For:** Marketing Team",
            f"",
            f"---",
            f"",
        ]
        
        # Key Insights
        lines.extend([
            "## Key Insights",
            "",
        ])
        
        # Top companies/brands mentioned
        companies = [e for e in entities if isinstance(e, dict) and e.get("type") == "Company"]
        if companies:
            lines.extend([
                "### Competitive Landscape",
                "",
            ])
            for company in companies[:5]:
                lines.append(f"- **{company['name']}**: Mentioned in {', '.join(set(company.get('sources', [])))}")
            lines.append("")
        
        # Trends identified
        trends = [e for e in entities if isinstance(e, dict) and e.get("type") == "Trend"]
        if trends:
            lines.extend([
                "### Emerging Trends",
                "",
            ])
            for trend in trends[:5]:
                lines.append(f"- **{trend.name}**: ({trend.confidence:.0%} confidence)")
            lines.append("")
        
        # Conflicts & Risks
        if conflicts:
            lines.extend([
                "## ⚠️  Intelligence Conflicts",
                "",
                "Sources disagree on the following points. Verify before acting:",
                "",
            ])
            for conflict in conflicts[:3]:
                lines.append(f"1. **{conflict.entity}**: '{conflict.fact_1}' vs '{conflict.fact_2}'")
            lines.append("")
        
        # Strategic Recommendations
        lines.extend([
            "## Strategic Recommendations",
            "",
        ])
        
        recommendations = self._generate_recommendations(entities, conflicts)
        for i, rec in enumerate(recommendations[:5], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")
        
        # Data Sources
        lines.extend([
            "## Data Sources",
            "",
        ])
        
        all_sources = set()
        for e in entities:
            if isinstance(e, dict):
                all_sources.update(e.get("sources", []))
            else:
                all_sources.update(e.sources)
        
        for source in sorted(all_sources):
            lines.append(f"- {source.capitalize()}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _calculate_overall_confidence(self, entities) -> float:
        """Calculate overall confidence score for the intelligence gathering."""
        if not entities:
            return 0.0
        
        # Handle both Entity objects and dicts
        total = 0
        count = 0
        for e in entities:
            if isinstance(e, dict):
                total += e.get("confidence", 0.5)
            else:
                total += e.confidence
            count += 1
        
        return total / count if count > 0 else 0.0
    
    def _generate_recommendations(self, entities, conflicts) -> list[str]:
        """Generate actionable recommendations based on intelligence."""
        recs = []
        
        # If lots of conflicts, recommend verification
        if len(conflicts) > 2:
            recs.append(
                "Multiple sources conflict on key claims. Prioritize primary sources "
                "and direct research before making decisions."
            )
        
        # If high company count, recommend competitive analysis
        companies = [e for e in entities if isinstance(e, dict) and e.get("type") == "Company"]
        if len(companies) > 3:
            recs.append(
                f"Strong competitive landscape identified ({len(companies)} companies). "
                "Consider deep-dive competitive analysis for top 3."
            )
        
        # If trends found, recommend monitoring
        trends = [e for e in entities if isinstance(e, dict) and e.get("type") == "Trend"]
        if trends:
            recs.append(
                f"Identified {len(trends)} emerging trends. Set up tracking to monitor "
                "evolution and adjust strategy accordingly."
            )
        
        # If low confidence overall, recommend more research
        avg_conf = self._calculate_overall_confidence(entities)
        if avg_conf < 0.6:
            recs.append(
                "Overall intelligence confidence is low. Conduct additional research "
                "across higher-credibility sources (LinkedIn, RSS, V2EX)."
            )
        
        if not recs:
            recs.append("Intelligence gathering complete. Review key entities and proceed with campaign planning.")
        
        return recs
    
    def export_bundle(self, topic: str, output_dir: Optional[Path] = None) -> dict:
        """
        Export complete intelligence bundle to disk.
        
        Returns paths to generated files.
        """
        output_dir = output_dir or Path.home() / ".silentreach" / "reports" / topic.replace(" ", "_")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Generate all outputs
        files = {}
        
        # 1. Executive summary (JSON for agents)
        exec_summary = self.generate_executive_summary(topic)
        summary_path = output_dir / f"executive_summary_{timestamp}.json"
        with open(summary_path, "w") as f:
            json.dump(exec_summary, f, indent=2)
        files["executive_summary"] = str(summary_path)
        
        # 2. Full agent bundle
        bundle = self.generate_agent_bundle(topic)
        bundle_path = output_dir / f"agent_bundle_{timestamp}.json"
        with open(bundle_path, "w") as f:
            json.dump(bundle, f, indent=2, default=str)
        files["agent_bundle"] = str(bundle_path)
        
        # 3. Campaign brief (Markdown for humans)
        brief = self.generate_campaign_brief(topic)
        brief_path = output_dir / f"campaign_brief_{timestamp}.md"
        with open(brief_path, "w") as f:
            f.write(brief)
        files["campaign_brief"] = str(brief_path)
        
        # 4. Entities CSV
        csv_content = self.kg.to_csv()
        csv_path = output_dir / f"entities_{timestamp}.csv"
        with open(csv_path, "w") as f:
            f.write(csv_content)
        files["entities_csv"] = str(csv_path)
        
        logger.info(f"Exported intelligence bundle to {output_dir}")
        return files
