#!/usr/bin/env python3
"""
Simple test script to verify Prometrix backend functionality
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.storage import storage, campaign_storage, brand_storage
from services.llm_orchestrator import orchestrator
from schemas.campaign import CampaignCreateRequest, LanguageConfig
from schemas.brand import BrandRegisterRequest, VoiceProfile, ContentPillar, ContentPillarType


async def test_storage():
    """Test JSON storage functionality"""
    print("🧪 Testing Storage...")
    
    # Test basic storage operations
    test_data = {
        "id": "test-123",
        "name": "Test Item",
        "description": "This is a test item"
    }
    
    # Save
    await storage.save("test", "test-123", test_data)
    print("✅ Storage save successful")
    
    # Load
    loaded_data = await storage.load("test", "test-123")
    assert loaded_data["name"] == "Test Item"
    print("✅ Storage load successful")
    
    # List
    items = await storage.list_items("test")
    assert len(items) >= 1
    print("✅ Storage list successful")
    
    # Delete
    success = await storage.delete("test", "test-123")
    assert success
    print("✅ Storage delete successful")


async def test_llm_orchestrator():
    """Test LLM orchestrator with mock provider"""
    print("\n🤖 Testing LLM Orchestrator...")
    
    # Test text generation
    payload = {
        "task_type": "text_generation",
        "prompt": "Write a short social media caption for a tech product",
        "parameters": {
            "max_tokens": 100,
            "temperature": 0.7
        },
        "request_id": "test-generation"
    }
    
    result = await orchestrator.generate(payload, provider="mock")
    assert result["success"]
    assert "content" in result
    print("✅ LLM text generation successful")
    
    # Test provider status
    status = orchestrator.get_provider_status()
    assert "mock" in status
    print("✅ LLM provider status check successful")


async def test_campaign_creation():
    """Test campaign creation workflow"""
    print("\n📋 Testing Campaign Creation...")
    
    # Create a test brand first
    brand_request = BrandRegisterRequest(
        brand_name="Test Brand",
        industry="technology",
        description="A test brand for backend testing",
        voice_profile=VoiceProfile(
            formality="casual",
            humor="subtle",
            tone="friendly"
        ),
        content_pillars=[
            ContentPillar(
                id="pillar-1",
                name="Innovation",
                type=ContentPillarType.EDUCATIONAL,
                description="Innovation content",
                percentage=50
            ),
            ContentPillar(
                id="pillar-2", 
                name="Community",
                type=ContentPillarType.COMMUNITY,
                description="Community content",
                percentage=50
            )
        ]
    )
    
    # Create brand
    brand_data = brand_request.model_dump()
    brand_id = await brand_storage.create_brand(brand_data)
    print(f"✅ Brand created: {brand_id}")
    
    # Create campaign
    campaign_request = CampaignCreateRequest(
        campaign_name="Test Campaign",
        campaign_objective="awareness",
        target_audience="Tech enthusiasts",
        start_date="2024-06-01",
        end_date="2024-08-31",
        frequency=2,
        selected_personas=["persona-1"],
        selected_brand_id=brand_id,
        language_config=LanguageConfig(
            primary_language="en"
        )
    )
    
    campaign_data = campaign_request.model_dump()
    campaign_id = await campaign_storage.create_campaign(campaign_data)
    print(f"✅ Campaign created: {campaign_id}")
    
    # Retrieve campaign
    retrieved_campaign = await campaign_storage.get_campaign(campaign_id)
    assert retrieved_campaign["campaign_name"] == "Test Campaign"
    print("✅ Campaign retrieval successful")


async def test_api_schemas():
    """Test Pydantic schema validation"""
    print("\n📝 Testing API Schemas...")
    
    # Test campaign schema
    campaign_data = {
        "campaign_name": "Test Campaign",
        "campaign_objective": "awareness",
        "target_audience": "Test audience",
        "start_date": "2024-06-01",
        "end_date": "2024-08-31",
        "frequency": 2,
        "selected_personas": ["persona-1"],
        "selected_brand_id": "brand-123",
        "language_config": {
            "primary_language": "en"
        }
    }
    
    try:
        campaign_request = CampaignCreateRequest(**campaign_data)
        assert campaign_request.campaign_name == "Test Campaign"
        print("✅ Campaign schema validation successful")
    except Exception as e:
        print(f"❌ Campaign schema validation failed: {e}")
        raise
    
    # Test brand schema
    brand_data = {
        "brand_name": "Test Brand",
        "industry": "technology", 
        "description": "Test description",
        "voice_profile": {
            "formality": "casual",
            "humor": "subtle",
            "tone": "friendly"
        },
        "content_pillars": [
            {
                "id": "pillar-1",
                "name": "Test Pillar",
                "type": "educational",
                "description": "Test pillar description",
                "percentage": 100
            }
        ]
    }
    
    try:
        brand_request = BrandRegisterRequest(**brand_data)
        assert brand_request.brand_name == "Test Brand"
        print("✅ Brand schema validation successful")
    except Exception as e:
        print(f"❌ Brand schema validation failed: {e}")
        raise


async def main():
    """Run all tests"""
    print("🚀 Starting Prometrix Backend Tests\n")
    
    try:
        await test_storage()
        await test_llm_orchestrator()
        await test_api_schemas()
        await test_campaign_creation()
        
        print("\n🎉 All tests passed! Backend is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())