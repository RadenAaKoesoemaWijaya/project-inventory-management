import streamlit as st
import pandas as pd
from utils.auth import login_user, logout_user, get_user_by_id, update_user
from utils.database import MongoDBConnection, get_items_low_stock, get_recent_transactions, init_db, get_warehouse_consumption
from utils.helpers import get_stock_status, get_department_consumption, get_top_consumed_items
import os
from datetime import datetime
from bson import ObjectId

# Initialize MongoDB connection and database
@st.cache_resource
def initialize_database():
    """Initialize database connection and create collections"""
    try:
        init_db()
        return True
    except Exception as e:
        st.error(f"Failed to initialize database: {e}")
        return False

# Set page configuration with agriculture theme
st.set_page_config(
    page_title="Lumbung Digital - Manajemen Hasil Pertanian",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Sistem Lumbung Digital - Manajemen hasil pertanian, forecasting bibit & pupuk, serta distribusi ke pedagang lokal"
    }
)

# Custom CSS for agriculture theme
st.markdown("""
<style>
    /* Agriculture theme colors */
    .stApp {
        background: linear-gradient(135deg, #f5f9f5 0%, #e8f5e8 100%);
    }
    
    /* Custom header */
    .agri-header {
        background: linear-gradient(135deg, #4CAF50, #8BC34A, #CDDC39);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Agriculture cards */
    .agri-card {
        background: white;
        border-left: 5px solid #4CAF50;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Fertilizer themed elements */
    .fertilizer-badge {
        background: linear-gradient(45deg, #FF6B35, #F7931E);
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
    }
    
    /* Seed themed elements */
    .seed-badge {
        background: linear-gradient(45deg, #8B4513, #D2691E);
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
    }
    
    /* Harvest themed elements */
    .harvest-badge {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #333;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Initialize database
if 'db_initialized' not in st.session_state:
    with st.spinner("🌾 Sedang mempersiapkan sistem lumbung digital..."):
        st.session_state['db_initialized'] = initialize_database()

# Sidebar navigation
def sidebar_nav():
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #4CAF50, #8BC34A); border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: white; margin: 0; font-size: 1.1em;">🌾 LUMBUNG DIGITAL</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 0.8em;">Sistem Manajemen Pertanian</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.get('authenticated', False):
        user = st.session_state['user']
        st.sidebar.write(f"Selamat datang, **{user['full_name']}**!")
        st.sidebar.write(f"Role: {user['role']}")
        st.sidebar.write(f"Departemen: {user.get('department', 'Tidak ditentukan')}")
        
        st.sidebar.divider()
        
        # Navigation menu
        menu_options = [
            "Dashboard",
            "Manajemen Lumbung", 
            "Manajemen Petani",
            "Manajemen Pedagang",
            "Hasil Panen",
            "Pemetaan Distribusi",
            "Forecasting Kebutuhan",
            "Laporan",
            "Profil Pengguna",
            "Notifikasi",
            "Analytics"
        ]
        
        # Filter menu based on role
        if user['role'] == 'admin':
            menu_options.append("Manajemen Pengguna")
        
        selected_page = st.sidebar.selectbox("Pilih Menu", menu_options)
        
        # Logout button
        if st.sidebar.button("Logout", use_container_width=True):
            from utils.auth import logout_user
            logout_user()
            st.rerun()
            
        return selected_page
    
    return None

# Login page
def login_page():
    st.title("Sistem Lumbung Digital - Manajemen Hasil Pertanian Desa")
    
    # Create tabs for login and registration
    login_tab, register_tab, info_tab = st.tabs(["Login", "Daftar Baru", "Tentang Aplikasi"])
    
    with login_tab:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Custom agriculture logo with fertilizer, seeds, and farming elements
            st.markdown("""
            <div style="text-align: center; background: linear-gradient(135deg, #4CAF50, #8BC34A, #CDDC39); padding: 25px; border-radius: 20px; box-shadow: 0 6px 12px rgba(0,0,0,0.3);">
                <div style="display: flex; justify-content: center; gap: 10px; margin-bottom: 10px;">
                    <div style="background: rgba(255,255,255,0.95); padding: 12px; border-radius: 50%; font-size: 2em; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🌾</div>
                    <div style="background: rgba(255,255,255,0.95); padding: 12px; border-radius: 50%; font-size: 2em; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🌱</div>
                    <div style="background: rgba(255,255,255,0.95); padding: 12px; border-radius: 50%; font-size: 2em; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">💧</div>
                </div>
                <h1 style="color: white; margin: 0; font-size: 1.8em; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">🚜 LUMBUNG DIGITAL 🌿</h1>
                <div style="display: flex; justify-content: center; gap: 15px; margin: 15px 0;">
                    <div style="background: rgba(139,69,19,0.9); color: white; padding: 8px 12px; border-radius: 15px; font-size: 0.9em;">🌰 Bibit</div>
                    <div style="background: rgba(255,140,0,0.9); color: white; padding: 8px 12px; border-radius: 15px; font-size: 0.9em;">💊 Pupuk</div>
                    <div style="background: rgba(34,139,34,0.9); color: white; padding: 8px 12px; border-radius: 15px; font-size: 0.9em;">🌾 Panen</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 10px; margin-top: 10px;">
                    <p style="color: white; margin: 0; font-size: 0.85em; font-weight: bold;">Sistem Manajemen Hasil Pertanian</p>
                    <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 0.75em;">Forecasting • Distribusi • Inventory</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.subheader("Silakan Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login"):
                if login_user(username, password):
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau password salah!")
    
    with register_tab:
        st.subheader("Daftar Pengguna Baru")
        
        # Registration form
        with st.form("registration_form"):
            full_name = st.text_input("Nama Lengkap")
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Konfirmasi Password", type="password")
            
            # Default role for new users
            role = st.selectbox("Role", ["staff", "manager"], index=0)
            
            # Updated warehouse selection for agricultural system
            warehouses = [
                "Lumbung Desa Sentra Tani",
                "Lumbung Desa Tambakrejo", 
                "Lumbung Desa Ngadirejo",
                "Lumbung Desa Tlogosari",
                "Lumbung Desa Bandungrejo",
                "Lumbung Desa Purworejo",
                "Lumbung Desa Sumberagung",
                "Lumbung Desa Karanganyar"
            ]
            
            department = st.selectbox("Lumbung/Lokasi", warehouses)
            
            submit_button = st.form_submit_button("Daftar")
            
            if submit_button:
                if not full_name or not new_username or not new_password:
                    st.error("Semua field harus diisi!")
                elif new_password != confirm_password:
                    st.error("Password dan konfirmasi password tidak cocok!")
                else:
                    # Register new user
                    from utils.auth import register_user
                    success, message = register_user(new_username, new_password, full_name, role, department)
                    
                    if success:
                        st.success(f"Pendaftaran berhasil! {message}")
                        st.info("Silakan login dengan akun baru Anda.")
                    else:
                        st.error(f"Pendaftaran gagal: {message}")
    
    with info_tab:
        st.subheader("Tentang Sistem Lumbung Digital")
        
        st.markdown("""
                
        ### Fungsi Utama:
        - **Manajemen Lumbung**: Monitoring stok hasil pertanian di lumbung desa secara real-time
        - **Manajemen Petani**: Data petani dan lahan pertanian
        - **Manajemen Pedagang**: Data pedagang lokal dan lokasi distribusi
        - **Hasil Panen**: Pencatatan dan analisis hasil panen per musim
        - **Pemetaan Distribusi**: Jalur distribusi paling efisien ke pedagang lokal
        - **Forecasting**: Prediksi kebutuhan bibit dan pupuk berdasarkan data historis
        
        ### Cara Penggunaan:
        1. **Login**: Gunakan akun yang telah terdaftar atau daftar akun baru
        2. **Dashboard**: Lihat ringkasan stok hasil panen dan distribusi
        3. **Manajemen Lumbung**: Kelola stok di berbagai lumbung desa
        4. **Manajemen Petani**: Tambah dan kelola data petani
        5. **Manajemen Pedagang**: Kelola data pedagang lokal
        6. **Hasil Panen**: Catat dan analisis hasil panen
        7. **Pemetaan Distribusi**: Tentukan jalur distribusi paling efisien
        8. **Forecasting**: Prediksi kebutuhan bibit dan pupuk
        9. **Laporan**: Lihat laporan hasil panen dan distribusi
        
        ### Role Pengguna:
        - **Admin**: Memiliki akses penuh ke semua fitur
        - **Staff**: Dapat mengelola inventori dan data petani
        - **Manager**: Dapat melihat laporan dan approve distribusi
        
        ### Fitur Tambahan:
        - Notifikasi stok hasil panen rendah otomatis
        - Prediksi kebutuhan bibit dan pupuk berdasarkan AI
        - Grafik visualisasi data panen dan distribusi
        - Export laporan ke format Excel/PDF
        - Pemetaan rute distribusi paling efisien
        - Analisis musim panen dan kualitas hasil
        """)
        
        st.info("💡 **Tips**: Pastikan untuk selalu logout setelah selesai menggunakan aplikasi untuk menjaga keamanan data!")

# Dashboard page
def dashboard_page():
    st.title("Dashboard Sistem Lumbung Digital")
    
    # Get stock status
    stock_status = get_stock_status()
    
    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Hasil Panen", stock_status['total_items'])
    
    with col2:
        st.metric("Stok Lumbung Sehat", stock_status['healthy_stock'])
    
    with col3:
        st.metric("Stok Lumbung Rendah", stock_status['low_stock'])
    
    with col4:
        st.metric("Stok Lumbung Habis", stock_status['out_of_stock'])
    
    # Display low stock items
    st.subheader("Item dengan Stok Rendah")
    low_stock_items = get_items_low_stock()
    
    if not low_stock_items.empty:
        # Add progress bar for stock level
        low_stock_items['stock_percentage'] = (low_stock_items['current_stock'] / low_stock_items['min_stock']) * 100
        low_stock_items['stock_percentage'] = low_stock_items['stock_percentage'].clip(upper=100)
        
        for _, item in low_stock_items.iterrows():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{item['name']}** ({item['category']})")
                st.progress(int(item['stock_percentage']))
                
            with col2:
                st.write(f"Stok: **{item['current_stock']}** {item['unit']}")
                st.write(f"Min: **{item['min_stock']}** {item['unit']}")
    else:
        st.info("Tidak ada item dengan stok rendah.")
    
    # Recent transactions
    st.subheader("Transaksi Terbaru")
    transactions = get_recent_transactions(limit=5)
    
    if not transactions.empty:
        st.dataframe(transactions)
    else:
        st.info("Belum ada transaksi.")
    
    # Warehouse consumption
    st.subheader("Distribusi per Lumbung (30 Hari Terakhir)")
    warehouse_consumption = get_warehouse_consumption()
    
    if not warehouse_consumption.empty:
        st.bar_chart(warehouse_consumption.set_index('warehouse')['total_distribution'])
    else:
        st.info("Belum ada data distribusi lumbung.")
    
    # Top consumed items
    st.subheader("Hasil Panen Terbanyak (30 Hari Terakhir)")
    top_items = get_top_consumed_items(limit=5)
    
    if not top_items.empty:
        st.bar_chart(top_items.set_index('item_name')['total_consumption'])
    else:
        st.info("Belum ada data hasil panen.")

# Profile page
def profile_page():
    st.title("Profil Pengguna")
    
    # Get current user info
    user_id = st.session_state['user']['id']
    username = st.session_state['user']['username']
    current_name = st.session_state['user']['full_name']
    current_role = st.session_state['user']['role']
    current_department = st.session_state['user']['department']
    
    # Display current info
    st.subheader("Informasi Profil")
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Username", value=username, disabled=True)
        st.text_input("Role", value=current_role.upper(), disabled=True)
    
    with col2:
        st.text_input("Departemen/Klaster", value=current_department, disabled=True)
    
    st.markdown("---")
    
    # Update profile form
    st.subheader("Update Profil")
    
    with st.form("update_profile_form"):
        new_full_name = st.text_input("Nama Lengkap Baru", value=current_name)
        
        # Updated warehouse selection for agricultural system
        warehouses = [
            "Lumbung Desa Sentra Tani",
            "Lumbung Desa Tambakrejo", 
            "Lumbung Desa Ngadirejo",
            "Lumbung Desa Tlogosari",
            "Lumbung Desa Bandungrejo",
            "Lumbung Desa Purworejo",
            "Lumbung Desa Sumberagung",
            "Lumbung Desa Karanganyar"
        ]
        
        # Find current warehouse index
        try:
            current_dept_index = warehouses.index(current_department)
        except ValueError:
            current_dept_index = 0
            
        new_department = st.selectbox("Lumbung/Lokasi Baru", warehouses, index=current_dept_index)
        
        submit_profile = st.form_submit_button("Update Profil")
        
        if submit_profile:
            if new_full_name != current_name or new_department != current_department:
                try:
                    # Update user in MongoDB
                    success = update_user(user_id, {
                        "full_name": new_full_name,
                        "department": new_department
                    })
                    
                    if success:
                        # Update session state
                        st.session_state['user']['full_name'] = new_full_name
                        st.session_state['user']['department'] = new_department
                        
                        st.success("Profil berhasil diperbarui!")
                        st.rerun()
                    else:
                        st.error("Gagal memperbarui profil")
                        
                except Exception as e:
                    st.error(f"Gagal update profil: {str(e)}")
            else:
                st.info("Tidak ada perubahan yang dilakukan.")
    
    st.markdown("---")
    
    # Change password form
    st.subheader("Ganti Password")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Password Lama", type="password")
        new_password = st.text_input("Password Baru", type="password")
        confirm_password = st.text_input("Konfirmasi Password Baru", type="password")
        
        submit_password = st.form_submit_button("Ganti Password")
        
        if submit_password:
            if not all([current_password, new_password, confirm_password]):
                st.error("Semua field password harus diisi!")
            elif new_password != confirm_password:
                st.error("Password baru dan konfirmasi tidak cocok!")
            elif len(new_password) < 6:
                st.error("Password minimal 6 karakter!")
            else:
                try:
                    from utils.auth import verify_password, hash_password
                    
                    # Get current user from database
                    user_data = get_user_by_id(user_id)
                    if not user_data:
                        st.error("Pengguna tidak ditemukan")
                        return
                    
                    # Verify current password
                    if verify_password(user_data['password'], current_password):
                        # Update password
                        hashed_new_password = hash_password(new_password)
                        
                        success = update_user(user_id, {
                            "password": hashed_new_password
                        })
                        
                        if success:
                            st.success("Password berhasil diubah!")
                        else:
                            st.error("Gagal mengubah password")
                    else:
                        st.error("Password lama tidak sesuai!")
                        
                except Exception as e:
                    st.error(f"Gagal mengubah password: {str(e)}")

# Wrapper functions for page modules
def inventory_page():
    from pages.warehouse import app
    app()

def farmers_page():
    from pages.farmers import app
    app()

def merchants_page():
    from pages.merchants import app
    app()

def harvests_page():
    from pages.harvests import app
    app()

def distribution_page():
    from pages.distribution import app
    app()

def report_page():
    from pages.report import app
    app()

def forecast_page():
    from pages.forecast import app
    app()

# Main app function
def main():
    # Check if database is initialized
    if not st.session_state.get('db_initialized', False):
        st.error("Database initialization failed. Please check your MongoDB connection.")
        return
    
    if not st.session_state.get('authenticated', False):
        login_page()
    else:
        page = sidebar_nav()
        
        if page == "Dashboard":
            dashboard_page()
        elif page == "Profil Pengguna":
            profile_page()
        elif page == "Manajemen Lumbung":
            inventory_page()
        elif page == "Manajemen Petani":
            farmers_page()
        elif page == "Manajemen Pedagang":
            merchants_page()
        elif page == "Hasil Panen":
            harvests_page()
        elif page == "Pemetaan Distribusi":
            distribution_page()
        elif page == "Forecasting Kebutuhan":
            forecast_page()
        elif page == "Laporan":
            report_page()
        elif page == "Notifikasi":
            from utils.notifications import NotificationManager
            manager = NotificationManager()
            manager.display_notification_dashboard()
        elif page == "Analytics":
            from utils.analytics import InventoryAnalytics
            analytics = InventoryAnalytics()
            analytics.display_analytics_dashboard()
        elif page == "Manajemen Pengguna":
            if st.session_state['user']['role'] == 'admin':
                st.title("Manajemen Pengguna")
                st.write("Fitur manajemen pengguna akan segera tersedia...")
                
                # You can add user management functionality here
                from utils.auth import get_all_users
                
                users = get_all_users()
                if users:
                    st.subheader("Daftar Pengguna")
                    # Convert to DataFrame for better display
                    import pandas as pd
                    users_df = pd.DataFrame(users)
                    st.dataframe(users_df[['username', 'full_name', 'role', 'department', 'is_active']])
                else:
                    st.info("Tidak ada pengguna ditemukan")
            else:
                st.error("Anda tidak memiliki akses ke halaman ini!")

if __name__ == "__main__":
    main()