# 🌾 Sistem Lumbung Digital Desa

Sistem manajemen lumbung digital berbasis web untuk monitoring dan pengelolaan hasil pertanian desa menggunakan teknologi SQLite dan Streamlit.

## 📋 Deskripsi

Sistem Lumbung Digital adalah aplikasi web yang dirancang khusus untuk mengelola stok hasil pertanian di lumbung-lumbung desa. Aplikasi ini menyediakan solusi komprehensif untuk tracking inventori, manajemen petani dan pedagang, distribusi hasil panen, serta forecasting kebutuhan pertanian.

## 🆕 Update Terbaru (v1.4.0)

### ✨ Fitur Baru
- **🗂️ Data Dummy Generator**: Generate 1000+ record untuk simulasi dan testing
- **📍 Enhanced Warehouse Locations**: Improved location management dengan SQLite integration
- **🛡️ Better Error Handling**: Robust error handling dan user feedback
- **📊 Real-time Statistics**: Live database statistics dan monitoring

### 🔧 Perbaikan & Optimasi
- **Database Migration**: Full migration dari MongoDB ke SQLite
- **Performance Improvement**: Query optimization dan faster loading
- **UI/UX Enhancements**: Better responsive design dan user experience
- **Security Updates**: Enhanced authentication dan input validation

### 📈 Data Generation Capabilities
- **👨‍🌾 300+ Data Petani**: Complete farmer profiles dengan lokasi dan lahan
- **🏪 150+ Data Pedagang**: Merchant database dengan kategori dan kontak
- **🌾 200+ Data Items**: Inventory items dengan stok dan pricing
- **🌱 100+ Data Bibit**: Seed inventory dengan expiry tracking
- **🧪 80+ Data Pupuk**: Fertilizer management system
- **📈 200+ Data Hasil Panen**: Harvest records dengan quality grading
- **🔄 500+ Data Transaksi**: Transaction history dan audit trail
- **🚚 100+ Data Rute Distribusi**: Distribution route optimization
- **🔔 150+ Data Notifikasi**: System notifications dan alerts

## ✨ Fitur Utama

### Dashboard Real-time
- **KPI Dashboard**: Monitoring stok, distribusi, dan kinerja real-time
- **Visualisasi Data**: Grafik interaktif untuk produksi dan distribusi
- **Notifikasi**: Alert otomatis untuk stok rendah dan kejadian penting
- **Ringkasan Cepat**: Overview kondisi lumbung dan status distribusi

### Data Dummy Management *(NEW)*
- **One-Click Generation**: Generate 1000+ record untuk testing dan demo (Admin)
- **Safe Simulation Mode**: Generate 50+ record untuk user biasa bermain simulasi
- **Role-Based Access**: Admin dapat generate full data, user dapat generate safe data
- **Realistic Data**: Data dummy yang realistis untuk simulasi pertanian
- **Admin Only**: Fitur khusus admin untuk development dan testing
- **Statistics Dashboard**: Live monitoring database statistics
- **Safe Generation**: Validasi data dan error handling yang robust

### Manajemen Pengguna
### � Manajemen Pengguna
- **Multi-Role System**: Admin, Staff, Manager dengan akses terbatas
- **Authentication**: Login aman dengan password hashing
- **Profile Management**: Update profil dan ganti password
- **Session Management**: Session state yang aman

### 🌾 Manajemen Petani
- **Data Petani Lengkap**: Nama, lokasi, luas lahan, komoditas utama
- **Tracking Lahan**: Informasi detail tentang lahan pertanian
- **Statistik Petani**: Analisis distribusi petani per lokasi
- **Kualitas Data**: Kategorisasi petani berdasarkan kualitas dan produktivitas

### 🏪 Manajemen Pedagang
- **Database Pedagang**: Informasi lengkap pedagang lokal
- **Kategorisasi**: Pengecer, grosir, restoran, warung
- **Lokasi Tracking**: Pemetaan lokasi pedagang untuk distribusi
- **Analisis Bisnis**: Trend penjualan dan preferensi produk

### 📊 Manajemen Hasil Panen
- **Pencatatan Panen**: Record semua hasil panen dengan kualitas
- **Musiman Tracking**: Monitoring berdasarkan musim tanam
- **Kualitas Grading**: Sistem grading A, B, C, D untuk hasil panen
- **Warehouse Assignment**: Otomatis assign ke lumbung yang tersedia

