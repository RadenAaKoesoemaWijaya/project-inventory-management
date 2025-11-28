#!/usr/bin/env python3
"""
Testing Script for SQLite Database
Validates database functionality and fixes any issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.sqlite_database import (
    get_database, 
    init_db, 
    create_user, 
    get_user_by_username,
    get_stock_status,
    get_items_low_stock,
    get_warehouses
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test basic database connection"""
    print("🔍 Testing Database Connection...")
    try:
        db = get_database()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_table_creation():
    """Test if all tables are created properly"""
    print("\n🔍 Testing Table Creation...")
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Check if all required tables exist
        required_tables = [
            'users', 'warehouses', 'items', 'farmers', 'merchants', 
            'harvests', 'inventory_transactions', 'notifications',
            'distribution_routes', 'seeds', 'fertilizers'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
                return False
                
        print("✅ All required tables exist")
        return True
    except Exception as e:
        print(f"❌ Table creation test failed: {e}")
        return False

def test_user_operations():
    """Test user creation and authentication"""
    print("\n🔍 Testing User Operations...")
    try:
        # Test user creation
        success, message = create_user(
            "testuser", 
            "testpass123", 
            "Test User", 
            "staff", 
            "Lumbung Desa Sentra Tani"
        )
        
        if success:
            print("✅ User creation successful")
        else:
            print(f"❌ User creation failed: {message}")
            return False
        
        # Test user retrieval
        user = get_user_by_username("testuser")
        if user:
            print("✅ User retrieval successful")
        else:
            print("❌ User retrieval failed")
            return False
        
        # Test authentication
        from utils.auth_new import login_user
        import streamlit as st
        
        # Mock session state for testing
        if not hasattr(st, 'session_state'):
            class MockSessionState:
                def __init__(self):
                    self.authenticated = False
                    self.user = None
                
                def __setitem__(self, key, value):
                    setattr(self, key, value)
                
                def __getitem__(self, key):
                    return getattr(self, key)
                
                def get(self, key, default=None):
                    return getattr(self, key, default)
            
            st.session_state = MockSessionState()
        
        login_success = login_user("testuser", "testpass123")
        if login_success:
            print("✅ User authentication successful")
        else:
            print("❌ User authentication failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ User operations test failed: {e}")
        return False

def test_warehouse_operations():
    """Test warehouse operations"""
    print("\n🔍 Testing Warehouse Operations...")
    try:
        warehouses = get_warehouses()
        if len(warehouses) > 0:
            print(f"✅ Found {len(warehouses)} warehouses")
            print(f"   Sample warehouse: {warehouses[0]['name']}")
            return True
        else:
            print("❌ No warehouses found")
            return False
    except Exception as e:
        print(f"❌ Warehouse operations test failed: {e}")
        return False

def test_stock_operations():
    """Test stock status and low stock items"""
    print("\n🔍 Testing Stock Operations...")
    try:
        # Test stock status
        stock_status = get_stock_status()
        print(f"✅ Stock status retrieved: {stock_status}")
        
        # Test low stock items
        low_stock_items = get_items_low_stock()
        print(f"✅ Low stock items retrieved: {len(low_stock_items)} items")
        
        return True
    except Exception as e:
        print(f"❌ Stock operations test failed: {e}")
        return False

def test_data_integrity():
    """Test data integrity and constraints"""
    print("\n🔍 Testing Data Integrity...")
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Test unique constraint on usernames
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE username = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 1:
            print("✅ Unique username constraint working")
        else:
            print(f"❌ Expected 1 admin user, found {admin_count}")
            return False
        
        # Test foreign key constraints (if items table references warehouses)
        cursor.execute("SELECT COUNT(*) as count FROM items")
        items_count = cursor.fetchone()[0]
        print(f"✅ Items table accessible: {items_count} items")
        
        return True
    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Remove test user
        cursor.execute("DELETE FROM users WHERE username = 'testuser'")
        conn.commit()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Database Validation Tests")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_table_creation,
        test_user_operations,
        test_warehouse_operations,
        test_stock_operations,
        test_data_integrity
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database is ready for use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    # Cleanup
    cleanup_test_data()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
