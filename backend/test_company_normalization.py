#!/usr/bin/env python3
"""
Test script to verify company name normalization works correctly
"""

import sys
sys.path.insert(0, 'backend')

from app.repositories.company import CompanyRepository

def test_normalization():
    """Test various company name inputs"""
    test_cases = [
        ("Tech Corp", "tech corp"),
        ("tech corp", "tech corp"),
        ("TECH CORP", "tech corp"),
        ("  Tech   Corp  ", "tech corp"),
        ("TechCorp", "techcorp"),
        ("tech-corp", "tech-corp"),
        ("Tech_Corp", "tech_corp"),
        ("  ACME  Inc  ", "acme inc"),
        ("My Company Name", "my company name"),
        ("MY COMPANY NAME", "my company name"),
    ]
    
    print("Testing Company Name Normalization")
    print("=" * 60)
    
    all_passed = True
    for input_name, expected in test_cases:
        result = CompanyRepository.normalize_company_name(input_name)
        passed = result == expected
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"{status} | Input: '{input_name}' → Output: '{result}'")
        if not passed:
            print(f"       Expected: '{expected}'")
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    success = test_normalization()
    sys.exit(0 if success else 1)
