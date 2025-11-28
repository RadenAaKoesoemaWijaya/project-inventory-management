import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
import uuid
from typing import Dict, List, Optional, Any
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteDatabase:
    """SQLite database manager for agricultural inventory system"""
    
    def __init__(self, db_path="inventory_new.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize_database()
    
    def _get_connection(self):
        """Get database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        return self.conn
    
    def _initialize_database(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                last_login TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        # Create warehouses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS warehouses (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                location TEXT,
                capacity INTEGER,
                coordinates TEXT,  -- JSON string for lat/lng
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
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
        
        # Create farmers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS farmers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT,
                coordinates TEXT,  -- JSON string for lat/lng
                land_area REAL,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create merchants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS merchants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                location TEXT,
                coordinates TEXT,  -- JSON string for lat/lng
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create harvests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS harvests (
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
        
        # Create inventory_transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id TEXT PRIMARY KEY,
                item_id TEXT,
                transaction_type TEXT,  -- 'in', 'out', 'transfer', 'distribution'
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
        
        # Create notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                message TEXT,
                type TEXT DEFAULT 'info',
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create distribution_routes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS distribution_routes (
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
        
        # Create seeds table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seeds (
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
        
        # Create fertilizers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fertilizers (
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
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_item ON inventory_transactions(item_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON inventory_transactions(transaction_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)')
        
        conn.commit()
        logger.info("Database tables initialized successfully")
    
    def insert_default_data(self):
        """Insert default data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Insert default warehouses
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
                INSERT OR IGNORE INTO warehouses (id, name, description, location, capacity)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), name, desc, location, capacity))
        
        # Insert admin user (password: admin123)
        hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, username, password, full_name, role, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), "admin", hashed_password, "Administrator Pertanian", "admin", "Lumbung Desa Sentra Tani"))
        
        conn.commit()
        logger.info("Default data inserted successfully")

# Global database instance
db_instance = None

def get_database():
    """Get database instance"""
    global db_instance
    if db_instance is None:
        db_instance = SQLiteDatabase()
    return db_instance

# Helper functions for data conversion
def dict_factory(cursor, row):
    """Convert SQLite row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def json_loads_safe(json_str):
    """Safely load JSON string"""
    if json_str and json_str.strip():
        try:
            return json.loads(json_str)
        except:
            return {}
    return {}

def json_dumps_safe(obj):
    """Safely dump object to JSON string"""
    if obj:
        try:
            return json.dumps(obj)
        except:
            return "{}"
    return "{}"

# Authentication functions
def hash_password(password):
    """Hash a password for storing"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')
    provided_password = provided_password.encode('utf-8') if isinstance(provided_password, str) else provided_password
    return bcrypt.checkpw(provided_password, stored_password)

# User management functions
def create_user(username, password, full_name, role, department=None):
    """Create a new user"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False, "Username sudah digunakan"
        
        hashed_password = hash_password(password)
        user_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO users (id, username, password, full_name, role, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, hashed_password, full_name, role, department))
        
        conn.commit()
        logger.info(f"User {username} created successfully")
        return True, "Pengguna baru berhasil didaftarkan"
        
    except Exception as e:
        logger.error(f"Error creating user {username}: {e}")
        return False, f"Error: {str(e)}"

def get_user_by_username(username):
    """Get user by username"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user:
            return dict(user)
        return None
        
    except Exception as e:
        logger.error(f"Error getting user {username}: {e}")
        return None

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            return dict(user)
        return None
        
    except Exception as e:
        logger.error(f"Error getting user by ID {user_id}: {e}")
        return None

