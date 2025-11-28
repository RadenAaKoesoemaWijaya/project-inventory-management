import sqlite3
import random
import uuid
from datetime import datetime, timedelta
import json
import bcrypt

class DummyDataGenerator:
    """Generate dummy data for agricultural inventory system"""
    
    def __init__(self, db_path="inventory_new.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Sample data pools
        self.farmer_names = [
            "Budi Santoso", "Ahmad Wijaya", "Siti Nurjanah", "Joko Prasetyo",
            "Dewi Lestari", "Rudi Hartono", "Endah Sulistiyowati", "Agus Setiawan",
            "Ratna Sari", "Eko Purnomo", "Yuni Anggraini", "Hendra Gunawan",
            "Maya Sari", "Bambang Sutrisno", "Fitri Handayani", "Doni Kusuma",
            "Wati Rahayu", "Toni Susanto", "Lina Marlina", "Fajar Nugroho"
        ]
        
        self.merchant_names = [
            "Toko Berkah Jaya", "Pasar Sentra Tani", "UD Makmur Sejahtera", "CV Harapan Baru",
            "Toko Sumber Rezeki", "Pasar Tradisional Ngadirejo", "UD Tani Makmur", "Toko Grosir Pertanian",
            "CV Agronis Jaya", "Pasar Desa Tambakrejo", "Toko Subur Jaya", "UD Panen Sukses",
            "Toko Tani Sejahtera", "Pasar Modern Tlogosari", "CV Harvest Prime", "Toko Agrifarm"
        ]
        
        self.crop_types = [
            "Padi", "Jagung", "Kedelai", "Kacang Tanah", "Ubi Jalar", "Singkong",
            "Tomat", "Cabai", "Terung", "Bayam", "Kangkung", "Sawi", "Wortel", "Kentang"
        ]
        
        self.item_categories = [
            "Bibit Unggul", "Pupuk Organik", "Pestisida Alami", "Alat Pertanian",
            "Hasil Panen", "Bahan Pangan", "Benih Sayuran", "Pupuk NPK"
        ]
        
        self.item_names = [
            "Bibit Padi IR64", "Bibit Jagung Hibrida", "Pupuk Urea", "Pupuk KCL",
            "Pestisida Organik", "Traktor Mini", "Mesin Perontok Padi", "Karung Plastik",
            "Bibit Kedelai", "Pupuk ZA", "Pupuk Organik Cair", "Sprayer Manual",
            "Cangkul", "Sabit", "Garpu Tanah", "Timba Air", "Sekop", "Arit",
            "Bibit Cabai Rawit", "Bibit Tomat", "Pupuk NPK 16-16-16", "Mulsa Plastik",
            "Jaring Penutup", "Tali Rafia", "Terpal", "Kain Penyaring"
        ]
        
        self.seasons = ["Musim Hujan", "Musim Kemarau", "Musim Transisi"]
        self.quality_grades = ["A", "B", "C", "Premium", "Standar", "Ekonomi"]
        self.units = ["kg", "ton", "karung", "sak", "liter", "botol", "pcs", "buah"]
        
        # Locations for coordinates
        self.locations = {
            "Pusat Desa": (-7.250445, 112.768045),
            "Tambakrejo": (-7.245123, 112.775234),
            "Ngadirejo": (-7.255678, 112.760123),
            "Tlogosari": (-7.240987, 112.778456),
            "Bandungrejo": (-7.262345, 112.752345),
            "Purworejo": (-7.238765, 112.765432),
            "Sumberagung": (-7.254321, 112.743210),
            "Karanganyar": (-7.271234, 112.756789)
        }
    
    def generate_coordinates(self, base_location):
        """Generate random coordinates near base location"""
        lat, lng = base_location
        # Add small random offset (within ~1km radius)
        lat_offset = random.uniform(-0.009, 0.009)
        lng_offset = random.uniform(-0.009, 0.009)
        return json.dumps({"lat": lat + lat_offset, "lng": lng + lng_offset})
    
    def generate_warehouses(self):
        """Generate additional warehouse data"""
        warehouses = []
        for i in range(5):  # Add 5 more warehouses
            location = random.choice(list(self.locations.keys()))
            warehouses.append((
                str(uuid.uuid4()),
                f"Lumbung Desa {location} #{i+1}",
                f"Lumbung tambahan untuk wilayah {location}",
                location,
                random.randint(10000, 60000),
                self.generate_coordinates(self.locations[location])
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO warehouses (id, name, description, location, capacity, coordinates)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', warehouses)
    
    def generate_farmers(self, count=300):
        """Generate farmer data"""
        farmers = []
        for i in range(count):
            location = random.choice(list(self.locations.keys()))
            farmers.append((
                str(uuid.uuid4()),
                random.choice(self.farmer_names) + f" {i+1}",
                location,
                self.generate_coordinates(self.locations[location]),
                round(random.uniform(0.5, 5.0), 2),  # land_area in hectares
                f"08{random.randint(100000000, 999999999)}",
                datetime.now() - timedelta(days=random.randint(30, 365))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO farmers (id, name, location, coordinates, land_area, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', farmers)
    
    def generate_merchants(self, count=150):
        """Generate merchant data"""
        merchants = []
        merchant_types = ["Grosir", "Eceran", "Kolektor", "Pengecer", "Distributor"]
        
        for i in range(count):
            location = random.choice(list(self.locations.keys()))
            merchants.append((
                str(uuid.uuid4()),
                random.choice(self.merchant_names) + f" {i+1}",
                random.choice(merchant_types),
                location,
                self.generate_coordinates(self.locations[location]),
                f"08{random.randint(100000000, 999999999)}",
                datetime.now() - timedelta(days=random.randint(15, 300))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO merchants (id, name, type, location, coordinates, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', merchants)
    
    def generate_items(self, count=200):
        """Generate item data"""
        # Get existing warehouses
        self.cursor.execute("SELECT id FROM warehouses")
        warehouse_ids = [row[0] for row in self.cursor.fetchall()]
        
        items = []
        for i in range(count):
            items.append((
                str(uuid.uuid4()),
                random.choice(self.item_names),
                random.choice(self.item_categories),
                round(random.uniform(0, 1000), 2),  # current_stock
                round(random.uniform(10, 100), 2),   # min_stock
                round(random.uniform(500, 2000), 2), # max_stock
                random.choice(self.units),
                round(random.uniform(1000, 50000), 2),  # price_per_unit
                (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),  # expiry_date
                random.choice(warehouse_ids),
                random.choice(self.seasons),
                datetime.now() - timedelta(days=random.randint(1, 200))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO items (id, name, category, current_stock, min_stock, max_stock, unit, price_per_unit, expiry_date, warehouse_id, harvest_season, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', items)
    
    def generate_seeds(self, count=100):
        """Generate seed data"""
        seeds = []
        seed_names = [
            "Bibit Padi IR64", "Bibit Padi Ciherang", "Bibit Jagung Bisi", "Bibit Kedelai Anjasmoro",
            "Bibit Kacang Tanah", "Bibit Ubi Jalar", "Bibit Singkong", "Bibit Tomat",
            "Bibit Cabai", "Bibit Terong", "Bibit Bayam", "Bibit Kangkung"
        ]
        
        for i in range(count):
            seeds.append((
                str(uuid.uuid4()),
                random.choice(seed_names),
                random.choice(self.crop_types),
                f"Supplier {random.choice(['A', 'B', 'C', 'D'])}",
                round(random.uniform(100, 5000), 2),
                random.choice(["kg", "ton"]),
                round(random.uniform(5000, 50000), 2),
                (datetime.now() + timedelta(days=random.randint(60, 730))).strftime('%Y-%m-%d'),
                datetime.now() - timedelta(days=random.randint(1, 180))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO seeds (id, name, crop_type, supplier, quantity_available, unit, price_per_unit, expiry_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', seeds)
    
    def generate_fertilizers(self, count=80):
        """Generate fertilizer data"""
        fertilizers = []
        fertilizer_names = [
            "Pupuk Urea", "Pupuk NPK 16-16-16", "Pupuk ZA", "Pupuk KCL",
            "Pupuk Organik Cair", "Pupuk Kompos", "Pupuk Dolomit", "Pupuk SP-36"
        ]
        
        for i in range(count):
            fertilizers.append((
                str(uuid.uuid4()),
                random.choice(fertilizer_names),
                random.choice(["Kimia", "Organik", "Hibrida"]),
                f"Supplier {random.choice(['Pupuk Indonesia', 'Petrokimia', 'Pupuk Kaltim'])}",
                round(random.uniform(50, 2000), 2),
                random.choice(["kg", "ton", "sak"]),
                round(random.uniform(2000, 15000), 2),
                (datetime.now() + timedelta(days=random.randint(90, 1095))).strftime('%Y-%m-%d'),
                datetime.now() - timedelta(days=random.randint(1, 150))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO fertilizers (id, name, type, supplier, quantity_available, unit, price_per_unit, expiry_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', fertilizers)
    
    def generate_harvests(self, count=200):
        """Generate harvest data"""
        # Get existing farmers and warehouses
        self.cursor.execute("SELECT id FROM farmers")
        farmer_ids = [row[0] for row in self.cursor.fetchall()]
        
        self.cursor.execute("SELECT id FROM warehouses")
        warehouse_ids = [row[0] for row in self.cursor.fetchall()]
        
        harvests = []
        for i in range(count):
            harvest_date = datetime.now() - timedelta(days=random.randint(1, 365))
            harvests.append((
                str(uuid.uuid4()),
                random.choice(farmer_ids),
                random.choice(warehouse_ids),
                harvest_date.strftime('%Y-%m-%d'),
                random.choice(self.seasons),
                random.choice(self.crop_types),
                round(random.uniform(100, 10000), 2),
                random.choice(["kg", "ton", "karung"]),
                random.choice(self.quality_grades),
                f"Catatan panen #{i+1}",
                harvest_date
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO harvests (id, farmer_id, warehouse_id, harvest_date, season, crop_type, quantity, unit, quality_grade, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', harvests)
    
    def generate_transactions(self, count=500):
        """Generate inventory transactions"""
        # Get existing items and warehouses
        self.cursor.execute("SELECT id FROM items")
        item_ids = [row[0] for row in self.cursor.fetchall()]
        
        self.cursor.execute("SELECT id FROM warehouses")
        warehouse_ids = [row[0] for row in self.cursor.fetchall()]
        
        transactions = []
        transaction_types = ['in', 'out', 'transfer', 'distribution']
        
        for i in range(count):
            transaction_type = random.choice(transaction_types)
            from_warehouse = random.choice(warehouse_ids) if transaction_type in ['out', 'transfer', 'distribution'] else None
            to_warehouse = random.choice(warehouse_ids) if transaction_type in ['in', 'transfer'] else None
            
            transactions.append((
                str(uuid.uuid4()),
                random.choice(item_ids),
                transaction_type,
                round(random.uniform(1, 1000), 2),
                from_warehouse,
                to_warehouse,
                datetime.now() - timedelta(days=random.randint(1, 180)),
                "system",  # created_by
                f"Transaksi {transaction_type} #{i+1}"
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO inventory_transactions (id, item_id, transaction_type, quantity, from_warehouse_id, to_warehouse_id, transaction_date, created_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', transactions)
    
    def generate_distribution_routes(self, count=100):
        """Generate distribution routes"""
        # Get existing warehouses and merchants
        self.cursor.execute("SELECT id FROM warehouses")
        warehouse_ids = [row[0] for row in self.cursor.fetchall()]
        
        self.cursor.execute("SELECT id FROM merchants")
        merchant_ids = [row[0] for row in self.cursor.fetchall()]
        
        routes = []
        road_conditions = ["Baik", "Sedang", "Rusak Ringan", "Rusak Berat"]
        
        for i in range(count):
            routes.append((
                str(uuid.uuid4()),
                f"Rute Distribusi #{i+1}",
                random.choice(warehouse_ids),
                random.choice(merchant_ids),
                round(random.uniform(1, 50), 2),  # distance in km
                round(random.uniform(15, 120), 2),  # travel_time in minutes
                round(random.uniform(0.5, 1.0), 2),  # efficiency_score
                round(random.uniform(5000, 50000), 2),  # fuel_cost
                random.choice(road_conditions),
                datetime.now() - timedelta(days=random.randint(1, 90))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO distribution_routes (id, route_name, from_warehouse_id, to_merchant_id, distance, travel_time, efficiency_score, fuel_cost, road_condition, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', routes)
    
    def generate_notifications(self, count=150):
        """Generate notifications"""
        # Get existing users
        self.cursor.execute("SELECT id FROM users")
        user_ids = [row[0] for row in self.cursor.fetchall()]
        
        if not user_ids:
            # Create a default user if none exists
            user_id = str(uuid.uuid4())
            hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (id, username, password, full_name, role, department)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, "admin", hashed_password, "Administrator", "admin", "IT"))
            user_ids = [user_id]
        
        notifications = []
        notification_types = ['info', 'warning', 'success', 'error']
        messages = [
            "Stok barang hampir habis",
            "Barang baru telah ditambahkan",
            "Transaksi berhasil diproses",
            "Laporan bulanan tersedia",
            "Sistem maintenance akan dilakukan",
            "Barang kedaluwarsa dalam 30 hari",
            "Pesanan distributor telah diterima",
            "Update harga barang terbaru"
        ]
        
        for i in range(count):
            notifications.append((
                str(uuid.uuid4()),
                random.choice(user_ids),
                random.choice(messages),
                random.choice(notification_types),
                random.choice([0, 1]),  # is_read
                datetime.now() - timedelta(days=random.randint(1, 60))
            ))
        
        self.cursor.executemany('''
            INSERT OR IGNORE INTO notifications (id, user_id, message, type, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', notifications)
    
    def generate_all_data(self):
        """Generate all dummy data"""
        print("🌾 Generating dummy data for agricultural inventory system...")
        
        try:
            # Generate data in order of dependencies
            print("Generating warehouses...")
            self.generate_warehouses()
            
            print("Generating farmers...")
            self.generate_farmers(300)
            
            print("Generating merchants...")
            self.generate_merchants(150)
            
            print("Generating items...")
            self.generate_items(200)
            
            print("Generating seeds...")
            self.generate_seeds(100)
            
            print("Generating fertilizers...")
            self.generate_fertilizers(80)
            
            print("Generating harvests...")
            self.generate_harvests(200)
            
            print("Generating transactions...")
            self.generate_transactions(500)
            
            print("Generating distribution routes...")
            self.generate_distribution_routes(100)
            
            print("Generating notifications...")
            self.generate_notifications(150)
            
            self.conn.commit()
            print("✅ Dummy data generation completed successfully!")
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            print(f"❌ Error generating dummy data: {e}")
            self.conn.rollback()
        finally:
            self.conn.close()
    
    def print_summary(self):
        """Print summary of generated data"""
        tables = ['users', 'warehouses', 'items', 'farmers', 'merchants', 'harvests', 
                 'inventory_transactions', 'seeds', 'fertilizers', 'distribution_routes', 'notifications']
        
        print("\n📊 Data Summary:")
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
        print("🎯 Target: 1000+ records achieved!")

if __name__ == "__main__":
    generator = DummyDataGenerator()
    generator.generate_all_data()
