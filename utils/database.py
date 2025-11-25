import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MONGODB_SETTINGS, REALTIME_SETTINGS
import json
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBConnection:
    """MongoDB connection manager with connection pooling"""
    
    _client = None
    _database = None
    
    @classmethod
    def get_client(cls):
        """Get MongoDB client with connection pooling"""
        if cls._client is None:
            try:
                # Build connection string
                if MONGODB_SETTINGS['username'] and MONGODB_SETTINGS['password']:
                    connection_string = f"mongodb://{MONGODB_SETTINGS['username']}:{MONGODB_SETTINGS['password']}@{MONGODB_SETTINGS['host']}:{MONGODB_SETTINGS['port']}/{MONGODB_SETTINGS['auth_source']}"
                else:
                    connection_string = f"mongodb://{MONGODB_SETTINGS['host']}:{MONGODB_SETTINGS['port']}"
                
                # Create client with connection pooling
                cls._client = MongoClient(
                    connection_string,
                    maxPoolSize=MONGODB_SETTINGS['maxPoolSize'],
                    minPoolSize=MONGODB_SETTINGS['minPoolSize'],
                    maxIdleTimeMS=MONGODB_SETTINGS['maxIdleTimeMS'],
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    retryWrites=True,
                    retryReads=True
                )
                
                # Test connection
                cls._client.admin.command('ping')
                logger.info("MongoDB connection established successfully")
                
            except ConnectionFailure as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
        
        return cls._client
    
    @classmethod
    def get_database(cls):
        """Get database instance"""
        if cls._database is None:
            client = cls.get_client()
            cls._database = client[MONGODB_SETTINGS['database']]
            
            # Create indexes for better performance
            cls._create_indexes(cls._database)
            
        return cls._database
    
    @classmethod
    def _create_indexes(cls, db):
        """Create indexes for optimal performance"""
        try:
            # Users collection indexes
            db.users.create_index([("username", ASCENDING)], unique=True)
            db.users.create_index([("role", ASCENDING)])
            db.users.create_index([("department", ASCENDING)])
            
            # Items collection indexes (agricultural products)
            db.items.create_index([("name", ASCENDING)])
            db.items.create_index([("category", ASCENDING)])
            db.items.create_index([("current_stock", ASCENDING)])
            db.items.create_index([("min_stock", ASCENDING)])
            db.items.create_index([("warehouse_id", ASCENDING)])
            db.items.create_index([("harvest_season", ASCENDING)])
            
            # Warehouses collection indexes
            db.warehouses.create_index([("name", ASCENDING)], unique=True)
            db.warehouses.create_index([("location", ASCENDING)])
            db.warehouses.create_index([("coordinates", "2dsphere")])  # Geospatial index
            
            # Farmers collection indexes
            db.farmers.create_index([("name", ASCENDING)])
            db.farmers.create_index([("location", ASCENDING)])
            db.farmers.create_index([("coordinates", "2dsphere")])  # Geospatial index
            
            # Merchants collection indexes
            db.merchants.create_index([("name", ASCENDING)])
            db.merchants.create_index([("location", ASCENDING)])
            db.merchants.create_index([("type", ASCENDING)])
            db.merchants.create_index([("coordinates", "2dsphere")])  # Geospatial index
            
            # Harvests collection indexes
            db.harvests.create_index([("farmer_id", ASCENDING)])
            db.harvests.create_index([("warehouse_id", ASCENDING)])
            db.harvests.create_index([("harvest_date", DESCENDING)])
            db.harvests.create_index([("season", ASCENDING)])
            
            # Seeds collection indexes
            db.seeds.create_index([("name", ASCENDING)])
            db.seeds.create_index([("crop_type", ASCENDING)])
            db.seeds.create_index([("supplier", ASCENDING)])
            
            # Fertilizers collection indexes
            db.fertilizers.create_index([("name", ASCENDING)])
            db.fertilizers.create_index([("type", ASCENDING)])
            db.fertilizers.create_index([("supplier", ASCENDING)])
            
            # Distribution routes collection indexes
            db.distribution_routes.create_index([("from_warehouse_id", ASCENDING)])
            db.distribution_routes.create_index([("to_merchant_id", ASCENDING)])
            db.distribution_routes.create_index([("distance", ASCENDING)])
            db.distribution_routes.create_index([("efficiency_score", DESCENDING)])
            
            # Transactions collection indexes
            db.inventory_transactions.create_index([("item_id", ASCENDING)])
            db.inventory_transactions.create_index([("transaction_type", ASCENDING)])
            db.inventory_transactions.create_index([("transaction_date", DESCENDING)])
            db.inventory_transactions.create_index([("created_by", ASCENDING)])
            db.inventory_transactions.create_index([("warehouse_id", ASCENDING)])
            
            # Requests collection indexes
            db.item_requests.create_index([("status", ASCENDING)])
            db.item_requests.create_index([("request_date", DESCENDING)])
            db.item_requests.create_index([("warehouse_id", ASCENDING)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    @classmethod
    def close_connection(cls):
        """Close MongoDB connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("MongoDB connection closed")

# Helper function to convert ObjectId to string
def object_id_to_str(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: object_id_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [object_id_to_str(item) for item in obj]
    return obj

# Database initialization functions
def init_db():
    """Initialize MongoDB database with collections and default data"""
    try:
        db = MongoDBConnection.get_database()
        
        # Create collections if they don't exist
        collections = ['users', 'items', 'warehouses', 'farmers', 'merchants', 'harvests', 'seeds', 'fertilizers', 'distribution_routes', 'inventory_transactions', 'item_requests', 'notifications']
        existing_collections = db.list_collection_names()
        
        for collection in collections:
            if collection not in existing_collections:
                db.create_collection(collection)
                logger.info(f"Created collection: {collection}")
        
        # Insert default warehouses (lumbung desa)
        default_warehouses = [
            {"name": "Lumbung Desa Sentra Tani", "description": "Lumbung utama untuk menyimpan hasil pertanian desa", "location": "Pusat Desa", "capacity": 50000},
            {"name": "Lumbung Desa Tambakrejo", "description": "Lumbung untuk wilayah Tambakrejo", "location": "Tambakrejo", "capacity": 30000},
            {"name": "Lumbung Desa Ngadirejo", "description": "Lumbung untuk wilayah Ngadirejo", "location": "Ngadirejo", "capacity": 25000},
            {"name": "Lumbung Desa Tlogosari", "description": "Lumbung untuk wilayah Tlogosari", "location": "Tlogosari", "capacity": 35000},
            {"name": "Lumbung Desa Bandungrejo", "description": "Lumbung untuk wilayah Bandungrejo", "location": "Bandungrejo", "capacity": 20000},
            {"name": "Lumbung Desa Purworejo", "description": "Lumbung untuk wilayah Purworejo", "location": "Purworejo", "capacity": 15000},
            {"name": "Lumbung Desa Sumberagung", "description": "Lumbung untuk wilayah Sumberagung", "location": "Sumberagung", "capacity": 40000},
            {"name": "Lumbung Desa Karanganyar", "description": "Lumbung untuk wilayah Karanganyar", "location": "Karanganyar", "capacity": 18000}
        ]
        
        for warehouse in default_warehouses:
            db.warehouses.update_one(
                {"name": warehouse["name"]},
                {"$set": warehouse},
                upsert=True
            )
        
        # Insert admin user (password: admin123)
        from utils.auth import hash_password
        admin_user = {
            "username": "admin",
            "password": hash_password("admin123"),
            "full_name": "Administrator Pertanian",
            "role": "admin",
            "department": "Lumbung Desa Sentra Tani",
            "created_at": datetime.utcnow(),
            "is_active": True,
            "last_login": None
        }
        
        db.users.update_one(
            {"username": "admin"},
            {"$set": admin_user},
            upsert=True
        )
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Real-time functions
def get_realtime_notifications(user_id: str, limit: int = 10):
    """Get real-time notifications for user"""
    try:
        db = MongoDBConnection.get_database()
        notifications = db.notifications.find(
            {"user_id": user_id, "is_read": False},
            sort=[("created_at", DESCENDING)]
        ).limit(limit)
        
        return list(notifications)
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return []

def create_notification(user_id: str, message: str, notification_type: str = "info"):
    """Create a notification for user"""
    try:
        db = MongoDBConnection.get_database()
        notification = {
            "user_id": user_id,
            "message": message,
            "type": notification_type,
            "is_read": False,
            "created_at": datetime.utcnow()
        }
        
        result = db.notifications.insert_one(notification)
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        return None

# Dashboard functions
def get_stock_status():
    """Get overall stock status"""
    try:
        db = MongoDBConnection.get_database()
        
        # Get all items
        items = list(db.items.find({}))
        
        total_items = len(items)
        healthy_stock = len([item for item in items if item.get('current_stock', 0) > item.get('min_stock', 0)])
        low_stock = len([item for item in items if 0 < item.get('current_stock', 0) <= item.get('min_stock', 0)])
        out_of_stock = len([item for item in items if item.get('current_stock', 0) == 0])
        
        return {
            'total_items': total_items,
            'healthy_stock': healthy_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock
        }
    except Exception as e:
        logger.error(f"Error getting stock status: {e}")
        return {'total_items': 0, 'healthy_stock': 0, 'low_stock': 0, 'out_of_stock': 0}

def get_items_low_stock(limit: int = 10):
    """Get items with low stock"""
    try:
        db = MongoDBConnection.get_database()
        
        low_stock_items = list(db.items.find({
            "$expr": {"$lte": ["$current_stock", "$min_stock"]}
        }).limit(limit))
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(low_stock_items)
        if not df.empty:
            df['_id'] = df['_id'].astype(str)
        
        return df
    except Exception as e:
        logger.error(f"Error getting warehouse consumption: {e}")
        return pd.DataFrame()

def get_warehouse_products(warehouse_id=None):
    """Get warehouse products with stock information"""
    try:
        db = MongoDBConnection.get_database()
        
        query = {}
        if warehouse_id:
            query["warehouse_id"] = ObjectId(warehouse_id)
        
        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "warehouses",
                    "localField": "warehouse_id",
                    "foreignField": "_id",
                    "as": "warehouse"
                }
            },
            {"$unwind": "$warehouse"},
            {
                "$project": {
                    "name": 1,
                    "category": 1,
                    "current_stock": 1,
                    "min_stock": 1,
                    "max_stock": 1,
                    "unit": 1,
                    "price_per_unit": 1,
                    "expiry_date": 1,
                    "warehouse_name": "$warehouse.name",
                    "status": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$current_stock", 0]}, "then": "habis"},
                                {"case": {"$lte": ["$current_stock", "$min_stock"]}, "then": "rendah"},
                                {"case": {"$gte": ["$current_stock", "$max_stock"]}, "then": "berlebih"}
                            ],
                            "default": "normal"
                        }
                    }
                }
            },
            {"$sort": {"warehouse_name": 1, "name": 1}}
        ]
        
        products = list(db.warehouse_products.aggregate(pipeline))
        return products
    except Exception as e:
        logger.error(f"Error getting warehouse products: {e}")
        return []

def add_warehouse_product(product_data):
    """Add new warehouse product"""
    try:
        db = MongoDBConnection.get_database()
        
        product_data['warehouse_id'] = ObjectId(product_data['warehouse_id'])
        product_data['created_date'] = datetime.utcnow()
        product_data['updated_date'] = datetime.utcnow()
        
        result = db.warehouse_products.insert_one(product_data)
        return result.inserted_id is not None
    except Exception as e:
        logger.error(f"Error adding warehouse product: {e}")
        return False

def update_warehouse_product(product_id, update_data):
    """Update warehouse product"""
    try:
        db = MongoDBConnection.get_database()
        
        update_data['updated_date'] = datetime.utcnow()
        
        result = db.warehouse_products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating warehouse product: {e}")
        return False

def get_product_categories():
    """Get unique product categories"""
    try:
        db = MongoDBConnection.get_database()
        
        categories = db.warehouse_products.distinct("category")
        return sorted(categories)
    except Exception as e:
        logger.error(f"Error getting product categories: {e}")
        return []

def get_recent_transactions(limit: int = 10):
    """Get recent inventory transactions"""
    try:
        db = MongoDBConnection.get_database()
        
        pipeline = [
            {
                "$lookup": {
                    "from": "items",
                    "localField": "item_id",
                    "foreignField": "_id",
                    "as": "item"
                }
            },
            {"$unwind": "$item"},
            {
                "$lookup": {
                    "from": "departments",
                    "localField": "from_department_id",
                    "foreignField": "_id",
                    "as": "from_department"
                }
            },
            {"$unwind": {"path": "$from_department", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "departments",
                    "localField": "to_department_id",
                    "foreignField": "_id",
                    "as": "to_department"
                }
            },
            {"$unwind": {"path": "$to_department", "preserveNullAndEmptyArrays": True}},
            {"$sort": {"transaction_date": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "item_name": "$item.name",
                    "quantity": 1,
                    "transaction_type": 1,
                    "from_department": "$from_department.name",
                    "to_department": "$to_department.name",
                    "transaction_date": 1,
                    "notes": 1
                }
            }
        ]
        
        transactions = list(db.inventory_transactions.aggregate(pipeline))
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        if not df.empty:
            df['_id'] = df['_id'].astype(str) if '_id' in df.columns else None
        
        return df
    except Exception as e:
        logger.error(f"Error getting recent transactions: {e}")
        return pd.DataFrame()

def get_warehouse_consumption(days: int = 30):
    """Get warehouse consumption for the last N days"""
    try:
        db = MongoDBConnection.get_database()
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "transaction_date": {"$gte": start_date},
                    "transaction_type": {"$in": ["distribution", "transfer_out"]}
                }
            },
            {
                "$lookup": {
                    "from": "warehouses",
                    "localField": "from_warehouse_id",
                    "foreignField": "_id",
                    "as": "warehouse"
                }
            },
            {"$unwind": "$warehouse"},
            {
                "$group": {
                    "_id": "$warehouse.name",
                    "total_distribution": {"$sum": "$quantity"}
                }
            },
            {
                "$project": {
                    "warehouse": "$_id",
                    "total_distribution": 1,
                    "_id": 0
                }
            },
            {"$sort": {"total_distribution": -1}}
        ]
        
        consumption = list(db.inventory_transactions.aggregate(pipeline))
        
        # Convert to DataFrame
        df = pd.DataFrame(consumption)
        return df
    except Exception as e:
        logger.error(f"Error getting warehouse consumption: {e}")
        return pd.DataFrame()

def get_top_consumed_items(limit: int = 5, days: int = 30):
    """Get top consumed items in the last N days"""
    try:
        db = MongoDBConnection.get_database()
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "transaction_date": {"$gte": start_date},
                    "transaction_type": {"$in": ["consumption", "transfer_out"]}
                }
            },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "item_id",
                    "foreignField": "_id",
                    "as": "item"
                }
            },
            {"$unwind": "$item"},
            {
                "$group": {
                    "_id": "$item.name",
                    "total_consumption": {"$sum": "$quantity"}
                }
            },
            {
                "$project": {
                    "item_name": "$_id",
                    "total_consumption": 1,
                    "_id": 0
                }
            },
            {"$sort": {"total_consumption": -1}},
            {"$limit": limit}
        ]
        
        top_items = list(db.inventory_transactions.aggregate(pipeline))
        
        # Convert to DataFrame
        df = pd.DataFrame(top_items)
        return df
    except Exception as e:
        logger.error(f"Error getting top consumed items: {e}")
        return pd.DataFrame()

# Real-time change stream monitoring
class ChangeStreamMonitor:
    """Monitor MongoDB change streams for real-time updates"""
    
    def __init__(self):
        self.db = MongoDBConnection.get_database()
        self.is_running = False
        self.change_streams = {}
    
    def start_monitoring(self, collection_name, callback):
        """Start monitoring changes in a collection"""
        if not REALTIME_SETTINGS['CHANGE_STREAM_ENABLED']:
            return
        
        try:
            collection = self.db[collection_name]
            change_stream = collection.watch()
            
            self.change_streams[collection_name] = change_stream
            self.is_running = True
            
            # Process changes in a separate thread
            import threading
            monitor_thread = threading.Thread(
                target=self._process_changes,
                args=(change_stream, callback),
                daemon=True
            )
            monitor_thread.start()
            
            logger.info(f"Started monitoring {collection_name} changes")
            
        except Exception as e:
            logger.error(f"Error starting change stream for {collection_name}: {e}")
    
    def _process_changes(self, change_stream, callback):
        """Process changes from the change stream"""
        try:
            for change in change_stream:
                if not self.is_running:
                    break
                
                # Call the callback function with the change
                callback(change)
                
        except Exception as e:
            logger.error(f"Error processing change stream: {e}")
    
    def stop_monitoring(self, collection_name=None):
        """Stop monitoring changes"""
        self.is_running = False
        
        if collection_name and collection_name in self.change_streams:
            self.change_streams[collection_name].close()
            del self.change_streams[collection_name]
        else:
            # Close all change streams
            for stream in self.change_streams.values():
                stream.close()
            self.change_streams.clear()
        
        logger.info("Stopped change stream monitoring")

# Agricultural-specific functions
def get_farmers(location=None, limit=50):
    """Get farmers list with optional location filter"""
    try:
        db = MongoDBConnection.get_database()
        
        query = {}
        if location:
            query["location"] = location
            
        farmers = list(db.farmers.find(query).limit(limit))
        
        # Convert to DataFrame
        df = pd.DataFrame(farmers)
        if not df.empty:
            df['_id'] = df['_id'].astype(str)
        
        return df
    except Exception as e:
        logger.error(f"Error getting farmers: {e}")
        return pd.DataFrame()

def get_merchants(merchant_type=None, location=None, limit=50):
    """Get merchants list with optional filters"""
    try:
        db = MongoDBConnection.get_database()
        
        query = {}
        if merchant_type:
            query["type"] = merchant_type
        if location:
            query["location"] = location
            
        merchants = list(db.merchants.find(query).limit(limit))
        
        # Convert to DataFrame
        df = pd.DataFrame(merchants)
        if not df.empty:
            df['_id'] = df['_id'].astype(str)
        
        return df
    except Exception as e:
        logger.error(f"Error getting merchants: {e}")
        return pd.DataFrame()

def get_harvests_by_season(season=None, warehouse_id=None, crop=None, limit=100):
    """Get harvests by season, warehouse, and crop type"""
    try:
        db = MongoDBConnection.get_database()
        
        query = {}
        if season:
            query["season"] = season
        if warehouse_id:
            query["warehouse_id"] = ObjectId(warehouse_id)
        if crop:
            query["crop_type"] = {"$regex": crop, "$options": "i"}  # Case insensitive search
            
        harvests = list(db.harvests.find(query).limit(limit))
        
        # Convert to DataFrame
        df = pd.DataFrame(harvests)
        if not df.empty:
            df['_id'] = df['_id'].astype(str)
            if 'farmer_id' in df.columns:
                df['farmer_id'] = df['farmer_id'].astype(str)
            if 'warehouse_id' in df.columns:
                df['warehouse_id'] = df['warehouse_id'].astype(str)
        
        return df
    except Exception as e:
        logger.error(f"Error getting harvests: {e}")
        return pd.DataFrame()

def get_optimal_distribution_routes(warehouse_id=None, limit=10):
    """Get optimal distribution routes based on efficiency score"""
    try:
        db = MongoDBConnection.get_database()
        
        query = {}
        if warehouse_id:
            query["from_warehouse_id"] = ObjectId(warehouse_id)
            
        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "warehouses",
                    "localField": "from_warehouse_id",
                    "foreignField": "_id",
                    "as": "from_warehouse"
                }
            },
            {"$unwind": "$from_warehouse"},
            {
                "$lookup": {
                    "from": "merchants",
                    "localField": "to_merchant_id",
                    "foreignField": "_id",
                    "as": "to_merchant"
                }
            },
            {"$unwind": "$to_merchant"},
            {"$sort": {"efficiency_score": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "route_name": 1,
                    "from_warehouse_name": "$from_warehouse.name",
                    "to_merchant_name": "$to_merchant.name",
                    "distance": 1,
                    "travel_time": 1,
                    "efficiency_score": 1,
                    "fuel_cost": 1,
                    "road_condition": 1
                }
            }
        ]
        
        routes = list(db.distribution_routes.aggregate(pipeline))
        
        # Convert to DataFrame
        df = pd.DataFrame(routes)
        if not df.empty:
            df['_id'] = df['_id'].astype(str)
        
        return df
    except Exception as e:
        logger.error(f"Error getting distribution routes: {e}")
        return pd.DataFrame()

def get_merchants(merchant_type=None, location=None, limit=50):
    """Get merchants with optional filtering"""
    try:
        db = MongoDBConnection.get_database()
        
        # Build query
        query = {}
        if merchant_type:
            query["type"] = merchant_type
        if location:
            query["location"] = {"$regex": location, "$options": "i"}
        
        merchants = list(db.merchants.find(query).limit(limit))
        
        # Convert to DataFrame
        df = pd.DataFrame(merchants)
        if not df.empty:
            df['_id'] = df['_id'].astype(str)
        
        return df
    except Exception as e:
        logger.error(f"Error getting merchants: {e}")
        return pd.DataFrame()

def get_warehouses(limit=50):
    """Get warehouses"""
    try:
        db = MongoDBConnection.get_database()
        
        warehouses = list(db.warehouses.find({}).limit(limit))
        
        # Convert to DataFrame
        df = pd.DataFrame(warehouses)
        if not df.empty:
            df['_id'] = df['_id'].astype(str)
        
        return df
    except Exception as e:
        logger.error(f"Error getting warehouses: {e}")
        return pd.DataFrame()

def get_seasonal_forecasting_data(crop_type=None, seasons=4):
    """Get data for seasonal forecasting analysis"""
    try:
        db = MongoDBConnection.get_database()
        
        query = {}
        if crop_type:
            query["crop_type"] = crop_type
            
        # Get harvest data from last few seasons
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": {
                        "season": "$season",
                        "year": {"$year": "$harvest_date"}
                    },
                    "total_yield": {"$sum": "$total_yield"},
                    "avg_quality": {"$avg": "$quality_score"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.year": -1, "_id.season": -1}},
            {"$limit": seasons},
            {
                "$project": {
                    "season": "$_id.season",
                    "year": "$_id.year",
                    "total_yield": 1,
                    "avg_quality": 1,
                    "count": 1,
                    "_id": 0
                }
            }
        ]
        
        data = list(db.harvests.aggregate(pipeline))
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        logger.error(f"Error getting seasonal forecasting data: {e}")
        return pd.DataFrame()