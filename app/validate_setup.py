#!/usr/bin/env python3

"""
Validation script for historical sync functionality
"""

def test_imports():
    """Test that all imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        from utils import (
            get_missing_date_ranges, 
            calculate_month_navigation, 
            split_date_range_by_month,
            format_date_for_display
        )
        print("✅ Utils imports: OK")
    except ImportError as e:
        print(f"❌ Utils imports failed: {e}")
        return False
    
    try:
        from qashier_scraper import QashierPOSScraper
        print("✅ QashierPOSScraper import: OK")
    except ImportError as e:
        print(f"❌ QashierPOSScraper import failed: {e}")
        return False
    
    try:
        from services import SalesService
        print("✅ SalesService import: OK")
    except ImportError as e:
        print(f"❌ SalesService import failed: {e}")
        return False
    
    return True

def test_utility_functions():
    """Test utility functions"""
    print("\n🧪 Testing utility functions...")
    
    from utils import (
        get_missing_date_ranges, 
        calculate_month_navigation, 
        split_date_range_by_month,
        format_date_for_display
    )
    from datetime import date
    
    # Test missing ranges
    try:
        missing = get_missing_date_ranges()
        print(f"✅ Missing ranges detected: {len(missing)} ranges")
        if missing:
            print(f"   First range: {missing[0][0]} to {missing[0][1]}")
    except Exception as e:
        print(f"❌ get_missing_date_ranges failed: {e}")
        return False
    
    # Test month navigation calculation
    try:
        current = date(2025, 1, 6)
        target = date(2024, 3, 1)
        nav = calculate_month_navigation(current, target)
        print(f"✅ Month navigation: {nav['steps_needed']} steps {nav['navigation_direction']}")
    except Exception as e:
        print(f"❌ calculate_month_navigation failed: {e}")
        return False
    
    # Test date range splitting
    try:
        start = date(2025, 1, 7)
        end = date(2025, 3, 15)
        chunks = split_date_range_by_month(start, end)
        print(f"✅ Date range splitting: {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ split_date_range_by_month failed: {e}")
        return False
    
    # Test date formatting
    try:
        test_date = date(2024, 3, 15)
        formatted = format_date_for_display(test_date)
        print(f"✅ Date formatting: {formatted['day_text']}")
    except Exception as e:
        print(f"❌ format_date_for_display failed: {e}")
        return False
    
    return True

def test_service_creation():
    """Test that services can be created"""
    print("\n🏗️ Testing service creation...")
    
    try:
        from services import SalesService
        service = SalesService()
        print("✅ SalesService creation: OK")
        
        # Test that the service has the new methods
        if hasattr(service, 'sync_historical_data'):
            print("✅ Historical sync method: Available")
        else:
            print("❌ Historical sync method: Missing")
            return False
            
        if hasattr(service, 'sync_missing_historical_data'):
            print("✅ Missing data sync method: Available")
        else:
            print("❌ Missing data sync method: Missing")
            return False
            
        if hasattr(service, 'get_data_coverage_report'):
            print("✅ Coverage report method: Available")
        else:
            print("❌ Coverage report method: Missing")
            return False
    
    except Exception as e:
        print(f"❌ Service creation failed: {e}")
        return False
    
    return True

def test_scraper_methods():
    """Test that scraper has new methods"""
    print("\n🕷️ Testing scraper methods...")
    
    try:
        from qashier_scraper import QashierPOSScraper
        scraper = QashierPOSScraper()
        print("✅ QashierPOSScraper creation: OK")
        
        # Test that the scraper has the new methods
        if hasattr(scraper, 'scrape_historical_data'):
            print("✅ Historical scrape method: Available")
        else:
            print("❌ Historical scrape method: Missing")
            return False
            
        if hasattr(scraper, '_select_historical_date_range'):
            print("✅ Date range selection method: Available")
        else:
            print("❌ Date range selection method: Missing")
            return False
    
    except Exception as e:
        print(f"❌ Scraper method test failed: {e}")
        return False
    
    return True

def main():
    """Run all validation tests"""
    print("🚀 Lengolf Sales Historical Sync Validation")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_utility_functions()
    all_passed &= test_service_creation()
    all_passed &= test_scraper_methods()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All validation tests PASSED!")
        print("\n📋 Next steps:")
        print("1. Start the API: python app.py")
        print("2. Test endpoints: python test_historical_api.py http://localhost:8080")
        print("3. Check data coverage: curl http://localhost:8080/data/coverage")
        print("4. Sync missing data: curl -X POST http://localhost:8080/sync/missing")
    else:
        print("❌ Some validation tests FAILED!")
        print("Please check the errors above and fix them before proceeding.")
    
    return all_passed

if __name__ == "__main__":
    main() 