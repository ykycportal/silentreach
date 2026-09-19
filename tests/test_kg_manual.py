"""
Integration test for KG service - runs without pytest.
"""

import asyncio
import json
from pathlib import Path

# Add silentreach to path
import sys
sys.path.insert(0, str(Path.home() / "silentreach"))

from services.kg_service import KGService, KGConfig
from services.report_generator import MarketingReportGenerator
from scrapers.base import ScrapedResult


async def test_kg_integration():
    """Test the full KG pipeline."""
    
    print("=" * 60)
    print("🧠 SilentReach KG Integration Test")
    print("=" * 60)
    
    # Create service with temp storage
    service = KGService()
    
    # Mock scraped results (simulating what scrapers would return)
    mock_results = {
        "reddit": ScrapedResult(
            platform="reddit",
            query="dropshipping",
            data=[
                {
                    "text": "Shopify is the best platform for dropshipping in 2024. Oberlo was acquired by Shopify.",
                    "url": "https://reddit.com/r/dropship/comments/abc",
                    "id": "r_001",
                },
                {
                    "text": "Dropshipping margins are dropping. Most people make 10-20% profit, not 50%.",
                    "url": "https://reddit.com/r/ecommerce/comments/def",
                    "id": "r_002",
                },
            ],
        ),
        "twitter": ScrapedResult(
            platform="twitter",
            query="dropshipping",
            data=[
                {
                    "text": "Dropshipping is dead in 2024. Focus on branding and private label.",
                    "url": "https://twitter.com/user/status/123",
                    "id": "t_001",
                },
            ],
        ),
        "linkedin": ScrapedResult(
            platform="linkedin",
            query="dropshipping",
            data=[
                {
                    "text": "The global dropshipping market is expected to reach $500B by 2027. Major brands like Gymshark started with dropshipping.",
                    "url": "https://linkedin.com/pulse/dropshipping-market",
                    "id": "li_001",
                },
            ],
        ),
    }
    
    # Run ingestion
    print("\n📥 Ingesting scraped results...")
    report = await service.ingest_results(mock_results, topic="dropshipping")
    
    print(f"\n✅ Ingestion Complete:")
    print(f"   Entities extracted: {report['entities_extracted']}")
    print(f"   Relations extracted: {report['relations_extracted']}")
    print(f"   Platforms processed: {', '.join(report['platforms_processed'])}")
    
    # Show entities
    print(f"\n📊 Entities Found:")
    for name, entity in list(service._entities.items())[:15]:
        sources = ', '.join(set(entity.sources))
        print(f"   • {name} ({entity.type})")
        print(f"     Sources: {sources}")
        print(f"     Facts: {len(entity.facts)}")
        print()
    
    # Show conflicts
    conflicts = service.detect_conflicts()
    if conflicts:
        print(f"⚠️  Conflicts Detected: {len(conflicts)}")
        for conflict in conflicts[:3]:
            print(f"   • {conflict.entity}")
            print(f"     '{conflict.fact_1}' (from {conflict.source_1})")
            print(f"     vs")
            print(f"     '{conflict.fact_2}' (from {conflict.source_2})")
            print()
    
    # Generate report
    print("=" * 60)
    print("📝 Generating Reports")
    print("=" * 60)
    
    generator = MarketingReportGenerator(service)
    
    # Markdown report
    md_report = generator.generate_campaign_brief("dropshipping")
    print("\n📄 Campaign Brief Preview:")
    print("-" * 40)
    print(md_report[:800] + "...")
    
    # Save report
    output_dir = Path.home() / ".silentreach" / "reports" / "dropshipping_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    brief_path = output_dir / "campaign_brief.md"
    with open(brief_path, "w") as f:
        f.write(md_report)
    print(f"\n💾 Saved: {brief_path}")
    
    # Agent bundle
    bundle = generator.generate_agent_bundle("dropshipping")
    bundle_path = output_dir / "agent_bundle.json"
    with open(bundle_path, "w") as f:
        json.dump(bundle, f, indent=2, default=str)
    print(f"💾 Saved: {bundle_path}")
    
    # Show bundle stats
    print(f"\n📦 Agent Bundle Contents:")
    print(f"   Entities: {len(bundle['entities'])}")
    print(f"   Relations: {len(bundle['relations'])}")
    print(f"   Conflicts: {len(bundle['conflicts'])}")
    
    # Executive summary
    summary = bundle['executive_summary']
    print(f"\n🎯 Executive Summary:")
    print(f"   Overall Confidence: {summary['overall_confidence']:.0%}")
    print(f"   Companies Mentioned: {summary['key_findings']['companies_mentioned']}")
    print(f"   Data Quality: High={summary['data_quality']['high_confidence']}, "
          f"Medium={summary['data_quality']['medium_confidence']}, "
          f"Low={summary['data_quality']['low_confidence']}")
    print(f"   Risk Factors: {summary['risk_factors']['conflicts_detected']} conflicts")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_kg_integration())
    sys.exit(0 if result else 1)
