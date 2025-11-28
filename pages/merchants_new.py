import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.auth_new import require_auth, require_role
from utils.sqlite_database import (
    get_merchants, 
    get_merchant_by_id,
    create_merchant,
    update_merchant,
    delete_merchant,
    get_database
)
import uuid

def app():
    require_auth()
    
    st.title("🏪 Manajemen Pedagang Desa")
    
    # Check if we're in editing mode
    if 'editing_merchant' in st.session_state:
        edit_merchant(st.session_state['editing_merchant'])
        return
    
    # Tabs for different merchant functions
    tab1, tab2, tab3, tab4 = st.tabs(["Daftar Pedagang", "Tambah Pedagang", "Statistik Pedagang", "Peta Pedagang"])
    
    with tab1:
        display_merchants()
    
    with tab2:
        add_merchant()
    
    with tab3:
        merchant_statistics()
    
    with tab4:
        merchant_map()

def display_merchants():
    st.subheader("📋 Daftar Pedagang")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location_filter = st.text_input("Filter berdasarkan lokasi", placeholder="Ketik nama desa...")
    
    with col2:
        type_filter = st.selectbox("Filter berdasarkan tipe", ["Semua", "Pengecer", "Grosir", "Restoran", "Warung", "Pasar"])
    
    with col3:
        limit = st.number_input("Jumlah data", min_value=5, max_value=200, value=50)
    
    # Get merchants data
    merchants_df = get_merchants(merchant_type=type_filter if type_filter != "Semua" else None, 
                                location=location_filter if location_filter else None, 
                                limit=limit)
    
    if not merchants_df.empty:
        # Display metrics
        col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
        
        with col_metrics1:
            st.metric("Total Pedagang", len(merchants_df))
        
        with col_metrics2:
            active_merchants = len(merchants_df[merchants_df['is_active'] == 1])
            st.metric("Pedagang Aktif", active_merchants)
        
        with col_metrics3:
            unique_locations = merchants_df['location'].nunique()
            st.metric("Lokasi Unik", unique_locations)
        
        # Display merchants in expandable cards
        st.subheader("👥 Detail Pedagang")
        
        for _, merchant in merchants_df.iterrows():
            with st.expander(f"🏪 {merchant.get('name', 'Nama Tidak Diketahui')} - {merchant.get('location', 'Lokasi Tidak Diketahui')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Nama:** {merchant.get('name', 'N/A')}")
                    st.write(f"**Lokasi:** {merchant.get('location', 'N/A')}")
                    st.write(f"**Tipe:** {merchant.get('type', 'N/A')}")
                    st.write(f"**No. Telepon:** {merchant.get('phone', 'N/A')}")
                
                with col2:
                    st.write(f"**Email:** {merchant.get('email', 'N/A')}")
                    st.write(f"**Status:** {'🟢 Aktif' if merchant.get('is_active', 0) else '🔴 Tidak Aktif'}")
                    st.write(f"**Tanggal Bergabung:** {merchant.get('join_date', 'N/A')}")
                    st.write(f"**Izin Usaha:** {merchant.get('business_license', 'N/A')}")
                
                # Action buttons
                col_action1, col_action2 = st.columns(2)
                
                with col_action1:
                    if st.button(f"✏️ Edit {merchant.get('name')}", key=f"edit_{merchant['id']}"):
                        st.session_state['editing_merchant'] = merchant['id']
                        st.rerun()
                
                with col_action2:
                    if st.button(f"🗑️ Hapus {merchant.get('name')}", key=f"delete_{merchant['id']}"):
                        if st.session_state['user']['role'] == 'admin':
                            success = delete_merchant(merchant['id'])
                            if success:
                                st.success("✅ Pedagang berhasil dihapus!")
                                st.rerun()
                            else:
                                st.error("❌ Gagal menghapus pedagang")
                        else:
                            st.error("❌ Hanya admin yang dapat menghapus pedagang")
        
        # Display merchants table
        st.subheader("📊 Tabel Data Pedagang")
        
        # Prepare display dataframe
        display_df = merchants_df.copy()
        display_df['status'] = display_df['is_active'].apply(lambda x: 'Aktif' if x else 'Tidak Aktif')
        
        # Select columns to display
        display_columns = ['name', 'location', 'type', 'phone', 'status']
        available_columns = [col for col in display_columns if col in display_df.columns]
        
        st.dataframe(
            display_df[available_columns].rename(columns={
                'name': 'Nama',
                'location': 'Lokasi',
                'type': 'Tipe',
                'phone': 'Telepon',
                'status': 'Status'
            }),
            use_container_width=True
        )
        
    else:
        st.info("📭 Tidak ada data pedagang yang ditemukan dengan filter yang dipilih.")
        
        # Add sample data button for admin users
        if st.session_state['user']['role'] == 'admin':
            if st.button("📊 Tambah Data Sampel Pedagang", use_container_width=True):
                add_sample_merchants()

