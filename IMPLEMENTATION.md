# SilentReach + Semantica Integration - Implementation Plan

## Objective
Combine SilentReach's web scraping with Semantica's knowledge graph capabilities to create an intelligent research system that doesn't just collect data—it understands it.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SilentReach Framework                     │
├─────────────────────────────────────────────────────────────┤
│  CLI Layer                                                   │
│  ├─ search (existing)                                        │
│  ├─ intel (existing)                                         │
│  └─ kg (NEW) ← knowledge graph commands                      │
├─────────────────────────────────────────────────────────────┤
│  Service Layer                                               │
│  ├─ KGService      ← bridges scrapers → Semantica            │
│  ├─ ConflictDetector ← flags cross-platform contradictions   │
│  └─ EntityResolver ← merges same entity across sources       │
├─────────────────────────────────────────────────────────────┤
│  Scraper Layer (unchanged)                                   │
│  └─ returns ScrapedResult[] with provenance metadata         │
├─────────────────────────────────────────────────────────────┤
│  Semantica Layer (new dependency)                            │
│  ├─ semantic_extract    NER + relations + triplets           │
│  ├─ kg                 Graph construction & queries          │
│  ├─ provenance         W3C PROV-O audit trail                │
│  └─ conflicts          Cross-source conflict detection       │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Add KGService (`services/kg_service.py`)

