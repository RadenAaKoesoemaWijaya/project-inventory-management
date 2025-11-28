import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.auth_new import require_auth, require_role
from utils.sqlite_database import (
    get_harvests,
    get_harvests_by_season,
    create_harvest,
    get_farmer_by_id,
    get_warehouses,
    get_database
)
import uuid

def app():
    require_auth()
    
    st.title("🌾 Manajemen Hasil Panen")
    
    # Check if we're in editing mode
    if 'editing_harvest' in st.session_state:
        edit_harvest(st.session_state['editing_harvest'])
        return
    
    # Tabs for different harvest functions
    tab1, tab2, tab3, tab4 = st.tabs(["Daftar Panen", "Tambah Panen", "Statistik Panen", "Analisis Musiman"])
    
    with tab1:
        display_harvests()
    
    with tab2:
        add_harvest()
    
    with tab3:
        harvest_statistics()
    
    with tab4:
        seasonal_analysis()

def display_harvests():
    st.subheader("📋 Daftar Hasil Panen")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        season_filter = st.selectbox("Filter Musim", ["Semua", "Musim Hujan", "Musim Kemarau", "Musim Hujan 2024", "Musim Kemarau 2024"])
    
    with col2:
        crop_filter = st.selectbox("Filter Komoditas", ["Semua", "Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah"])
    
    with col3:
        warehouse_filter = st.selectbox("Filter Lumbung", ["Semua"])
        # Get actual warehouses
        warehouses = get_warehouses()
        if warehouses:
            warehouse_options = ["Semua"] + [w['name'] for w in warehouses]
            warehouse_filter = st.selectbox("Filter Lumbung", warehouse_options)
    
    with col4:
        limit = st.number_input("Jumlah data", min_value=5, max_value=200, value=50)
    
    # Get harvests data
    harvests_df = get_harvests(limit=limit)
    
    # Apply filters
    if season_filter != "Semua":
        harvests_df = harvests_df[harvests_df['season'].str.contains(season_filter.replace("Semua", ""), case=False, na=False)]
    
    if crop_filter != "Semua":
        harvests_df = harvests_df[harvests_df['crop_type'].str.contains(crop_filter, case=False, na=False)]
    
    if warehouse_filter != "Semua":
        harvests_df = harvests_df[harvests_df['warehouse_name'] == warehouse_filter]
    
    if not harvests_df.empty:
        # Display metrics
        col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
        
        with col_metrics1:
            total_quantity = harvests_df['quantity'].sum()
            st.metric("Total Panen", f"{total_quantity:.1f} kg")
        
        with col_metrics2:
            avg_quality = harvests_df['quality_grade'].value_counts().index[0] if not harvests_df['quality_grade'].isna().all() else "N/A"
            st.metric("Kualitas Rata-rata", avg_quality)
        
        with col_metrics3:
            unique_crops = harvests_df['crop_type'].nunique()
            st.metric("Jenis Komoditas", unique_crops)
        
        with col_metrics4:
            recent_harvests = len(harvests_df[pd.to_datetime(harvests_df['harvest_date'], errors='coerce') >= datetime.now() - timedelta(days=30)])
            st.metric("Panen 30 Hari Terakhir", recent_harvests)
        
        # Display harvests in expandable cards
        st.subheader("🌾 Detail Hasil Panen")
        
        for _, harvest in harvests_df.iterrows():
            with st.expander(f"🌾 {harvest.get('crop_type', 'Unknown')} - {harvest.get('harvest_date', 'Unknown Date')} ({harvest.get('quantity', 0)} {harvest.get('unit', 'kg')})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Komoditas:** {harvest.get('crop_type', 'N/A')}")
                    st.write(f"**Tanggal Panen:** {harvest.get('harvest_date', 'N/A')}")
                    st.write(f"**Musim:** {harvest.get('season', 'N/A')}")
                    st.write(f"**Jumlah:** {harvest.get('quantity', 0)} {harvest.get('unit', 'kg')}")
                
                with col2:
                    st.write(f"**Kualitas:** {harvest.get('quality_grade', 'N/A')}")
                    st.write(f"**Lumbung:** {harvest.get('warehouse_name', 'N/A')}")
                    st.write(f"**Petani ID:** {harvest.get('farmer_id', 'N/A')}")
                    st.write(f"**Catatan:** {harvest.get('notes', 'Tidak ada')}")
                
                # Quality indicator
                quality_colors = {
                    'A': '🟢',
                    'B': '🟡', 
                    'C': '🟠',
                    'D': '🔴'
                }
                quality_indicator = quality_colors.get(harvest.get('quality_grade', 'N/A'), '⚪')
                st.write(f"**Indikator Kualitas:** {quality_indicator} {harvest.get('quality_grade', 'N/A')}")
        
        # Display harvests table
        st.subheader("📊 Tabel Data Panen")
        
        # Prepare display dataframe
        display_df = harvests_df.copy()
        display_df['tanggal'] = pd.to_datetime(display_df['harvest_date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Select columns to display
        display_columns = ['tanggal', 'crop_type', 'season', 'quantity', 'unit', 'quality_grade', 'warehouse_name']
        available_columns = [col for col in display_columns if col in display_df.columns]
        
        st.dataframe(
            display_df[available_columns].rename(columns={
                'tanggal': 'Tanggal',
                'crop_type': 'Komoditas',
                'season': 'Musim',
                'quantity': 'Jumlah',
                'unit': 'Satuan',
                'quality_grade': 'Kualitas',
                'warehouse_name': 'Lumbung'
            }),
            use_container_width=True
        )
        
    else:
        st.info("📭 Tidak ada data panen yang ditemukan dengan filter yang dipilih.")
        
        # Add sample data button for admin users
        if st.session_state['user']['role'] == 'admin':
            if st.button("📊 Tambah Data Sampel Panen", use_container_width=True):
                add_sample_harvests()

def add_harvest():
    st.subheader("➕ Tambah Hasil Panen Baru")
    
    with st.form("add_harvest_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Get warehouses for selection
            warehouses = get_warehouses()
            if warehouses:
                warehouse_options = {w['name']: w['id'] for w in warehouses}
                selected_warehouse = st.selectbox("Lumbung*", list(warehouse_options.keys()))
                warehouse_id = warehouse_options[selected_warehouse]
            else:
                st.error("Tidak ada lumbung tersedia!")
                warehouse_id = None
            
            harvest_date = st.date_input("Tanggal Panen*", value=datetime.now())
            season = st.selectbox("Musim*", ["Musim Hujan", "Musim Kemarau", "Musim Hujan 2024", "Musim Kemarau 2024", "Lainnya"])
            crop_type = st.selectbox("Komoditas*", ["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"])
        
        with col2:
            quantity = st.number_input("Jumlah Panen*", min_value=0.1, step=0.1, value=100.0)
            unit = st.selectbox("Satuan*", ["kg", "ton", "karung", "sak"])
            quality_grade = st.selectbox("Kualitas*", ["A", "B", "C", "D"])
            
            # Get farmers for selection
            from utils.sqlite_database import get_farmers
            farmers_df = get_farmers(limit=100)
            if not farmers_df.empty:
                farmer_options = {"Pilih Petani": None}
                farmer_options.update({f"{row['name']} - {row['location']}": row['id'] for _, row in farmers_df.iterrows()})
                selected_farmer = st.selectbox("Petani (Opsional)", list(farmer_options.keys()))
                farmer_id = farmer_options[selected_farmer]
            else:
                st.warning("Tidak ada data petani. Anda bisa menambahkan petani terlebih dahulu.")
                farmer_id = None
        
        # Additional information
        st.subheader("📝 Informasi Tambahan")
        
        col3, col4 = st.columns(2)
        
        with col3:
            harvest_method = st.selectbox("Metode Panen", ["Manual", "Mekanis", "Campuran", "Lainnya"])
            weather_condition = st.selectbox("Kondisi Cuaca", ["Cerah", "Berawan", "Hujan Ringan", "Hujan Lebat"])
        
        with col4:
            storage_condition = st.selectbox("Kondisi Penyimpanan", ["Baik", "Cukup Baik", "Kurang Baik"])
            estimated_market_price = st.number_input("Estimasi Harga Pasar (Rp/kg)", min_value=0, step=100, value=10000)
        
        notes = st.text_area("Catatan", placeholder="Informasi tambahan tentang hasil panen...")
        
        submit_harvest = st.form_submit_button("🌾 Tambah Hasil Panen", use_container_width=True)
        
        if submit_harvest and warehouse_id:
            if harvest_date and season and crop_type and quantity > 0:
                success, message = create_harvest(
                    warehouse_id=warehouse_id,
                    farmer_id=farmer_id,
                    harvest_date=harvest_date.isoformat(),
                    season=season,
                    crop_type=crop_type,
                    quantity=quantity,
                    unit=unit,
                    quality_grade=quality_grade,
                    notes=f"{notes}\nMetode Panen: {harvest_method}\nKondisi Cuaca: {weather_condition}\nKondisi Penyimpanan: {storage_condition}\nEstimasi Harga: Rp {estimated_market_price}/kg"
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Mohon lengkapi field yang wajib diisi (ditandai *)!")

def edit_harvest(harvest_id):
    st.subheader(f"✏️ Edit Hasil Panen")
    
    # Get harvest data
    harvests_df = get_harvests(limit=1000)
    harvest = harvests_df[harvests_df['id'] == harvest_id]
    
    if harvest.empty:
        st.error("❌ Data panen tidak ditemukan!")
        if st.button("Kembali"):
            del st.session_state['editing_harvest']
            st.rerun()
        return
    
    harvest = harvest.iloc[0]
    
    with st.form("edit_harvest_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Get warehouses for selection
            warehouses = get_warehouses()
            if warehouses:
                warehouse_options = {w['name']: w['id'] for w in warehouses}
                current_warehouse = harvest.get('warehouse_name', 'Unknown')
                if current_warehouse in warehouse_options:
                    selected_warehouse = st.selectbox("Lumbung*", list(warehouse_options.keys()), 
                                                     index=list(warehouse_options.keys()).index(current_warehouse))
                else:
                    selected_warehouse = st.selectbox("Lumbung*", list(warehouse_options.keys()))
                warehouse_id = warehouse_options[selected_warehouse]
            
            harvest_date = st.date_input("Tanggal Panen*", value=pd.to_datetime(harvest.get('harvest_date')).date())
            season = st.selectbox("Musim*", ["Musim Hujan", "Musim Kemarau", "Musim Hujan 2024", "Musim Kemarau 2024", "Lainnya"],
                                  index=["Musim Hujan", "Musim Kemarau", "Musim Hujan 2024", "Musim Kemarau 2024", "Lainnya"].index(harvest.get('season', 'Musim Hujan')))
            crop_type = st.selectbox("Komoditas*", ["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"],
                                    index=["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"].index(harvest.get('crop_type', 'Beras')))
        
        with col2:
            quantity = st.number_input("Jumlah Panen*", min_value=0.1, step=0.1, value=float(harvest.get('quantity', 100.0)))
            unit = st.selectbox("Satuan*", ["kg", "ton", "karung", "sak"],
                              index=["kg", "ton", "karung", "sak"].index(harvest.get('unit', 'kg')))
            quality_grade = st.selectbox("Kualitas*", ["A", "B", "C", "D"],
                                       index=["A", "B", "C", "D"].index(harvest.get('quality_grade', 'A')))
        
        notes = st.text_area("Catatan", value=harvest.get('notes', ''), placeholder="Informasi tambahan tentang hasil panen...")
        
        col_submit1, col_submit2 = st.columns(2)
        
        with col_submit1:
            submit_edit = st.form_submit_button("💾 Simpan Perubahan")
        
        with col_submit2:
            cancel_edit = st.form_submit_button("❌ Batal")
        
        if submit_edit:
            if harvest_date and season and crop_type and quantity > 0:
                # Update harvest in database
                db = get_database()
                conn = db._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE harvests 
                    SET warehouse_id = ?, harvest_date = ?, season = ?, crop_type = ?, 
                        quantity = ?, unit = ?, quality_grade = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (warehouse_id, harvest_date.isoformat(), season, crop_type, quantity, unit, quality_grade, notes, harvest_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    st.success("✅ Data panen berhasil diupdate!")
                    del st.session_state['editing_harvest']
                    st.rerun()
                else:
                    st.error("❌ Gagal mengupdate data panen")
            else:
                st.error("❌ Mohon lengkapi field yang wajib diisi!")
        
        if cancel_edit:
            del st.session_state['editing_harvest']
            st.rerun()

def harvest_statistics():
    st.subheader("📊 Statistik Hasil Panen")
    
    # Get all harvests data
    harvests_df = get_harvests(limit=1000)
    
    if not harvests_df.empty:
        # Convert dates
        harvests_df['harvest_date_dt'] = pd.to_datetime(harvests_df['harvest_date'], errors='coerce')
        
        # Overview metrics
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            total_quantity = harvests_df['quantity'].sum()
            st.metric("Total Produksi", f"{total_quantity:.1f} kg")
        
        with col_stat2:
            avg_harvest = harvests_df['quantity'].mean()
            st.metric("Rata-rata per Panen", f"{avg_harvest:.1f} kg")
        
        with col_stat3:
            total_harvests = len(harvests_df)
            st.metric("Total Panen", total_harvests)
        
        with col_stat4:
            unique_crops = harvests_df['crop_type'].nunique()
            st.metric("Jenis Komoditas", unique_crops)
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Crop type distribution
            crop_totals = harvests_df.groupby('crop_type')['quantity'].sum().sort_values(ascending=False)
            
            fig = px.bar(
                x=crop_totals.values,
                y=crop_totals.index,
                orientation='h',
                title="Total Produksi per Komoditas",
                color=crop_totals.values,
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            # Quality grade distribution
            quality_counts = harvests_df['quality_grade'].value_counts()
            
            fig = px.pie(
                values=quality_counts.values, 
                names=quality_counts.index,
                title="Distribusi Kualitas Panen",
                color_discrete_map={"A": "green", "B": "lightgreen", "C": "orange", "D": "red"}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Seasonal trends
        st.subheader("📈 Tren Produksi Musiman")
        
        harvests_df['harvest_month'] = harvests_df['harvest_date_dt'].dt.to_period('M')
        monthly_totals = harvests_df.groupby('harvest_month')['quantity'].sum().reset_index()
        monthly_totals['harvest_month'] = monthly_totals['harvest_month'].dt.to_timestamp()
        
        if not monthly_totals.empty:
            fig = px.line(
                monthly_totals, 
                x='harvest_month', 
                y='quantity',
                title="Tren Produksi Bulanan",
                markers=True,
                line_shape='linear'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Warehouse distribution
        st.subheader("🏪 Distribusi Produksi per Lumbung")
        
        warehouse_totals = harvests_df.groupby('warehouse_name')['quantity'].sum().sort_values(ascending=False)
        
        fig = px.bar(
            x=warehouse_totals.values,
            y=warehouse_totals.index,
            orientation='h',
            title="Total Produksi per Lumbung",
            color=warehouse_totals.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data panen untuk statistik.")

def seasonal_analysis():
    st.subheader("🌾 Analisis Musiman")
    
    # Get all harvests data
    harvests_df = get_harvests(limit=1000)
    
    if not harvests_df.empty:
        # Convert dates
        harvests_df['harvest_date_dt'] = pd.to_datetime(harvests_df['harvest_date'], errors='coerce')
        
        # Season comparison
        st.subheader("📊 Perbandingan Musiman")
        
        season_stats = harvests_df.groupby('season').agg({
            'quantity': ['sum', 'mean', 'count'],
            'crop_type': 'nunique'
        }).round(2)
        
        season_stats.columns = ['Total Produksi (kg)', 'Rata-rata (kg)', 'Jumlah Panen', 'Jenis Komoditas']
        
        st.dataframe(season_stats, use_container_width=True)
        
        # Quality by season
        st.subheader("🟢 Kualitas per Musim")
        
        quality_by_season = pd.crosstab(harvests_df['season'], harvests_df['quality_grade'])
        
        fig = px.imshow(
            quality_by_season.values,
            x=quality_by_season.columns,
            y=quality_by_season.index,
            title="Heatmap Kualitas per Musim",
            color_continuous_scale='RdYlGn',
            aspect="auto"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Crop performance by season
        st.subheader("🌱 Performa Komoditas per Musim")
        
        crop_season_performance = harvests_df.groupby(['season', 'crop_type'])['quantity'].sum().unstack(fill_value=0)
        
        st.dataframe(crop_season_performance, use_container_width=True)
        
        # Year over year comparison
        st.subheader("📈 Perbandingan Tahun ke Tahun")
        
        harvests_df['year'] = harvests_df['harvest_date_dt'].dt.year
        yearly_totals = harvests_df.groupby('year')['quantity'].sum()
        
        if len(yearly_totals) > 1:
            fig = px.bar(
                x=yearly_totals.index,
                y=yearly_totals.values,
                title="Total Produksi Tahunan",
                color=yearly_totals.values,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data panen untuk analisis musiman.")

def add_sample_harvests():
    """Add sample harvest data for testing"""
    # Get warehouses
    warehouses = get_warehouses()
    if not warehouses:
        st.error("Tidak ada lumbung tersedia!")
        return
    
    warehouse_id = warehouses[0]['id']
    
    sample_harvests = [
        {
            'warehouse_id': warehouse_id,
            'farmer_id': None,
            'harvest_date': (datetime.now() - timedelta(days=30)).isoformat(),
            'season': 'Musim Hujan 2024',
            'crop_type': 'Beras',
            'quantity': 500.0,
            'unit': 'kg',
            'quality_grade': 'A',
            'notes': 'Panen musim hujan dengan kualitas terbaik'
        },
        {
            'warehouse_id': warehouse_id,
            'farmer_id': None,
            'harvest_date': (datetime.now() - timedelta(days=20)).isoformat(),
            'season': 'Musim Hujan 2024',
            'crop_type': 'Jagung',
            'quantity': 300.0,
            'unit': 'kg',
            'quality_grade': 'B',
            'notes': 'Panen jagung dengan kualitas baik'
        },
        {
            'warehouse_id': warehouse_id,
            'farmer_id': None,
            'harvest_date': (datetime.now() - timedelta(days=10)).isoformat(),
            'season': 'Musim Hujan 2024',
            'crop_type': 'Kacang-kacangan',
            'quantity': 150.0,
            'unit': 'kg',
            'quality_grade': 'A',
            'notes': 'Panen kacang-kacangan organik'
        }
    ]
    
    for harvest_data in sample_harvests:
        create_harvest(**harvest_data)
    
    st.success("✅ Data sampel panen berhasil ditambahkan!")
    st.rerun()

if __name__ == "__main__":
    app()
