#!/usr/bin/env python3
"""
Fix Database Issues
Resolves database initialization and data insertion problems
"""

import sys
import os
import sqlite3
import uuid
import bcrypt
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Completely reset the database"""
    print("🔄 Resetting database...")
    
    db_path = "inventory_new.db"
    
    # Remove existing database file
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ Removed existing database file: {db_path}")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create tables
    print("📝 Creating tables...")
    
    # Users table
    cursor.execute('''
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            last_login TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    
    # Warehouses table
    cursor.execute('''
        CREATE TABLE warehouses (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            location TEXT,
            capacity INTEGER,
            coordinates TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Items table
    cursor.execute('''
        CREATE TABLE items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            current_stock REAL DEFAULT 0,
            min_stock REAL DEFAULT 0,
            max_stock REAL DEFAULT 0,
            unit TEXT,
            price_per_unit REAL,
            expiry_date DATE,
            warehouse_id TEXT,
            harvest_season TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        )
    ''')
    
    # Farmers table
    cursor.execute('''
        CREATE TABLE farmers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            coordinates TEXT,
            land_area REAL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Merchants table
    cursor.execute('''
        CREATE TABLE merchants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            location TEXT,
            coordinates TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Harvests table
    cursor.execute('''
        CREATE TABLE harvests (
            id TEXT PRIMARY KEY,
            farmer_id TEXT,
            warehouse_id TEXT,
            harvest_date DATE,
            season TEXT,
            crop_type TEXT,
            quantity REAL,
            unit TEXT,
            quality_grade TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES farmers(id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        )
    ''')
    
    # Inventory transactions table
    cursor.execute('''
        CREATE TABLE inventory_transactions (
            id TEXT PRIMARY KEY,
            item_id TEXT,
            transaction_type TEXT,
            quantity REAL,
            from_warehouse_id TEXT,
            to_warehouse_id TEXT,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            notes TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id),
            FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(id),
            FOREIGN KEY (to_warehouse_id) REFERENCES warehouses(id)
        )
    ''')
    
    # Notifications table
    cursor.execute('''
        CREATE TABLE notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            message TEXT,
            type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Distribution routes table
    cursor.execute('''
        CREATE TABLE distribution_routes (
            id TEXT PRIMARY KEY,
            route_name TEXT,
            from_warehouse_id TEXT,
            to_merchant_id TEXT,
            distance REAL,
            travel_time REAL,
            efficiency_score REAL,
            fuel_cost REAL,
            road_condition TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(id),
            FOREIGN KEY (to_merchant_id) REFERENCES merchants(id)
        )
    ''')
    
    # Seeds table
    cursor.execute('''
        CREATE TABLE seeds (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            crop_type TEXT,
            supplier TEXT,
            quantity_available REAL,
            unit TEXT,
            price_per_unit REAL,
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Fertilizers table
    cursor.execute('''
        CREATE TABLE fertilizers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            supplier TEXT,
            quantity_available REAL,
            unit TEXT,
            price_per_unit REAL,
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("✅ All tables created successfully")
    
    # Insert default data
    print("📊 Inserting default data...")
    
    # Insert warehouses
    default_warehouses = [
        ("Lumbung Desa Sentra Tani", "Lumbung utama untuk menyimpan hasil pertanian desa", "Pusat Desa", 50000),
        ("Lumbung Desa Tambakrejo", "Lumbung untuk wilayah Tambakrejo", "Tambakrejo", 30000),
        ("Lumbung Desa Ngadirejo", "Lumbung untuk wilayah Ngadirejo", "Ngadirejo", 25000),
        ("Lumbung Desa Tlogosari", "Lumbung untuk wilayah Tlogosari", "Tlogosari", 35000),
        ("Lumbung Desa Bandungrejo", "Lumbung untuk wilayah Bandungrejo", "Bandungrejo", 20000),
        ("Lumbung Desa Purworejo", "Lumbung untuk wilayah Purworejo", "Purworejo", 15000),
        ("Lumbung Desa Sumberagung", "Lumbung untuk wilayah Sumberagung", "Sumberagung", 40000),
        ("Lumbung Desa Karanganyar", "Lumbung untuk wilayah Karanganyar", "Karanganyar", 18000)
    ]
    
    for name, desc, location, capacity in default_warehouses:
        cursor.execute('''
            INSERT INTO warehouses (id, name, description, location, capacity)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), name, desc, location, capacity))
    
    print(f"✅ Inserted {len(default_warehouses)} warehouses")
    
    # Insert admin user
    hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT INTO users (id, username, password, full_name, role, department)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (str(uuid.uuid4()), "admin", hashed_password, "Administrator Pertanian", "admin", "Lumbung Desa Sentra Tani"))
    
    print("✅ Inserted admin user")
    
    # Insert sample items
    sample_items = [
        ("Beras Organik", "Beras", 1000, 100, 2000, "kg", 15000, None, None, "Musim Hujan 2024"),
        ("Jagung Manis", "Jagung", 500, 50, 1000, "kg", 8000, None, None, "Musim Kemarau 2024"),
        ("Kedelai Hitam", "Kacang-kacangan", 300, 30, 600, "kg", 12000, None, None, "Musim Hujan 2024"),
        ("Cabai Merah", "Sayuran", 200, 20, 400, "kg", 25000, None, None, "Musim Panen 2024"),
        ("Tomat", "Sayuran", 150, 15, 300, "kg", 18000, None, None, "Musim Panen 2024")
    ]
    
    # Get first warehouse ID for items
    cursor.execute("SELECT id FROM warehouses LIMIT 1")
    warehouse_id = cursor.fetchone()[0]
    
    for name, category, stock, min_stock, max_stock, unit, price, expiry, warehouse_id_param, season in sample_items:
        cursor.execute('''
            INSERT INTO items (id, name, category, current_stock, min_stock, max_stock, unit, price_per_unit, expiry_date, warehouse_id, harvest_season)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), name, category, stock, min_stock, max_stock, unit, price, expiry, warehouse_id, season))
    
    print(f"✅ Inserted {len(sample_items)} sample items")
    
    # Insert sample farmers
    sample_farmers = [
        ("Bapak Ahmad", "Desa Sentra Tani", None, 2.5, "081234567890"),
        ("Ibu Siti", "Desa Tambakrejo", None, 1.8, "082345678901"),
        ("Bapak Budi", "Desa Ngadirejo", None, 3.2, "083456789012")
    ]
    
    for name, location, coordinates, land_area, phone in sample_farmers:
        cursor.execute('''
            INSERT INTO farmers (id, name, location, coordinates, land_area, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), name, location, coordinates, land_area, phone))
    
    print(f"✅ Inserted {len(sample_farmers)} sample farmers")
    
    # Insert sample merchants
    sample_merchants = [
        ("Pasar Tradisional Sentra", "Pasar", "Pusat Kota", None, "084567890123"),
        ("Toko Sayur Segar", "Retail", "Desa Tambakrejo", None, "085678901234"),
        ("Koperasi Tani Makmur", "Koperasi", "Kota", None, "086789012345")
    ]
    
    for name, type_merchant, location, coordinates, phone in sample_merchants:
        cursor.execute('''
            INSERT INTO merchants (id, name, type, location, coordinates, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), name, type_merchant, location, coordinates, phone))
    
    print(f"✅ Inserted {len(sample_merchants)} sample merchants")
    
    # Create indexes
    print("🔍 Creating indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)",
        "CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)",
        "CREATE INDEX IF NOT EXISTS idx_items_warehouse ON items(warehouse_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_item ON inventory_transactions(item_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_date ON inventory_transactions(transaction_date)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)"
    ]
    
    for index_query in indexes:
        cursor.execute(index_query)
    
    print("✅ All indexes created")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print("🎉 Database reset and initialization completed successfully!")
    return True

def verify_database():
    """Verify database contents"""
    print("\n🔍 Verifying database contents...")
    
    conn = sqlite3.connect("inventory_new.db")
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
    
    # Check data counts
    table_counts = {
        'users': 'SELECT COUNT(*) FROM users',
        'warehouses': 'SELECT COUNT(*) FROM warehouses',
        'items': 'SELECT COUNT(*) FROM items',
        'farmers': 'SELECT COUNT(*) FROM farmers',
        'merchants': 'SELECT COUNT(*) FROM merchants'
    }
    
    for table, query in table_counts.items():
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"✅ {table.title()}: {count} records")
    
    conn.close()
    print("✅ Database verification completed")

def main():
    """Main function"""
    print("🚀 Database Fix and Reset Utility")
    print("=" * 50)
    
    try:
        if reset_database():
            verify_database()
            print("\n🎉 Database is now ready for use!")
            return True
        else:
            print("\n❌ Database reset failed!")
            return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