def add_merchant():
    st.subheader("➕ Tambah Pedagang Baru")
    
    with st.form("add_merchant_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nama Pedagang*", placeholder="Contoh: Warung Makmur")
            location = st.text_input("Lokasi*", placeholder="Contoh: Desa Sentra Tani")
            phone = st.text_input("No. Telepon", placeholder="Contoh: 08123456789")
            email = st.text_input("Email", placeholder="Contoh: warung@makmur.com")
        
        with col2:
            merchant_type = st.selectbox("Tipe Pedagang*", ["Pengecer", "Grosir", "Restoran", "Warung", "Pasar", "Lainnya"])
            business_license = st.text_input("Nomor Izin Usaha", placeholder="Contoh: IU-123456789")
            join_date = st.date_input("Tanggal Bergabung", value=datetime.now())
        
        # Additional information
        st.subheader("📝 Informasi Tambahan")
        
        col3, col4 = st.columns(2)
        
        with col3:
            business_hours = st.text_input("Jam Operasional", placeholder="Contoh: 08:00 - 21:00")
            payment_methods = st.text_input("Metode Pembayaran", placeholder="Contoh: Tunai, Transfer, E-Wallet")
        
        with col4:
            delivery_service = st.selectbox("Layanan Pengiriman", ["Tersedia", "Tidak Tersedia"])
            product_categories = st.text_input("Kategori Produk", placeholder="Contoh: Sembako, Sayuran, Buah")
        
        notes = st.text_area("Catatan", placeholder="Informasi tambahan tentang pedagang...")
        
        submit_merchant = st.form_submit_button("🏪 Tambah Pedagang", use_container_width=True)
        
        if submit_merchant:
            if name and location and merchant_type:
                success, message = create_merchant(
                    name=name,
                    location=location,
                    merchant_type=merchant_type,
                    phone=phone,
                    email=email,
                    business_license=business_license,
                    join_date=join_date.isoformat(),
                    notes=f"{notes}\nJam Operasional: {business_hours}\nMetode Pembayaran: {payment_methods}\nLayanan Pengiriman: {delivery_service}\nKategori Produk: {product_categories}"
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Mohon lengkapi field yang wajib diisi (ditandai *)!")

def edit_merchant(merchant_id):
    st.subheader(f"✏️ Edit Pedagang")
    
    # Get merchant data
    merchant = get_merchant_by_id(merchant_id)
    
    if not merchant:
        st.error("❌ Pedagang tidak ditemukan!")
        if st.button("Kembali"):
            del st.session_state['editing_merchant']
            st.rerun()
        return
    
    with st.form("edit_merchant_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nama Pedagang*", value=merchant.get('name', ''))
            location = st.text_input("Lokasi*", value=merchant.get('location', ''))
            phone = st.text_input("No. Telepon", value=merchant.get('phone', ''))
            email = st.text_input("Email", value=merchant.get('email', ''))
        
        with col2:
            merchant_type = st.selectbox("Tipe Pedagang*", ["Pengecer", "Grosir", "Restoran", "Warung", "Pasar", "Lainnya"],
                                        index=["Pengecer", "Grosir", "Restoran", "Warung", "Pasar", "Lainnya"].index(merchant.get('type', 'Pengecer')))
            business_license = st.text_input("Nomor Izin Usaha", value=merchant.get('business_license', ''))
            is_active = st.checkbox("Status Aktif", value=bool(merchant.get('is_active', 1)))
        
        # Additional information
        st.subheader("📝 Informasi Tambahan")
        
        notes = st.text_area("Catatan", value=merchant.get('notes', ''), placeholder="Informasi tambahan tentang pedagang...")
        
        col_submit1, col_submit2 = st.columns(2)
        
        with col_submit1:
            submit_edit = st.form_submit_button("💾 Simpan Perubahan")
        
        with col_submit2:
            cancel_edit = st.form_submit_button("❌ Batal")
        
        if submit_edit:
            if name and location and merchant_type:
                update_data = {
                    'name': name,
                    'location': location,
                    'phone': phone,
                    'email': email,
                    'type': merchant_type,
                    'business_license': business_license,
                    'is_active': 1 if is_active else 0,
                    'notes': notes,
                    'updated_at': datetime.now().isoformat()
                }
                
                success = update_merchant(merchant_id, update_data)
                
                if success:
                    st.success("✅ Data pedagang berhasil diupdate!")
                    del st.session_state['editing_merchant']
                    st.rerun()
                else:
                    st.error("❌ Gagal mengupdate data pedagang")
            else:
                st.error("❌ Mohon lengkapi field yang wajib diisi!")
        
        if cancel_edit:
            del st.session_state['editing_merchant']
            st.rerun()

def merchant_statistics():
    st.subheader("📊 Statistik Pedagang")
    
    # Get all merchants data
    merchants_df = get_merchants(limit=200)
    
    if not merchants_df.empty:
        # Overview metrics
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Total Pedagang", len(merchants_df))
        
        with col_stat2:
            active_merchants = len(merchants_df[merchants_df['is_active'] == 1])
            st.metric("Pedagang Aktif", active_merchants)
        
        with col_stat3:
            unique_locations = merchants_df['location'].nunique()
            st.metric("Lokasi Unik", unique_locations)
        
        with col_stat4:
            new_merchants = len(merchants_df[pd.to_datetime(merchants_df['join_date'], errors='coerce') >= datetime.now() - timedelta(days=30)])
            st.metric("Pedagang Baru (30 hari)", new_merchants)
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Merchant type distribution
            type_counts = merchants_df['type'].value_counts()
            
            fig = px.pie(
                values=type_counts.values, 
                names=type_counts.index,
                title="Distribusi Tipe Pedagang",
                color_discrete_sequence=px.colors.qualitative.Blues
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            # Location distribution
            location_counts = merchants_df['location'].value_counts().head(10)
            
            fig = px.bar(
                x=location_counts.values,
                y=location_counts.index,
                orientation='h',
                title="10 Lokasi dengan Pedagang Terbanyak",
                color=location_counts.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Join date trends
        st.subheader("📈 Tren Pendaftaran Pedagang")
        
        merchants_df['join_date_dt'] = pd.to_datetime(merchants_df['join_date'], errors='coerce')
        merchants_df['join_month'] = merchants_df['join_date_dt'].dt.to_period('M')
        
        monthly_counts = merchants_df.groupby('join_month').size().reset_index(name='count')
        monthly_counts['join_month'] = monthly_counts['join_month'].dt.to_timestamp()
        
        if not monthly_counts.empty:
            fig = px.line(
                monthly_counts, 
                x='join_month', 
                y='count',
                title="Tren Pendaftaran Pedagang per Bulan",
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Active vs Inactive
        st.subheader("🟢 Status Pedagang")
        
        status_counts = merchants_df['is_active'].value_counts()
        status_labels = ['Aktif', 'Tidak Aktif']
        status_values = [status_counts.get(1, 0), status_counts.get(0, 0)]
        
        fig = px.pie(
            values=status_values, 
            names=status_labels,
            title="Status Aktivasi Pedagang",
            color_discrete_map={"Aktif": "green", "Tidak Aktif": "red"}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data pedagang untuk statistik.")

def merchant_map():
    st.subheader("🗺️ Peta Sebaran Pedagang")
    
    # Get all merchants data
    merchants_df = get_merchants(limit=200)
    
    if not merchants_df.empty:
        st.info("📍 Fitur peta akan segera tersedia. Saat ini menampilkan data lokasi dalam bentuk tabel.")
        
        # Location summary
        location_summary = merchants_df.groupby('location').agg({
            'name': 'count',
            'type': lambda x: ', '.join(x.unique()),
            'is_active': lambda x: f"{x.sum()}/{len(x)} aktif"
        }).rename(columns={
            'name': 'Jumlah Pedagang',
            'type': 'Tipe Pedagang',
            'is_active': 'Status Aktivasi'
        })
        
        st.subheader("📍 Ringkasan per Lokasi")
        st.dataframe(location_summary, use_container_width=True)
        
        # Merchant types per location
        st.subheader("🏪 Tipe Pedagang per Lokasi")
        
        location_types = merchants_df.groupby(['location', 'type']).size().unstack(fill_value=0)
        st.dataframe(location_types, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data pedagang untuk peta sebaran.")

def add_sample_merchants():
    """Add sample merchant data for testing"""
    sample_merchants = [
        {
            'name': 'Warung Makmur',
            'location': 'Desa Sentra Tani',
            'merchant_type': 'Pengecer',
            'phone': '08123456789',
            'email': 'warung@makmur.com',
            'business_license': 'IU-123456789'
        },
        {
            'name': 'Toko Sembako Jaya',
            'location': 'Desa Tambakrejo',
            'merchant_type': 'Grosir',
            'phone': '08234567890',
            'email': 'sembako@jaya.com',
            'business_license': 'IU-987654321'
        },
        {
            'name': 'Restoran Desa',
            'location': 'Desa Ngadirejo',
            'merchant_type': 'Restoran',
            'phone': '08345678901',
            'email': 'resto@desa.com',
            'business_license': 'IU-456789123'
        }
    ]
    
    for merchant_data in sample_merchants:
        create_merchant(
            name=merchant_data['name'],
            location=merchant_data['location'],
            merchant_type=merchant_data['merchant_type'],
            phone=merchant_data['phone'],
            email=merchant_data['email'],
            business_license=merchant_data['business_license'],
            join_date=datetime.now().isoformat()
        )
    
    st.success("✅ Data sampel pedagang berhasil ditambahkan!")
    st.rerun()

if __name__ == "__main__":
    app()