```python
"""
Knowledge Graph Service - bridges SilentReach scrapers with Semantica KG.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class KGConfig:
    """Configuration for knowledge graph storage."""
    backend: str = "sqlite"  # sqlite, neo4j, falkordb
    connection_string: Optional[str] = None
    storage_path: Path = None
    
    def __post_init__(self):
        if self.storage_path is None:
            self.storage_path = Path.home() / ".silentreach" / "kg"


class KGService:
    """
    Integrates SilentReach scraped results into a Semantica knowledge graph.
    
    Usage:
        service = KGService()
        await service.ingest_results(results, topic="AI regulation")
        conflicts = service.find_conflicts("AI")
    """
    
    def __init__(self, config: Optional[KgConfig] = None):
        self.config = config or KGConfig()
        self._session = None
        self._provenance = None
        
        # Create storage directories
        self.config.storage_path.mkdir(parents=True, exist_ok=True)
        (self.config.storage_path / "provenance").mkdir(exist_ok=True)
        (self.config.storage_path / "graphs").mkdir(exist_ok=True)
    
    async def _ensure_session(self):
        """Lazy-initialize Semantica graph session."""
        if self._session is not None:
            return
        
        try:
            from semantica.kg import GraphSession
            from semantica.provenance import ProvenanceManager
            
            conn = self.config.connection_string or str(
                self.config.storage_path / "provenance" / "kg.db"
            )
            
            self._session = GraphSession(backend=self.config.backend, connection=conn)
            self._provenance = ProvenanceManager(
                storage_path=str(self.config.storage_path / "provenance")
            )
            
            logger.info(f"Initialized KG session with backend={self.config.backend}")
            
        except ImportError:
            raise ImportError(
                "Semantica not installed. Install with: pip install 'silentreach[kg]'"
            )
    
    async def ingest_results(self, results: dict, topic: str, session_id: str = None):
        """
        Ingest scraped results into the knowledge graph.
        
        Args:
            results: Dict of {platform: ScrapedResult}
            topic: Research topic being investigated
            session_id: Optional session identifier for grouping
        
        Returns:
            KGIngestionReport with statistics
        """
        await self._ensure_session()
        
        report = KGIngestionReport(topic=topic, session_id=session_id)
        
        for platform, result in results.items():
            if result.error or not result.data:
                report.skipped_platforms.append(platform)
                continue
            
            for item in result.data:
                text = self._extract_text(item)
                if not text:
                    continue
                
                # Extract entities and relations
                entities = await self._extract_entities(text)
                triplets = await self._extract_triplets(text)
                
                # Register provenance
                prov_id = self._provenance.register_source(
                    source_type="web_scraper",
                    source_id=f"{platform}:{item.get('id', 'unknown')}",
                    source_url=item.get("url"),
                    credibility_score=self._platform_credibility(platform),
                    timestamp=datetime.utcnow()
                )
                
                # Add to graph
                for entity in entities:
                    self._session.add_entity(
                        name=entity["name"],
                        type=entity.get("type", "Entity"),
                        provenance_id=prov_id
                    )
                    report.entities_added += 1
                
                for triplet in triplets:
                    self._session.add_relation(
                        subject=triplet[0],
                        predicate=triplet[1],
                        object=triplet[2],
                        provenance_id=prov_id
                    )
                    report.relations_added += 1
                
                report.items_processed += 1
        
        return report
    
    async def find_conflicts(self, entity_name: str) -> list[dict]:
        """
        Find conflicting facts about an entity across all sources.
        
        Returns list of conflicts with evidence from each source.
        """
        await self._ensure_session()
        
        from semantica.conflicts import ConflictDetector
        
        detector = ConflictDetector(session=self._session)
        return detector.detect_conflicts(entity_name)
    
    async def query_graph(self, query: str, query_type: str = "sparql") -> list[dict]:
        """
        Query the knowledge graph.
        
        Supports SPARQL and Cypher query languages.
        """
        await self._ensure_session()
        
        if query_type == "sparql":
            return self._session.sparql_query(query)
        elif query_type == "cypher":
            return self._session.cypher_query(query)
        else:
            raise ValueError(f"Unknown query type: {query_type}")
    
    async def get_entity_timeline(self, entity_name: str, since: int = None) -> list[dict]:
        """
        Get temporal evolution of facts about an entity.
        
        Args:
            entity_name: Name of entity to trace
            since: Optional days ago filter
        
        Returns chronologically ordered list of facts.
        """
        await self._ensure_session()
        
        return self._session.get_entity_timeline(
            entity_name, since_days=since
        )
    
    def _extract_text(self, item: dict) -> str:
        """Extract readable text from scraped item."""
        fields = ["text", "content", "body", "description", "title"]
        for field in fields:
            if field in item and isinstance(item[field], str):
                return item[field]
        return ""
    
    def _platform_credibility(self, platform: str) -> float:
        """Credibility score for different platforms."""
        scores = {
            "reddit": 0.7,
            "twitter": 0.5,      # High noise, unverified claims
            "youtube": 0.6,
            "linkedin": 0.8,     # Professional context
            "bilibili": 0.6,
            "v2ex": 0.75,
            "rss": 0.85,         # Curated sources
            "instagram": 0.4,    # Visual, less textual analysis
            "facebook": 0.5,
            "xiaohongshu": 0.6,
        }
        return scores.get(platform, 0.5)
    
    async def _extract_entities(self, text: str) -> list[dict]:
        """Extract entities from text using Semantica."""
        from semantica.semantic_extract import SemanticExtractor
        
        extractor = SemanticExtractor()
        result = await extractor.process_batch([text])
        
        entities = []
        for entity in result.get("entities", []):
            entities.append({
                "name": entity["text"],
                "type": entity.get("label", "Entity"),
                "confidence": entity.get("confidence", 0.8)
            })
        
        return entities
    
    async def _extract_triplets(self, text: str) -> list[tuple]:
        """Extract subject-predicate-object triplets from text."""
        from semantica.semantic_extract import TripletExtractor
        
        extractor = TripletExtractor(
            include_temporal=True,
            include_provenance=True
        )
        triplets = await extractor.extract_triplets(text)
        
        return triplets


class KGIngestionReport:
    """Statistics from a KG ingestion operation."""
    
    def __init__(self, topic: str, session_id: str = None):
        self.topic = topic
        self.session_id = session_id or datetime.utcnow().isoformat()
        self.entities_added = 0
        self.relations_added = 0
        self.items_processed = 0
        self.conflicts_detected = 0
        self.skipped_platforms = []
    
    def summary(self) -> str:
        return (
            f"KG Ingestion Report\n"
            f"{'=' * 40}\n"
            f"Topic: {self.topic}\n"
            f"Session: {self.session_id}\n"
            f"Items processed: {self.items_processed}\n"
            f"Entities extracted: {self.entities_added}\n"
            f"Relations extracted: {self.relations_added}\n"
            f"Conflicts found: {self.conflicts_detected}\n"
            f"Skipped platforms: {', '.join(self.skipped_platforms) or 'None'}\n"
        )
```

