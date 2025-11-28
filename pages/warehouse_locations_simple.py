import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime
from utils.sqlite_database import SQLiteDatabase

def app():
    st.title("📍 Lokasi Lumbung Desa")
    st.markdown("Kelola lokasi dan informasi lumbung desa")
    
    # Initialize database
    try:
        db = SQLiteDatabase()
        conn = db._get_connection()
        cursor = conn.cursor()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return
    
    # Sidebar menu
    menu = st.sidebar.selectbox("Pilih Menu", ["📋 Daftar Lumbung", "➕ Tambah Lumbung"])
    
    if menu == "➕ Tambah Lumbung":
        add_warehouse_page(cursor, conn)
    else:
        display_warehouse_page(cursor, conn)

def add_warehouse_page(cursor, conn):
    st.header("➕ Tambah Lumbung Baru")
    
    with st.form("add_warehouse_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nama Lumbung*", placeholder="Lumbung Desa Tambakrejo")
            location = st.text_input("Lokasi*", placeholder="Tambakrejo")
            description = st.text_area("Deskripsi", placeholder="Lumbung utama untuk wilayah Tambakrejo")
            capacity = st.number_input("Kapasitas (ton)*", min_value=1, max_value=1000, value=50)
        
        with col2:
            lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=-7.250445, format="%.6f")
            lng = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=112.768045, format="%.6f")
            st.info("📍 Koordinat untuk lokasi lumbung")
        
        submitted = st.form_submit_button("💾 Simpan Lumbung", use_container_width=True)
        
        if submitted:
            if not all([name, location]):
                st.error("Nama dan lokasi wajib diisi!")
                return
            
            try:
                warehouse_id = str(uuid.uuid4())
                coordinates = json.dumps({"lat": lat, "lng": lng})
                
                cursor.execute('''
                    INSERT INTO warehouses (id, name, description, location, capacity, coordinates, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (warehouse_id, name, description, location, capacity, coordinates, datetime.now()))
                
                conn.commit()
                st.success(f"✅ Lumbung '{name}' berhasil ditambahkan!")
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {e}")

def display_warehouse_page(cursor, conn):
    st.header("📋 Daftar Lumbung Desa")
    
    try:
        cursor.execute("SELECT * FROM warehouses ORDER BY name")
        warehouses = cursor.fetchall()
        
        if not warehouses:
            st.info("Belum ada data lumbung desa.")
            return
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(warehouses, columns=columns)
        
        # Add formatted coordinates
        def format_coordinates(coords):
            if coords:
                try:
                    coord_data = json.loads(coords)
                    return f"{coord_data['lat']:.6f}, {coord_data['lng']:.6f}"
                except:
                    return coords
            return "N/A"
        
        df['koordinat'] = df['coordinates'].apply(format_coordinates)
        
        # Search and filter
        search = st.text_input("🔍 Cari lumbung", placeholder="Nama atau lokasi")
        
        if search:
            df = df[df['name'].str.contains(search, case=False, na=False) | 
                   df['location'].str.contains(search, case=False, na=False)]
        
        # Display data
        st.write(f"Menampilkan {len(df)} lumbung")
        
        for _, warehouse in df.iterrows():
            with st.expander(f"🏪 {warehouse['name']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**📍 Lokasi:** {warehouse['location']}")
                    st.write(f"**📝 Deskripsi:** {warehouse.get('description', 'N/A')}")
                    st.write(f"**📦 Kapasitas:** {warehouse['capacity']} ton")
                    st.write(f"**🗺️ Koordinat:** {warehouse['koordinat']}")
                    st.write(f"**📅 Dibuat:** {warehouse['created_at']}")
                
                with col2:
                    if st.button("🗑️ Hapus", key=f"delete_{warehouse['id']}"):
                        try:
                            cursor.execute("DELETE FROM warehouses WHERE id = ?", (warehouse['id'],))
                            conn.commit()
                            st.success("Lumbung berhasil dihapus!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error menghapus: {e}")
        
        # Summary statistics
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Total Lumbung", len(df))
        
        with col2:
            total_capacity = df['capacity'].sum()
            st.metric("📦 Total Kapasitas", f"{total_capacity:,} ton")
        
        with col3:
            avg_capacity = df['capacity'].mean()
            st.metric("📈 Rata-rata Kapasitas", f"{avg_capacity:.1f} ton")
        
    except Exception as e:
        st.error(f"Error mengambil data: {e}")

if __name__ == "__main__":
    app()