def update_user(user_id, update_data):
    """Update user data"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Hash password if provided
        if 'password' in update_data:
            update_data['password'] = hash_password(update_data['password'])
        
        # Add updated timestamp
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Build update query
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values()) + [user_id]
        
        cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        
        if cursor.rowcount > 0:
            conn.commit()
            logger.info(f"User {user_id} updated successfully")
            return True
        else:
            logger.warning(f"No changes made to user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False

def get_all_users(limit=100, skip=0, include_inactive=False):
    """Get all users with pagination"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        filter_query = ""
        params = []
        
        if not include_inactive:
            filter_query = "WHERE is_active = 1"
        
        cursor.execute(f"SELECT * FROM users {filter_query} LIMIT ? OFFSET ?", params + [limit, skip])
        users = cursor.fetchall()
        
        return [dict(user) for user in users]
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

# Dashboard functions
def get_stock_status():
    """Get overall stock status"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT current_stock, min_stock FROM items")
        items = cursor.fetchall()
        
        total_items = len(items)
        healthy_stock = 0
        low_stock = 0
        out_of_stock = 0
        
        for item in items:
            current_stock = item['current_stock'] or 0
            min_stock = item['min_stock'] or 0
            
            if current_stock == 0:
                out_of_stock += 1
            elif current_stock <= min_stock:
                low_stock += 1
            else:
                healthy_stock += 1
        
        return {
            'total_items': total_items,
            'healthy_stock': healthy_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock
        }
    except Exception as e:
        logger.error(f"Error getting stock status: {e}")
        return {'total_items': 0, 'healthy_stock': 0, 'low_stock': 0, 'out_of_stock': 0}

def get_items(limit=100, skip=0, warehouse_id=None):
    """Get all items with optional filtering"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        if warehouse_id:
            cursor.execute('''
                SELECT * FROM items 
                WHERE warehouse_id = ?
                ORDER BY name ASC
                LIMIT ? OFFSET ?
            ''', (warehouse_id, limit, skip))
        else:
            cursor.execute('''
                SELECT * FROM items 
                ORDER BY name ASC
                LIMIT ? OFFSET ?
            ''', (limit, skip))
        
        items = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(item) for item in items])
        return df
        
    except Exception as e:
        logger.error(f"Error getting items: {e}")
        return pd.DataFrame()

def get_items_low_stock(limit=10):
    """Get items with low stock"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM items 
            WHERE current_stock <= min_stock OR current_stock = 0
            ORDER BY current_stock ASC
            LIMIT ?
        ''', (limit,))
        
        items = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(item) for item in items])
        return df
        
    except Exception as e:
        logger.error(f"Error getting low stock items: {e}")
        return pd.DataFrame()

def get_recent_transactions(limit=10):
    """Get recent inventory transactions"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                it.*,
                i.name as item_name,
                w1.name as from_warehouse_name,
                w2.name as to_warehouse_name
            FROM inventory_transactions it
            LEFT JOIN items i ON it.item_id = i.id
            LEFT JOIN warehouses w1 ON it.from_warehouse_id = w1.id
            LEFT JOIN warehouses w2 ON it.to_warehouse_id = w2.id
            ORDER BY it.transaction_date DESC
            LIMIT ?
        ''', (limit,))
        
        transactions = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(t) for t in transactions])
        return df
        
    except Exception as e:
        logger.error(f"Error getting recent transactions: {e}")
        return pd.DataFrame()

def get_warehouse_consumption(days=30):
    """Get warehouse consumption for the last N days"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT 
                w.name as warehouse,
                SUM(it.quantity) as total_distribution
            FROM inventory_transactions it
            LEFT JOIN warehouses w ON it.from_warehouse_id = w.id
            WHERE it.transaction_date >= ? 
            AND it.transaction_type IN ('distribution', 'transfer_out')
            GROUP BY w.id, w.name
            ORDER BY total_distribution DESC
        ''', (start_date,))
        
        consumption = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(c) for c in consumption])
        return df
        
    except Exception as e:
        logger.error(f"Error getting warehouse consumption: {e}")
        return pd.DataFrame()