### Step 2: Update CLI (`scripts/silentreach.py`)

Add `kg` subcommand group:

```python
# In main():
# KG command
kg_parser = subparsers.add_parser("kg", help="Knowledge graph operations")
kg_sub = kg_parser.add_subparsers(dest="kg_command")

# kg build
kg_build = kg_sub.add_parser("build", help="Build KG from topic")
kg_build.add_argument("topic", help="Research topic")
kg_build.add_argument("--platform", "-p", default="all")
kg_build.add_argument("--depth", "-d", choices=["quick", "full"], default="full")
kg_build.set_defaults(func=cmd_kg_build)

# kg query
kg_query = kg_sub.add_parser("query", help="Query the knowledge graph")
kg_query.add_argument("query", help="SPARQL or Cypher query")
kg_query.add_argument("--type", "-t", choices=["sparql", "cypher"], default="sparql")
kg_query.set_defaults(func=cmd_kg_query)

# kg conflicts
kg_conflicts = kg_sub.add_parser("conflicts", help="Find conflicting facts")
kg_conflicts.add_argument("entity", help="Entity name to check")
kg_conflicts.set_defaults(func=cmd_kg_conflicts)

# kg timeline
kg_timeline = kg_sub.add_parser("timeline", help="View entity history")
kg_timeline.add_argument("entity", help="Entity name")
kg_timeline.add_argument("--since", "-s", type=int, help="Days ago")
kg_timeline.set_defaults(func=cmd_kg_timeline)

# kg export
kg_export = kg_sub.add_parser("export", help="Export graph")
kg_export.add_argument("--format", "-f", choices=["json", "rdf", "csv", "markdown"], default="markdown")
kg_export.add_argument("--output", "-o", help="Output file")
kg_export.set_defaults(func=cmd_kg_export)
```

Add handler functions:

```python
async def cmd_kg_build(args):
    """Build knowledge graph from topic search."""
    from services.kg_service import KGService
    
    service = KGService()
    
    # First, run the search
    print(f"🔍 Searching for: {args.topic}")
    search_results = await cmd_search(args)
    
    # Then ingest into KG
    print(f"🧠 Building knowledge graph...")
    report = await service.ingest_results(search_results, topic=args.topic)
    
    print(report.summary())
    
    if args.output:
        # Save report
        with open(args.output, "w") as f:
            f.write(report.summary())
        print(f"✅ Report saved to {args.output}")


async def cmd_kg_query(args):
    """Query the knowledge graph."""
    from services.kg_service import KGService
    
    service = KGService()
    results = await service.query_graph(args.query, args.type)
    
    print(f"\n📊 Query Results ({len(results)} results):\n")
    for row in results[:20]:
        print(json.dumps(row, indent=2))
    
    if len(results) > 20:
        print(f"\n... and {len(results) - 20} more results")


async def cmd_kg_conflicts(args):
    """Find conflicts about an entity."""
    from services.kg_service import KGService
    
    service = KGService()
    conflicts = await service.find_conflicts(args.entity)
    
    if not conflicts:
        print(f"✅ No conflicts found for '{args.entity}'")
        return
    
    print(f"\n⚠️  Found {len(conflicts)} conflicts for '{args.entity}':\n")
    
    for conflict in conflicts:
        print(f"Entity: {conflict['entity']}")
        print(f"Claim 1: {conflict['fact_1']} (from {conflict['source_1']})")
        print(f"Claim 2: {conflict['fact_2']} (from {conflict['source_2']})")
        print(f"Confidence: {conflict['confidence']:.2f}")
        print("---")


async def cmd_kg_timeline(args):
    """Show entity timeline."""
    from services.kg_service import KGService
    
    service = KGService()
    timeline = await service.get_entity_timeline(args.entity, args.since)
    
    print(f"\n📅 Timeline for '{args.entity}':\n")
    
    for fact in timeline:
        date = fact.get("recorded_at", "unknown")
        print(f"[{date}] {fact['subject']} {fact['predicate']} {fact['object']}")
        print(f"   Source: {fact.get('source', 'unknown')}")
        print()


async def cmd_kg_export(args):
    """Export knowledge graph."""
    from services.kg_service import KGService
    
    service = KGService()
    
    if args.format == "json":
        data = service.export_graph(format="json")
        output = json.dumps(data, indent=2)
    elif args.format == "rdf":
        data = service.export_graph(format="rdf")
        output = data
    elif args.format == "csv":
        data = service.export_graph(format="csv")
        output = "\n".join(data)
    else:  # markdown
        data = service.export_graph(format="markdown")
        output = data
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"✅ Exported to {args.output}")
    else:
        print(output)
```

