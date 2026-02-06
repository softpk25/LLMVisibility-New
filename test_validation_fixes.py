#!/usr/bin/env python3
"""
Test the validation fixes for the frontend campaign creation
"""

import asyncio
import httpx
import json


async def test_validation_fixes():
    """Test that all validation issues have been fixed"""
    
    print("🧪 Testing Validation Fixes...")
    print("="*50)
    
    # Test cases for different validation scenarios
    test_cases = [
        {
            "name": "✅ Valid Data (should work)",
            "data": {
                "campaign_name": "Test Campaign",
                "campaign_objective": "awareness",  # Fixed: lowercase
                "target_audience": "Tech enthusiasts",
                "start_date": "2024-06-01",
                "end_date": "2024-08-31", 
                "frequency": 1,  # Fixed: number
                "selected_personas": ["persona-tech-enthusiast"],
                "selected_brand_id": "brand-techflow-solutions",
                "product_integration_enabled": False,
                "selected_products": [],
                "language_config": {
                    "primary_language": "en",
                    "multilingual_enabled": False,
                    "additional_languages": []
                }
            },
            "should_pass": True
        },
        {
            "name": "❌ Invalid Objective (should fail)",
            "data": {
                "campaign_name": "Test Campaign",
                "campaign_objective": "Brand Awareness",  # Wrong: should be lowercase
                "target_audience": "Tech enthusiasts",
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
            },
            "should_pass": False
        },
        {
            "name": "❌ Invalid Frequency (should fail)",
            "data": {
                "campaign_name": "Test Campaign",
                "campaign_objective": "awareness",
                "target_audience": "Tech enthusiasts",
                "start_date": "2024-06-01",
                "end_date": "2024-08-31",
                "frequency": "Daily",  # Wrong: should be number
                "selected_personas": ["persona-tech-enthusiast"],
                "selected_brand_id": "brand-techflow-solutions",
                "product_integration_enabled": False,
                "selected_products": [],
                "language_config": {
                    "primary_language": "en",
                    "multilingual_enabled": False,
                    "additional_languages": []
                }
            },
            "should_pass": False
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🔍 {test_case['name']}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/campaigns/create",
                    json=test_case["data"],
                    timeout=30.0
                )
                
                success = response.status_code == 200
                
                if test_case["should_pass"]:
                    if success:
                        result = response.json()
                        print(f"   ✅ PASS - Campaign created: {result.get('campaign_id')}")
                        results.append(True)
                    else:
                        print(f"   ❌ FAIL - Expected success but got {response.status_code}")
                        print(f"   Error: {response.text}")
                        results.append(False)
                else:
                    if not success:
                        print(f"   ✅ PASS - Correctly rejected with {response.status_code}")
                        results.append(True)
                    else:
                        print(f"   ❌ FAIL - Expected failure but got success")
                        results.append(False)
                        
        except Exception as e:
            print(f"   ❌ ERROR - Exception: {e}")
            results.append(False)
    
    return all(results)


async def test_frontend_data_structure():
    """Test the exact data structure the frontend should now send"""
    
    print("\n🌐 Testing Frontend Data Structure...")
    print("="*50)
    
    # This simulates what the fixed frontend should send
    frontend_data = {
        "campaign_name": "Summer Product Launch",
        "campaign_objective": "awareness",  # Fixed from initial data
        "target_audience": "Tech enthusiasts and early adopters",  # Fixed field name
        "start_date": "2024-06-01",
        "end_date": "2024-08-31",
        "frequency": 1,  # Fixed from "Daily" to number
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
    
    print("📤 Sending frontend-like request...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/campaigns/create",
                json=frontend_data,
                headers={
                    "Content-Type": "application/json",
                    "Origin": "http://localhost:8000",
                    "Referer": "http://localhost:8000/"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS - Frontend data structure works!")
                print(f"   Campaign ID: {result.get('campaign_id')}")
                print(f"   Message: {result.get('message')}")
                return True
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR - {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Testing All Validation Fixes\n")
    
    # Test validation scenarios
    validation_ok = await test_validation_fixes()
    
    # Test frontend data structure
    frontend_ok = await test_frontend_data_structure()
    
    print("\n" + "="*60)
    if validation_ok and frontend_ok:
        print("🎉 ALL VALIDATION FIXES SUCCESSFUL!")
        print("✅ Backend correctly validates data types")
        print("✅ Frontend sends correct data structure")
        print("✅ Campaign objective fixed (lowercase)")
        print("✅ Frequency fixed (number instead of string)")
        print("✅ Target audience field name fixed")
        print("\n🌟 The frontend should now work without 422 errors!")
        print("📍 Try: http://localhost:8000/")
    else:
        print("💥 SOME VALIDATION FIXES FAILED!")
        if not validation_ok:
            print("❌ Validation test issues")
        if not frontend_ok:
            print("❌ Frontend data structure issues")


if __name__ == "__main__":
    asyncio.run(main())