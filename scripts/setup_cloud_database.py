#!/usr/bin/env python3
"""
Script untuk setup dan inisialisasi database MongoDB Cloud
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import MongoDBConnection, init_db
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_cloud_database():
    """Setup database di MongoDB Cloud"""
    try:
        logger.info("🚀 Setting up MongoDB Cloud database...")
        
        # Test koneksi
        client = MongoDBConnection.get_client()
        logger.info("✅ Koneksi ke MongoDB Atlas berhasil!")
        
        # Initialize database
        logger.info("📋 Initializing database collections...")
        init_db()
        logger.info("✅ Database initialization completed!")
        
        # Verify setup
        db = MongoDBConnection.get_database()
        collections = db.list_collection_names()
        
        logger.info(f"📊 Database: {db.name}")
        logger.info(f"📁 Collections created: {len(collections)}")
        
        # Check default data
        warehouses_count = db.warehouses.count_documents({})
        users_count = db.users.count_documents({})
        
        logger.info(f"🏠 Default warehouses: {warehouses_count}")
        logger.info(f"👥 Default users: {users_count}")
        
        # Test admin user
        admin_user = db.users.find_one({"username": "admin"})
        if admin_user:
            logger.info("✅ Admin user created successfully")
            logger.info("🔑 Login credentials:")
            logger.info("   Username: admin")
            logger.info("   Password: admin123")
        else:
            logger.warning("⚠️ Admin user not found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False

def test_application_ready():
    """Test apakah aplikasi siap digunakan"""
    try:
        logger.info("🧪 Testing application readiness...")
        
        db = MongoDBConnection.get_database()
        
        # Test collections exist
        required_collections = [
            'users', 'items', 'warehouses', 'farmers', 'merchants', 
            'harvests', 'seeds', 'fertilizers', 'distribution_routes', 
            'inventory_transactions', 'item_requests', 'notifications'
        ]
        
        missing_collections = []
        for collection in required_collections:
            if collection not in db.list_collection_names():
                missing_collections.append(collection)
        
        if missing_collections:
            logger.error(f"❌ Missing collections: {missing_collections}")
            return False
        
        # Test admin access
        admin_user = db.users.find_one({"username": "admin"})
        if not admin_user:
            logger.error("❌ Admin user not found")
            return False
        
        # Test warehouses data
        warehouse_count = db.warehouses.count_documents({})
        if warehouse_count == 0:
            logger.error("❌ No warehouses found")
            return False
        
        logger.info("✅ Application is ready to use!")
        logger.info(f"📊 {len(required_collections)} collections available")
        logger.info(f"🏠 {warehouse_count} warehouses configured")
        logger.info("👤 Admin user ready for login")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Readiness test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🌾 LUMBUNG DIGITAL - MONGODB CLOUD SETUP")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🔧 Setting up cloud database...")
    if setup_cloud_database():
        print("\n🧪 Testing application readiness...")
        if test_application_ready():
            print("\n" + "=" * 60)
            print("🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("📱 You can now run the application:")
            print("   streamlit run app.py")
            print()
            print("🔑 Login credentials:")
            print("   Username: admin")
            print("   Password: admin123")
            print()
            print("🌐 Your data is now stored in MongoDB Cloud!")
            print("=" * 60)
        else:
            print("\n❌ Application is not ready. Check the errors above.")
    else:
        print("\n❌ Setup failed. Check your MongoDB Cloud configuration.")
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify MongoDB Atlas cluster is running")
        print("2. Check IP whitelist in Network Access")
        print("3. Verify username and password")
        print("4. Ensure database name is correct")
