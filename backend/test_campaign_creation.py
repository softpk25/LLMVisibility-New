#!/usr/bin/env python3
"""
Test campaign creation API
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

import httpx


async def test_campaign_creation():
    """Test the campaign creation API"""
    
    # Test data
    campaign_data = {
        "campaign_name": "Test AI Campaign",
        "campaign_objective": "awareness",
        "target_audience": "Tech enthusiasts and early adopters",
        "start_date": "2024-06-01",
        "end_date": "2024-08-31",
        "frequency": 2,
        "selected_personas": ["persona-tech-enthusiast"],
        "selected_brand_id": "brand-techflow-solutions",
        "product_integration_enabled": False,
        "selected_products": [],
        "language_config": {
            "primary_language": "en",
            "multilingual_enabled": False,
            "additional_languages": []
        }
    }
    
    print("🧪 Testing Campaign Creation API...")
    print(f"📋 Campaign Data: {json.dumps(campaign_data, indent=2)}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8009/api/v1/campaigns/create",
                json=campaign_data,
                timeout=30.0
            )
            
            print(f"\n📊 Response Status: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS! Campaign created:")
                print(f"   Campaign ID: {result.get('campaign_id')}")
                print(f"   Status: {result.get('status')}")
                print(f"   Message: {result.get('message')}")
                
                if result.get('data'):
                    data = result['data']
                    print(f"   Campaign Name: {data.get('campaign_metadata', {}).get('name')}")
                    print(f"   Brand: {data.get('brand_context', {}).get('brand_name')}")
                    
                    if data.get('content_plan'):
                        content_plan = data['content_plan'].get('generated_plan', '')
                        print(f"   AI Content Plan: {content_plan[:200]}...")
                
                return True
            else:
                print(f"❌ FAILED! Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Raw Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Testing Prometrix Campaign Creation\n")
    
    success = await test_campaign_creation()
    
    if success:
        print("\n🎉 Campaign creation test PASSED!")
        print("The AI blueprint generation should now work in the frontend.")
    else:
        print("\n💥 Campaign creation test FAILED!")
        print("Check the server logs for more details.")


if __name__ == "__main__":
    asyncio.run(main())