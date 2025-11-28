import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.auth_new import require_auth, require_role
from utils.sqlite_database import (
    get_farmers, 
    get_farmer_by_id,
    create_farmer,
    update_farmer,
    delete_farmer,
    get_harvests_by_season,
    get_database
)
import uuid

def app():
    require_auth()
    
    st.title("🌾 Manajemen Petani Desa")
    
    # Check if we're in editing mode
    if 'editing_farmer' in st.session_state:
        edit_farmer(st.session_state['editing_farmer'])
        return
    
    # Tabs for different farmer functions
    tab1, tab2, tab3, tab4 = st.tabs(["Daftar Petani", "Tambah Petani", "Statistik Petani", "Peta Petani"])
    
    with tab1:
        display_farmers()
    
    with tab2:
        add_farmer()
    
    with tab3:
        farmer_statistics()
    
    with tab4:
        farmer_map()

def display_farmers():
    st.subheader("📋 Daftar Petani")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location_filter = st.text_input("Filter berdasarkan lokasi", placeholder="Ketik nama desa...")
    
    with col2:
        crop_filter = st.selectbox("Filter berdasarkan komoditas", ["Semua", "Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah"])
    
    with col3:
        limit = st.number_input("Jumlah data", min_value=5, max_value=200, value=50)
    
    # Get farmers data
    farmers_df = get_farmers(location=location_filter if location_filter else None, limit=limit)
    
    # Apply crop filter if selected
    if crop_filter != "Semua":
        farmers_df = farmers_df[farmers_df['main_crop'].str.contains(crop_filter, case=False, na=False)]
    
    if not farmers_df.empty:
        # Display metrics
        col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
        
        with col_metrics1:
            st.metric("Total Petani", len(farmers_df))
        
        with col_metrics2:
            avg_land = farmers_df['land_area'].mean()
            st.metric("Rata-rata Lahan", f"{avg_land:.1f} Ha")
        
        with col_metrics3:
            active_farmers = len(farmers_df[farmers_df['is_active'] == 1])
            st.metric("Petani Aktif", active_farmers)
        
        # Display farmers in expandable cards
        st.subheader("👥 Detail Petani")
        
        for _, farmer in farmers_df.iterrows():
            with st.expander(f"🌾 {farmer.get('name', 'Nama Tidak Diketahui')} - {farmer.get('location', 'Lokasi Tidak Diketahui')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Nama:** {farmer.get('name', 'N/A')}")
                    st.write(f"**Lokasi:** {farmer.get('location', 'N/A')}")
                    st.write(f"**Luas Lahan:** {farmer.get('land_area', 0)} Ha")
                    st.write(f"**Komoditas Utama:** {farmer.get('main_crop', 'N/A')}")
                
                with col2:
                    st.write(f"**No. Telepon:** {farmer.get('phone', 'N/A')}")
                    st.write(f"**Email:** {farmer.get('email', 'N/A')}")
                    st.write(f"**Status:** {'🟢 Aktif' if farmer.get('is_active', 0) else '🔴 Tidak Aktif'}")
                    st.write(f"**Tanggal Bergabung:** {farmer.get('join_date', 'N/A')}")
                
                # Action buttons
                col_action1, col_action2 = st.columns(2)
                
                with col_action1:
                    if st.button(f"✏️ Edit {farmer.get('name')}", key=f"edit_{farmer['id']}"):
                        st.session_state['editing_farmer'] = farmer['id']
                        st.rerun()
                
                with col_action2:
                    if st.button(f"🗑️ Hapus {farmer.get('name')}", key=f"delete_{farmer['id']}"):
                        if st.session_state['user']['role'] == 'admin':
                            success = delete_farmer(farmer['id'])
                            if success:
                                st.success("✅ Petani berhasil dihapus!")
                                st.rerun()
                            else:
                                st.error("❌ Gagal menghapus petani")
                        else:
                            st.error("❌ Hanya admin yang dapat menghapus petani")
        
        # Display farmers table
        st.subheader("📊 Tabel Data Petani")
        
        # Prepare display dataframe
        display_df = farmers_df.copy()
        display_df['status'] = display_df['is_active'].apply(lambda x: 'Aktif' if x else 'Tidak Aktif')
        
        # Select columns to display
        display_columns = ['name', 'location', 'land_area', 'main_crop', 'phone', 'status']
        available_columns = [col for col in display_columns if col in display_df.columns]
        
        st.dataframe(
            display_df[available_columns].rename(columns={
                'name': 'Nama',
                'location': 'Lokasi',
                'land_area': 'Luas Lahan (Ha)',
                'main_crop': 'Komoditas Utama',
                'phone': 'Telepon',
                'status': 'Status'
            }),
            use_container_width=True
        )
        
    else:
        st.info("📭 Tidak ada data petani yang ditemukan dengan filter yang dipilih.")
        
        # Add sample data button for admin users
        if st.session_state['user']['role'] == 'admin':
            if st.button("📊 Tambah Data Sampel Petani", use_container_width=True):
                add_sample_farmers()

