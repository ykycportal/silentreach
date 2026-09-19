# SilentReach + Semantica Integration Design

## The Idea

SilentReach scrapes the web. Semantica turns that scraped content into a structured, queryable knowledge graph with provenance.

**Pipeline:**
```
silentreach search "topic" -p all
    ↓
ScrapedResult[] (raw content from platforms)
    ↓
semantica.semantic_extract.extract_entities() + extract_triplets()
    ↓
KG with nodes = entities, edges = relations, provenance = source URLs
    ↓
Query: "Who are the key players in X?" or "What changed about Y this month?"
```

## Why This Matters

| SilentReach alone | + Semantica |
|---|---|
| Raw posts/articles | Structured knowledge |
| "Here's what I found" | "Here's what I know, and where I learned it" |
| No cross-platform correlation | Detects conflicts across sources |
| Can't ask complex questions | SPARQL/graph queries over all data |
| One-shot searches | Persistent context graph you build over time |

## Integration Points

### 1. New Command: `silentreach KG`
```bash
# Build knowledge graph from a topic across all platforms
silentreach kg "dropshipping" --platform all --store neo4j

# Query the graph
silentreach kg query "SELECT ?entity WHERE { ?entity rdfs:label 'dropshipping' }"

# Show conflicts (same entity, different facts across platforms)
silentreach kg conflicts "AI agents"

# Time travel: what did we know about X last week?
silentreach kg timeline "crypto regulation" --since 7d
```

### 2. New Service: `KGService`
Location: `services/kg_service.py`

```python
class KGService:
    """Bridges SilentReach scraped results into Semantica knowledge graphs."""
    
    def __init__(self, graph_backend="sqlite", connection_string=None):
        # Initialize Semantica graph store
        from semantica.kg import GraphSession
        self.session = GraphSession(backend=graph_backend, connection=connection_string)
        self.provenance = ProvenanceManager(storage_path=Path.home() / ".silentreach" / "provenance.db")
    
    async def ingest_results(self, results: dict[str, ScrapedResult], topic: str):
        """Ingest scraped results into the knowledge graph."""
        for platform, result in results.items():
            if result.error:
                continue
            
            for item in result.data:
                text = self._extract_text(item)
                
                # Extract entities and triplets
                entities = semantic_extract.extract_entities(text)
                triplets = semantic_extract.extract_triplets(text)
                
                # Add to graph with provenance
                for triplet in triplets:
                    self.session.add_fact(
                        subject=triplet[0],
                        predicate=triplet[1],
                        object=triplet[2],
                        provenance=self.provenance.register(
                            source_type="web_scraper",
                            source_id=result.platform,
                            source_url=item.get("url"),
                            credibility_score=self._platform_credibility(platform)
                        )
                    )
    
    def _platform_credibility(self, platform: str) -> float:
        """Credibility score per platform (Reddit = 0.7, News = 0.9, etc.)"""
        scores = {
            "reddit": 0.7,
            "twitter": 0.5,  # high noise
            "youtube": 0.6,
            "linkedin": 0.8,
            # ...
        }
        return scores.get(platform, 0.5)
    
    def find_conflicts(self, entity: str) -> list[dict]:
        """Find conflicting facts about an entity across sources."""
        from semantica.conflicts import ConflictDetector
        detector = ConflictDetector(session=self.session)
        return detector.detect_conflicts(entity)
    
    def query_graph(self, sparql: str) -> list[dict]:
        """Run SPARQL query over accumulated knowledge."""
        return self.session.query(sparql)
```

### 3. Cross-Platform Entity Resolution
When the same person/company appears on Reddit AND Twitter:
- Semantica's deduplication resolves them as one node
- Confidence scores aggregate across sources
- Conflicting claims get flagged

### 4. Conflict Detection
Example:
- Reddit says: "Dropshipping margins are 30-50%"
- Twitter says: "Dropshipping margins are dead, only 5-10%"
- Semantica flags this as a **FACT_CONFLICT** and shows both sources

### 5. Temporal Intelligence
Track how knowledge changes:
- "What did people say about AI agents in March vs September?"
- Bi-temporal facts: when was it true in the world vs. when did we learn it?

