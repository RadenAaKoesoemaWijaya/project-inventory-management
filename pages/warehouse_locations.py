import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import MongoDBConnection
from utils.geocoding import get_coordinates_from_address

def add_warehouse_location():
    st.subheader("➕ Tambah Lokasi Lumbung Desa Baru")
    
    with st.form("add_warehouse_location_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nama Lumbung Desa*", 
                               placeholder="Contoh: Lumbung Desa Tambakrejo",
                               help="Nama lengkap lumbung desa")
            
            location = st.text_input("Desa/Kelurahan*", 
                                   placeholder="Contoh: Tambakrejo",
                                   help="Nama desa tempat lumbung berada")
            
            sub_district = st.text_input("Kecamatan*", 
                                       placeholder="Contoh: Pakisaji",
                                       help="Nama kecamatan")
            
            district = st.text_input("Kabupaten/Kota*", 
                                 placeholder="Contoh: Malang",
                                 help="Nama kabupaten atau kota")
            
            province = st.selectbox("Provinsi*", [
                "Jawa Timur", "Jawa Tengah", "Jawa Barat", "DI Yogyakarta",
                "Banten", "DKI Jakarta", "Lampung", "Sumatera Selatan",
                "Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur"
            ], index=0)
            
            capacity = st.number_input("Kapasitas Lumbung (ton)*", 
                                     min_value=1, max_value=1000, value=50,
                                     help="Kapasitas maksimal lumbung dalam ton")
            
            manager_name = st.text_input("Nama Pengelola*", 
                                       placeholder="Contoh: Budi Santoso",
                                       help="Nama lengkap pengelola lumbung")
            
            manager_phone = st.text_input("No. HP Pengelola*", 
                                          placeholder="081234567890",
                                          help="Nomor HP yang dapat dihubungi")
        
        with col2:
            # Address for coordinate extraction
            st.write("### 🗺️ Informasi Lokasi untuk Koordinat")
            
            address = st.text_area("Alamat Lengkap*", 
                                 placeholder="Jl. Raya Tambakrejo No. 123, RT 01/RW 02, Tambakrejo, Pakisaji, Malang, Jawa Timur",
                                 help="Alamat lengkap untuk ekstraksi koordinat menggunakan Google Maps")
            
            # Coordinate extraction section
            st.write("#### Ekstraksi Koordinat Lokasi")
            
            extract_coords = st.form_submit_button("🗺️ Ekstrak Koordinat dari Google Maps", 
                                                 use_container_width=True)
            
            # Manual coordinate input
            st.write("#### Atau Masukkan Koordinat Manual")
            
            lat_col, lng_col = st.columns(2)
            with lat_col:
                manual_lat = st.number_input("Latitude", 
                                             min_value=-90.0, max_value=90.0, 
                                             value=st.session_state.get('extracted_lat', -7.0),
                                             format="%.6f",
                                             help="Garis lintang (contoh: -7.981298)")
            
            with lng_col:
                manual_lng = st.number_input("Longitude", 
                                             min_value=-180.0, max_value=180.0, 
                                             value=st.session_state.get('extracted_lng', 112.0),
                                             format="%.6f",
                                             help="Garis bujur (contoh: 112.631178)")
            
            # Display extracted coordinates if available
            if st.session_state.get('extracted_lat') and st.session_state.get('extracted_lng'):
                st.success(f"✅ Koordinat diekstrak: {st.session_state.extracted_lat:.6f}, {st.session_state.extracted_lng:.6f}")
                st.info("Koordinat ini akan digunakan untuk lokasi lumbung")
        
        # Form submission
        submitted = st.form_submit_button("💾 Simpan Data Lumbung", use_container_width=True)
        
        if submitted:
            # Validate required fields
            if not all([name, location, sub_district, district, province, 
                       address, manager_name, manager_phone]):
                st.error("Semua field bertanda * wajib diisi!")
                return
            
            # Use extracted coordinates if available, otherwise use manual input
            if st.session_state.get('extracted_lat') and st.session_state.get('extracted_lng'):
                lat = st.session_state.extracted_lat
                lng = st.session_state.extracted_lng
                coordinate_source = "google_maps"
            else:
                lat = manual_lat
                lng = manual_lng
                coordinate_source = "manual"
            
            try:
                # Save to database
                db = MongoDBConnection.get_database()
                
                warehouse_data = {
                    "name": name,
                    "location": location,
                    "sub_district": sub_district,
                    "district": district,
                    "province": province,
                    "address": address,
                    "coordinates": {
                        "lat": lat,
                        "lng": lng
                    },
                    "coordinate_source": coordinate_source,
                    "capacity": capacity,
                    "manager_name": manager_name,
                    "manager_phone": manager_phone,
                    "current_stock": 0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                result = db.warehouses.insert_one(warehouse_data)
                
                if result.inserted_id:
                    st.success(f"✅ Lokasi lumbung '{name}' berhasil ditambahkan!")
                    st.info(f"Koordinat: {lat:.6f}, {lng:.6f} (Sumber: {coordinate_source})")
                    
                    # Clear session state
                    if 'extracted_lat' in st.session_state:
                        del st.session_state.extracted_lat
                    if 'extracted_lng' in st.session_state:
                        del st.session_state.extracted_lng
                    
                    st.rerun()
                else:
                    st.error("Gagal menyimpan data lumbung!")
                    
            except Exception as e:
                st.error(f"Error saat menyimpan data: {e}")

def display_warehouse_locations():
    st.subheader("📍 Daftar Lokasi Lumbung Desa")
    
    try:
        db = MongoDBConnection.get_database()
        warehouses = list(db.warehouses.find().sort("name", 1))
        
        if not warehouses:
            st.info("Belum ada data lokasi lumbung desa.")
            return
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(warehouses)
        
        # Add coordinate display
        df['koordinat'] = df.apply(lambda row: f"{row['coordinates']['lat']:.6f}, {row['coordinates']['lng']:.6f}" 
                                  if 'coordinates' in row and row['coordinates'] 
                                  else "Tidak tersedia", axis=1)
        
        df['sumber_koordinat'] = df.get('coordinate_source', 'tidak_diketahui')
        
        # Display options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Cari lumbung", "", 
                                      placeholder="Nama lumbung atau lokasi")
        
        with col2:
            province_filter = st.selectbox("🏛️ Filter Provinsi", 
                                         ["Semua"] + list(df['province'].unique()) if 'province' in df.columns else ["Semua"])
        
        with col3:
            show_map = st.checkbox("🗺️ Tampilkan di Peta", value=False)
        
        # Filter data
        filtered_df = df.copy()
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['name'].str.contains(search_term, case=False, na=False) |
                filtered_df['location'].str.contains(search_term, case=False, na=False)
            ]
        
        if province_filter != "Semua":
            filtered_df = filtered_df[filtered_df['province'] == province_filter]
        
        # Display results
        st.write(f"Menampilkan {len(filtered_df)} dari {len(df)} lokasi lumbung")
        
        if show_map and len(filtered_df) > 0:
            st.map(filtered_df[['coordinates.lat', 'coordinates.lng']].rename(columns={
                'coordinates.lat': 'lat',
                'coordinates.lng': 'lon'
            }))
        
        # Display table
        for _, warehouse in filtered_df.iterrows():
            with st.expander(f"🏪 {warehouse['name']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**📍 Lokasi:** {warehouse['location']}, {warehouse['sub_district']}, {warehouse['district']}")
                    st.write(f"**🏛️ Provinsi:** {warehouse['province']}")
                    st.write(f"**🧑‍🌾 Pengelola:** {warehouse['manager_name']} ({warehouse['manager_phone']})")
                    st.write(f"**📦 Kapasitas:** {warehouse['capacity']} ton")
                    
                    if 'coordinates' in warehouse and warehouse['coordinates']:
                        st.write(f"**🗺️ Koordinat:** {warehouse['koordinat']}")
                        st.write(f"**📍 Sumber Koordinat:** {warehouse['sumber_koordinat']}")
                    
                    st.write(f"**📅 Dibuat:** {warehouse['created_at'].strftime('%d/%m/%Y %H:%M')}")
                
                with col2:
                    # Action buttons
                    if st.button("✏️ Edit", key=f"edit_{warehouse['_id']}", use_container_width=True):
                        st.session_state.editing_warehouse = str(warehouse['_id'])
                        st.rerun()
                    
                    if st.button("🗑️ Hapus", key=f"delete_{warehouse['_id']}", 
                                use_container_width=True, type="secondary"):
                        if st.checkbox(f"Konfirmasi hapus {warehouse['name']}?", 
                                     key=f"confirm_{warehouse['_id']}"):
                            try:
                                db.warehouses.delete_one({"_id": warehouse['_id']})
                                st.success(f"Lokasi lumbung '{warehouse['name']}' berhasil dihapus!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saat menghapus data: {e}")
        
    except Exception as e:
        st.error(f"Error saat mengambil data lokasi lumbung: {e}")