### 🚚 Sistem Distribusi
- **Route Optimization**: Pemetaan rute distribusi efisien
- **Status Tracking**: Real-time tracking status pengiriman
- **Cost Analysis**: Analisis biaya distribusi per kg dan per rute
- **Delivery Management**: Jadwal dan prioritas pengiriman

### 📈 Forecasting & Analytics
- **Production Forecast**: Prediksi produksi berdasarkan data historis
- **Needs Prediction**: Forecast kebutuhan bibit, pupuk, pestisida
- **Trend Analysis**: Analisis trend produksi, kualitas, distribusi
- **Strategic Recommendations**: Rekomendasi untuk peningkatan kinerja

### 📋 Laporan & Export
- **Comprehensive Reports**: Laporan detail untuk semua aspek
- **Multi-format Export**: CSV, Excel, JSON
- **Custom Date Range**: Filter laporan berdasarkan periode
- **Financial Analysis**: Laporan keuangan dan ROI

## 🏗️ Arsitektur Teknis

### 🗄️ Database
- **SQLite**: Database file-based yang ringan dan reliable
- **Schema Normalized**: Struktur database yang optimal
- **ACID Compliance**: Transaksi yang aman dan konsisten
- **Backup & Recovery**: Mudah backup dan restore

### 🎨 Frontend
- **Streamlit**: Framework Python untuk web apps
- **Responsive Design**: UI yang adaptif untuk berbagai device
- **Real-time Updates**: Auto-refresh untuk data real-time
- **Interactive Charts**: Visualisasi dengan Plotly

### 🔐 Security
- **Password Hashing**: bcrypt untuk password security
- **Role-based Access**: Kontrol akses berdasarkan peran
- **Session Management**: Session state yang aman
- **Input Validation**: Validasi data input yang robust

## 📦 Struktur Proyek

```
project-inventory-management/
├── app.py                      # Main application
├── config_new.py              # Database configuration
├── requirements_new.txt       # Python dependencies
├── pages/                     # Streamlit pages
│   ├── dashboard_new.py       # Dashboard utama
│   ├── warehouse_new.py       # Manajemen lumbung
│   ├── warehouse_locations_simple.py  # Lokasi lumbung (SQLite)
│   ├── farmers_new.py         # Manajemen petani
│   ├── merchants_new.py       # Manajemen pedagang
│   ├── harvests_new.py        # Manajemen hasil panen
│   ├── distribution_new.py    # Manajemen distribusi
│   ├── report_new.py          # Laporan & analytics
│   └── forecast_new.py        # Forecasting & prediksi
├── utils/                     # Utility functions
│   ├── sqlite_database.py     # Database operations (SQLite)
│   ├── dummy_data_generator.py # Full data dummy generator (Admin)
│   ├── dummy_data_generator_safe.py # Safe simulation generator (Users)
│   ├── auth_new.py           # Authentication system
│   └── helpers_new.py        # Helper functions
├── scripts/                   # Utility scripts
├── static/                    # Static assets
└── data/                      # Data files
```

## 🚀 Instalasi & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Quick Start

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd project-inventory-management
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements_new.txt
   ```

3. **Initialize Database**
   ```bash
   python fix_database.py
   ```

4. **(Optional) Generate Data Dummy untuk Testing**
   ```bash
   python utils/dummy_data_generator.py
   ```

5. **Run Application**
   ```bash
   streamlit run app.py
   ```

6. **Access Application**
   - Buka browser dan kunjungi `http://localhost:8501`
   - Login dengan akun default:
     - Username: `admin`
     - Password: `admin123`

7. **Generate Data Dummy via UI** *(Recommended)*
   - Login sebagai admin atau user biasa
   - Navigate ke menu "Data Dummy" di sidebar
   - **Admin**: Klik "🚀 Generate Data Dummy" untuk membuat 1000+ record
   - **User**: Klik "🚀 Generate Data Simulasi" untuk membuat 50+ record
   - Monitor progress dan statistik database real-time

## 👤 Pengguna & Roles

### 🔴 Admin
- **Full Access**: Akses penuh ke semua fitur
- **User Management**: Kelola pengguna dan roles
- **System Configuration**: Konfigurasi sistem
- **Master Data**: Kelola data master (lumbung, petani, pedagang)
- **Data Dummy Management**: Generate dan manage data dummy untuk testing *(NEW)*

### 🟡 Manager
- **Reports Access**: Akses ke semua laporan
- **Approval**: Approve distribusi dan transaksi penting
- **Analytics**: Analisis data dan forecasting
- **Strategic Planning**: Perencanaan strategis

