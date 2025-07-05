import streamlit as st
import pandas as pd
from utils.auth import login_user, logout_user
from utils.database import get_db_connection, get_items_low_stock, get_recent_transactions
from utils.helpers import get_stock_status, get_department_consumption, get_top_consumed_items
import os

# Set page configuration
st.set_page_config(
    page_title="Sistem Manajemen Inventaris Rumah Sakit",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Sidebar navigation
def sidebar_nav():
    st.sidebar.title("Navigasi")
    
    if st.session_state.get('authenticated', False):
        user = st.session_state['user']
        st.sidebar.write(f"Selamat datang, **{user['full_name']}**!")
        st.sidebar.write(f"Role: {user['role']}")
        
        # Navigation links
        page = st.sidebar.radio(
            "Pilih Halaman:",
            ["Dashboard", "Inventaris", "Transfer Barang", "Permintaan Barang", "Laporan", "Prediksi", "Pengaturan"]
        )
        # In the sidebar_nav function
        if st.sidebar.button("Logout"):
            logout_user()
            st.rerun()  # Changed from st.experimental_rerun()
            
        return page
    return None

# Login page
def login_page():
    st.title("Login Sistem Manajemen Inventaris")
    
    # Create tabs for login and registration
    login_tab, register_tab = st.tabs(["Login", "Daftar Baru"])
    
    with login_tab:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image("https://img.freepik.com/free-vector/hospital-logo-design-vector-medical-cross_53876-136743.jpg", width=300)
            
        with col2:
            st.subheader("Silakan Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login"):
                # In the login_page function
                if login_user(username, password):
                    st.success("Login berhasil!")
                    st.rerun()  # Changed from st.experimental_rerun()
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
            role = "staff"
            
            # Department selection
            from utils.database import get_db_connection
            conn = get_db_connection()
            departments = pd.read_sql_query("SELECT id, name FROM departments ORDER BY name", conn)
            conn.close()
            
            if not departments.empty:
                department = st.selectbox("Departemen", departments['name'].tolist())
                dept_id = departments[departments['name'] == department]['id'].iloc[0]
            else:
                department = st.text_input("Departemen")
                dept_id = None
            
            submit_button = st.form_submit_button("Daftar")
            
            if submit_button:
                if not full_name or not new_username or not new_password:
                    st.error("Semua field harus diisi!")
                elif new_password != confirm_password:
                    st.error("Password dan konfirmasi password tidak cocok!")
                else:
                    # Register new user
                    from utils.auth import register_user
                    success, message = register_user(new_username, new_password, full_name, role, dept_id)
                    
                    if success:
                        st.success(f"Pendaftaran berhasil! {message}")
                        st.info("Silakan login dengan akun baru Anda.")
                    else:
                        st.error(f"Pendaftaran gagal: {message}")

# Dashboard page
def dashboard_page():
    st.title("Dashboard Inventaris Rumah Sakit")
    
    # Get stock status
    stock_status = get_stock_status()
    
    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Item", stock_status['total_items'])
    
    with col2:
        st.metric("Stok Sehat", stock_status['healthy_stock'])
    
    with col3:
        st.metric("Stok Rendah", stock_status['low_stock'])
    
    with col4:
        st.metric("Stok Habis", stock_status['out_of_stock'])
    
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
    
    # Department consumption
    st.subheader("Konsumsi per Departemen (30 Hari Terakhir)")
    dept_consumption = get_department_consumption()
    
    if not dept_consumption.empty:
        st.bar_chart(dept_consumption.set_index('department')['total_consumption'])
    else:
        st.info("Belum ada data konsumsi departemen.")
    
    # Top consumed items
    st.subheader("Item Paling Banyak Digunakan (30 Hari Terakhir)")
    top_items = get_top_consumed_items(limit=5)
    
    if not top_items.empty:
        st.bar_chart(top_items.set_index('item_name')['total_consumption'])
    else:
        st.info("Belum ada data konsumsi item.")

# Main app
def main():
    if not st.session_state.get('authenticated', False):
        login_page()
    else:
        page = sidebar_nav()
        
        if page == "Dashboard":
            dashboard_page()
        elif page == "Inventaris":
            st.title("Manajemen Inventaris")
            st.write("Halaman ini akan menampilkan daftar inventaris dan memungkinkan pengguna untuk mengelola stok.")
        elif page == "Transfer Barang":
            st.title("Transfer Barang")
            st.write("Halaman ini akan menangani transfer barang antar departemen.")
        elif page == "Permintaan Barang":
            st.title("Permintaan Barang")
            st.write("Halaman ini akan menangani permintaan barang dari departemen.")
        elif page == "Laporan":
            st.title("Laporan")
            st.write("Halaman ini akan menampilkan berbagai laporan inventaris.")
        elif page == "Prediksi":
            st.title("Prediksi Kebutuhan")
            st.write("Halaman ini akan menampilkan prediksi kebutuhan barang di masa depan.")
        elif page == "Pengaturan":
            st.title("Pengaturan")
            st.write("Halaman ini akan memungkinkan pengguna untuk mengubah pengaturan aplikasi.")

if __name__ == "__main__":
    main()