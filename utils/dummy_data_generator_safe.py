import sqlite3
import random
import uuid
from datetime import datetime, timedelta
import json
import bcrypt

class SafeDummyDataGenerator:
    """Generate dummy data for agricultural inventory system - Safe mode for regular users"""
    
    def __init__(self, db_path="inventory_new.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Smaller dataset for safe simulation
        self.farmer_names = [
            "Budi Santoso", "Ahmad Wijaya", "Siti Nurjanah", "Joko Prasetyo",
            "Dewi Lestari", "Rudi Hartono", "Endah Sulistiyowati", "Agus Setiawan"
        ]
        
        self.merchant_names = [
            "Toko Berkah Jaya", "Pasar Sentra Tani", "UD Makmur Sejahtera", "CV Harapan Baru",
            "Toko Sumber Rezeki", "Pasar Tradisional Ngadirejo", "UD Tani Makmur"
        ]
        
        self.crop_types = [
            "Padi", "Jagung", "Kedelai", "Kacang Tanah", "Ubi Jalar", "Singkong",
            "Tomat", "Cabai", "Terung", "Bayam"
        ]
        
        self.item_names = [
            "Bibit Padi IR64", "Bibit Jagung Hibrida", "Pupuk Urea", "Pupuk KCL",
            "Pestisida Organik", "Traktor Mini", "Mesin Perontok Padi", "Karung Plastik",
            "Bibit Kedelai", "Pupuk ZA", "Pupuk Organik Cair", "Sprayer Manual"
        ]
        
        self.seasons = ["Musim Hujan", "Musim Kemarau"]
        self.quality_grades = ["A", "B", "C"]
        self.units = ["kg", "ton", "karung", "sak", "liter", "pcs"]
        
        # Locations for coordinates
        self.locations = {
            "Pusat Desa": (-7.250445, 112.768045),
            "Tambakrejo": (-7.245123, 112.775234),
            "Ngadirejo": (-7.255678, 112.760123),
            "Tlogosari": (-7.240987, 112.778456)
        }
    
    def generate_coordinates(self, base_location):
        """Generate random coordinates near base location"""
        lat, lng = base_location
        # Add small random offset (within ~1km radius)
        lat_offset = random.uniform(-0.009, 0.009)
        lng_offset = random.uniform(-0.009, 0.009)
        return json.dumps({"lat": lat + lat_offset, "lng": lng + lng_offset})
    
    def check_existing_data(self):
        """Check if data already exists to avoid duplicates"""
        tables = ['farmers', 'merchants', 'items', 'harvests', 'inventory_transactions']
        existing_counts = {}
        
        for table in tables:
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                existing_counts[table] = count
            except:
                existing_counts[table] = 0
        
        return existing_counts
    
    def generate_safe_farmers(self, count=20):
        """Generate small amount of farmer data for safe simulation"""
        farmers = []
        for i in range(count):
            location = random.choice(list(self.locations.keys()))
            farmers.append((
                str(uuid.uuid4()),
                random.choice(self.farmer_names) + f" {i+1}",
                location,
                self.generate_coordinates(self.locations[location]),
                round(random.uniform(0.5, 3.0), 2),  # land_area in hectares
                f"08{random.randint(100000000, 999999999)}",
                datetime.now() - timedelta(days=random.randint(30, 180))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO farmers (id, name, location, coordinates, land_area, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', farmers)
    
    def generate_safe_merchants(self, count=10):
        """Generate small amount of merchant data for safe simulation"""
        merchants = []
        merchant_types = ["Grosir", "Eceran", "Kolektor", "Pengecer"]
        
        for i in range(count):
            location = random.choice(list(self.locations.keys()))
            merchants.append((
                str(uuid.uuid4()),
                random.choice(self.merchant_names) + f" {i+1}",
                random.choice(merchant_types),
                location,
                self.generate_coordinates(self.locations[location]),
                f"08{random.randint(100000000, 999999999)}",
                datetime.now() - timedelta(days=random.randint(15, 120))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO merchants (id, name, type, location, coordinates, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', merchants)
    
    def generate_safe_items(self, count=30):
        """Generate small amount of item data for safe simulation"""
        # Get existing warehouses
        self.cursor.execute("SELECT id FROM warehouses LIMIT 5")
        warehouse_ids = [row[0] for row in self.cursor.fetchall()]
        
        if not warehouse_ids:
            return
        
        items = []
        for i in range(count):
            items.append((
                str(uuid.uuid4()),
                random.choice(self.item_names),
                "Inventori",
                round(random.uniform(0, 500), 2),  # current_stock
                round(random.uniform(10, 50), 2),   # min_stock
                round(random.uniform(200, 1000), 2), # max_stock
                random.choice(self.units),
                round(random.uniform(1000, 25000), 2),  # price_per_unit
                (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),  # expiry_date
                random.choice(warehouse_ids),
                random.choice(self.seasons),
                datetime.now() - timedelta(days=random.randint(1, 100))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO items (id, name, category, current_stock, min_stock, max_stock, unit, price_per_unit, expiry_date, warehouse_id, harvest_season, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', items)
    
    def generate_safe_harvests(self, count=25):
        """Generate small amount of harvest data for safe simulation"""
        # Get existing farmers and warehouses
        self.cursor.execute("SELECT id FROM farmers LIMIT 10")
        farmer_ids = [row[0] for row in self.cursor.fetchall()]
        
        self.cursor.execute("SELECT id FROM warehouses LIMIT 5")
        warehouse_ids = [row[0] for row in self.cursor.fetchall()]
        
        if not farmer_ids or not warehouse_ids:
            return
        
        harvests = []
        # Generate data for 1.5 years to support seasonal forecasting
        start_date = datetime.now() - timedelta(days=540)
        
        for i in range(count):
            # Distribute dates across the period
            days_offset = random.randint(0, 540)
            harvest_date = start_date + timedelta(days=days_offset)
            
            harvests.append((
                str(uuid.uuid4()),
                random.choice(farmer_ids),
                random.choice(warehouse_ids),
                harvest_date.strftime('%Y-%m-%d'),
                random.choice(self.seasons),
                random.choice(self.crop_types),
                round(random.uniform(50, 500), 2),
                random.choice(["kg", "ton"]),
                random.choice(self.quality_grades),
                f"Panen simulasi #{i+1}",
                harvest_date
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO harvests (id, farmer_id, warehouse_id, harvest_date, season, crop_type, quantity, unit, quality_grade, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', harvests)
    
    def generate_safe_transactions(self, count=50):
        """Generate small amount of transaction data for safe simulation"""
        # Get existing items and warehouses
        self.cursor.execute("SELECT id FROM items LIMIT 20")
        item_ids = [row[0] for row in self.cursor.fetchall()]
        
        self.cursor.execute("SELECT id FROM warehouses LIMIT 5")
        warehouse_ids = [row[0] for row in self.cursor.fetchall()]
        
        if not item_ids or not warehouse_ids:
            return
        
        transactions = []
        # Increase 'out' transactions for consumption forecasting
        transaction_types = ['in', 'out', 'out', 'transfer', 'distribution']
        
        for i in range(count):
            transaction_type = random.choice(transaction_types)
            from_warehouse = random.choice(warehouse_ids) if transaction_type in ['out', 'transfer', 'distribution'] else None
            to_warehouse = random.choice(warehouse_ids) if transaction_type in ['in', 'transfer'] else None
            
            transactions.append((
                str(uuid.uuid4()),
                random.choice(item_ids),
                transaction_type,
                round(random.uniform(1, 100), 2),
                from_warehouse,
                to_warehouse,
                datetime.now() - timedelta(days=random.randint(1, 90)),
                "simulation_user",  # created_by
                f"Transaksi simulasi {transaction_type} #{i+1}"
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO inventory_transactions (id, item_id, transaction_type, quantity, from_warehouse_id, to_warehouse_id, transaction_date, created_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', transactions)
    
    def generate_safe_distributions(self, count=20):
        """Generate small amount of distribution data for safe simulation"""
        # Get existing merchants and warehouses
        self.cursor.execute("SELECT id FROM merchants LIMIT 10")
        merchant_ids = [row[0] for row in self.cursor.fetchall()]
        
        self.cursor.execute("SELECT id FROM warehouses LIMIT 5")
        warehouse_ids = [row[0] for row in self.cursor.fetchall()]
        
        if not merchant_ids or not warehouse_ids:
            return

        distributions = []
        statuses = ['Pending', 'In Progress', 'In Progress', 'Completed']
        priorities = ['Normal', 'Tinggi']
        delivery_methods = ['Truk', 'Pickup']
        
        for i in range(count):
            status = random.choice(statuses)
            delivery_date = datetime.now()
            
            if status == 'Completed':
                delivery_date = datetime.now() - timedelta(days=random.randint(1, 14))
            elif status == 'Pending':
                delivery_date = datetime.now() + timedelta(days=random.randint(1, 5))
            
            distributions.append((
                str(uuid.uuid4()),
                random.choice(merchant_ids),
                random.choice(warehouse_ids),
                delivery_date.strftime('%Y-%m-%d'),
                random.choice(self.crop_types),
                round(random.uniform(20, 500), 2),
                "kg",
                random.choice(priorities),
                random.choice(delivery_methods),
                round(random.uniform(2, 20), 2), # distance
                round(random.uniform(2, 20), 2), # estimated_distance
                round(random.uniform(20000, 200000), 2), # estimated_cost
                status,
                f"Distribusi simulasi #{i+1}",
                datetime.now()
            ))
            
        self.cursor.executemany('''
            INSERT OR IGNORE INTO distributions (
                id, merchant_id, warehouse_id, delivery_date, crop_type, quantity, unit, 
                priority, delivery_method, distance, estimated_distance, estimated_cost, 
                status, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', distributions)
    
    def generate_all_safe_data(self):
        """Generate safe simulation data for regular users"""
        print("🌾 Generating safe simulation data for agricultural inventory system...")
        
        try:
            # Check existing data first
            existing = self.check_existing_data()
            print(f"📊 Existing data: {existing}")
            
            # Generate data in order of dependencies
            print("Generating farmers...")
            self.generate_safe_farmers(20)
            
            print("Generating merchants...")
            self.generate_safe_merchants(10)
            
            print("Generating items...")
            self.generate_safe_items(30)
            
            print("Generating harvests...")
            self.generate_safe_harvests(40) # Increased count
            
            print("Generating transactions...")
            self.generate_safe_transactions(50)
            
            print("Generating distributions...")
            self.generate_safe_distributions(20)
            
            self.conn.commit()
            print("✅ Safe simulation data generation completed successfully!")
            
            # Print summary
            self.print_safe_summary()
            
        except Exception as e:
            print(f"❌ Error generating safe simulation data: {e}")
            self.conn.rollback()
        finally:
            self.conn.close()
    
    def print_safe_summary(self):
        """Print summary of generated safe data"""
        tables = ['users', 'warehouses', 'items', 'farmers', 'merchants', 'harvests', 
                 'inventory_transactions', 'seeds', 'fertilizers', 'distribution_routes', 'notifications', 'distributions']
        
        print("\n📊 Safe Simulation Data Summary:")
        print("-" * 40)
        total_records = 0
        
        for table in tables:
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                print(f"{table}: {count:,} records")
                total_records += count
            except:
                print(f"{table}: Error counting records")
        
        print("-" * 40)
        print(f"Total records: {total_records:,}")
        print("🎯 Safe simulation data ready for user exploration!")

if __name__ == "__main__":
    generator = SafeDummyDataGenerator()
    generator.generate_all_safe_data()