def add_farmer():
    st.subheader("➕ Tambah Petani Baru")
    
    with st.form("add_farmer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nama Petani*", placeholder="Contoh: Budi Santoso")
            location = st.text_input("Lokasi/Lahan*", placeholder="Contoh: Desa Sentra Tani")
            phone = st.text_input("No. Telepon", placeholder="Contoh: 08123456789")
            email = st.text_input("Email", placeholder="Contoh: budi@sentra.tani")
        
        with col2:
            land_area = st.number_input("Luas Lahan (Ha)*", min_value=0.1, step=0.1, value=1.0)
            main_crop = st.selectbox("Komoditas Utama*", ["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"])
            farming_experience = st.number_input("Pengalaman Bertani (Tahun)", min_value=0, step=1, value=5)
            join_date = st.date_input("Tanggal Bergabung", value=datetime.now())
        
        # Additional information
        st.subheader("📝 Informasi Tambahan")
        col3, col4 = st.columns(2)
        
        with col3:
            farming_type = st.selectbox("Jenis Pertanian", ["Organik", "Konvensional", "Hidroponik", "Lainnya"])
            irrigation_source = st.selectbox("Sumber Air", ["Sumur", "Sungai", "Hujan", "Irigasi", "Lainnya"])
        
        with col4:
            soil_type = st.selectbox("Jenis Tanah", ["Latosol", "Andosol", "Aluvial", "Regosol", "Lainnya"])
            harvest_frequency = st.selectbox("Frekuensi Panen per Tahun", ["1 kali", "2 kali", "3 kali", "4+ kali"])
        
        notes = st.text_area("Catatan", placeholder="Informasi tambahan tentang petani...")
        
        submit_farmer = st.form_submit_button("🌾 Tambah Petani", use_container_width=True)
        
        if submit_farmer:
            if name and location and land_area > 0 and main_crop:
                success, message = create_farmer(
                    name=name,
                    location=location,
                    phone=phone,
                    email=email,
                    land_area=land_area,
                    main_crop=main_crop,
                    farming_experience=farming_experience,
                    join_date=join_date.isoformat(),
                    farming_type=farming_type,
                    irrigation_source=irrigation_source,
                    soil_type=soil_type,
                    harvest_frequency=harvest_frequency,
                    notes=notes
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Mohon lengkapi field yang wajib diisi (ditandai *)!")

def edit_farmer(farmer_id):
    st.subheader(f"✏️ Edit Petani")
    
    # Get farmer data
    farmer = get_farmer_by_id(farmer_id)
    
    if not farmer:
        st.error("❌ Petani tidak ditemukan!")
        if st.button("Kembali"):
            del st.session_state['editing_farmer']
            st.rerun()
        return
    
    with st.form("edit_farmer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nama Petani*", value=farmer.get('name', ''))
            location = st.text_input("Lokasi/Lahan*", value=farmer.get('location', ''))
            phone = st.text_input("No. Telepon", value=farmer.get('phone', ''))
            email = st.text_input("Email", value=farmer.get('email', ''))
        
        with col2:
            land_area = st.number_input("Luas Lahan (Ha)*", min_value=0.1, step=0.1, value=float(farmer.get('land_area', 1.0)))
            main_crop = st.selectbox("Komoditas Utama*", ["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"], 
                                   index=["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"].index(farmer.get('main_crop', 'Beras')))
            farming_experience = st.number_input("Pengalaman Bertani (Tahun)", min_value=0, step=1, value=int(farmer.get('farming_experience', 5)))
            is_active = st.checkbox("Status Aktif", value=bool(farmer.get('is_active', 1)))
        
        # Additional information
        st.subheader("📝 Informasi Tambahan")
        col3, col4 = st.columns(2)
        
        with col3:
            farming_type = st.selectbox("Jenis Pertanian", ["Organik", "Konvensional", "Hidroponik", "Lainnya"],
                                       index=["Organik", "Konvensional", "Hidroponik", "Lainnya"].index(farmer.get('farming_type', 'Konvensional')))
            irrigation_source = st.selectbox("Sumber Air", ["Sumur", "Sungai", "Hujan", "Irigasi", "Lainnya"],
                                           index=["Sumur", "Sungai", "Hujan", "Irigasi", "Lainnya"].index(farmer.get('irrigation_source', 'Hujan')))
        
        with col4:
            soil_type = st.selectbox("Jenis Tanah", ["Latosol", "Andosol", "Aluvial", "Regosol", "Lainnya"],
                                    index=["Latosol", "Andosol", "Aluvial", "Regosol", "Lainnya"].index(farmer.get('soil_type', 'Latosol')))
            harvest_frequency = st.selectbox("Frekuensi Panen per Tahun", ["1 kali", "2 kali", "3 kali", "4+ kali"],
                                            index=["1 kali", "2 kali", "3 kali", "4+ kali"].index(farmer.get('harvest_frequency', '2 kali')))
        
        notes = st.text_area("Catatan", value=farmer.get('notes', ''), placeholder="Informasi tambahan tentang petani...")
        
        col_submit1, col_submit2 = st.columns(2)
        
        with col_submit1:
            submit_edit = st.form_submit_button("💾 Simpan Perubahan")
        
        with col_submit2:
            cancel_edit = st.form_submit_button("❌ Batal")
        
        if submit_edit:
            if name and location and land_area > 0 and main_crop:
                update_data = {
                    'name': name,
                    'location': location,
                    'phone': phone,
                    'email': email,
                    'land_area': land_area,
                    'main_crop': main_crop,
                    'farming_experience': farming_experience,
                    'is_active': 1 if is_active else 0,
                    'farming_type': farming_type,
                    'irrigation_source': irrigation_source,
                    'soil_type': soil_type,
                    'harvest_frequency': harvest_frequency,
                    'notes': notes,
                    'updated_at': datetime.now().isoformat()
                }
                
                success = update_farmer(farmer_id, update_data)
                
                if success:
                    st.success("✅ Data petani berhasil diupdate!")
                    del st.session_state['editing_farmer']
                    st.rerun()
                else:
                    st.error("❌ Gagal mengupdate data petani")
            else:
                st.error("❌ Mohon lengkapi field yang wajib diisi!")
        
        if cancel_edit:
            del st.session_state['editing_farmer']
            st.rerun()

def farmer_statistics():
    st.subheader("📊 Statistik Petani")
    
    # Get all farmers data
    farmers_df = get_farmers(limit=200)
    
    if not farmers_df.empty:
        # Overview metrics
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Total Petani", len(farmers_df))
        
        with col_stat2:
            total_land = farmers_df['land_area'].sum()
            st.metric("Total Lahan", f"{total_land:.1f} Ha")
        
        with col_stat3:
            active_farmers = len(farmers_df[farmers_df['is_active'] == 1])
            st.metric("Petani Aktif", active_farmers)
        
        with col_stat4:
            avg_experience = farmers_df['farming_experience'].mean()
            st.metric("Rata-rata Pengalaman", f"{avg_experience:.1f} Tahun")
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Main crop distribution
            crop_counts = farmers_df['main_crop'].value_counts()
            
            fig = px.pie(
                values=crop_counts.values, 
                names=crop_counts.index,
                title="Distribusi Komoditas Utama",
                color_discrete_sequence=px.colors.qualitative.Greens
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            # Land area distribution
            fig = px.histogram(
                farmers_df, 
                x='land_area',
                title="Distribusi Luas Lahan",
                nbins=10,
                color='land_area',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Location distribution
        st.subheader("📍 Distribusi Petani per Lokasi")
        
        location_counts = farmers_df['location'].value_counts().head(10)
        
        if not location_counts.empty:
            fig = px.bar(
                x=location_counts.values,
                y=location_counts.index,
                orientation='h',
                title="10 Lokasi dengan Petani Terbanyak",
                color=location_counts.values,
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Experience distribution
        st.subheader("📈 Distribusi Pengalaman Bertani")
        
        experience_ranges = pd.cut(farmers_df['farming_experience'], 
                                  bins=[0, 5, 10, 20, 50], 
                                  labels=['<5 Tahun', '5-10 Tahun', '10-20 Tahun', '>20 Tahun'])
        experience_counts = experience_ranges.value_counts()
        
        fig = px.bar(
            x=experience_counts.index,
            y=experience_counts.values,
            title="Distribusi Pengalaman Bertani",
            color=experience_counts.values,
            color_continuous_scale='Greens'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data petani untuk statistik.")

def farmer_map():
    st.subheader("🗺️ Peta Sebaran Petani")
    
    # Get all farmers data
    farmers_df = get_farmers(limit=200)
    
    if not farmers_df.empty:
        st.info("📍 Fitur peta akan segera tersedia. Saat ini menampilkan data lokasi dalam bentuk tabel.")
        
        # Location summary
        location_summary = farmers_df.groupby('location').agg({
            'name': 'count',
            'land_area': 'sum',
            'farming_experience': 'mean'
        }).rename(columns={
            'name': 'Jumlah Petani',
            'land_area': 'Total Lahan (Ha)',
            'farming_experience': 'Rata-rata Pengalaman (Tahun)'
        }).round(2)
        
        st.subheader("📍 Ringkasan per Lokasi")
        st.dataframe(location_summary, use_container_width=True)
        
        # Main crops per location
        st.subheader("🌾 Komoditas Utama per Lokasi")
        
        location_crops = farmers_df.groupby(['location', 'main_crop']).size().unstack(fill_value=0)
        st.dataframe(location_crops, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data petani untuk peta sebaran.")

def add_sample_farmers():
    """Add sample farmer data for testing"""
    sample_farmers = [
        {
            'name': 'Budi Santoso',
            'location': 'Desa Sentra Tani',
            'phone': '08123456789',
            'email': 'budi@sentra.tani',
            'land_area': 2.5,
            'main_crop': 'Beras',
            'farming_experience': 10,
            'farming_type': 'Organik',
            'irrigation_source': 'Irigasi',
            'soil_type': 'Latosol',
            'harvest_frequency': '2 kali'
        },
        {
            'name': 'Siti Nurjanah',
            'location': 'Desa Tambakrejo',
            'phone': '08234567890',
            'email': 'siti@tambakrejo.tani',
            'land_area': 1.8,
            'main_crop': 'Jagung',
            'farming_experience': 7,
            'farming_type': 'Konvensional',
            'irrigation_source': 'Hujan',
            'soil_type': 'Andosol',
            'harvest_frequency': '2 kali'
        },
        {
            'name': 'Ahmad Fauzi',
            'location': 'Desa Ngadirejo',
            'phone': '08345678901',
            'email': 'ahmad@ngadirejo.tani',
            'land_area': 3.2,
            'main_crop': 'Kacang-kacangan',
            'farming_experience': 15,
            'farming_type': 'Organik',
            'irrigation_source': 'Sumur',
            'soil_type': 'Aluvial',
            'harvest_frequency': '3 kali'
        }
    ]
    
    for farmer_data in sample_farmers:
        create_farmer(
            name=farmer_data['name'],
            location=farmer_data['location'],
            phone=farmer_data['phone'],
            email=farmer_data['email'],
            land_area=farmer_data['land_area'],
            main_crop=farmer_data['main_crop'],
            farming_experience=farmer_data['farming_experience'],
            join_date=datetime.now().isoformat(),
            farming_type=farmer_data['farming_type'],
            irrigation_source=farmer_data['irrigation_source'],
            soil_type=farmer_data['soil_type'],
            harvest_frequency=farmer_data['harvest_frequency']
        )
    
    st.success("✅ Data sampel petani berhasil ditambahkan!")
    st.rerun()

if __name__ == "__main__":
    app()
