#!/usr/bin/env python3
"""
Script untuk migrasi data dari MongoDB lokal ke MongoDB Atlas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from utils.database import MongoDBConnection
from config import MONGODB_SETTINGS
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_to_cloud():
    """Migrasi data dari MongoDB lokal ke MongoDB Atlas"""
    
    # Koneksi ke MongoDB lokal (sumber)
    try:
        local_client = MongoClient("mongodb://localhost:27017")
        local_db = local_client[MONGODB_SETTINGS['database']]
        logger.info("Terhubung ke MongoDB lokal")
    except Exception as e:
        logger.error(f"Gagal koneksi ke MongoDB lokal: {e}")
        return False
    
    # Koneksi ke MongoDB Atlas (tujuan)
    try:
        cloud_client = MongoDBConnection.get_client()
        cloud_db = MongoDBConnection.get_database()
        logger.info("Terhubung ke MongoDB Atlas")
    except Exception as e:
        logger.error(f"Gagal koneksi ke MongoDB Atlas: {e}")
        return False
    
    # Daftar koleksi yang akan dimigrasi
    collections_to_migrate = [
        'users', 'items', 'warehouses', 'farmers', 'merchants', 
        'harvests', 'seeds', 'fertilizers', 'distribution_routes', 
        'inventory_transactions', 'item_requests', 'notifications'
    ]
    
    total_migrated = 0
    
    for collection_name in collections_to_migrate:
        try:
            logger.info(f"Migrasi koleksi: {collection_name}")
            
            # Cek apakah koleksi ada di lokal
            if collection_name not in local_db.list_collection_names():
                logger.warning(f"Koleksi {collection_name} tidak ditemukan di lokal, dilewati")
                continue
            
            # Ambil semua data dari koleksi lokal
            local_collection = local_db[collection_name]
            documents = list(local_collection.find())
            
            if not documents:
                logger.info(f"Koleksi {collection_name} kosong, dilewati")
                continue
            
            # Hapus data existing di cloud
            cloud_collection = cloud_db[collection_name]
            cloud_collection.delete_many({})
            
            # Insert data ke cloud
            if documents:
                cloud_collection.insert_many(documents)
                migrated_count = len(documents)
                total_migrated += migrated_count
                logger.info(f"Berhasil migrasi {migrated_count} dokumen dari {collection_name}")
            
        except Exception as e:
            logger.error(f"Gagal migrasi koleksi {collection_name}: {e}")
            continue
    
    # Tutup koneksi
    local_client.close()
    MongoDBConnection.close_connection()
    
    logger.info(f"Migrasi selesai! Total {total_migrated} dokumen dimigrasi")
    return True

def verify_migration():
    """Verifikasi hasil migrasi"""
    try:
        cloud_db = MongoDBConnection.get_database()
        
        logger.info("Verifikasi migrasi:")
        for collection_name in cloud_db.list_collection_names():
            count = cloud_db[collection_name].count_documents({})
            logger.info(f"- {collection_name}: {count} dokumen")
        
        return True
    except Exception as e:
        logger.error(f"Gagal verifikasi: {e}")
        return False

if __name__ == "__main__":
    print("=== MIGRASI MONGODB LOKAL KE MONGODB ATLAS ===")
    print("Pastikan MongoDB lokal sedang berjalan")
    print("Pastikan konfigurasi .env sudah diatur untuk MongoDB Atlas")
    print()
    
    confirm = input("Apakah Anda ingin melanjutkan migrasi? (y/N): ")
    if confirm.lower() == 'y':
        if migrate_to_cloud():
            print("\n=== VERIFIKASI MIGRASI ===")
            verify_migration()
            print("\nMigrasi selesai!")
        else:
            print("Migrasi gagal!")
    else:
        print("Migrasi dibatalkan")