def get_top_consumed_items(limit=5, days=30):
    """Get top consumed items in the last N days"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT 
                i.name as item_name,
                SUM(it.quantity) as total_consumption
            FROM inventory_transactions it
            LEFT JOIN items i ON it.item_id = i.id
            WHERE it.transaction_date >= ? 
            AND it.transaction_type IN ('consumption', 'transfer_out')
            GROUP BY i.id, i.name
            ORDER BY total_consumption DESC
            LIMIT ?
        ''', (start_date, limit))
        
        items = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(item) for item in items])
        return df
        
    except Exception as e:
        logger.error(f"Error getting top consumed items: {e}")
        return pd.DataFrame()

# Warehouse functions
def get_warehouses(limit=50):
    """Get warehouses"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM warehouses ORDER BY name LIMIT ?", (limit,))
        warehouses = cursor.fetchall()
        
        return [dict(w) for w in warehouses]
        
    except Exception as e:
        logger.error(f"Error getting warehouses: {e}")
        return []

# Agricultural functions
def get_farmers(location=None, limit=50):
    """Get farmers list with optional location filter"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        if location:
            cursor.execute("SELECT * FROM farmers WHERE location LIKE ? ORDER BY name LIMIT ?", 
                         (f"%{location}%", limit))
        else:
            cursor.execute("SELECT * FROM farmers ORDER BY name LIMIT ?", (limit,))
        
        farmers = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(f) for f in farmers])
        return df
        
    except Exception as e:
        logger.error(f"Error getting farmers: {e}")
        return pd.DataFrame()

def get_merchants(merchant_type=None, location=None, limit=50):
    """Get merchants list with optional filters"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM merchants"
        params = []
        
        conditions = []
        if merchant_type:
            conditions.append("type LIKE ?")
            params.append(f"%{merchant_type}%")
        if location:
            conditions.append("location LIKE ?")
            params.append(f"%{location}%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY name LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        merchants = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(m) for m in merchants])
        return df
        
    except Exception as e:
        logger.error(f"Error getting merchants: {e}")
        return pd.DataFrame()

def get_harvests_by_season(season=None, warehouse_id=None, crop=None, limit=100):
    """Get harvests by season, warehouse, and crop type"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM harvests"
        params = []
        
        conditions = []
        if season:
            conditions.append("season = ?")
            params.append(season)
        if warehouse_id:
            conditions.append("warehouse_id = ?")
            params.append(warehouse_id)
        if crop:
            conditions.append("crop_type LIKE ?")
            params.append(f"%{crop}%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY harvest_date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        harvests = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(h) for h in harvests])
        return df
        
    except Exception as e:
        logger.error(f"Error getting harvests: {e}")
        return pd.DataFrame()

# Initialize database with default data
def init_db():
    """Initialize database with default data"""
    try:
        db = get_database()
        db.insert_default_data()
        logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

# Close database connection
def close_connection():
    """Close database connection"""
    if db_instance.conn:
        db_instance.conn.close()
        db_instance.conn = None
        logger.info("Database connection closed")

# Create item
def create_item(name, category, current_stock, min_stock, max_stock, unit, price_per_unit, warehouse_id, expiry_date=None, harvest_season=None):
    """Create a new item"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO items (id, name, category, current_stock, min_stock, max_stock, unit, price_per_unit, warehouse_id, expiry_date, harvest_season)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), name, category, current_stock, min_stock, max_stock, unit, price_per_unit, warehouse_id, expiry_date, harvest_season))
        
        conn.commit()
        logger.info(f"Item {name} created successfully")
        return True, f"Item {name} created successfully"
        
    except Exception as e:
        logger.error(f"Error creating item {name}: {e}")
        return False, f"Error: {str(e)}"

def update_item(item_id, update_data):
    """Update item data"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values()) + [item_id]
        
        cursor.execute(f'''
            UPDATE items 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', values)
        
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Item {item_id} updated successfully")
            return True
        else:
            logger.warning(f"No changes made to item {item_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {e}")
        return False

def delete_item(item_id):
    """Delete item"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Item {item_id} deleted successfully")
            return True
        else:
            logger.warning(f"Item {item_id} not found")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {e}")
        return False

