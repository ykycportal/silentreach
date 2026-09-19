"""
Knowledge Graph Service - bridges SilentReach scrapers with Semantica.
Transforms raw web intelligence into structured marketing knowledge.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class KGConfig:
    """Configuration for knowledge graph storage."""
    backend: str = "sqlite"  # sqlite, neo4j, falkordb
    connection_string: Optional[str] = None
    storage_path: Optional[Path] = None
    auto_ingest: bool = True
    
    def __post_init__(self):
        if self.storage_path is None:
            self.storage_path = Path.home() / ".silentreach" / "kg"
        
        # Ensure paths exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "graphs").mkdir(exist_ok=True)
        (self.storage_path / "reports").mkdir(exist_ok=True)
        (self.storage_path / "agents").mkdir(exist_ok=True)


@dataclass
class Entity:
    """An extracted entity from scraped content."""
    name: str
    type: str  # Person, Company, Product, Concept, Platform, Trend, etc.
    confidence: float
    sources: list = field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    facts: list = field(default_factory=list)  # (predicate, object, source, confidence)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "confidence": self.confidence,
            "sources": self.sources,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "fact_count": len(self.facts),
            "sample_facts": self.facts[:3],
        }


@dataclass
class Conflict:
    """A detected conflict between sources."""
    entity: str
    fact_1: str
    source_1: str
    credibility_1: float
    fact_2: str
    source_2: str
    credibility_2: float
    confidence: float  # How confident we are this is a real conflict
    
    def to_dict(self) -> dict:
        return {
            "entity": self.entity,
            "claim_a": self.fact_1,
            "source_a": self.source_1,
            "credibility_a": self.credibility_1,
            "claim_b": self.fact_2,
            "source_b": self.source_2,
            "credibility_b": self.credibility_2,
            "conflict_confidence": self.confidence,
        }


class KGService:
    """
    Knowledge Graph Service for Marketing Intelligence.
    
    Converts SilentReach scraped results into:
    - Structured knowledge graphs (entities, relations, facts)
    - Conflict reports (when sources disagree)
    - Agent-ready JSON (for AI marketing agents to consume)
    - Human-readable reports (for marketing teams)
    """
    
    # Platform credibility scores for marketing context
    PLATFORM_CREDIBILITY = {
        "reddit": 0.65,      # Anonymous, mixed quality
        "twitter": 0.50,     # High noise, fast-moving
        "youtube": 0.60,     # Video content, varies
        "linkedin": 0.80,    # Professional context
        "bilibili": 0.55,    # Chinese platform, regional
        "v2ex": 0.75,        # Tech-focused, higher quality
        "rss": 0.85,         # Curated sources
        "instagram": 0.45,   # Visual, less analytical
        "facebook": 0.50,    # Mixed demographics
        "xiaohongshu": 0.60, # Chinese lifestyle, reviews
    }
    
    # Marketing-relevant entity types
    ENTITY_TYPES = {
        "brand": "Company",
        "company": "Company",
        "product": "Product",
        "person": "Person",
        "ceo": "Person",
        "founder": "Person",
        "influencer": "Person",
        "trend": "Trend",
        "platform": "Platform",
        "channel": "Platform",
        "campaign": "Campaign",
        "strategy": "Concept",
        "metric": "Concept",
        "competitor": "Company",
        "tool": "Product",
        "software": "Product",
        "saas": "Product",
    }
    
    def __init__(self, config: Optional[KGConfig] = None):
        self.config = config or KGConfig()
        self._entities: dict[str, Entity] = {}
        self._relations: list[dict] = []
        self._provenance: list[dict] = []
        self._created_at = datetime.utcnow()
        
        # Paths are already created in KGConfig.__post_init__
    
    # -------------------------------------------------------------------------
    # Core Ingestion
    # -------------------------------------------------------------------------
    
    async def ingest_results(self, results: dict, topic: str, session_id: Optional[str] = None) -> dict:
        """
        Ingest scraped results into the knowledge graph.
        
        Args:
            results: Dict of {platform: ScrapedResult}
            topic: Research topic
            session_id: Optional session identifier
        
        Returns:
            Ingestion report with statistics
        """
        session_id = session_id or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report = {
            "session_id": session_id,
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat(),
            "entities_extracted": 0,
            "relations_extracted": 0,
            "conflicts_found": 0,
            "platforms_processed": [],
            "platforms_skipped": [],
        }
        
        for platform, result in results.items():
            if result.error or not result.data:
                report["platforms_skipped"].append(platform)
                logger.warning(f"Skipping {platform}: {result.error or 'no data'}")
                continue
            
            report["platforms_processed"].append(platform)
            
            for item in result.data:
                text = self._extract_text(item)
                if not text:
                    continue
                
                # Extract entities and relations
                entities = self._extract_entities(text, platform)
                triplets = self._extract_triplets(text, platform)
                
                report["entities_extracted"] += len(entities)
                report["relations_extracted"] += len(triplets)
                
                # Store entities
                for entity in entities:
                    self._add_entity(entity, platform, item)
                
                # Store relations
                for triplet in triplets:
                    self._add_relation(triplet, platform, item)
        
        # Detect conflicts after ingestion
        report["conflicts_found"] = len(self.detect_conflicts())
        
        # Save session
        self._save_session(session_id, report)
        
        return report
    
    # -------------------------------------------------------------------------
    # Entity Management
    # -------------------------------------------------------------------------
    
    def _add_entity(self, entity: dict, platform: str, source_item: dict):
        """Add or update an entity in the graph."""
        name = entity["name"]
        now = datetime.utcnow()
        
        if name in self._entities:
            existing = self._entities[name]
            existing.sources.append(platform)
            existing.last_seen = now
            if entity.get("type"):
                existing.type = entity["type"]
        else:
            self._entities[name] = Entity(
                name=name,
                type=entity.get("type", "Concept"),
                confidence=entity.get("confidence", 0.7),
                sources=[platform],
                first_seen=now,
                last_seen=now,
            )
    
    def _extract_entities(self, text: str, platform: str) -> list[dict]:
        """Extract marketing-relevant entities from text.
        
        Tries Semantica LLM-based extraction first, falls back to pattern matching.
        """
        entities = []
        
        # Try Semantica first (LLM-powered NER)
        semantica_entities = self._try_semantica_extract(text)
        if semantica_entities:
            entities.extend(semantica_entities)
        
        # Always add pattern-based extraction as fallback
        entities.extend(self._extract_pattern_entities(text, platform))
        
        # Deduplicate
        return self._deduplicate_entities(entities)
    
    def _try_semantica_extract(self, text: str) -> list[dict]:
        """Try to extract entities using Semantica LLM. Returns empty list if unavailable."""
        try:
            from semantica.semantic_extract import SemanticExtractor
            
            extractor = SemanticExtractor()
            # Process in batch for efficiency
            result = extractor.process_batch([text])
            
            entities = []
            for entity in result.get("entities", []):
                entities.append({
                    "name": entity.get("text", ""),
                    "type": entity.get("label", "Entity"),
                    "confidence": entity.get("confidence", 0.8),
                })
            
            if entities:
                logger.debug(f"Extracted {len(entities)} entities via Semantica")
            
            return entities
        except ImportError:
            # Semantica not installed, fall back to patterns
            return []
        except Exception as e:
            logger.warning(f"Semantica extraction failed: {e}")
            return []
    
    def _extract_pattern_entities(self, text: str, platform: str) -> list[dict]:
        """Pattern-based entity extraction (fallback when Semantica unavailable)."""
        entities = []
        text_lower = text.lower()
        
        # Brand/company detection
        brand_patterns = [
            (r'\bshopify\b', 'Company'),
            (r'\bsell\s?on\s+amazon\b', 'Platform'),
            (r'\btiktok\s?shop\b', 'Platform'),
            (r'\bmeta\s?ads\b', 'Platform'),
            (r'\bgoogle\s?ads\b', 'Platform'),
            (r'\bfacebook\s?ads\b', 'Platform'),
            (r'\bclaud\b', 'Product'),
            (r'\bclaude\s?code\b', 'Product'),
            (r'\bcursor\b', 'Product'),
            (r'\bwindsurf\b', 'Product'),
            (r'\bhermes\b', 'Product'),
            (r'\bdropshipping\b', 'Concept'),
            (r'\bdirect\s?to\s?consumer\b', 'Strategy'),
            (r'\bDTC\b', 'Strategy'),
            (r'\bemail\s?marketing\b', 'Channel'),
            (r'\bcontent\s?marketing\b', 'Channel'),
            (r'\bsocial\s?media\s?marketing\b', 'Channel'),
            (r'\bseo\b', 'Strategy'),
            (r'\bsem\b', 'Strategy'),
            (r'\bppc\b', 'Strategy'),
            (r'\broas\b', 'Metric'),
            (r'\bcpa\b', 'Metric'),
            (r'\bctr\b', 'Metric'),
            (r'\bconversion\s?rate\b', 'Metric'),
            (r'\bchurn\b', 'Metric'),
            (r'\bltv\b', 'Metric'),
            (r'\bcac\b', 'Metric'),
        ]
        
        for pattern, etype in brand_patterns:
            if pattern.lower() in text_lower:
                name = pattern.split()[0].title() if " " in pattern else pattern.title()
                entities.append({
                    "name": name,
                    "type": etype,
                    "confidence": 0.85,
                })
        
        # Named entity heuristic (capitalized words that look like names)
        import re
        # Skip common non-entities
        skip_words = {
            "the", "and", "for", "with", "from", "this", "that", "these", "those",
            "was", "are", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "may", "might",
            "can", "know", "get", "got", "just", "like", "also", "very", "really",
            "much", "many", "more", "most", "other", "some", "such", "than", "too",
            "into", "over", "after", "before", "between", "through", "during",
            "about", "against", "above", "under", "again", "further", "then",
            "once", "here", "there", "when", "where", "why", "how", "all", "each",
            "every", "both", "few", "new", "old", "same", "high", "low", "long",
            "great", "small", "large", "right", "left", "next", "last", "first",
            "well", "back", "still", "any", "only", "own", "out", "up", "down",
            "off", "by", "at", "an", "or", "if", "it", "is", "in", "on", "as",
        }
        
        # Extract capitalized phrases that might be entities
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for phrase in capitalized:
            words = phrase.split()
            if any(w.lower() in skip_words for w in words):
                continue
            if len(phrase) > 2 and len(phrase) < 50:
                entities.append({
                    "name": phrase,
                    "type": "Entity",
                    "confidence": 0.5,
                })
        
        return entities
    
    def _deduplicate_entities(self, entities: list[dict]) -> list[dict]:
        """Remove duplicate entities by name (case-insensitive)."""
        seen = set()
        unique = []
        for e in entities:
            key = e["name"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique
    
    # -------------------------------------------------------------------------
    # Relation Extraction
    # -------------------------------------------------------------------------
    
    def _add_relation(self, triplet: tuple, platform: str, source_item: dict):
        """Add a relation to the graph."""
        subject, predicate, obj = triplet
        self._relations.append({
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "source_platform": platform,
            "source_url": source_item.get("url", ""),
            "recorded_at": datetime.utcnow().isoformat(),
        })
        
        # Add fact to entity if exists
        if subject in self._entities:
            self._entities[subject].facts.append({
                "predicate": predicate,
                "object": obj,
                "source": platform,
                "confidence": 0.6,
            })
    
    def _extract_triplets(self, text: str, platform: str) -> list[tuple]:
        """Extract subject-predicate-object triplets from text."""
        triplets = []
        
        # Pattern 1: "X is Y"
        import re
        is_patterns = re.findall(r'(\w+(?:\s+\w+)?)\s+is\s+(\w+(?:\s+\w+)?)', text)
        for subj, obj in is_patterns:
            if len(subj) > 2 and len(obj) > 2:
                triplets.append((subj.title(), "is", obj.title()))
        
        # Pattern 2: "X uses Y"
        uses_patterns = re.findall(r'(\w+(?:\s+\w+)?)\s+uses\s+(\w+(?:\s+\w+)?)', text)
        for subj, obj in uses_patterns:
            if len(subj) > 2 and len(obj) > 2:
                triplets.append((subj.title(), "uses", obj.title()))
        
        # Pattern 3: "X vs Y"
        vs_patterns = re.findall(r'(\w+(?:\s+\w+)?)\s+vs\.?\s+(\w+(?:\s+\w+)?)', text)
        for a, b in vs_patterns:
            if len(a) > 2 and len(b) > 2:
                triplets.append((a.title(), "compared_to", b.title()))
        
        # Pattern 4: "X for Y"
        for_patterns = re.findall(r'(\w+(?:\s+\w+)?)\s+for\s+(\w+(?:\s+\w+)?)', text)
        for subj, obj in for_patterns:
            if len(subj) > 2 and len(obj) > 2:
                triplets.append((subj.title(), "used_for", obj.title()))
        
        return triplets
    
    def _extract_text(self, item: dict) -> str:
        """Extract readable text from scraped item."""
        fields = ["text", "content", "body", "description", "title"]
        for field in fields:
            if field in item and isinstance(item[field], str):
                return item[field]
        return ""
    
    def _platform_credibility(self, platform: str) -> float:
        """Get credibility score for a platform."""
        return self.PLATFORM_CREDIBILITY.get(platform, 0.5)
    
    # -------------------------------------------------------------------------
    # Conflict Detection
    # -------------------------------------------------------------------------
    
    def detect_conflicts(self) -> list[Conflict]:
        """Find conflicting facts across sources."""
        conflicts = []
        
        # Group facts by entity
        entity_facts: dict[str, list] = {}
        for entity_name, entity in self._entities.items():
            for fact in entity.facts:
                key = f"{fact['predicate']}_{fact['object']}"
                if key not in entity_facts:
                    entity_facts[key] = []
                entity_facts[key].append({
                    "entity": entity_name,
                    "fact": fact,
                })
        
        # Check for contradictions
        for key, facts in entity_facts.items():
            if len(facts) < 2:
                continue
            
            # Look for opposing predicates
            predicates = set(f["fact"]["predicate"] for f in facts)
            if len(predicates) > 1:
                for i, f1 in enumerate(facts):
                    for f2 in facts[i+1:]:
                        if f1["fact"]["predicate"] != f2["fact"]["predicate"]:
                            conflicts.append(Conflict(
                                entity=f1["entity"],
                                fact_1=f1["fact"]["object"],
                                source_1=f1["fact"]["source"],
                                credibility_1=self.PLATFORM_CREDIBILITY.get(f1["fact"]["source"], 0.5),
                                fact_2=f2["fact"]["object"],
                                source_2=f2["fact"]["source"],
                                credibility_2=self.PLATFORM_CREDIBILITY.get(f2["fact"]["source"], 0.5),
                                confidence=0.7,
                            ))
        
        return conflicts
    
    # -------------------------------------------------------------------------
    # Query Interface
    # -------------------------------------------------------------------------
    
    def query_entities(self, search_term: Optional[str] = None, entity_type: Optional[str] = None) -> list[dict]:
        """Query entities with optional filters."""
        results = []
        
        for name, entity in self._entities.items():
            if search_term and search_term.lower() not in name.lower():
                continue
            if entity_type and entity.type != entity_type:
                continue
            
            results.append(entity.to_dict())
        
        return sorted(results, key=lambda x: x["fact_count"], reverse=True)
    
    def query_relations(self, subject: Optional[str] = None, predicate: Optional[str] = None) -> list[dict]:
        """Query relations with optional filters."""
        results = []
        
        for rel in self._relations:
            if subject and subject.lower() not in rel["subject"].lower():
                continue
            if predicate and predicate.lower() not in rel["predicate"].lower():
                continue
            
            results.append(rel)
        
        return results
    
    # -------------------------------------------------------------------------
    # Output Formatters
    # -------------------------------------------------------------------------
    
    def to_agent_json(self) -> str:
        """Export as agent-ready JSON (compact, structured)."""
        data = {
            "graph_version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "entity_count": len(self._entities),
            "relation_count": len(self._relations),
            "conflict_count": len(self.detect_conflicts()),
            "entities": {name: e.to_dict() for name, e in self._entities.items()},
            "relations": self._relations[-100:],  # Last 100 relations
            "top_conflicts": [c.to_dict() for c in self.detect_conflicts()[:10]],
        }
        return json.dumps(data, indent=2, default=str)
    
    def to_markdown_report(self, title: str = "Marketing Intelligence Report") -> str:
        """Export as human-readable markdown report."""
        lines = [
            f"# {title}",
            f"",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Entities:** {len(self._entities)} | **Relations:** {len(self._relations)} | **Conflicts:** {len(self.detect_conflicts())}",
            f"",
            f"---",
            f"",
        ]
        
        # Executive Summary
        lines.extend([
            "## Executive Summary",
            "",
            f"This knowledge graph contains **{len(self._entities)} entities** extracted from web intelligence sources.",
            "",
        ])
        
        # Entity categories
        type_counts = {}
        for e in self._entities.values():
            type_counts[e.type] = type_counts.get(e.type, 0) + 1
        
        lines.append("**Entity Breakdown:**")
        lines.append("")
        for etype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {etype}: {count}")
        lines.append("")
        
        # Key Entities
        lines.extend([
            "## Key Entities",
            "",
        ])
        
        top_entities = sorted(
            self._entities.values(),
            key=lambda e: len(e.facts),
            reverse=True
        )[:10]
        
        for i, entity in enumerate(top_entities, 1):
            lines.extend([
                f"### {i}. {entity.name}",
                "",
                f"- **Type:** {entity.type}",
                f"- **Sources:** {', '.join(set(entity.sources))}",
                f"- **Facts:** {len(entity.facts)}",
                "",
            ])
            
            # Sample facts
            for fact in entity.facts[:3]:
                lines.append(f"  - {fact['predicate']}: {fact['object']} ({fact['source']})")
            lines.append("")
        
        # Conflicts
        conflicts = self.detect_conflicts()
        if conflicts:
            lines.extend([
                "## ⚠️  Detected Conflicts",
                "",
                f"Found {len(conflicts)} potential conflicts across sources:",
                "",
            ])
            
            for i, conflict in enumerate(conflicts[:5], 1):
                lines.extend([
                    f"### {i}. {conflict.entity}",
                    "",
                    f"- **Claim A:** {conflict.fact_1} (from {conflict.source_1}, credibility: {conflict.credibility_1})",
                    f"- **Claim B:** {conflict.fact_2} (from {conflict.source_2}, credibility: {conflict.credibility_2})",
                    f"- **Confidence:** {conflict.confidence:.0%}",
                    "",
                ])
        
        # Top Relations
        lines.extend([
            "## Top Relations",
            "",
        ])
        
        top_rels = sorted(self._relations, key=lambda r: r.get("recorded_at", ""), reverse=True)[:15]
        for rel in top_rels:
            lines.append(f"- {rel['subject']} → {rel['predicate']} → {rel['object']}")
        lines.append("")
        
        # Recommendations
        lines.extend([
            "## Recommendations",
            "",
        ])
        
        if conflicts:
            lines.append("1. **Resolve conflicts**: Multiple sources disagree on key claims. Verify with primary sources.")
        if len(self._entities) < 5:
            lines.append("2. **Expand research**: Low entity count. Consider deeper searches across more platforms.")
        else:
            lines.append("1. **Validate top entities**: Cross-reference key findings with primary sources.")
        lines.append("2. **Monitor for changes**: Re-run intelligence collection weekly to track evolution.")
        lines.append("3. **Feed to agents**: Export agent JSON for automated analysis workflows.")
        lines.append("")
        
        return "\n".join(lines)
    
    def to_csv(self) -> str:
        """Export as CSV for spreadsheet analysis."""
        import io
        
        output = io.StringIO()
        writer = __import__('csv').writer(output)
        
        # Header
        writer.writerow(["Entity", "Type", "Sources", "Fact Count", "First Seen", "Last Seen"])
        
        # Rows
        for name, entity in self._entities.items():
            writer.writerow([
                name,
                entity.type,
                "; ".join(set(entity.sources)),
                len(entity.facts),
                entity.first_seen.strftime("%Y-%m-%d") if entity.first_seen else "",
                entity.last_seen.strftime("%Y-%m-%d") if entity.last_seen else "",
            ])
        
        return output.getvalue()
    
    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------
    
    def _save_session(self, session_id: str, report: dict):
        """Save session data to disk."""
        session_path = self.config.storage_path / "graphs" / f"{session_id}.json"
        data = {
            "report": report,
            "entities": {name: e.to_dict() for name, e in self._entities.items()},
            "relations": self._relations,
            "saved_at": datetime.utcnow().isoformat(),
        }
        with open(session_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved KG session to {session_path}")
    
    def load_session(self, session_id: Optional[str] = None) -> bool:
        """Load a previous session's graph data."""
        # storage_path is guaranteed non-None by KGConfig.__post_init__
        assert self.config.storage_path is not None
        
        graphs_dir = self.config.storage_path / "graphs"
        
        if session_id is None:
            # Load most recent
            graphs = sorted(
                (p for p in graphs_dir.glob("*.json")),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if not graphs:
                return False
            session_id = graphs[0].stem
        
        session_path = graphs_dir / f"{session_id}.json"
        if not session_path.exists():
            return False
        
        with open(session_path) as f:
            data = json.load(f)
        
        self._entities = {
            name: Entity(**props) 
            for name, props in data.get("entities", {}).items()
        }
        self._relations = data.get("relations", [])
        
        return True
    
    def list_sessions(self) -> list[dict]:
        """List available KG sessions."""
        graphs_dir = self.config.storage_path / "graphs"
        if not graphs_dir.exists():
            return []
        
        sessions = []
        for path in sorted(graphs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            with open(path) as f:
                data = json.load(f)
            sessions.append({
                "id": path.stem,
                "topic": data.get("report", {}).get("topic", "Unknown"),
                "timestamp": data.get("saved_at", ""),
                "entities": data.get("report", {}).get("entities_extracted", 0),
                "relations": data.get("report", {}).get("relations_extracted", 0),
            })
        
        return sessions