### Step 3: Update `setup.py`

```python
extras_require={
    "dev": [...],
    "kg": [
        "semantica>=0.7.0",
        "neo4j>=5.0.0; extra='graph-neo4j'",
    ],
    "all": [
        "silentreach[kg]",
        # ... other extras
    ],
}
```

### Step 4: Configuration (`config/kg_settings.yaml`)

```yaml
# ~/.silentreach/kg_settings.yaml
kg:
  backend: sqlite  # sqlite, neo4j, falkordb
  connection: null  # Override for Neo4j: neo4j://user:pass@localhost:7687
  
  # Platform credibility scores (0.0 - 1.0)
  credibility:
    reddit: 0.7
    twitter: 0.5
    youtube: 0.6
    linkedin: 0.8
    bilibili: 0.6
    v2ex: 0.75
    rss: 0.85
  
  # Conflict detection settings
  conflict:
    threshold: 0.3  # Flag conflicts below this confidence
    max_sources: 10
  
  # Export settings
  export:
    default_format: markdown
    include_provenance: true
```

## Testing

```python
# tests/test_kg.py
import pytest
from services.kg_service import KGService, KGConfig

@pytest.mark.asyncio
async def test_ingest_basic():
    service = KGService()
    
    mock_results = {
        "reddit": ScrapedResult(
            platform="reddit",
            query="AI regulation",
            data=[{"text": "Elon Musk supports AI regulation...", "url": "https://reddit.com/..."}]
        )
    }
    
    report = await service.ingest_results(mock_results, topic="AI regulation")
    
    assert report.entities_added > 0
    assert report.relations_added > 0
    assert len(report.skipped_platforms) == 0

@pytest.mark.asyncio
async def test_conflict_detection():
    service = KGService()
    
    # Ingest conflicting sources
    await service.ingest_results({
        "reddit": ScrapedResult(data=[{"text": "AI will take all jobs"}]),
        "twitter": ScrapedResult(data=[{"text": "AI won't replace human jobs"}]),
    }, topic="AI jobs")
    
    conflicts = await service.find_conflicts("AI jobs")
    
    assert len(conflicts) > 0
    assert any("reddit" in c.get("source_1", "") for c in conflicts)
```

## Documentation Updates

Update `README.md` with:
- New `kg` command section
- Installation instructions for KG extras
- Example workflows
- Architecture diagram

Update `CLI.md` with:
- All new `kg` subcommands
- Query language reference (SPARQL/Cypher)
- Configuration options

Update `ARCHITECTURE.md` with:
- KGService architecture
- Data flow diagrams
- Semantica integration details

## Rollback Plan

If integration causes issues:
1. KG is optional (`pip install silentreach[kg]`)
2. Original functionality untouched
3. Clear error messages if Semantica not installed
4. Graceful fallback to basic search without KG

## Success Metrics

- Entity extraction accuracy > 80%
- Conflict detection catches > 90% of obvious contradictions
- Query response time < 500ms for graphs up to 10k nodes
- Zero data loss (provenance preserved)