def get_farmer_by_id(farmer_id):
    """Get farmer by ID"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,))
        farmer = cursor.fetchone()
        
        return dict(farmer) if farmer else None
        
    except Exception as e:
        logger.error(f"Error getting farmer {farmer_id}: {e}")
        return None

def get_merchant_by_id(merchant_id):
    """Get merchant by ID"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM merchants WHERE id = ?", (merchant_id,))
        merchant = cursor.fetchone()
        
        return dict(merchant) if merchant else None
        
    except Exception as e:
        logger.error(f"Error getting merchant {merchant_id}: {e}")
        return None

def create_harvest(warehouse_id, farmer_id, harvest_date, season, crop_type, quantity, unit, quality_grade=None, notes=None):
    """Create a new harvest record"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO harvests (id, warehouse_id, farmer_id, harvest_date, season, crop_type, quantity, unit, quality_grade, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), warehouse_id, farmer_id, harvest_date, season, crop_type, quantity, unit, quality_grade, notes))
        
        conn.commit()
        logger.info(f"Harvest record created successfully")
        return True, f"Harvest record created successfully"
        
    except Exception as e:
        logger.error(f"Error creating harvest record: {e}")
        return False, f"Error: {str(e)}"

def get_harvests(limit=100, skip=0):
    """Get harvest records"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT h.*, w.name as warehouse_name 
            FROM harvests h 
            LEFT JOIN warehouses w ON h.warehouse_id = w.id 
            ORDER BY h.harvest_date DESC
            LIMIT ? OFFSET ?
        ''', (limit, skip))
        
        harvests = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(harvest) for harvest in harvests])
        return df
        
    except Exception as e:
        logger.error(f"Error getting harvests: {e}")
        return pd.DataFrame()

def create_notification(user_id, message, notification_type="info"):
    """Create a notification"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (id, user_id, message, type)
            VALUES (?, ?, ?, ?)
        ''', (str(uuid.uuid4()), user_id, message, notification_type))
        
        conn.commit()
        logger.info(f"Notification created successfully")
        return True, f"Notification created successfully"
        
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        return False, f"Error: {str(e)}"

def get_notifications(user_id=None, limit=50, unread_only=False):
    """Get notifications"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        if user_id and unread_only:
            cursor.execute('''
                SELECT * FROM notifications 
                WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        elif user_id:
            cursor.execute('''
                SELECT * FROM notifications 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM notifications 
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        notifications = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(notification) for notification in notifications])
        return df
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return pd.DataFrame()

# Farmer functions
def create_farmer(name, location, phone=None, email=None, land_area=1.0, main_crop="Beras", 
                  farming_experience=0, join_date=None, farming_type="Konvensional", 
                  irrigation_source="Hujan", soil_type="Latosol", harvest_frequency="2 kali", notes=None):
    """Create a new farmer"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO farmers (id, name, location, phone, email, land_area, main_crop, 
                               farming_experience, join_date, farming_type, irrigation_source, 
                               soil_type, harvest_frequency, notes, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (str(uuid.uuid4()), name, location, phone, email, land_area, main_crop, 
              farming_experience, join_date or datetime.now().isoformat(), farming_type, 
              irrigation_source, soil_type, harvest_frequency, notes))
        
        conn.commit()
        logger.info(f"Farmer {name} created successfully")
        return True, f"Petani {name} berhasil ditambahkan"
        
    except Exception as e:
        logger.error(f"Error creating farmer {name}: {e}")
        return False, f"Error: {str(e)}"

