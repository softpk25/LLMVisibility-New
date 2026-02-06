#!/usr/bin/env python3
"""
Test the frontend fix by simulating browser behavior
"""

import asyncio
import httpx
import json


async def test_frontend_campaign_creation():
    """Test the exact request the fixed frontend should make"""
    
    print("🧪 Testing Fixed Frontend Campaign Creation...")
    
    # This simulates what the frontend form would send after the fix
    campaign_data = {
        "campaign_name": "Test Campaign from Browser",
        "campaign_objective": "awareness", 
        "target_audience": "Tech enthusiasts and early adopters",  # Fixed field name
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
    
    # Simulate browser headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "http://localhost:8000",
        "Referer": "http://localhost:8000/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print("📤 Sending request to /api/v1/campaigns/create...")
            
            response = await client.post(
                "http://localhost:8000/api/v1/campaigns/create",
                json=campaign_data,
                headers=headers,
                timeout=30.0
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS! Campaign created successfully")
                print(f"   Campaign ID: {result.get('campaign_id')}")
                print(f"   Status: {result.get('status')}")
                print(f"   Message: {result.get('message')}")
                
                # Check if AI strategy was generated
                if result.get('data', {}).get('content_plan'):
                    content_plan = result['data']['content_plan'].get('generated_plan', '')
                    print(f"   AI Strategy: {content_plan[:100]}...")
                
                return True
            else:
                print(f"❌ FAILED! Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_frontend_loading():
    """Test that the frontend loads without errors"""
    print("\n🌐 Testing Frontend Loading...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/", timeout=10.0)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check for the fixed field reference
                if "this.workflow.audience" in html_content:
                    print("   ✅ Fixed field reference found in frontend")
                else:
                    print("   ❌ Fixed field reference not found")
                
                # Check for key elements
                checks = [
                    ("createCampaignBlueprint", "Campaign creation function"),
                    ("✨ Create Campaign Blueprint", "Create button"),
                    ("x-model=\"workflow.audience\"", "Target audience field binding")
                ]
                
                all_good = True
                for check_text, description in checks:
                    if check_text in html_content:
                        print(f"   ✅ {description} - OK")
                    else:
                        print(f"   ❌ {description} - MISSING")
                        all_good = False
                
                return all_good
            else:
                print(f"   ❌ Frontend failed to load: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ Frontend loading error: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Testing Frontend Fix\n")
    print("This verifies that the field name mismatch has been resolved.")
    
    # Test frontend loading
    frontend_ok = await test_frontend_loading()
    
    # Test API integration
    api_ok = await test_frontend_campaign_creation()
    
    print("\n" + "="*60)
    if frontend_ok and api_ok:
        print("🎉 FRONTEND FIX SUCCESSFUL!")
        print("✅ Frontend loads correctly with fixed field references")
        print("✅ Campaign creation API works with correct field names")
        print("✅ The 'Generate Campaign Blueprint' button should now work!")
        print("\n🌟 Try it now:")
        print("📍 Visit: http://localhost:8000/")
        print("📝 Fill the form and click 'Create Campaign Blueprint'")
        print("🎯 It should work without the 500 error!")
    else:
        print("💥 FRONTEND FIX INCOMPLETE!")
        if not frontend_ok:
            print("❌ Frontend loading issues")
        if not api_ok:
            print("❌ API integration issues")


if __name__ == "__main__":
    asyncio.run(main())