### 🟢 Staff
- **Data Entry**: Input data harian (panen, distribusi)
- **Inventory Management**: Kelola stok lumbung
- **Basic Reports**: Laporan operasional
- **Customer Service**: Layanan ke petani dan pedagang
- **Simulation Access**: Generate data simulasi untuk training *(NEW)*

## 📊 Fitur Detail

### 🌾 Dashboard Features
- **Real-time KPI**: Total stok, distribusi hari ini, alert
- **Production Chart**: Grafik produksi mingguan/bulanan
- **Distribution Map**: Peta distribusi real-time
- **Quality Metrics**: Indikator kualitas produk
- **Low Stock Alerts**: Notifikasi stok rendah

### 🏪 Warehouse Management
- **Multi-warehouse**: Support multiple lumbung locations
- **Stock Tracking**: Real-time stock monitoring
- **Quality Control**: Quality grading dan tracking
- **Transfer Management**: Transfer antar lumbung
- **Storage Optimization**: Optimasi penyimpanan

### 👨‍🌾 Farmer Management
- **Complete Profile**: Data lengkap petani dan lahan
- **Crop Tracking**: Monitoring komoditas per petani
- **Performance Analysis**: Analisis produktivitas
- **Seasonal Planning**: Perencanaan musim tanam
- **Support Services**: Layanan pendukung petani

### 🚚 Distribution System
- **Route Planning**: Optimasi rute distribusi
- **Status Tracking**: Real-time delivery status
- **Cost Management**: Monitoring biaya distribusi
- **Performance Metrics**: KPI distribusi
- **Customer Satisfaction**: Feedback dan rating

### 📈 Analytics & Reporting
- **Production Analytics**: Analisis trend produksi
- **Quality Analytics**: Trend kualitas produk
- **Financial Reports**: Laporan keuangan lengkap
- **Operational KPI**: KPI operasional
- **Custom Reports**: Report builder untuk kebutuhan khusus

## 🔧 Konfigurasi

### Database Settings
```python
# config_new.py
DATABASE_CONFIG = {
    'database': 'inventory_new.db',
    'backup_enabled': True,
    'auto_backup_interval': 24  # hours
}
```

### Application Settings
```python
# Environment variables
STREAMLIT_SERVER_PORT = 8501
STREAMLIT_SERVER_HEADLESS = false
DEBUG_MODE = false
```

## 🧪 Testing

### Run Tests
```bash
# Database tests
python test_database.py

# Complete system tests
python test_complete.py

# Integration tests
python test_integration.py

# Test dummy data generation
python utils/dummy_data_generator.py
```

### Test Coverage
- ✅ Database operations
- ✅ Authentication system
- ✅ CRUD operations
- ✅ Business logic
- ✅ API endpoints
- ✅ Data validation
- ✅ Data dummy generation *(NEW)*
- ✅ SQLite integration *(NEW)*

## 🔄 Migration dari MongoDB

### Perubahan Utama
- **Database**: MongoDB → SQLite
- **Dependencies**: pymongo → sqlite3 (built-in)
- **Configuration**: Connection string → file path
- **Queries**: MongoDB queries → SQL queries

### Benefits
- ✅ **Simpler Setup**: Tidak perlu external database
- ✅ **Lower Cost**: Tidak ada biaya hosting database
- ✅ **Better Performance**: Query yang lebih cepat untuk data kecil-menengah
- ✅ **Easier Backup**: File-based backup yang sederhana
- ✅ **Offline Capability**: Bisa berjalan tanpa internet

### 🆕 SQLite Integration Features
- **🗄️ Optimized Schema**: Database structure yang optimal untuk SQLite
- **🔄 Auto Migration**: Automatic data migration dari MongoDB format
- **📊 Enhanced Analytics**: Better query performance untuk analytics
- **🛡️ Data Integrity**: ACID compliance untuk data consistency

## 📱 User Interface

### Design Principles
- **Mobile First**: Responsive design untuk mobile devices
- **Agricultural Theme**: Warna dan elemen UI tema pertanian
- **Intuitive Navigation**: Menu sidebar yang jelas
- **Fast Loading**: Optimized untuk koneksi internet lambat
- **Accessibility**: Support untuk screen readers

### Key UI Elements
- **Dashboard**: Overview dengan cards dan charts
- **Forms**: Input forms dengan validation
- **Tables**: Sortable dan searchable data tables
- **Charts**: Interactive charts dengan Plotly
- **Maps**: Peta distribusi dan lokasi

