import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.database import MongoDBConnection, get_harvests_by_season
from datetime import datetime, timedelta
from bson import ObjectId

def app():
    require_auth()
    
    st.title("Manajemen Hasil Panen")
    
    # Tabs for different harvest functions
    tab1, tab2, tab3, tab4 = st.tabs(["Daftar Hasil Panen", "Tambah Hasil Panen", "Statistik Musim", "Prediksi Musim"])
    
    with tab1:
        display_harvests()
    
    with tab2:
        add_harvest()
    
    with tab3:
        seasonal_statistics()
    
    with tab4:
        seasonal_forecast()

def display_harvests():
    st.subheader("Daftar Hasil Panen")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        crop_filter = st.text_input("Filter berdasarkan jenis tanaman", "")
    
    with col2:
        season_filter = st.selectbox("Filter berdasarkan musim", ["Semua Musim", "Musim Hujan", "Musim Kemarau", "Musim Panen"])
    
    with col3:
        limit = st.number_input("Jumlah data", min_value=5, max_value=200, value=50)
    
    # Get harvests data
    season = None if season_filter == "Semua Musim" else season_filter
    harvests_df = get_harvests_by_season(crop=crop_filter if crop_filter else None, season=season, limit=limit)
    
    if not harvests_df.empty:
        # Display harvests in a nice format
        for _, harvest in harvests_df.iterrows():
            with st.expander(f"🌾 {harvest.get('crop_type', 'Tanaman Tidak Diketahui')} - {harvest.get('farmer_name', 'Petani Tidak Diketahui')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Petani:** {harvest.get('farmer_name', 'Tidak diketahui')}")
                    st.write(f"**Lokasi:** {harvest.get('location', 'Tidak diketahui')}")
                    st.write(f"**Jumlah Panen:** {harvest.get('harvest_amount', 0)} {harvest.get('unit', 'kg')}")
                    st.write(f"**Kualitas:** {harvest.get('quality_grade', 'Tidak diketahui')}")
                
                with col2:
                    st.write(f"**Tanggal Panen:** {harvest.get('harvest_date', 'Tidak diketahui')}")
                    st.write(f"**Musim:** {harvest.get('season', 'Tidak diketahui')}")
                    st.write(f"**Harga per Unit:** Rp {harvest.get('price_per_unit', 0):,.0f}")
                    st.write(f"**Total Nilai:** Rp {harvest.get('total_value', 0):,.0f}")
                
                st.write(f"**Catatan:** {harvest.get('notes', 'Tidak ada catatan')}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Edit", key=f"edit_{harvest['_id']}"):
                        st.session_state['editing_harvest'] = harvest['_id']
                        st.rerun()
                with col2:
                    if st.button("Hapus", key=f"delete_{harvest['_id']}"):
                        delete_harvest(harvest['_id'])
                with col3:
                    if st.button("Lihat Detail", key=f"detail_{harvest['_id']}"):
                        st.session_state['viewing_harvest_detail'] = harvest['_id']
                        st.rerun()
    else:
        st.info("Belum ada data hasil panen. Silakan tambahkan hasil panen baru.")

