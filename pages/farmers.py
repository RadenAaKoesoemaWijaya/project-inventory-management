import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.database import MongoDBConnection, get_farmers
from utils.geocoding import get_coordinates_from_address
from datetime import datetime
from bson import ObjectId

def app():
    require_auth()
    
    st.title("Manajemen Petani")
    
    # Check if we're in editing mode
    if 'editing_farmer' in st.session_state:
        edit_farmer(st.session_state['editing_farmer'])
        return
    
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
                
                # Display coordinates if available
                if 'coordinates' in farmer and farmer['coordinates']:
                    coords = farmer['coordinates']
                    source = coords.get('source', 'manual')
                    source_icon = '🗺️' if source == 'google_maps' else '✏️'
                    st.write(f"**Koordinat Lokasi:** {coords['lat']:.6f}, {coords['lng']:.6f} {source_icon} ({source.replace('_', ' ').title()})")
                
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
    
    # Initialize session state for coordinate extraction
    if 'coordinates_extracted' not in st.session_state:
        st.session_state.coordinates_extracted = False
    if 'extracted_coordinates' not in st.session_state:
        st.session_state.extracted_coordinates = None
    
    with st.form("add_farmer_form"):
        name = st.text_input("Nama Petani*", placeholder="Masukkan nama lengkap petani")
        location = st.text_input("Lokasi/Lokasi Lahan*", placeholder="Contoh: Tambakrejo, Ngadirejo, dll")
        
        # Coordinate extraction section
        st.write("### Ekstraksi Koordinat Lokasi")
        col_addr1, col_addr2 = st.columns([3, 1])
        with col_addr1:
            full_address = st.text_area("Alamat Lengkap untuk Koordinat*", 
                                      placeholder="Jl. Nama Jalan, RT/RW, Desa, Kecamatan, Kabupaten",
                                      help="Alamat lengkap akan digunakan untuk mengekstrak koordinat lokasi menggunakan Google Maps")
        with col_addr2:
            st.write("&nbsp;")
            extract_coords = st.form_submit_button("🗺️ Ekstrak Koordinat", use_container_width=True)
        
        # Extract coordinates when button is clicked
        if extract_coords:
            if not full_address:
                st.error("Alamat lengkap harus diisi untuk ekstraksi koordinat!")
            else:
                with st.spinner("Mengekstrak koordinat dari Google Maps..."):
                    try:
                        coordinates = get_coordinates_from_address(full_address, location)
                        if coordinates:
                            st.session_state.coordinates_extracted = True
                            st.session_state.extracted_coordinates = coordinates
                            st.success(f"✅ Koordinat berhasil diekstrak: {coordinates['lat']:.6f}, {coordinates['lng']:.6f}")
                        else:
                            st.warning("⚠️ Tidak dapat menemukan koordinat untuk alamat tersebut. Silakan periksa alamat atau tambahkan koordinat secara manual.")
                    except Exception as e:
                        st.error(f"Error saat ekstraksi koordinat: {e}")
        
        # Display extracted coordinates
        if st.session_state.coordinates_extracted and st.session_state.extracted_coordinates:
            coords = st.session_state.extracted_coordinates
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            land_area = st.number_input("Luas Lahan (hektar)*", min_value=0.1, max_value=1000.0, value=1.0, step=0.1)
            primary_crop = st.text_input("Jenis Tanaman Utama*", placeholder="Contoh: Padi, Jagung, Kedelai")
            phone = st.text_input("No. Telepon", placeholder="0812xxxxxx")
        
        with col2:
            email = st.text_input("Email", placeholder="petani@email.com")
            address = full_address  # Use the same address field
            notes = st.text_area("Catatan Tambahan", placeholder="Informasi tambahan tentang petani")
        
        submit = st.form_submit_button("Tambah Petani", use_container_width=True)
        
        if submit:
            if not name or not location or not primary_crop or not full_address:
                st.error("Nama petani, lokasi, jenis tanaman utama, dan alamat lengkap harus diisi!")
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
                    
                    # Add coordinates if extracted or manually entered
                    if latitude != 0.0 and longitude != 0.0:
                        farmer_data["coordinates"] = {
                            "lat": latitude,
                            "lng": longitude,
                            "source": "google_maps" if st.session_state.coordinates_extracted else "manual"
                        }
                    
                    result = db.farmers.insert_one(farmer_data)
                    
                    if result.inserted_id:
                        st.success(f"Petani {name} berhasil ditambahkan!")
                        if latitude != 0.0 and longitude != 0.0:
                            st.info(f"Koordinat lokasi: {latitude:.6f}, {longitude:.6f}")
                        st.balloons()
                        # Reset coordinate extraction state
                        st.session_state.coordinates_extracted = False
                        st.session_state.extracted_coordinates = None
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

