# 🚀 Quick Start Guide - Lumbung Digital dengan MongoDB Cloud

## 📋 Prerequisites

- ✅ MongoDB Atlas cluster sudah dibuat
- ✅ Database user sudah dikonfigurasi
- ✅ IP address sudah di-whitelist
- ✅ Python dependencies sudah terinstall

## ⚙️ Konfigurasi

File `.env` sudah dikonfigurasi dengan MongoDB Cloud:

```env
# MongoDB Cloud Configuration
MONGODB_HOST=cluster0.qrwajos.mongodb.net
MONGODB_DATABASE=Cluster0
MONGODB_USERNAME=siludi_db_user
MONGODB_PASSWORD=@Cilacap25Juli1986
```

## 🚀 Setup Database

Jalankan script setup untuk inisialisasi database:

```bash
python scripts/setup_cloud_database.py
```

Script ini akan:
- 🔌 Test koneksi ke MongoDB Atlas
- 📁 Buat semua collections yang diperlukan
- 🏠 Insert default warehouses (lumbung desa)
- 👤 Buat admin user
- ✅ Verifikasi setup berhasil

## 🏃‍♂️ Jalankan Aplikasi

Setelah setup selesai, jalankan aplikasi:

```bash
streamlit run app.py
```

## 🔑 Login

Gunakan credentials default:
- **Username**: `admin`
- **Password**: `admin123`

## 🌾 Fitur Utama

### Dashboard
- 📊 Monitor stok hasil pertanian
- 📈 Analisis distribusi per lumbung
- 🔔 Notifikasi stok rendah

### Manajemen Lumbung
- 🏠 8 Lumbung desa pre-configured
- 📦 Tracking stok real-time
- 📍 Lokasi dan kapasitas

### Manajemen Petani
- 👨‍🌾 Data petani dan lahan
- 📍 Koordinat lokasi
- 📊 Historis panen

### Manajemen Pedagang
- 🏪 Data pedagang lokal
- 🚐 Rute distribusi
- 📈 Performa distribusi

### Forecasting
- 📊 Prediksi kebutuhan bibit
- 🌱 Prediksi kebutuhan pupuk
- 📈 Analisis musim panen

## 📱 Navigation

Sidebar navigation yang tersedia:
- Dashboard
- Manajemen Lumbung
- Lokasi Lumbung Desa
- Manajemen Petani
- Manajemen Pedagang
- Hasil Panen
- Pemetaan Distribusi
- Forecasting Kebutuhan
- Laporan
- Profil Pengguna
- Notifikasi
- Analytics

## 🔧 Troubleshooting

### Connection Issues
```bash
# Test koneksi manual
python -c "from utils.database import MongoDBConnection; print(MongoDBConnection.get_client().admin.command('ping'))"
```

### Reset Database
```bash
# Re-initialize database
python scripts/setup_cloud_database.py
```

### Check Collections
```bash
# Lihat semua collections
python -c "from utils.database import MongoDBConnection; db=MongoDBConnection.get_database(); print(db.list_collection_names())"
```

## 📊 Data Structure

### Collections
- `users` - Data pengguna & authentication
- `warehouses` - Data lumbung desa
- `items` - Data produk pertanian
- `farmers` - Data petani
- `merchants` - Data pedagang
- `harvests` - Data hasil panen
- `inventory_transactions` - Transaksi stok
- `distribution_routes` - Rute distribusi

### Default Data
- 8 Lumbung desa dengan kapasitas berbeda
- 1 Admin user untuk akses penuh
- Indexes untuk performa optimal

## 🌐 Cloud Benefits

### Advantages
- 🔄 Auto-backup oleh MongoDB Atlas
- 📈 Scalable sesuai kebutuhan
- 🔒 Security & encryption
- 🌍 Akses dari mana saja
- 📊 Monitoring dashboard

### Performance
- ⚡ Connection pooling (100 connections)
- 🚀 Optimized indexes
- 📱 Real-time updates
- 🔄 Retry mechanisms

## 📞 Support

### Documentation
- 📖 `MONGODB_CLOUD_SETUP.md` - Setup lengkap
- 📋 `QUICK_START_GUIDE.md` - Quick start
- 🔧 Scripts di folder `scripts/`

### Common Issues
1. **Connection timeout** - Check IP whitelist
2. **Auth failed** - Verify username/password
3. **Database not found** - Check database name
4. **Collections empty** - Run setup script

## 🎯 Next Steps

1. ✅ **Setup completed** - Aplikasi siap digunakan
2. 📊 **Add data** - Input petani & pedagang
3. 📦 **Manage inventory** - Tracking stok produk
4. 🚚 **Plan distribution** - Optimasi rute
5. 📈 **Generate reports** - Analisis performa

---

🌾 **Selamat menggunakan Lumbung Digital dengan MongoDB Cloud!**

*Your agricultural inventory management system is now running on the cloud with enhanced scalability, reliability, and performance.*