def update_farmer(farmer_id, update_data):
    """Update farmer data"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values()) + [farmer_id]
        
        cursor.execute(f'''
            UPDATE farmers 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', values)
        
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Farmer {farmer_id} updated successfully")
            return True
        else:
            logger.warning(f"No changes made to farmer {farmer_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating farmer {farmer_id}: {e}")
        return False

def delete_farmer(farmer_id):
    """Delete farmer (soft delete by setting is_active to False)"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE farmers SET is_active = 0 WHERE id = ?", (farmer_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Farmer {farmer_id} deleted successfully")
            return True
        else:
            logger.warning(f"Farmer {farmer_id} not found")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting farmer {farmer_id}: {e}")
        return False

# Merchant functions
def create_merchant(name, location, merchant_type="Pengecer", phone=None, email=None, 
                   business_license=None, join_date=None, notes=None):
    """Create a new merchant"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO merchants (id, name, location, type, phone, email, 
                                  business_license, join_date, notes, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (str(uuid.uuid4()), name, location, merchant_type, phone, email, 
              business_license, join_date or datetime.now().isoformat(), notes))
        
        conn.commit()
        logger.info(f"Merchant {name} created successfully")
        return True, f"Pedagang {name} berhasil ditambahkan"
        
    except Exception as e:
        logger.error(f"Error creating merchant {name}: {e}")
        return False, f"Error: {str(e)}"

def update_merchant(merchant_id, update_data):
    """Update merchant data"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values()) + [merchant_id]
        
        cursor.execute(f'''
            UPDATE merchants 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', values)
        
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Merchant {merchant_id} updated successfully")
            return True
        else:
            logger.warning(f"No changes made to merchant {merchant_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating merchant {merchant_id}: {e}")
        return False

def delete_merchant(merchant_id):
    """Delete merchant (soft delete by setting is_active to False)"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE merchants SET is_active = 0 WHERE id = ?", (merchant_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Merchant {merchant_id} deleted successfully")
            return True
        else:
            logger.warning(f"Merchant {merchant_id} not found")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting merchant {merchant_id}: {e}")
        return False

# Distribution functions
def get_distributions(limit=50, status=None, warehouse_id=None, merchant_id=None):
    """Get distributions data from database"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT d.*, m.name as merchant_name, m.location as merchant_location,
                   w.name as warehouse_name, w.location as warehouse_location
            FROM distributions d
            LEFT JOIN merchants m ON d.merchant_id = m.id
            LEFT JOIN warehouses w ON d.warehouse_id = w.id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += " AND d.status = ?"
            params.append(status)
        
        if warehouse_id:
            query += " AND d.warehouse_id = ?"
            params.append(warehouse_id)
        
        if merchant_id:
            query += " AND d.merchant_id = ?"
            params.append(merchant_id)
        
        query += " ORDER BY d.delivery_date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        distributions = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(distribution) for distribution in distributions])
        return df
        
    except Exception as e:
        logger.error(f"Error getting distributions: {e}")
        return pd.DataFrame()

def create_distribution(merchant_id, warehouse_id, delivery_date, crop_type, quantity, unit, 
                       priority="Normal", delivery_method="Truck", estimated_distance=5.0, 
                       estimated_cost=50000, notes=None):
    """Create a new distribution"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        distribution_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO distributions (id, merchant_id, warehouse_id, delivery_date, crop_type, 
                                    quantity, unit, priority, delivery_method, estimated_distance, 
                                    estimated_cost, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        ''', (distribution_id, merchant_id, warehouse_id, delivery_date, crop_type, quantity, unit,
              priority, delivery_method, estimated_distance, estimated_cost, notes))
        
        conn.commit()
        logger.info(f"Distribution {distribution_id} created successfully")
        return True, f"Distribusi berhasil ditambahkan dengan ID: {distribution_id}"
        
    except Exception as e:
        logger.error(f"Error creating distribution: {e}")
        return False, f"Error: {str(e)}"

def update_distribution_status(distribution_id, new_status="Completed"):
    """Update distribution status"""
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE distributions 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (new_status, distribution_id))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Distribution {distribution_id} status updated to {new_status}")
            return True
        else:
            logger.warning(f"Distribution {distribution_id} not found")
            return False
            
    except Exception as e:
        logger.error(f"Error updating distribution status: {e}")
        return False

def close_connection():
    """Close database connection"""
    try:
        db = get_database()
        if db.conn:
            db.conn.close()
            db.conn = None
            logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")