def edit_warehouse_location(warehouse_id):
    st.subheader("✏️ Edit Lokasi Lumbung Desa")
    
    try:
        db = MongoDBConnection.get_database()
        warehouse = db.warehouses.find_one({"_id": warehouse_id})
        
        if not warehouse:
            st.error("Data lumbung tidak ditemukan!")
            return
        
        with st.form("edit_warehouse_location_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nama Lumbung Desa*", 
                                   value=warehouse.get('name', ''))
                
                location = st.text_input("Desa/Kelurahan*", 
                                       value=warehouse.get('location', ''))
                
                sub_district = st.text_input("Kecamatan*", 
                                             value=warehouse.get('sub_district', ''))
                
                district = st.text_input("Kabupaten/Kota*", 
                                       value=warehouse.get('district', ''))
                
                province = st.selectbox("Provinsi*", [
                    "Jawa Timur", "Jawa Tengah", "Jawa Barat", "DI Yogyakarta",
                    "Banten", "DKI Jakarta", "Lampung", "Sumatera Selatan",
                    "Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur"
                ], index=0)
                
                capacity = st.number_input("Kapasitas Lumbung (ton)*", 
                                         min_value=1, max_value=1000, 
                                         value=warehouse.get('capacity', 50))
                
                manager_name = st.text_input("Nama Pengelola*", 
                                           value=warehouse.get('manager_name', ''))
                
                manager_phone = st.text_input("No. HP Pengelola*", 
                                            value=warehouse.get('manager_phone', ''))
            
            with col2:
                # Address for coordinate extraction
                st.write("### 🗺️ Update Informasi Lokasi")
                
                address = st.text_area("Alamat Lengkap*", 
                                     value=warehouse.get('address', ''))
                
                # Current coordinates display
                current_coords = warehouse.get('coordinates', {})
                st.write(f"**Koordinat Saat Ini:** {current_coords.get('lat', 'Tidak tersedia')}, {current_coords.get('lng', 'Tidak tersedia')}")
                
                # Coordinate extraction section
                st.write("#### Update Koordinat Lokasi")
                
                extract_coords = st.form_submit_button("🗺️ Ekstrak Koordinat Baru dari Google Maps", 
                                                     use_container_width=True)
                
                # Manual coordinate input
                st.write("#### Atau Update Koordinat Manual")
                
                lat_col, lng_col = st.columns(2)
                with lat_col:
                    manual_lat = st.number_input("Latitude", 
                                                 min_value=-90.0, max_value=90.0, 
                                                 value=st.session_state.get('extracted_lat', current_coords.get('lat', -7.0)),
                                                 format="%.6f")
                
                with lng_col:
                    manual_lng = st.number_input("Longitude", 
                                                 min_value=-180.0, max_value=180.0, 
                                                 value=st.session_state.get('extracted_lng', current_coords.get('lng', 112.0)),
                                                 format="%.6f")
                
                # Display extracted coordinates if available
                if st.session_state.get('extracted_lat') and st.session_state.get('extracted_lng'):
                    st.success(f"✅ Koordinat diekstrak: {st.session_state.extracted_lat:.6f}, {st.session_state.extracted_lng:.6f}")
            
            # Handle coordinate extraction
            if extract_coords:
                if not address:
                    st.error("Alamat lengkap harus diisi untuk ekstraksi koordinat!")
                else:
                    with st.spinner("Mengekstrak koordinat dari Google Maps..."):
                        try:
                            coordinates = get_coordinates_from_address(address, warehouse.get('location', ''))
                            if coordinates:
                                st.session_state.extracted_lat = coordinates['lat']
                                st.session_state.extracted_lng = coordinates['lng']
                                st.success(f"✅ Koordinat berhasil diekstrak: {coordinates['lat']:.6f}, {coordinates['lng']:.6f}")
                                st.rerun()
                            else:
                                st.warning("⚠️ Tidak dapat menemukan koordinat untuk alamat tersebut.")
                        except Exception as e:
                            st.error(f"Error saat ekstraksi koordinat: {e}")
            
            # Form submission
            submitted = st.form_submit_button("💾 Update Data Lumbung", use_container_width=True)
            
            if submitted:
                # Validate required fields
                if not all([name, location, sub_district, district, province, 
                           address, manager_name, manager_phone]):
                    st.error("Semua field bertanda * wajib diisi!")
                    return
                
                # Use extracted coordinates if available, otherwise use manual input
                if st.session_state.get('extracted_lat') and st.session_state.get('extracted_lng'):
                    lat = st.session_state.extracted_lat
                    lng = st.session_state.extracted_lng
                    coordinate_source = "google_maps"
                else:
                    lat = manual_lat
                    lng = manual_lng
                    coordinate_source = "manual"
                
                try:
                    # Update database
                    update_data = {
                        "name": name,
                        "location": location,
                        "sub_district": sub_district,
                        "district": district,
                        "province": province,
                        "address": address,
                        "coordinates": {
                            "lat": lat,
                            "lng": lng
                        },
                        "coordinate_source": coordinate_source,
                        "capacity": capacity,
                        "manager_name": manager_name,
                        "manager_phone": manager_phone,
                        "updated_at": datetime.now()
                    }
                    
                    result = db.warehouses.update_one(
                        {"_id": warehouse_id},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                        st.success(f"✅ Lokasi lumbung '{name}' berhasil diupdate!")
                        st.info(f"Koordinat: {lat:.6f}, {lng:.6f} (Sumber: {coordinate_source})")
                        
                        # Clear session state
                        if 'extracted_lat' in st.session_state:
                            del st.session_state.extracted_lat
                        if 'extracted_lng' in st.session_state:
                            del st.session_state.extracted_lng
                        
                        # Clear editing mode
                        if 'editing_warehouse' in st.session_state:
                            del st.session_state.editing_warehouse
                        
                        st.rerun()
                    else:
                        st.error("Tidak ada perubahan yang dilakukan atau data tidak ditemukan!")
                        
                except Exception as e:
                    st.error(f"Error saat update data: {e}")
        
    except Exception as e:
        st.error(f"Error saat mengambil data lumbung: {e}")

def app():
    st.title("🏪 Manajemen Lokasi Lumbung Desa")
    st.markdown("---")
    
    # Initialize session state for coordinate extraction
    if 'extracted_lat' not in st.session_state:
        st.session_state.extracted_lat = None
    if 'extracted_lng' not in st.session_state:
        st.session_state.extracted_lng = None
    
    # Check if we're in editing mode
    if 'editing_warehouse' in st.session_state:
        edit_warehouse_location(st.session_state.editing_warehouse)
        
        # Add back button
        if st.button("⬅️ Kembali ke Daftar Lokasi"):
            del st.session_state.editing_warehouse
            st.rerun()
    else:
        # Create tabs for different functions
        tab1, tab2 = st.tabs(["📍 Daftar Lokasi", "➕ Tambah Lokasi Baru"])
        
        with tab1:
            display_warehouse_locations()
        
        with tab2:
            add_warehouse_location()