import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.database import MongoDBConnection, get_merchants
from utils.geocoding import get_coordinates_from_address
from datetime import datetime
from bson import ObjectId

def app():
    require_auth()
    
    st.title("Manajemen Pedagang Lokal")
    
    # Check if we're in editing mode
    if 'editing_merchant' in st.session_state:
        edit_merchant(st.session_state['editing_merchant'])
        return
    
    # Tabs for different merchant functions
    tab1, tab2, tab3 = st.tabs(["Daftar Pedagang", "Tambah Pedagang", "Statistik Pedagang"])
    
    with tab1:
        display_merchants()
    
    with tab2:
        add_merchant()
    
    with tab3:
        merchant_statistics()

def display_merchants():
    st.subheader("Daftar Pedagang Lokal")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        merchant_type_filter = st.selectbox("Filter berdasarkan Tipe", ["Semua", "Pengecer", "Grosir", "Pasar Tradisional", "Toko Modern"])
    
    with col2:
        location_filter = st.text_input("Filter berdasarkan lokasi", "")
    
    with col3:
        limit = st.number_input("Jumlah data", min_value=5, max_value=200, value=50)
    
    # Get merchants data
    merchant_type = None if merchant_type_filter == "Semua" else merchant_type_filter
    merchants_df = get_merchants(merchant_type=merchant_type, location=location_filter if location_filter else None, limit=limit)
    
    if not merchants_df.empty:
        # Display merchants in a nice format
        for _, merchant in merchants_df.iterrows():
            with st.expander(f"🏪 {merchant.get('name', 'Nama Tidak Diketahui')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Tipe:** {merchant.get('type', 'Tidak diketahui')}")
                    st.write(f"**Lokasi:** {merchant.get('location', 'Tidak diketahui')}")
                    st.write(f"**Alamat:** {merchant.get('address', 'Tidak diketahui')}")
                
                with col2:
                    st.write(f"**No. Telepon:** {merchant.get('phone', 'Tidak tersedia')}")
                    st.write(f"**Email:** {merchant.get('email', 'Tidak tersedia')}")
                    st.write(f"**Kapasitas:** {merchant.get('capacity', 'Tidak diketahui')}")
                
                # Display coordinates if available
                if 'coordinates' in merchant and merchant['coordinates']:
                    coords = merchant['coordinates']
                    source = coords.get('source', 'manual')
                    source_icon = '🗺️' if source == 'google_maps' else '✏️'
                    st.write(f"**Koordinat Lokasi:** {coords['lat']:.6f}, {coords['lng']:.6f} {source_icon} ({source.replace('_', ' ').title()})")
                
                st.write(f"**Catatan:** {merchant.get('notes', 'Tidak ada catatan')}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Edit", key=f"edit_{merchant['_id']}"):
                        st.session_state['editing_merchant'] = merchant['_id']
                        st.rerun()
                with col2:
                    if st.button("Hapus", key=f"delete_{merchant['_id']}"):
                        delete_merchant(merchant['_id'])
                with col3:
                    if st.button("Lihat Rute", key=f"route_{merchant['_id']}"):
                        st.session_state['viewing_merchant_routes'] = merchant['_id']
                        st.rerun()
    else:
        st.info("Belum ada data pedagang. Silakan tambahkan pedagang baru.")

