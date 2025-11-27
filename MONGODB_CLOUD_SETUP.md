# Panduan Koneksi MongoDB Cloud (MongoDB Atlas)

## 📋 Overview

Aplikasi Lumbung Digital mendukung koneksi ke MongoDB Atlas (cloud database) untuk meningkatkan skalabilitas, reliability, dan aksesibilitas data.

## 🚀 Langkah-Langkah Setup

### 1. Setup MongoDB Atlas

1. **Buat Account**: Login ke [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. **Create Cluster**: 
   - Pilih "Create Cluster"
   - Pilih M0 (Free Tier) untuk development
   - Pilih region terdekat (misal: Singapore)
3. **Database User**:
   - Menu "Database Access" → "Add New Database User"
   - Username: `lumbung_admin` (atau sesuai keinginan)
   - Password: Buat password yang kuat
   - Permissions: Read and write to any database
4. **Network Access**:
   - Menu "Network Access" → "Add IP Address"
   - Untuk development: `0.0.0.0/0` (allow access from anywhere)
   - Untuk production: Tambah IP spesifik server Anda

### 2. Get Connection String

1. Klik "Connect" pada cluster Anda
2. Pilih "Connect your application"
3. Copy connection string, formatnya seperti:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/
   ```

### 3. Konfigurasi Environment

Buat/edit file `.env` di root project:

```env
# MongoDB Cloud Configuration
MONGODB_HOST=cluster0.xxxxx.mongodb.net
MONGODB_PORT=27017
MONGODB_DATABASE=kalkulis_inventory
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_AUTH_SOURCE=admin

# Connection Pool Settings
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
MONGODB_MAX_IDLE_TIME=45000
```

### 4. Install Dependencies

```bash
pip install pymongo[srv] python-dotenv
```

### 5. Testing Koneksi

Jalankan script testing:
```bash
python scripts/test_cloud_connection.py
```

## 🔄 Migrasi Data

### Dari Local ke Cloud

Jika Anda memiliki data di MongoDB lokal dan ingin migrasi ke cloud:

1. Pastikan MongoDB lokal sedang berjalan
2. Konfigurasi `.env` untuk MongoDB Atlas
3. Jalankan migrasi script:
   ```bash
   python scripts/migrate_to_cloud.py
   ```

### Backup & Restore

**Backup dari Cloud:**
```bash
mongodump "mongodb+srv://username:password@cluster.mongodb.net/" --out=backup/
```

**Restore ke Cloud:**
```bash
mongorestore "mongodb+srv://username:password@cluster.mongodb.net/" backup/
```

## ⚙️ Konfigurasi Lanjutan

### Connection Pooling

Aplikasi sudah terkonfigurasi dengan connection pooling:
- `maxPoolSize=100`: Maksimal 100 koneksi
- `minPoolSize=10`: Minimal 10 koneksi
- `maxIdleTimeMS=45000`: T idle time 45 detik

### Retry Policy

- `retryWrites=true`: Otomatis retry write operations
- `retryReads=true`: Otomatis retry read operations
- `serverSelectionTimeoutMS=5000`: Timeout 5 detik

### Index Optimization

Database otomatis membuat indexes untuk performa optimal:
- Users: username, role, department
- Items: name, category, warehouse_id
- Transactions: item_id, transaction_type, date
- Geospatial indexes untuk lokasi

## 🔧 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Periksa username & password di `.env`
   - Pastikan user sudah dibuat di MongoDB Atlas

2. **Network Access Denied**
   - Tambah IP address ke whitelist
   - Pastikan firewall tidak blocking

3. **Connection Timeout**
   - Periksa koneksi internet
   - Pastikan cluster status "Running"

4. **DNS Resolution Error**
   - Install `pymongo[srv]` untuk DNS SRV support
   - Periksa connection string format

### Testing Commands

```bash
# Test koneksi dasar
python -c "from utils.database import MongoDBConnection; print(MongoDBConnection.get_client().admin.command('ping'))"

# Test database operations
python scripts/test_cloud_connection.py

# Verifikasi data
python scripts/migrate_to_cloud.py --verify
```

## 📊 Monitoring

### MongoDB Atlas Dashboard

Monitor melalui MongoDB Atlas dashboard:
- **Metrics**: CPU, Memory, Disk usage
- **Performance**: Query performance, slow queries
- **Alerts**: Setup alerts untuk monitoring

### Application Logging

Aplikasi menggunakan logging untuk monitoring:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Database operation completed")
```

## 🔒 Security Best Practices

### Production Environment

1. **Environment Variables**: Jangan hardcode credentials
2. **IP Whitelisting**: Batasi akses ke IP spesifik
3. **Network Peering**: Gunakan VPC peering untuk production
4. **Encryption**: Enable encryption at rest & in transit
5. **Audit Logs**: Monitor database access logs

### Connection String Security

```bash
# ✅ Benar: Gunakan environment variables
MONGODB_HOST=${MONGODB_HOST}

# ❌ Salah: Hardcode credentials
MONGODB_HOST=cluster0.xxxxx.mongodb.net
```

## 🚀 Performance Optimization

### Tips untuk Production

1. **Index Strategy**: Buat indexes untuk query yang sering digunakan
2. **Connection Pool**: Sesuaikan pool size dengan traffic
3. **Read Preference**: Gunakan secondary untuk read operations
4. **Write Concern**: Sesuaikan write concern untuk consistency
5. **Monitoring**: Setup alerts untuk performance metrics

### Example Production Config

```env
MONGODB_MAX_POOL_SIZE=50
MONGODB_MIN_POOL_SIZE=5
MONGODB_MAX_IDLE_TIME=30000
ENABLE_REALTIME=true
CHANGE_STREAM_ENABLED=true
```

## 📞 Support

### Resources
- [MongoDB Atlas Documentation](https://docs.mongodb.com/atlas/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [Connection String Guide](https://docs.mongodb.com/manual/reference/connection-string/)

### Emergency Contacts
- Database Admin: [Your DBA Contact]
- Development Team: [Dev Team Contact]
