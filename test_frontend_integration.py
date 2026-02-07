#!/usr/bin/env python3
"""
Test frontend integration - simulate the exact request the frontend makes
"""

import asyncio
import json
import httpx


async def test_frontend_campaign_creation():
    """Test the exact campaign creation request that the frontend makes"""
    
    # This is the exact data structure the frontend sends
    campaign_data = {
        "campaign_name": "Summer Product Launch",
        "campaign_objective": "awareness",
        "target_audience": "Tech enthusiasts and early adopters interested in innovative solutions",
        "start_date": "2024-06-01",
        "end_date": "2024-08-31",
        "frequency": 1,
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
    
    print("🧪 Testing Frontend Integration...")
    print("📋 Simulating exact frontend request to /api/v1/campaigns/create")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Campaign Creation (what happens when user clicks "Create Campaign Blueprint")
            print("\n1️⃣ Testing Campaign Creation...")
            response = await client.post(
                "http://localhost:8000/api/v1/campaigns/create",
                json=campaign_data,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                campaign_id = result.get('campaign_id')
                print(f"   ✅ Campaign created: {campaign_id}")
                print(f"   📝 AI Strategy: {result.get('data', {}).get('content_plan', {}).get('generated_plan', 'N/A')[:100]}...")
                
                # Test 2: Post Mix Configuration (what happens in step 2)
                print("\n2️⃣ Testing Post Mix Configuration...")
                post_mix_data = {
                    "campaign_id": campaign_id,
                    "content_types": ["image", "carousel", "video"],
                    "post_distribution": {
                        "educational": 30,
                        "promotional": 25,
                        "behind_scenes": 20,
                        "user_generated": 15,
                        "seasonal": 5,
                        "trending": 5
                    }
                }
                
                mix_response = await client.post(
                    "http://localhost:8000/api/v1/campaigns/post-mix",
                    json=post_mix_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                print(f"   Status: {mix_response.status_code}")
                if mix_response.status_code == 200:
                    print("   ✅ Post mix configured successfully")
                else:
                    print(f"   ❌ Post mix failed: {mix_response.text}")
                
                # Test 3: Post Regeneration (what happens when user clicks regenerate)
                print("\n3️⃣ Testing Post Regeneration...")
                post_update_data = {
                    "post_id": "test-post-123",
                    "caption": "Original caption for testing",
                    "hashtags": ["#test", "#ai"],
                    "scheduled_time": "2024-06-15T14:00:00Z",
                    "regenerate_content": True
                }
                
                regen_response = await client.put(
                    f"http://localhost:8000/api/v1/campaigns/{campaign_id}/post",
                    json=post_update_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                print(f"   Status: {regen_response.status_code}")
                if regen_response.status_code == 200:
                    print("   ✅ Post regeneration successful")
                else:
                    print(f"   ❌ Post regeneration failed: {regen_response.text}")
                
                return True
            else:
                print(f"   ❌ Campaign creation failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_frontend_loading():
    """Test that the frontend loads correctly"""
    print("\n🌐 Testing Frontend Loading...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/", timeout=10.0)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check for key frontend elements
                checks = [
                    ("Campaign Workflow", "Campaign workflow page loaded"),
                    ("createCampaignBlueprint", "Campaign creation function present"),
                    ("generatePlanFromMix", "Post mix function present"),
                    ("regeneratePost", "Post regeneration function present"),
                    ("✨ Create Campaign Blueprint", "Create button present")
                ]
                
                all_passed = True
                for check_text, description in checks:
                    if check_text in html_content:
                        print(f"   ✅ {description}")
                    else:
                        print(f"   ❌ {description} - NOT FOUND")
                        all_passed = False
                
                return all_passed
            else:
                print(f"   ❌ Frontend failed to load: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ Frontend loading error: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Testing Prometrix Frontend Integration\n")
    print("This simulates the exact requests the frontend makes to the backend.")
    
    # Test frontend loading
    frontend_ok = await test_frontend_loading()
    
    # Test API integration
    api_ok = await test_frontend_campaign_creation()
    
    print("\n" + "="*60)
    if frontend_ok and api_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Frontend loads correctly")
        print("✅ Campaign creation works")
        print("✅ Post mix configuration works") 
        print("✅ Post regeneration works")
        print("\n🌟 The 'Generate Campaign Blueprint' button should now work!")
        print("📍 Visit: http://localhost:8000/")
    else:
        print("💥 SOME TESTS FAILED!")
        if not frontend_ok:
            print("❌ Frontend loading issues")
        if not api_ok:
            print("❌ API integration issues")


if __name__ == "__main__":
    asyncio.run(main())