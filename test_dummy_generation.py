import sqlite3
import os
import sys
# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.dummy_data_generator import DummyDataGenerator
from utils.dummy_data_generator_safe import SafeDummyDataGenerator
from utils.sqlite_database import SQLiteDatabase

DB_PATH = "test_inventory.db"

def verify_data():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Initialize database schema
    print("Initializing database schema...")
    # SQLiteDatabase __init__ calls _initialize_database
    db = SQLiteDatabase(db_path=DB_PATH)
    
    print("Testing DummyDataGenerator...")
    generator = DummyDataGenerator(db_path=DB_PATH)
    generator.generate_all_data()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verify distributions
    cursor.execute("SELECT COUNT(*) FROM distributions")
    dist_count = cursor.fetchone()[0]
    print(f"Distributions count: {dist_count}")
    assert dist_count > 0, "Distributions should be generated"
    
    # Verify harvests date range
    cursor.execute("SELECT MIN(harvest_date), MAX(harvest_date) FROM harvests")
    min_date, max_date = cursor.fetchone()
    print(f"Harvests date range: {min_date} to {max_date}")
    
    # Verify 'out' transactions
    cursor.execute("SELECT COUNT(*) FROM inventory_transactions WHERE transaction_type='out'")
    out_count = cursor.fetchone()[0]
    print(f"Out transactions count: {out_count}")
    assert out_count > 0, "Out transactions should be generated"
    
    conn.close()
    
    # Clean up
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    print("\nTesting SafeDummyDataGenerator...")
    # Initialize database schema again for safe generator test
    db = SQLiteDatabase(db_path=DB_PATH)
    
    safe_generator = SafeDummyDataGenerator(db_path=DB_PATH)
    safe_generator.generate_all_safe_data()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verify distributions
    cursor.execute("SELECT COUNT(*) FROM distributions")
    dist_count = cursor.fetchone()[0]
    print(f"Safe Distributions count: {dist_count}")
    assert dist_count > 0, "Safe Distributions should be generated"
    
    conn.close()
    
    # Clean up
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    print("\n✅ Verification successful!")

if __name__ == "__main__":
    verify_data()