def edit_farmer(farmer_id):
    """Edit farmer data with coordinate support"""
    db = MongoDBConnection.get_database()
    farmer = db.farmers.find_one({"_id": ObjectId(farmer_id)})
    
    if not farmer:
        st.error("Petani tidak ditemukan!")
        return
    
    st.subheader(f"Edit Petani: {farmer.get('name', '')}")
    
    with st.form("edit_farmer_form"):
        name = st.text_input("Nama Petani*", value=farmer.get('name', ''))
        location = st.text_input("Lokasi/Lokasi Lahan*", value=farmer.get('location', ''))
        
        # Coordinate extraction section for editing
        st.write("### Update Koordinat Lokasi")
        col_addr1, col_addr2 = st.columns([3, 1])
        with col_addr1:
            full_address = st.text_area("Alamat Lengkap untuk Koordinat*", 
                                      value=farmer.get('address', ''),
                                      help="Alamat lengkap akan digunakan untuk mengekstrak koordinat lokasi menggunakan Google Maps")
        with col_addr2:
            st.write("&nbsp;")
            extract_coords = st.form_submit_button("🗺️ Ekstrak Koordinat", use_container_width=True)
        
        # Extract coordinates when button is clicked
        if extract_coords:
            if not full_address:
                st.error("Alamat lengkap harus diisi untuk ekstraksi koordinat!")
            else:
                with st.spinner("Mengekstrak koordinat dari Google Maps..."):
                    try:
                        coordinates = get_coordinates_from_address(full_address, location)
                        if coordinates:
                            st.session_state.coordinates_extracted = True
                            st.session_state.extracted_coordinates = coordinates
                            st.success(f"✅ Koordinat berhasil diekstrak: {coordinates['lat']:.6f}, {coordinates['lng']:.6f}")
                        else:
                            st.warning("⚠️ Tidak dapat menemukan koordinat untuk alamat tersebut. Silakan periksa alamat atau tambahkan koordinat secara manual.")
                    except Exception as e:
                        st.error(f"Error saat ekstraksi koordinat: {e}")
        
        # Display current or extracted coordinates
        current_coords = farmer.get('coordinates', {})
        if st.session_state.get('coordinates_extracted') and st.session_state.get('extracted_coordinates'):
            coords = st.session_state.extracted_coordinates
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            land_area = st.number_input("Luas Lahan (hektar)*", 
                                      min_value=0.1, max_value=1000.0, 
                                      value=float(farmer.get('land_area', 1.0)), step=0.1)
            primary_crop = st.text_input("Jenis Tanaman Utama*", 
                                         value=farmer.get('primary_crop', ''))
            phone = st.text_input("No. Telepon", value=farmer.get('phone', ''))
        
        with col2:
            email = st.text_input("Email", value=farmer.get('email', ''))
            notes = st.text_area("Catatan Tambahan", value=farmer.get('notes', ''))
        
        col_submit1, col_submit2 = st.columns(2)
        with col_submit1:
            submit = st.form_submit_button("Update Petani", use_container_width=True)
        with col_submit2:
            cancel = st.form_submit_button("Batal", use_container_width=True)
        
        if submit:
            if not name or not location or not primary_crop or not full_address:
                st.error("Nama petani, lokasi, jenis tanaman utama, dan alamat lengkap harus diisi!")
            else:
                try:
                    update_data = {
                        "name": name,
                        "location": location,
                        "land_area": land_area,
                        "primary_crop": primary_crop,
                        "phone": phone,
                        "email": email,
                        "address": full_address,
                        "notes": notes,
                        "updated_at": datetime.now()
                    }
                    
                    # Add coordinates if provided
                    if latitude != 0.0 and longitude != 0.0:
                        update_data["coordinates"] = {
                            "lat": latitude,
                            "lng": longitude,
                            "source": "google_maps" if st.session_state.get('coordinates_extracted') else "manual"
                        }
                    
                    result = db.farmers.update_one(
                        {"_id": ObjectId(farmer_id)},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                        st.success(f"Petani {name} berhasil diupdate!")
                        if latitude != 0.0 and longitude != 0.0:
                            st.info(f"Koordinat lokasi: {latitude:.6f}, {longitude:.6f}")
                        st.balloons()
                        # Clear editing state
                        if 'editing_farmer' in st.session_state:
                            del st.session_state['editing_farmer']
                        # Reset coordinate extraction state
                        st.session_state.coordinates_extracted = False
                        st.session_state.extracted_coordinates = None
                        st.rerun()
                    else:
                        st.error("Gagal mengupdate petani.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if cancel:
            # Clear editing state
            if 'editing_farmer' in st.session_state:
                del st.session_state['editing_farmer']
            # Reset coordinate extraction state
            st.session_state.coordinates_extracted = False
            st.session_state.extracted_coordinates = None
            st.rerun()