def add_merchant():
    st.subheader("Tambah Pedagang Baru")
    
    # Initialize session state for coordinate extraction
    if 'merchant_coordinates_extracted' not in st.session_state:
        st.session_state.merchant_coordinates_extracted = False
    if 'merchant_extracted_coordinates' not in st.session_state:
        st.session_state.merchant_extracted_coordinates = None
    
    with st.form("add_merchant_form"):
        name = st.text_input("Nama Pedagang*", placeholder="Masukkan nama pedagang")
        
        col1, col2 = st.columns(2)
        
        with col1:
            merchant_type = st.selectbox("Tipe Pedagang*", ["Pengecer", "Grosir", "Pasar Tradisional", "Toko Modern"])
            location = st.text_input("Lokasi*", placeholder="Contoh: Pusat Pasar, Desa Tambakrejo")
            phone = st.text_input("No. Telepon", placeholder="0812xxxxxx")
        
        with col2:
            email = st.text_input("Email", placeholder="pedagang@email.com")
            capacity = st.text_input("Kapasitas", placeholder="Contoh: 100 kg/hari, 50 paket/hari")
        
        # Coordinate extraction section
        st.write("### Ekstraksi Koordinat Lokasi")
        col_addr1, col_addr2 = st.columns([3, 1])
        with col_addr1:
            address = st.text_area("Alamat Lengkap untuk Koordinat*", 
                                 placeholder="Jl. Nama Jalan, RT/RW, Desa, Kecamatan, Kabupaten",
                                 help="Alamat lengkap akan digunakan untuk mengekstrak koordinat lokasi menggunakan Google Maps")
        with col_addr2:
            st.write("&nbsp;")
            extract_coords = st.form_submit_button("🗺️ Ekstrak Koordinat", use_container_width=True)
        
        # Extract coordinates when button is clicked
        if extract_coords:
            if not address:
                st.error("Alamat lengkap harus diisi untuk ekstraksi koordinat!")
            else:
                with st.spinner("Mengekstrak koordinat dari Google Maps..."):
                    try:
                        coordinates = get_coordinates_from_address(address, location)
                        if coordinates:
                            st.session_state.merchant_coordinates_extracted = True
                            st.session_state.merchant_extracted_coordinates = coordinates
                            st.success(f"✅ Koordinat berhasil diekstrak: {coordinates['lat']:.6f}, {coordinates['lng']:.6f}")
                        else:
                            st.warning("⚠️ Tidak dapat menemukan koordinat untuk alamat tersebut. Silakan periksa alamat atau tambahkan koordinat secara manual.")
                    except Exception as e:
                        st.error(f"Error saat ekstraksi koordinat: {e}")
        
        # Display extracted coordinates
        if st.session_state.merchant_coordinates_extracted and st.session_state.merchant_extracted_coordinates:
            coords = st.session_state.merchant_extracted_coordinates
            col_lat, col_lng = st.columns(2)
            with col_lat:
                latitude = st.number_input("Latitude", value=float(coords['lat']), 
                                         min_value=-90.0, max_value=90.0, format="%.6f")
            with col_lng:
                longitude = st.number_input("Longitude", value=float(coords['lng']), 
                                          min_value=-180.0, max_value=180.0, format="%.6f")
        else:
            # Manual coordinate input
            st.write("### Koordinat Lokasi (Opsional)")
            col_lat, col_lng = st.columns(2)
            with col_lat:
                latitude = st.number_input("Latitude", value=0.0, 
                                         min_value=-90.0, max_value=90.0, format="%.6f")
            with col_lng:
                longitude = st.number_input("Longitude", value=0.0, 
                                          min_value=-180.0, max_value=180.0, format="%.6f")
        
        notes = st.text_area("Catatan Tambahan", placeholder="Informasi tambahan tentang pedagang")
        
        submit = st.form_submit_button("Tambah Pedagang", use_container_width=True)
        
        if submit:
            if not name or not merchant_type or not location or not address:
                st.error("Nama pedagang, tipe, lokasi, dan alamat lengkap harus diisi!")
            else:
                try:
                    db = MongoDBConnection.get_database()
                    
                    merchant_data = {
                        "name": name,
                        "type": merchant_type,
                        "location": location,
                        "address": address,
                        "phone": phone,
                        "email": email,
                        "capacity": capacity,
                        "notes": notes,
                        "registration_date": datetime.now(),
                        "created_by": ObjectId(st.session_state['user']['id']),
                        "is_active": True
                    }
                    
                    # Add coordinates if extracted or manually entered
                    if latitude != 0.0 and longitude != 0.0:
                        merchant_data["coordinates"] = {
                            "lat": latitude,
                            "lng": longitude,
                            "source": "google_maps" if st.session_state.merchant_coordinates_extracted else "manual"
                        }
                    
                    result = db.merchants.insert_one(merchant_data)
                    
                    if result.inserted_id:
                        st.success(f"Pedagang {name} berhasil ditambahkan!")
                        if latitude != 0.0 and longitude != 0.0:
                            st.info(f"Koordinat lokasi: {latitude:.6f}, {longitude:.6f}")
                        st.balloons()
                        # Reset coordinate extraction state
                        st.session_state.merchant_coordinates_extracted = False
                        st.session_state.merchant_extracted_coordinates = None
                    else:
                        st.error("Gagal menambahkan pedagang.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

def merchant_statistics():
    st.subheader("Statistik Pedagang")
    
    # Get statistics
    db = MongoDBConnection.get_database()
    
    # Total merchants
    total_merchants = db.merchants.count_documents({})
    
    # Merchants by type
    type_stats = list(db.merchants.aggregate([
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))
    
    # Merchants by location
    location_stats = list(db.merchants.aggregate([
        {"$group": {"_id": "$location", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Pedagang", total_merchants)
    
    with col2:
        if type_stats:
            top_type = type_stats[0]
            st.metric("Tipe Terbanyak", f"{top_type['_id']} ({top_type['count']} pedagang)")
        else:
            st.metric("Tipe Terbanyak", "Belum ada data")
    
    with col3:
        if location_stats:
            top_location = location_stats[0]
            st.metric("Lokasi Terbanyak", f"{top_location['_id']} ({top_location['count']} pedagang)")
        else:
            st.metric("Lokasi Terbanyak", "Belum ada data")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if type_stats:
            st.subheader("Pedagang berdasarkan Tipe")
            type_df = pd.DataFrame(type_stats)
            type_df.columns = ['Tipe', 'Jumlah']
            st.bar_chart(type_df.set_index('Tipe')['Jumlah'])
    
    with col2:
        if location_stats:
            st.subheader("Pedagang berdasarkan Lokasi")
            location_df = pd.DataFrame(location_stats)
            location_df.columns = ['Lokasi', 'Jumlah']
            st.bar_chart(location_df.set_index('Lokasi')['Jumlah'])

def delete_merchant(merchant_id):
    """Delete merchant from database"""
    try:
        db = MongoDBConnection.get_database()
        result = db.merchants.delete_one({"_id": ObjectId(merchant_id)})
        
        if result.deleted_count > 0:
            st.success("Pedagang berhasil dihapus!")
            st.rerun()
        else:
            st.error("Gagal menghapus pedagang.")
    except Exception as e:
        st.error(f"Error menghapus pedagang: {e}")

def edit_merchant(merchant_id):
    """Edit merchant data with coordinate support"""
    db = MongoDBConnection.get_database()
    merchant = db.merchants.find_one({"_id": ObjectId(merchant_id)})
    
    if not merchant:
        st.error("Pedagang tidak ditemukan!")
        return
    
    st.subheader(f"Edit Pedagang: {merchant.get('name', '')}")
    
    with st.form("edit_merchant_form"):
        name = st.text_input("Nama Pedagang*", value=merchant.get('name', ''))
        
        col1, col2 = st.columns(2)
        
        with col1:
            merchant_type = st.selectbox("Tipe Pedagang*", 
                                       ["Pengecer", "Grosir", "Pasar Tradisional", "Toko Modern"],
                                       index=["Pengecer", "Grosir", "Pasar Tradisional", "Toko Modern"].index(merchant.get('type', 'Pengecer')))
            location = st.text_input("Lokasi*", value=merchant.get('location', ''))
            phone = st.text_input("No. Telepon", value=merchant.get('phone', ''))
        
        with col2:
            email = st.text_input("Email", value=merchant.get('email', ''))
            capacity = st.text_input("Kapasitas", value=merchant.get('capacity', ''))
        
        # Coordinate extraction section for editing
        st.write("### Update Koordinat Lokasi")
        col_addr1, col_addr2 = st.columns([3, 1])
        with col_addr1:
            address = st.text_area("Alamat Lengkap untuk Koordinat*", 
                                 value=merchant.get('address', ''),
                                 help="Alamat lengkap akan digunakan untuk mengekstrak koordinat lokasi menggunakan Google Maps")
        with col_addr2:
            st.write("&nbsp;")
            extract_coords = st.form_submit_button("🗺️ Ekstrak Koordinat", use_container_width=True)
        
        # Extract coordinates when button is clicked
        if extract_coords:
            if not address:
                st.error("Alamat lengkap harus diisi untuk ekstraksi koordinat!")
            else:
                with st.spinner("Mengekstrak koordinat dari Google Maps..."):
                    try:
                        coordinates = get_coordinates_from_address(address, location)
                        if coordinates:
                            st.session_state.merchant_coordinates_extracted = True
                            st.session_state.merchant_extracted_coordinates = coordinates
                            st.success(f"✅ Koordinat berhasil diekstrak: {coordinates['lat']:.6f}, {coordinates['lng']:.6f}")
                        else:
                            st.warning("⚠️ Tidak dapat menemukan koordinat untuk alamat tersebut. Silakan periksa alamat atau tambahkan koordinat secara manual.")
                    except Exception as e:
                        st.error(f"Error saat ekstraksi koordinat: {e}")
        
        # Display current or extracted coordinates
        current_coords = merchant.get('coordinates', {})
        if st.session_state.get('merchant_coordinates_extracted') and st.session_state.get('merchant_extracted_coordinates'):
            coords = st.session_state.merchant_extracted_coordinates
            col_lat, col_lng = st.columns(2)
            with col_lat:
                latitude = st.number_input("Latitude", value=float(coords['lat']), 
                                         min_value=-90.0, max_value=90.0, format="%.6f")
            with col_lng:
                longitude = st.number_input("Longitude", value=float(coords['lng']), 
                                          min_value=-180.0, max_value=180.0, format="%.6f")
        elif current_coords:
            col_lat, col_lng = st.columns(2)
            with col_lat:
                latitude = st.number_input("Latitude", value=float(current_coords.get('lat', 0.0)), 
                                         min_value=-90.0, max_value=90.0, format="%.6f")
            with col_lng:
                longitude = st.number_input("Longitude", value=float(current_coords.get('lng', 0.0)), 
                                          min_value=-180.0, max_value=180.0, format="%.6f")
        else:
            # Manual coordinate input
            st.write("### Koordinat Lokasi (Opsional)")
            col_lat, col_lng = st.columns(2)
            with col_lat:
                latitude = st.number_input("Latitude", value=0.0, 
                                         min_value=-90.0, max_value=90.0, format="%.6f")
            with col_lng:
                longitude = st.number_input("Longitude", value=0.0, 
                                          min_value=-180.0, max_value=180.0, format="%.6f")
        
        notes = st.text_area("Catatan Tambahan", value=merchant.get('notes', ''))
        
        col_submit1, col_submit2 = st.columns(2)
        with col_submit1:
            submit = st.form_submit_button("Update Pedagang", use_container_width=True)
        with col_submit2:
            cancel = st.form_submit_button("Batal", use_container_width=True)
        
        if submit:
            if not name or not merchant_type or not location or not address:
                st.error("Nama pedagang, tipe, lokasi, dan alamat lengkap harus diisi!")
            else:
                try:
                    update_data = {
                        "name": name,
                        "type": merchant_type,
                        "location": location,
                        "address": address,
                        "phone": phone,
                        "email": email,
                        "capacity": capacity,
                        "notes": notes,
                        "updated_at": datetime.now()
                    }
                    
                    # Add coordinates if provided
                    if latitude != 0.0 and longitude != 0.0:
                        update_data["coordinates"] = {
                            "lat": latitude,
                            "lng": longitude,
                            "source": "google_maps" if st.session_state.get('merchant_coordinates_extracted') else "manual"
                        }
                    
                    result = db.merchants.update_one(
                        {"_id": ObjectId(merchant_id)},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                        st.success(f"Pedagang {name} berhasil diupdate!")
                        if latitude != 0.0 and longitude != 0.0:
                            st.info(f"Koordinat lokasi: {latitude:.6f}, {longitude:.6f}")
                        st.balloons()
                        # Clear editing state
                        if 'editing_merchant' in st.session_state:
                            del st.session_state['editing_merchant']
                        # Reset coordinate extraction state
                        st.session_state.merchant_coordinates_extracted = False
                        st.session_state.merchant_extracted_coordinates = None
                        st.rerun()
                    else:
                        st.error("Gagal mengupdate pedagang.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if cancel:
            # Clear editing state
            if 'editing_merchant' in st.session_state:
                del st.session_state['editing_merchant']
            # Reset coordinate extraction state
            st.session_state.merchant_coordinates_extracted = False
            st.session_state.merchant_extracted_coordinates = None
            st.rerun()