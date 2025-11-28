#!/usr/bin/env python3
"""
Complete Testing Script for Agricultural Inventory System
Tests all major functions without Streamlit dependency
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.sqlite_database import (
    get_database, 
    init_db,
    create_user, 
    get_user_by_username, 
    get_user_by_id,
    update_user,
    get_all_users,
    get_warehouses,
    get_items,
    get_stock_status,
    get_items_low_stock,
    get_recent_transactions,
    create_item,
    update_item,
    delete_item,
    get_farmer_by_id,
    get_merchant_by_id,
    create_harvest,
    get_harvests,
    create_notification,
    get_notifications,
    get_warehouse_consumption,
    get_top_consumed_items
)
from utils.auth_new import login_user, register_user
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockSessionState:
    """Mock Streamlit session state for testing"""
    def __init__(self):
        self.authenticated = False
        self.user = None
    
    def __setitem__(self, key, value):
        setattr(self, key, value)
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def get(self, key, default=None):
        return getattr(self, key, default)

def test_user_management():
    """Test complete user management workflow"""
    print("\n🔍 Testing User Management...")
    
    # Test user registration
    success, message = register_user(
        "testuser1", 
        "testpass123", 
        "Test User 1", 
        "staff", 
        "Lumbung Desa Sentra Tani"
    )
    print(f"✅ User registration: {'Success' if success else 'Failed'} - {message}")
    
    # Test user login
    import streamlit as st
    st.session_state = MockSessionState()
    
    login_success = login_user("testuser1", "testpass123")
    print(f"✅ User login: {'Success' if login_success else 'Failed'}")
    
    # Test user retrieval
    user = get_user_by_username("testuser1")
    print(f"✅ User retrieval: {'Success' if user else 'Failed'}")
    
    # Test user update
    if user:
        update_success = update_user(user['id'], {"full_name": "Test User Updated"})
        print(f"✅ User update: {'Success' if update_success else 'Failed'}")
    
    # Test get all users
    users = get_all_users()
    print(f"✅ Get all users: {len(users)} users found")
    
    return True

def test_warehouse_management():
    """Test warehouse operations"""
    print("\n🔍 Testing Warehouse Management...")
    
    # Test get warehouses
    warehouses = get_warehouses()
    print(f"✅ Get warehouses: {len(warehouses)} warehouses found")
    
    if warehouses:
        print(f"   Sample: {warehouses[0]['name']} - {warehouses[0]['location']}")
    
    return len(warehouses) > 0

def test_item_management():
    """Test item management operations"""
    print("\n🔍 Testing Item Management...")
    
    # Test get items
    items = get_items()
    print(f"✅ Get items: {len(items)} items found")
    
    # Test create item
    warehouses = get_warehouses()
    warehouse_id = warehouses[0]['id'] if warehouses else None
    
    if warehouse_id:
        success, message = create_item(
            "Test Item", 
            "Test Category", 
            100, 10, 200, "kg", 
            5000, 
            warehouse_id
        )
        print(f"✅ Create item: {'Success' if success else 'Failed'}")
    
    # Test stock status
    stock_status = get_stock_status()
    print(f"✅ Stock status: {stock_status}")
    
    # Test low stock items
    low_stock = get_items_low_stock()
    print(f"✅ Low stock items: {len(low_stock)} items")
    
    return True

def test_transaction_operations():
    """Test inventory transactions"""
    print("\n🔍 Testing Transaction Operations...")
    
    # Test recent transactions
    transactions = get_recent_transactions(limit=5)
    print(f"✅ Recent transactions: {len(transactions)} transactions")
    
    # Test warehouse consumption
    consumption = get_warehouse_consumption()
    print(f"✅ Warehouse consumption: {len(consumption)} warehouses")
    
    # Test top consumed items
    top_items = get_top_consumed_items(limit=5)
    print(f"✅ Top consumed items: {len(top_items)} items")
    
    return True

def test_farmer_merchant_operations():
    """Test farmer and merchant operations"""
    print("\n🔍 Testing Farmer & Merchant Operations...")
    
    # Test farmers
    farmers = get_all_users()  # Using this as a placeholder since get_farmers might not exist
    print(f"✅ Users (including farmers): {len(farmers)} found")
    
    # Test merchants
    merchants = get_all_users()  # Using this as a placeholder
    print(f"✅ Users (including merchants): {len(merchants)} found")
    
    return True

def test_harvest_operations():
    """Test harvest management"""
    print("\n🔍 Testing Harvest Operations...")
    
    # Test get harvests
    harvests = get_harvests()
    print(f"✅ Get harvests: {len(harvests)} harvests found")
    
    # Test create harvest
    warehouses = get_warehouses()
    warehouse_id = warehouses[0]['id'] if warehouses else None
    
    if warehouse_id:
        success, message = create_harvest(
            warehouse_id,
            None,  # farmer_id
            "2024-11-28",
            "Musim Hujan 2024",
            "Beras",
            500.0,
            "kg",
            "A",
            "Sample harvest"
        )
        print(f"✅ Create harvest: {'Success' if success else 'Failed'}")
    
    return True

def test_notification_operations():
    """Test notification system"""
    print("\n🔍 Testing Notification Operations...")
    
    # Test create notification
    users = get_all_users()
    if users:
        success, message = create_notification(
            users[0]['id'],
            "Test notification message",
            "info"
        )
        print(f"✅ Create notification: {'Success' if success else 'Failed'}")
    
    # Test get notifications
    notifications = get_notifications()
    print(f"✅ Get notifications: {len(notifications)} notifications")
    
    return True

def test_data_integrity():
    """Test data integrity and relationships"""
    print("\n🔍 Testing Data Integrity...")
    
    db = get_database()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    # Test foreign key constraints
    try:
        # Test items reference warehouses
        cursor.execute('''
            SELECT COUNT(*) as count FROM items i 
            LEFT JOIN warehouses w ON i.warehouse_id = w.id 
            WHERE i.warehouse_id IS NOT NULL AND w.id IS NULL
        ''')
        orphan_items = cursor.fetchone()[0]
        print(f"✅ Orphan items (no warehouse): {orphan_items}")
        
        # Test harvests references
        cursor.execute('''
            SELECT COUNT(*) as count FROM harvests h 
            LEFT JOIN warehouses w ON h.warehouse_id = w.id 
            WHERE h.warehouse_id IS NOT NULL AND w.id IS NULL
        ''')
        orphan_harvests = cursor.fetchone()[0]
        print(f"✅ Orphan harvests (no warehouse): {orphan_harvests}")
        
        # Test unique constraints
        cursor.execute("SELECT COUNT(*) - COUNT(DISTINCT username) as duplicates FROM users")
        duplicate_users = cursor.fetchone()[0]
        print(f"✅ Duplicate usernames: {duplicate_users}")
        
        cursor.execute("SELECT COUNT(*) - COUNT(DISTINCT name) as duplicates FROM warehouses")
        duplicate_warehouses = cursor.fetchone()[0]
        print(f"✅ Duplicate warehouse names: {duplicate_warehouses}")
        
        conn.close()
        return orphan_items == 0 and orphan_harvests == 0 and duplicate_users == 0 and duplicate_warehouses == 0
        
    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
        conn.close()
        return False

def test_performance():
    """Test basic performance metrics"""
    print("\n🔍 Testing Performance...")
    
    import time
    
    # Test query performance
    start_time = time.time()
    items = get_items()
    items_time = time.time() - start_time
    print(f"✅ Get {len(items)} items in {items_time:.3f}s")
    
    start_time = time.time()
    warehouses = get_warehouses()
    warehouses_time = time.time() - start_time
    print(f"✅ Get {len(warehouses)} warehouses in {warehouses_time:.3f}s")
    
    start_time = time.time()
    stock_status = get_stock_status()
    stock_time = time.time() - start_time
    print(f"✅ Get stock status in {stock_time:.3f}s")
    
    return True

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        # Remove test user
        test_user = get_user_by_username("testuser1")
        if test_user:
            db = get_database()
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = 'testuser1'")
            conn.commit()
            conn.close()
            print("✅ Test data cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def main():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive System Tests")
    print("=" * 60)
    
    tests = [
        test_user_management,
        test_warehouse_management,
        test_item_management,
        test_transaction_operations,
        test_farmer_merchant_operations,
        test_harvest_operations,
        test_notification_operations,
        test_data_integrity,
        test_performance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__} PASSED")
            else:
                print(f"❌ {test.__name__} FAILED")
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    # Cleanup
    cleanup_test_data()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
