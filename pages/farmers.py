import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.database import MongoDBConnection, get_farmers
from datetime import datetime
from bson import ObjectId

def app():
    require_auth()
    
    st.title("Manajemen Petani")
    
    # Tabs for different farmer functions
    tab1, tab2, tab3 = st.tabs(["Daftar Petani", "Tambah Petani", "Statistik Petani"])
    
    with tab1:
        display_farmers()
    
    with tab2:
        add_farmer()
    
    with tab3:
        farmer_statistics()

def display_farmers():
    st.subheader("Daftar Petani")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        location_filter = st.text_input("Filter berdasarkan lokasi", "")
    
    with col2:
        limit = st.number_input("Jumlah data", min_value=5, max_value=200, value=50)
    
    # Get farmers data
    farmers_df = get_farmers(location=location_filter if location_filter else None, limit=limit)
    
    if not farmers_df.empty:
        # Display farmers in a nice format
        for _, farmer in farmers_df.iterrows():
            with st.expander(f"🌾 {farmer.get('name', 'Nama Tidak Diketahui')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Lokasi:** {farmer.get('location', 'Tidak diketahui')}")
                    st.write(f"**Luas Lahan:** {farmer.get('land_area', 0)} hektar")
                    st.write(f"**Jenis Tanaman Utama:** {farmer.get('primary_crop', 'Tidak diketahui')}")
                
                with col2:
                    st.write(f"**No. Telepon:** {farmer.get('phone', 'Tidak tersedia')}")
                    st.write(f"**Email:** {farmer.get('email', 'Tidak tersedia')}")
                    st.write(f"**Tanggal Bergabung:** {farmer.get('join_date', 'Tidak diketahui')}")
                
                st.write(f"**Alamat:** {farmer.get('address', 'Tidak diketahui')}")
                st.write(f"**Catatan:** {farmer.get('notes', 'Tidak ada catatan')}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Edit", key=f"edit_{farmer['_id']}"):
                        st.session_state['editing_farmer'] = farmer['_id']
                        st.rerun()
                with col2:
                    if st.button("Hapus", key=f"delete_{farmer['_id']}"):
                        delete_farmer(farmer['_id'])
                with col3:
                    if st.button("Lihat Hasil Panen", key=f"harvest_{farmer['_id']}"):
                        st.session_state['viewing_farmer_harvests'] = farmer['_id']
                        st.rerun()
    else:
        st.info("Belum ada data petani. Silakan tambahkan petani baru.")

def add_farmer():
    st.subheader("Tambah Petani Baru")
    
    with st.form("add_farmer_form"):
        name = st.text_input("Nama Petani*", placeholder="Masukkan nama lengkap petani")
        location = st.text_input("Lokasi/Lokasi Lahan*", placeholder="Contoh: Tambakrejo, Ngadirejo, dll")
        
        col1, col2 = st.columns(2)
        
        with col1:
            land_area = st.number_input("Luas Lahan (hektar)*", min_value=0.1, max_value=1000.0, value=1.0, step=0.1)
            primary_crop = st.text_input("Jenis Tanaman Utama*", placeholder="Contoh: Padi, Jagung, Kedelai")
            phone = st.text_input("No. Telepon", placeholder="0812xxxxxx")
        
        with col2:
            email = st.text_input("Email", placeholder="petani@email.com")
            address = st.text_area("Alamat Lengkap", placeholder="Jl. Nama Jalan, RT/RW, Desa, Kecamatan")
            notes = st.text_area("Catatan Tambahan", placeholder="Informasi tambahan tentang petani")
        
        submit = st.form_submit_button("Tambah Petani", use_container_width=True)
        
        if submit:
            if not name or not location or not primary_crop:
                st.error("Nama petani, lokasi, dan jenis tanaman utama harus diisi!")
            else:
                try:
                    db = MongoDBConnection.get_database()
                    
                    farmer_data = {
                        "name": name,
                        "location": location,
                        "land_area": land_area,
                        "primary_crop": primary_crop,
                        "phone": phone,
                        "email": email,
                        "address": address,
                        "notes": notes,
                        "join_date": datetime.now(),
                        "created_by": ObjectId(st.session_state['user']['id']),
                        "is_active": True
                    }
                    
                    result = db.farmers.insert_one(farmer_data)
                    
                    if result.inserted_id:
                        st.success(f"Petani {name} berhasil ditambahkan!")
                        st.balloons()
                    else:
                        st.error("Gagal menambahkan petani.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

def farmer_statistics():
    st.subheader("Statistik Petani")
    
    # Get statistics
    db = MongoDBConnection.get_database()
    
    # Total farmers
    total_farmers = db.farmers.count_documents({})
    
    # Farmers by location
    location_stats = list(db.farmers.aggregate([
        {"$group": {"_id": "$location", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))
    
    # Farmers by primary crop
    crop_stats = list(db.farmers.aggregate([
        {"$group": {"_id": "$primary_crop", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Petani", total_farmers)
    
    with col2:
        if location_stats:
            top_location = location_stats[0]
            st.metric("Lokasi Terbanyak", f"{top_location['_id']} ({top_location['count']} petani)")
        else:
            st.metric("Lokasi Terbanyak", "Belum ada data")
    
    with col3:
        if crop_stats:
            top_crop = crop_stats[0]
            st.metric("Tanaman Utama Terbanyak", f"{top_crop['_id']} ({top_crop['count']} petani)")
        else:
            st.metric("Tanaman Utama Terbanyak", "Belum ada data")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if location_stats:
            st.subheader("Petani berdasarkan Lokasi")
            location_df = pd.DataFrame(location_stats)
            location_df.columns = ['Lokasi', 'Jumlah']
            st.bar_chart(location_df.set_index('Lokasi')['Jumlah'])
    
    with col2:
        if crop_stats:
            st.subheader("Petani berdasarkan Tanaman Utama")
            crop_df = pd.DataFrame(crop_stats)
            crop_df.columns = ['Tanaman', 'Jumlah']
            st.bar_chart(crop_df.set_index('Tanaman')['Jumlah'])

def delete_farmer(farmer_id):
    """Delete farmer from database"""
    try:
        db = MongoDBConnection.get_database()
        result = db.farmers.delete_one({"_id": ObjectId(farmer_id)})
        
        if result.deleted_count > 0:
            st.success("Petani berhasil dihapus!")
            st.rerun()
        else:
            st.error("Gagal menghapus petani.")
    except Exception as e:
        st.error(f"Error menghapus petani: {e}")