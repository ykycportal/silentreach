"""Test with Semantica LLM extraction enabled."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "silentreach"))

from services.kg_service import KGService
from scrapers.base import ScrapedResult


async def test_with_semantica():
    """Test KG with Semantica LLM extraction."""
    
    print("=" * 60)
    print("🧠 Testing with Semantica LLM")
    print("=" * 60)
    
    service = KGService()
    
    # Test text with marketing entities
    test_texts = [
        "Elon Musk says Shopify is the best platform for dropshipping. Oberlo was acquired by Shopify.",
        "OpenAI and Anthropic are competing in AI regulation. Claude and GPT-4 are leading models.",
        "Meta ads and Google ads drive most e-commerce traffic. ROAS matters more than CTR.",
    ]
    
    results = {
        "reddit": ScrapedResult(
            platform="reddit",
            query="marketing",
            data=[{"text": t, "url": f"https://reddit.com/test/{i}"} for i, t in enumerate(test_texts)],
        ),
    }
    
    print("\n📥 Ingesting with LLM extraction...")
    report = await service.ingest_results(results, topic="marketing intelligence")
    
    print(f"\n✅ Results:")
    print(f"   Entities: {report['entities_extracted']}")
    print(f"   Relations: {report['relations_extracted']}")
    
    print(f"\n📊 Entities Found:")
    for name, entity in service._entities.items():
        print(f"   • {name} ({entity.type}) - conf: {entity.confidence:.2f}")
        if entity.facts:
            for fact in entity.facts[:2]:
                print(f"     - {fact['predicate']}: {fact['object']}")
    
    print(f"\n🔍 Sample Relations:")
    for rel in service._relations[:5]:
        print(f"   {rel['subject']} → {rel['predicate']} → {rel['object']}")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_with_semantica())