def add_harvest():
    st.subheader("Tambah Hasil Panen Baru")
    
    # Get farmers data for dropdown
    db = MongoDBConnection.get_database()
    farmers = list(db.farmers.find({}, {"name": 1, "location": 1, "primary_crop": 1}))
    
    if not farmers:
        st.warning("Belum ada data petani. Silakan tambahkan data petani terlebih dahulu.")
        return
    
    farmer_names = [farmer['name'] for farmer in farmers]
    
    with st.form("add_harvest_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            selected_farmer = st.selectbox("Pilih Petani*", farmer_names)
            crop_type = st.text_input("Jenis Tanaman*", placeholder="Contoh: Padi, Jagung, Kedelai")
            harvest_amount = st.number_input("Jumlah Panen*", min_value=0.1, max_value=10000.0, value=100.0, step=0.1)
            unit = st.selectbox("Satuan*", ["kg", "ton", "kwintal", "ikat", "karung"])
        
        with col2:
            harvest_date = st.date_input("Tanggal Panen*", datetime.now())
            quality_grade = st.selectbox("Kualitas*", ["Grade A", "Grade B", "Grade C", "Grade D"])
            price_per_unit = st.number_input("Harga per Unit (Rp)*", min_value=100, value=5000, step=100)
        
        season = st.selectbox("Musim*", ["Musim Hujan", "Musim Kemarau", "Musim Panen"])
        notes = st.text_area("Catatan Tambahan", placeholder="Informasi tambahan tentang hasil panen")
        
        submit = st.form_submit_button("Tambah Hasil Panen", use_container_width=True)
        
        if submit:
            if not selected_farmer or not crop_type or harvest_amount <= 0:
                st.error("Semua field wajib harus diisi dengan benar!")
            else:
                try:
                    # Get farmer details
                    farmer = next((f for f in farmers if f['name'] == selected_farmer), None)
                    if not farmer:
                        st.error("Petani tidak ditemukan.")
                        return
                    
                    total_value = harvest_amount * price_per_unit
                    
                    harvest_data = {
                        "farmer_id": farmer['_id'],
                        "farmer_name": selected_farmer,
                        "location": farmer.get('location', ''),
                        "crop_type": crop_type,
                        "harvest_amount": harvest_amount,
                        "unit": unit,
                        "harvest_date": harvest_date,
                        "quality_grade": quality_grade,
                        "price_per_unit": price_per_unit,
                        "total_value": total_value,
                        "season": season,
                        "notes": notes,
                        "created_date": datetime.now(),
                        "created_by": ObjectId(st.session_state['user']['id'])
                    }
                    
                    result = db.harvests.insert_one(harvest_data)
                    
                    if result.inserted_id:
                        st.success(f"Hasil panen {crop_type} dari {selected_farmer} berhasil ditambahkan!")
                        st.balloons()
                    else:
                        st.error("Gagal menambahkan hasil panen.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

def seasonal_statistics():
    st.subheader("Statistik Musim Panen")
    
    # Get seasonal statistics
    db = MongoDBConnection.get_database()
    
    # Total harvests by season
    season_stats = list(db.harvests.aggregate([
        {"$group": {"_id": "$season", "total_harvest": {"$sum": "$harvest_amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total_harvest": -1}}
    ]))
    
    # Average price by season
    price_stats = list(db.harvests.aggregate([
        {"$group": {"_id": "$season", "avg_price": {"$avg": "$price_per_unit"}}},
        {"$sort": {"avg_price": -1}}
    ]))
    
    # Top crops by season
    crop_stats = list(db.harvests.aggregate([
        {"$group": {"_id": {"season": "$season", "crop": "$crop_type"}, "total_amount": {"$sum": "$harvest_amount"}}},
        {"$sort": {"total_amount": -1}}
    ]))
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if season_stats:
            top_season = season_stats[0]
            st.metric("Musim Terbanyak", f"{top_season['_id']} ({top_season['count']} panen)")
        else:
            st.metric("Musim Terbanyak", "Belum ada data")
    
    with col2:
        if price_stats:
            highest_price_season = price_stats[0]
            st.metric("Musim Harga Tertinggi", f"{highest_price_season['_id']} (Rp {highest_price_season['avg_price']:,.0f}/unit)")
        else:
            st.metric("Musim Harga Tertinggi", "Belum ada data")
    
    with col3:
        total_harvest = sum(stat['total_harvest'] for stat in season_stats)
        st.metric("Total Panen Keseluruhan", f"{total_harvest:,.1f} kg")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if season_stats:
            st.subheader("Total Panen berdasarkan Musim")
            season_df = pd.DataFrame(season_stats)
            season_df.columns = ['Musim', 'Total Panen (kg)', 'Jumlah']
            st.bar_chart(season_df.set_index('Musim')['Total Panen (kg)'])
    
    with col2:
        if price_stats:
            st.subheader("Harga Rata-rata berdasarkan Musim")
            price_df = pd.DataFrame(price_stats)
            price_df.columns = ['Musim', 'Harga Rata-rata (Rp)']
            st.bar_chart(price_df.set_index('Musim')['Harga Rata-rata (Rp)'])

def seasonal_forecast():
    st.subheader("Prediksi Musim Panen")
    
    st.info("Fitur prediksi musim panen akan segera tersedia dengan algoritma machine learning!")
    
    # Placeholder for future forecasting implementation
    st.write("Prediksi ini akan mencakup:")
    st.write("📊 Jumlah hasil panen yang diperkirakan untuk musim berikutnya")
    st.write("💰 Prediksi harga pasar berdasarkan tren historis")
    st.write("🌦️ Rekomendasi jenis tanaman berdasarkan kondisi cuaca")
    st.write("📈 Analisis tren permintaan pasar")
    
    # Simple trend analysis (placeholder)
    db = MongoDBConnection.get_database()
    
    # Get last 6 months data
    six_months_ago = datetime.now() - timedelta(days=180)
    recent_harvests = list(db.harvests.find({"harvest_date": {"$gte": six_months_ago}}))
    
    if recent_harvests:
        st.write("### Tren Panen 6 Bulan Terakhir")
        
        # Convert to DataFrame for analysis
        recent_df = pd.DataFrame(recent_harvests)
        
        # Simple trend visualization
        monthly_trend = recent_df.groupby(recent_df['harvest_date'].dt.to_period('M'))['harvest_amount'].sum()
        
        if not monthly_trend.empty:
            st.line_chart(monthly_trend)
        
        st.write("### Rekomendasi Sederhana")
        st.write("Berdasarkan data historis, pertimbangkan untuk:")
        st.write("🌱 Menambah varietas tanaman yang memiliki tren naik")
        st.write("💡 Meningkatkan kualitas hasil panen untuk mendapatkan harga lebih baik")
        st.write("📅 Menyesuaikan jadwal tanam dengan musim yang optimal")

def delete_harvest(harvest_id):
    """Delete harvest from database"""
    try:
        db = MongoDBConnection.get_database()
        result = db.harvests.delete_one({"_id": ObjectId(harvest_id)})
        
        if result.deleted_count > 0:
            st.success("Hasil panen berhasil dihapus!")
            st.rerun()
        else:
            st.error("Gagal menghapus hasil panen.")
    except Exception as e:
        st.error(f"Error menghapus hasil panen: {e}")