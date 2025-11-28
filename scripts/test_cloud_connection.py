#!/usr/bin/env python3
"""
Script untuk testing koneksi MongoDB Atlas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import MongoDBConnection, init_db
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test koneksi ke MongoDB Atlas"""
    try:
        logger.info("Testing koneksi ke MongoDB Atlas...")
        
        # Test koneksi
        client = MongoDBConnection.get_client()
        db = MongoDBConnection.get_database()
        
        # Test ping
        client.admin.command('ping')
        logger.info("✅ Koneksi berhasil ke MongoDB Atlas!")
        
        # Test database info
        collections = db.list_collection_names()
        logger.info(f"📁 Database: {db.name}")
        logger.info(f"📋 Jumlah koleksi: {len(collections)}")
        
        # Test insert/read
        test_collection = db.test_connection
        test_doc = {
            "test": True,
            "timestamp": datetime.utcnow(),
            "message": "Test koneksi MongoDB Atlas"
        }
        
        result = test_collection.insert_one(test_doc)
        logger.info(f"✅ Insert test berhasil dengan ID: {result.inserted_id}")
        
        # Read test
        found_doc = test_collection.find_one({"_id": result.inserted_id})
        logger.info(f"✅ Read test berhasil: {found_doc['message']}")
        
        # Clean up
        test_collection.delete_one({"_id": result.inserted_id})
        logger.info("🧹 Test document dihapus")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Koneksi gagal: {e}")
        return False

def test_database_operations():
    """Test operasi database dasar"""
    try:
        logger.info("Testing operasi database...")
        
        db = MongoDBConnection.get_database()
        
        # Test collections
        collections = db.list_collection_names()
        logger.info(f"Koleksi tersedia: {collections}")
        
        # Test users collection
        if 'users' in collections:
            user_count = db.users.count_documents({})
            logger.info(f"Jumlah users: {user_count}")
        
        # Test warehouses collection
        if 'warehouses' in collections:
            warehouse_count = db.warehouses.count_documents({})
            logger.info(f"Jumlah warehouses: {warehouse_count}")
        
        logger.info("✅ Operasi database berhasil!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Operasi database gagal: {e}")
        return False

if __name__ == "__main__":
    print("=== TESTING KONEKSI MONGODB ATLAS ===")
    print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test koneksi
    if test_connection():
        print("\n=== TESTING OPERASI DATABASE ===")
        test_database_operations()
        print("\n✅ Semua test berhasil! Aplikasi siap menggunakan MongoDB Atlas")
    else:
        print("\n❌ Test koneksi gagal! Periksa konfigurasi .env Anda")
        print("\nTips:")
        print("1. Pastikan MongoDB Atlas cluster sudah berjalan")
        print("2. Pastikan IP address sudah di-whitelist")
        print("3. Pastikan username & password benar")
        print("4. Pastikan connection string format benar")
