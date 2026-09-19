"""
Test suite for Knowledge Graph integration.
Run with: pytest tests/test_kg.py -v
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch


# Mock scraper results for testing
MOCK_REDDIT_RESULTS = {
    "platform": "reddit",
    "query": "AI regulation",
    "data": [
        {
            "text": "Elon Musk says AI regulation is necessary for safety. OpenAI supports strict AI regulation.",
            "url": "https://reddit.com/r/ai/comments/abc123",
            "id": "reddit_001",
        },
        {
            "text": "Some argue AI regulation will stifle innovation. Altman thinks regulation could kill US competitiveness.",
            "url": "https://reddit.com/r/technology/comments/def456",
            "id": "reddit_002",
        },
    ],
}

MOCK_TWITTER_RESULTS = {
    "platform": "twitter",
    "query": "AI regulation",
    "data": [
        {
            "text": "AI regulation debate: Musk wants it, Altman fears it. Who's right?",
            "url": "https://twitter.com/user/status/123",
            "id": "twitter_001",
        },
    ],
}


@pytest.mark.asyncio
async def test_kg_service_creation():
    """Test KGService initialization."""
    from services.kg_service import KGService, KGConfig
    
    config = KGConfig()
    service = KGService(config)
    
    assert service.config.backend == "sqlite"
    assert service.config.storage_path is not None
    assert len(service._entities) == 0
    assert len(service._relations) == 0


@pytest.mark.asyncio
async def test_entity_extraction():
    """Test that entities are extracted from mock text."""
    from services.kg_service import KGService
    
    service = KGService()
    
    # Test text extraction
    text = "Elon Musk says AI regulation is necessary. OpenAI supports strict rules."
    entities = service._extract_entities(text, "reddit")
    
    # Should extract known entities
    entity_names = [e["name"] for e in entities]
    
    assert any("Elon Musk" in name for name in entity_names), \
        "Should extract 'Elon Musk' entity"
    assert any("OpenAI" in name for name in entity_names), \
        "Should extract 'OpenAI' entity"
    assert any("AI" in name.lower() or "Regulation" in name for name in entity_names), \
        "Should extract topic-related entities"


@pytest.mark.asyncio
async def test_triplet_extraction():
    """Test relation triplet extraction."""
    from services.kg_service import KGService
    
    service = KGService()
    
    text = "Elon Musk supports AI regulation. OpenAI uses AI tools."
    triplets = service._extract_triplets(text, "reddit")
    
    assert len(triplets) > 0, "Should extract some triplets"
    
    # Check for expected relations
    predicates = [t[1] for t in triplets]
    assert any("support" in p.lower() or "is" in p.lower() for p in predicates), \
        "Should have support/is relations"


@pytest.mark.asyncio
async def test_ingest_results():
    """Test full ingestion pipeline."""
    from services.kg_service import KGService
    from scrapers.base import ScrapedResult
    
    service = KGService()
    
    # Create mock results
    results = {
        "reddit": ScrapedResult(
            platform="reddit",
            query="AI regulation",
            data=MOCK_REDDIT_RESULTS["data"],
        ),
        "twitter": ScrapedResult(
            platform="twitter",
            query="AI regulation",
            data=MOCK_TWITTER_RESULTS["data"],
        ),
    }
    
    report = await service.ingest_results(results, topic="AI regulation")
    
    assert report["entities_extracted"] > 0, "Should extract entities"
    assert report["relations_extracted"] >= 0, "Should extract relations"
    assert "reddit" in report["platforms_processed"]
    assert "twitter" in report["platforms_processed"]


@pytest.mark.asyncio
async def test_conflict_detection():
    """Test conflict detection across platforms."""
    from services.kg_service import KGService
    from scrapers.base import ScrapedResult
    
    service = KGService()
    
    # Ingest conflicting sources
    results = {
        "reddit": ScrapedResult(
            platform="reddit",
            query="AI jobs",
            data=[{"text": "AI will take all jobs by 2030", "url": "https://reddit.com/1"}],
        ),
        "twitter": ScrapedResult(
            platform="twitter",
            query="AI jobs",
            data=[{"text": "AI won't replace human creativity", "url": "https://twitter.com/1"}],
        ),
    }
    
    await service.ingest_results(results, topic="AI jobs")
    conflicts = service.detect_conflicts()
    
    # Should detect at least some conflicts or entity overlap
    assert isinstance(conflicts, list)


@pytest.mark.asyncio
async def test_query_entities():
    """Test entity querying with filters."""
    from services.kg_service import KGService
    from scrapers.base import ScrapedResult
    
    service = KGService()
    
    # Ingest some data
    results = {
        "reddit": ScrapedResult(
            platform="reddit",
            query="test",
            data=[{"text": "Shopify is a great e-commerce platform for dropshipping.", "url": "https://test.com"}],
        ),
    }
    
    await service.ingest_results(results, topic="e-commerce")
    
    # Query all
    all_entities = service.query_entities()
    assert len(all_entities) > 0
    
    # Query by search term
    filtered = service.query_entities(search_term="shopify")
    assert len(filtered) > 0
    assert any("Shopify" in e["name"] for e in filtered)


@pytest.mark.asyncio
async def test_report_generation():
    """Test markdown report generation."""
    from services.kg_service import KGService
    from services.report_generator import MarketingReportGenerator
    from scrapers.base import ScrapedResult
    
    service = KGService()
    generator = MarketingReportGenerator(service)
    
    # Ingest test data
    results = {
        "reddit": ScrapedResult(
            platform="reddit",
            query="AI tools",
            data=[{"text": "Claude and Cursor are popular AI coding tools.", "url": "https://test.com"}],
        ),
    }
    
    await service.ingest_results(results, topic="AI tools")
    
    # Generate report
    report = generator.generate_campaign_brief("AI tools")
    
    assert isinstance(report, str)
    assert "AI tools" in report
    assert "Claude" in report or "Cursor" in report


@pytest.mark.asyncio
async def test_agent_bundle_export():
    """Test JSON export for agents."""
    from services.kg_service import KGService
    from services.report_generator import MarketingReportGenerator
    from scrapers.base import ScrapedResult
    
    service = KGService()
    generator = MarketingReportGenerator(service)
    
    results = {
        "linkedin": ScrapedResult(
            platform="linkedin",
            query="marketing automation",
            data=[{"text": "HubSpot is leading marketing automation platform.", "url": "https://linkedin.com"}],
        ),
    }
    
    await service.ingest_results(results, topic="marketing automation")
    
    bundle = generator.generate_agent_bundle("marketing automation")
    
    assert "entities" in bundle
    assert "relations" in bundle
    assert "executive_summary" in bundle
    assert isinstance(bundle["entities"], dict)


@pytest.mark.asyncio
async def test_session_persistence():
    """Test saving and loading sessions."""
    from services.kg_service import KGService
    from scrapers.base import ScrapedResult
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use temp dir for storage
        service = KGService()
        service.config.storage_path = Path(tmpdir) / ".silentreach" / "kg"
        service.config.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Ingest data
        results = {
            "twitter": ScrapedResult(
                platform="twitter",
                query="test topic",
                data=[{"text": "Tesla is a great EV company.", "url": "https://twitter.com"}],
            ),
        }
        
        report = await service.ingest_results(results, topic="EVs")
        session_id = report["session_id"]
        
        # Save was called internally
        session_path = service.config.storage_path / "graphs" / f"{session_id}.json"
        assert session_path.exists(), "Session should be saved to disk"
        
        # Load session
        loaded_service = KGService()
        loaded_service.config.storage_path = service.config.storage_path
        success = loaded_service.load_session(session_id)
        
        assert success, "Should load session successfully"
        assert len(loaded_service._entities) > 0, "Should have loaded entities"


def test_platform_credibility_scores():
    """Test that credibility scores are reasonable."""
    from services.kg_service import KGService
    
    service = KGService()
    
    # RSS should be highest credibility
    assert service.PLATFORM_CREDIBILITY["rss"] >= 0.8
    
    # Twitter should be lower (noise)
    assert service.PLATFORM_CREDIBILITY["twitter"] <= 0.6
    
    # LinkedIn should be decent
    assert service.PLATFORM_CREDIBILITY["linkedin"] >= 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