## Data Flow

```
User: silentreach kg "quantum computing" -p reddit,youtube,twitter
    ↓
1. SilentReach scrapes all 3 platforms
    ↓
2. For each result item:
   a. Extract text/content
   b. Run NER → entities
   c. Run relation extraction → triplets
   d. Register provenance (source platform, URL, timestamp)
    ↓
3. Insert into Semantica graph
   - Neo4j (if configured) or SQLite (default)
    ↓
4. Return summary:
   - 47 entities extracted
   - 123 relations identified
   - 3 conflicts detected
   - Graph saved to ~/.silentreach/kg.graph
```

## Storage Options

| Backend | When to use |
|---------|-------------|
| SQLite (default) | Local dev, small graphs, no setup |
| Neo4j | Production, large graphs, complex queries |
| FalkorDB | Redis-compatible, fast prototyping |
| DuckDB | Analytics, OLAP-style queries |

## CLI Commands

```bash
# Build KG from topic
silentreach kg build "topic" --platform all --depth full

# View graph
silentreach kg view "entity_name"

# Query with SPARQL
silentreach kg query "SELECT ?x WHERE { ?x type Person }"

# Find conflicts
silentreach kg conflicts "entity_name"

# Export graph
silentreach kg export --format rdf  # or json, csv

# Merge with existing graph
silentreach kg merge ~/previous_kg.graph

# Timeline view
silentreach kg timeline "topic" --since 30d
```

## File Structure Changes

```
silentreach/
├── services/
│   ├── kg_service.py          # NEW: KG bridge
│   ├── stealth_engine.py
│   └── ...
├── scrapers/
│   └── ...
├── scripts/
│   └── silentreach.py         # Modified: add kg subcommand
├── config/
│   └── kg_settings.yaml       # NEW: KG backend config
└── tests/
    └── test_kg.py             # NEW: KG integration tests
```

## Dependencies to Add

```python
# In setup.py extras
kg = [
    "semantica>=0.7.0",
    "neo4j>=5.0.0; extra='graph-neo4j'",
]

# Or optional install
pip install "silentreach[kg]"
```

## MVP Scope

**Phase 1** (MVP):
- [ ] Install semantica as optional dependency
- [ ] Add `kg build` command
- [ ] Extract entities from scraped results
- [ ] Store in SQLite with provenance
- [ ] Basic query interface

**Phase 2**:
- [ ] Conflict detection
- [ ] Cross-platform entity resolution
- [ ] Neo4j backend option
- [ ] SPARQL query support

**Phase 3**:
- [ ] Temporal/timeline queries
- [ ] Graph visualization (integrate Semantica's explorer)
- [ ] Export to RDF/OWL
- [ ] Web dashboard with graph view

## Example Workflow

```bash
# 1. Research a topic over time
silentreach kg build "AI regulation" -p reddit,twitter,linkedin --weekly

# 2. Check for conflicting narratives
silentreach kg conflicts "AI regulation"
# → Found 3 conflicts:
#   - Reddit: "EU AI Act is restrictive" (credibility 0.7)
#   - LinkedIn: "EU AI Act is balanced" (credibility 0.8)
#   - Twitter: "AI Act killed innovation" (credibility 0.5)

# 3. Query the graph
silentreach kg query "MATCH (e:Entity)-[:SUBJECT_TO]->(l:Law) WHERE l.name = 'EU AI Act' RETURN e.name"

# 4. Export for report
silentreach kg export --format markdown --output report.md
```

## Security Considerations

- All graph data stays local (`~/.silentreach/kg/`)
- No telemetry, no phone home
- Provenance tracking ensures audit trail
- Credibility scoring prevents low-quality sources from dominating

## Why This Combo Wins

1. **SilentReach** = discovery (find the data)
2. **Semantica** = understanding (structure the data)
3. **Together** = intelligence (ask questions, find answers, trace sources)

---

**Next step:** Want me to implement Phase 1 (MVP)? I can:
1. Add the `KGService` class
2. Modify the CLI to add `kg` subcommands
3. Set up SQLite-backed graph storage
4. Write basic entity extraction from scraped content