## 🛠️ Development

### Code Structure
- **Modular Architecture**: Pisahkan logic per module
- **Database Layer**: Abstraksi database operations
- **Business Logic**: Business rules terpisah dari UI
- **Error Handling**: Comprehensive error handling
- **Logging**: Detailed logging untuk debugging

### Best Practices
- **Code Documentation**: Docstrings untuk semua functions
- **Type Hints**: Type hints untuk better code quality
- **Testing**: Unit tests untuk critical functions
- **Version Control**: Git workflow yang proper
- **Code Review**: Code review process

## 📞 Support & Maintenance

### Troubleshooting
- **Database Issues**: Check file permissions dan disk space
- **Performance Issues**: Monitor memory usage dan query optimization
- **UI Issues**: Clear browser cache dan check JavaScript console
- **Login Issues**: Verify user credentials dan database connection

### Maintenance Tasks
- **Database Backup**: Regular backup schedule
- **Log Rotation**: Manage log file sizes
- **Performance Monitoring**: Monitor application performance
- **Security Updates**: Regular security patches
- **User Training**: Training untuk pengguna baru

## 🚀 Roadmap

### Version 1.5 (In Progress)
- 📊 **Advanced Analytics**: Enhanced analytics capabilities
- 🔗 **API Integration**: REST API untuk third-party integration
- 📱 **PWA Support**: Progressive Web App features
- 🎯 **Goal Setting**: Target dan goal tracking
- 💬 **Chat Support**: In-app chat support

### Version 2.0 (Planned)
- 🌐 **Mobile App**: Native mobile application
- 🤖 **AI Integration**: Machine learning untuk better forecasting
- 📡 **IoT Sensors**: Integration dengan sensor hardware
- 🔄 **Real-time Sync**: Real-time synchronization
- 🌍 **Multi-language**: Support untuk multiple languages

### 🆕 Recent Releases (v1.4.0)
- ✅ **Data Dummy Generator**: Complete data generation system
- ✅ **SQLite Migration**: Full database migration
- ✅ **Enhanced UI**: Better user experience
- ✅ **Performance Optimization**: Faster loading dan queries

## 📄 License

MIT License - lihat file LICENSE untuk detail lengkap.

## 🤝 Kontribusi

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

### Cara Kontribusi
1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Kontak

- **Project Maintainer**: [Nama Maintainer]
- **Email**: [email@example.com]
- **Issues**: GitHub Issues
- **Documentation**: [Link ke dokumentasi]

---

## 🎯 Quick Start Summary

1. **Install**: `pip install -r requirements_new.txt`
2. **Setup DB**: `python fix_database.py`
3. **(Optional) Data Dummy**: `python utils/dummy_data_generator.py` atau via UI
4. **Run**: `streamlit run app.py`
5. **Login**: Username: `admin`, Password: `admin123`
6. **Explore**: Navigasi melalui sidebar menu
7. **Generate Data**: Menu "Data Dummy" → "🚀 Generate Data Dummy"

**🌾 Selamat menggunakan Sistem Lumbung Digital Desa v1.4.0!**

---

## 📊 Version History

### v1.4.0 (Latest) - *(November 2024)*
- ✨ **Data Dummy Generator**: 1000+ record generation system
- 🔧 **SQLite Migration**: Complete database migration from MongoDB
- 📍 **Enhanced Locations**: Improved warehouse location management
- 🛡️ **Better Security**: Enhanced authentication and validation
- 📈 **Performance**: Optimized queries and faster loading

### v1.3.0 - *(October 2024)*
- 📊 **Analytics Dashboard**: Enhanced reporting capabilities
- 🔄 **Distribution Management**: Improved route optimization
- 📱 **Mobile Responsive**: Better mobile experience

### v1.2.0 - *(September 2024)*
- 👥 **Multi-User Support**: Role-based access control
- 🌾 **Harvest Management**: Complete harvest tracking system
- 📋 **Inventory Management**: Advanced stock management

### v1.1.0 - *(August 2024)*
- 🏠 **Dashboard**: Real-time monitoring dashboard
- 🔐 **Authentication**: Secure login system
- 📊 **Basic Reports**: Initial reporting features

### v1.0.0 - *(July 2024)*
- 🚀 **Initial Release**: Basic inventory management system
- 🗄️ **MongoDB Integration**: Initial database implementation
