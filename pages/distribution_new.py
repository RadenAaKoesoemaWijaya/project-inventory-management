import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.auth_new import require_auth, require_role
from utils.sqlite_database import (
    get_merchants,
    get_warehouses,
    get_harvests,
    get_database,
    get_distributions,
    create_distribution,
    update_distribution_status
)
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)

def app():
    require_auth()
    
    st.title("🚚 Pemetaan Distribusi Hasil Panen")
    
    # Check if we're in editing mode
    if 'editing_distribution' in st.session_state:
        edit_distribution(st.session_state['editing_distribution'])
        return
    
    # Tabs for different distribution functions
    tab1, tab2, tab3, tab4 = st.tabs(["Daftar Distribusi", "Tambah Distribusi", "Rute Distribusi", "Analisis Distribusi"])
    
    with tab1:
        display_distributions()
    
    with tab2:
        add_distribution()
    
    with tab3:
        route_mapping()
    
    with tab4:
        distribution_analysis()

def display_distributions():
    st.subheader("📋 Daftar Distribusi")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox("Filter Status", ["Semua", "Pending", "In Progress", "Completed", "Cancelled"])
    
    with col2:
        warehouse_filter = st.selectbox("Filter Lumbung Asal", ["Semua"])
        # Get actual warehouses
        warehouses = get_warehouses()
        if warehouses:
            warehouse_options = ["Semua"] + [w['name'] for w in warehouses]
            warehouse_filter = st.selectbox("Filter Lumbung Asal", warehouse_options)
    
    with col3:
        merchant_filter = st.selectbox("Filter Pedagang", ["Semua"])
        # Get actual merchants
        merchants_df = get_merchants(limit=100)
        if not merchants_df.empty:
            merchant_options = ["Semua"] + merchants_df['name'].tolist()[:10]
            merchant_filter = st.selectbox("Filter Pedagang", merchant_options)
    
    with col4:
        limit = st.number_input("Jumlah data", min_value=5, max_value=200, value=50)
    
    # Get distributions data
    distributions_df = get_distributions(limit=limit)
    
    # Apply filters
    if status_filter != "Semua":
        distributions_df = distributions_df[distributions_df['status'].str.contains(status_filter, case=False, na=False)]
    
    if warehouse_filter != "Semua":
        distributions_df = distributions_df[distributions_df['warehouse_name'] == warehouse_filter]
    
    if merchant_filter != "Semua":
        distributions_df = distributions_df[distributions_df['merchant_name'] == merchant_filter]
    
    if not distributions_df.empty:
        # Display metrics
        col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
        
        with col_metrics1:
            total_distributed = distributions_df['quantity'].sum()
            st.metric("Total Terdistribusi", f"{total_distributed:.1f} kg")
        
        with col_metrics2:
            active_distributions = len(distributions_df[distributions_df['status'].isin(['Pending', 'In Progress'])])
            st.metric("Distribusi Aktif", active_distributions)
        
        with col_metrics3:
            completed_distributions = len(distributions_df[distributions_df['status'] == 'Completed'])
            st.metric("Selesai", completed_distributions)
        
        with col_metrics4:
            avg_distance = distributions_df['distance'].mean() if 'distance' in distributions_df.columns else 0
            st.metric("Rata-rata Jarak", f"{avg_distance:.1f} km")
        
        # Display distributions in expandable cards
        st.subheader("🚚 Detail Distribusi")
        
        for _, distribution in distributions_df.iterrows():
            with st.expander(f"🚚 {distribution.get('merchant_name', 'Unknown')} - {distribution.get('status', 'Unknown')} ({distribution.get('quantity', 0)} {distribution.get('unit', 'kg')})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID Distribusi:** {distribution.get('id', 'N/A')}")
                    st.write(f"**Pedagang:** {distribution.get('merchant_name', 'N/A')}")
                    st.write(f"**Lumbung Asal:** {distribution.get('warehouse_name', 'N/A')}")
                    st.write(f"**Komoditas:** {distribution.get('crop_type', 'N/A')}")
                
                with col2:
                    st.write(f"**Jumlah:** {distribution.get('quantity', 0)} {distribution.get('unit', 'kg')}")
                    st.write(f"**Tanggal Pengiriman:** {distribution.get('delivery_date', 'N/A')}")
                    st.write(f"**Status:** {get_status_emoji(distribution.get('status', 'N/A'))} {distribution.get('status', 'N/A')}")
                    st.write(f"**Jarak:** {distribution.get('distance', 0)} km")
                
                # Action buttons
                col_action1, col_action2 = st.columns(2)
                
                with col_action1:
                    if st.button(f"✏️ Edit {distribution.get('id')}", key=f"edit_{distribution['id']}"):
                        st.session_state['editing_distribution'] = distribution['id']
                        st.rerun()
                
                with col_action2:
                    if st.button(f"🚚 Update Status {distribution.get('id')}", key=f"status_{distribution['id']}"):
                        update_distribution_status(distribution['id'])
                        st.rerun()
        
        # Display distributions table
        st.subheader("📊 Tabel Data Distribusi")
        
        # Prepare display dataframe
        display_df = distributions_df.copy()
        display_df['tanggal'] = pd.to_datetime(display_df['delivery_date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Select columns to display
        display_columns = ['tanggal', 'merchant_name', 'warehouse_name', 'crop_type', 'quantity', 'unit', 'status']
        available_columns = [col for col in display_columns if col in display_df.columns]
        
        st.dataframe(
            display_df[available_columns].rename(columns={
                'tanggal': 'Tanggal',
                'merchant_name': 'Pedagang',
                'warehouse_name': 'Lumbung Asal',
                'crop_type': 'Komoditas',
                'quantity': 'Jumlah',
                'unit': 'Satuan',
                'status': 'Status'
            }),
            use_container_width=True
        )
        
    else:
        st.info("📭 Tidak ada data distribusi yang ditemukan dengan filter yang dipilih.")
        
        # Add sample data button for admin users
        if st.session_state['user']['role'] == 'admin':
            if st.button("📊 Tambah Data Sampel Distribusi", use_container_width=True):
                add_sample_distributions()

def add_distribution():
    st.subheader("➕ Tambah Distribusi Baru")
    
    with st.form("add_distribution_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Get merchants for selection
            merchants_df = get_merchants(limit=100)
            if not merchants_df.empty:
                merchant_options = {f"{row['name']} - {row['location']}": row['id'] for _, row in merchants_df.iterrows()}
                selected_merchant = st.selectbox("Pedagang*", list(merchant_options.keys()))
                merchant_id = merchant_options[selected_merchant]
            else:
                st.error("Tidak ada data pedagang. Tambahkan pedagang terlebih dahulu!")
                merchant_id = None
            
            # Get warehouses for selection
            warehouses = get_warehouses()
            if warehouses:
                warehouse_options = {w['name']: w['id'] for w in warehouses}
                selected_warehouse = st.selectbox("Lumbung Asal*", list(warehouse_options.keys()))
                warehouse_id = warehouse_options[selected_warehouse]
            else:
                st.error("Tidak ada lumbung tersedia!")
                warehouse_id = None
        
        with col2:
            delivery_date = st.date_input("Tanggal Pengiriman*", value=datetime.now())
            crop_type = st.selectbox("Komoditas*", ["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"])
            quantity = st.number_input("Jumlah*", min_value=0.1, step=0.1, value=100.0)
            unit = st.selectbox("Satuan*", ["kg", "ton", "karung", "sak"])
        
        # Additional information
        st.subheader("📝 Informasi Tambahan")
        
        col3, col4 = st.columns(2)
        
        with col3:
            priority = st.selectbox("Prioritas", ["Normal", "Tinggi", "Rendah"])
            delivery_method = st.selectbox("Metode Pengiriman", ["Truk", "Pickup", "Motor", "Lainnya"])
        
        with col4:
            estimated_distance = st.number_input("Estimasi Jarak (km)", min_value=0.1, step=0.1, value=5.0)
            estimated_cost = st.number_input("Estimasi Biaya (Rp)", min_value=0, step=1000, value=50000)
        
        notes = st.text_area("Catatan", placeholder="Informasi tambahan tentang distribusi...")
        
        submit_distribution = st.form_submit_button("🚚 Tambah Distribusi", use_container_width=True)
        
        if submit_distribution and merchant_id and warehouse_id:
            if delivery_date and crop_type and quantity > 0:
                success, message = create_distribution(
                    merchant_id=merchant_id,
                    warehouse_id=warehouse_id,
                    delivery_date=delivery_date.isoformat(),
                    crop_type=crop_type,
                    quantity=quantity,
                    unit=unit,
                    priority=priority,
                    delivery_method=delivery_method,
                    estimated_distance=estimated_distance,
                    estimated_cost=estimated_cost,
                    notes=notes
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Mohon lengkapi field yang wajib diisi (ditandai *)!")

def route_mapping():
    st.subheader("🗺️ Pemetaan Rute Distribusi")
    
    # Get active distributions
    distributions_df = get_distributions(status="In Progress")
    
    if not distributions_df.empty:
        # Optimization Options
        st.subheader("🎯 Opsi Optimalisasi Rute")
        
        col_opt1, col_opt2, col_opt3 = st.columns(3)
        
        with col_opt1:
            optimization_method = st.selectbox("Metode Optimalisasi", [
                "Distance (2-opt)",
                "VRP (OR-Tools)",
                "Simple TSP"
            ])
            
        with col_opt2:
            num_vehicles = st.number_input("Jumlah Kendaraan", min_value=1, max_value=10, value=1)
            
        with col_opt3:
            vehicle_capacity = st.number_input("Kapasitas per Kendaraan (kg)", min_value=100, max_value=10000, value=1000)
            
        if st.button("� Optimalkan Rute", use_container_width=True):
            with st.spinner("Mengoptimalkan rute..."):
                # Prepare data for optimizer
                destinations = []
                for _, row in distributions_df.iterrows():
                    if row.get('merchant_location'):
                        try:
                            lat, lng = map(float, row['merchant_location'].split(','))
                            destinations.append({
                                'id': row['id'],
                                'merchant_name': row['merchant_name'],
                                'coordinates': {'lat': lat, 'lng': lng},
                                'weight_kg': row['quantity']
                            })
                        except:
                            continue
                
                # Get warehouse location (assuming first one for now or from filter)
                # Ideally should be selected
                warehouse_coord = (-7.250445, 112.768845) # Default Surabaya
                if not distributions_df.empty and distributions_df.iloc[0].get('warehouse_location'):
                    try:
                        w_lat, w_lng = map(float, distributions_df.iloc[0]['warehouse_location'].split(','))
                        warehouse_coord = (w_lat, w_lng)
                    except:
                        pass
                
                # Run optimization
                optimizer = DistributionOptimizer()
                
                opt_type_map = {
                    "Distance (2-opt)": "distance",
                    "VRP (OR-Tools)": "vrp",
                    "Simple TSP": "simple"
                }
                
                result = optimizer.optimize_delivery_route(
                    destinations, 
                    warehouse_coord, 
                    optimization_type=opt_type_map[optimization_method],
                    num_vehicles=num_vehicles,
                    vehicle_capacity=vehicle_capacity
                )
                
                if result.get('error'):
                    st.error(f"❌ Error: {result['error']}")
                else:
                    st.success("✅ Rute berhasil dioptimalkan!")
                    
                    # Display results
                    col_res1, col_res2 = st.columns(2)
                    
                    with col_res1:
                        st.metric("Total Jarak", f"{result['cost']['total_distance_km']} km")
                        st.metric("Total Biaya", f"Rp {result['cost']['total_cost_rp']:,.0f}")
                    
                    with col_res2:
                        st.metric("Efisiensi", f"{result['efficiency']} kg/km")
                        st.metric("Biaya per kg", f"Rp {result['cost']['cost_per_kg']:,.0f}")
                    
                    # Display routes
                    if 'routes' in result:
                        st.subheader("🚚 Detail Rute per Kendaraan")
                        for route in result['routes']:
                            with st.expander(f"Kendaraan {route['vehicle_id']} (Muatan: {route['load_kg']} kg, Jarak: {route['distance_km']:.1f} km)"):
                                st.write(f"**Total Muatan:** {route['load_kg']} kg")
                                st.write(f"**Jarak Tempuh:** {route['distance_km']:.1f} km")
                                st.write("**Urutan Pengiriman:**")
                                for idx, stop in enumerate(route['route']):
                                    st.write(f"{idx+1}. {stop['merchant_name']} ({stop['weight_kg']} kg)")
                    else:
                        st.subheader("🚚 Urutan Pengiriman")
                        for idx, stop in enumerate(result['route']):
                            st.write(f"{idx+1}. {stop['merchant_name']} ({stop['weight_kg']} kg)")
                            
                    # Map visualization (Placeholder)
                    st.info("📍 Peta rute akan ditampilkan di sini (menggunakan Folium/Plotly Map)")
        
        # Route summary table
        st.subheader("📊 Ringkasan Data Distribusi")
        route_summary = distributions_df.groupby(['warehouse_name', 'merchant_name']).agg({
            'quantity': 'sum',
            'distance': 'mean',
            'estimated_cost': 'sum'
        }).round(2)
        
        route_summary.columns = ['Total Jumlah (kg)', 'Rata-rata Jarak (km)', 'Total Biaya (Rp)']
        st.dataframe(route_summary, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada distribusi aktif untuk dipetakan.")

def distribution_analysis():
    st.subheader("📊 Analisis Distribusi")
    
    # Get all distributions data
    distributions_df = get_distributions(limit=1000)
    
    if not distributions_df.empty:
        # Convert dates
        distributions_df['delivery_date_dt'] = pd.to_datetime(distributions_df['delivery_date'], errors='coerce')
        
        # Overview metrics
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            total_distributed = distributions_df['quantity'].sum()
            st.metric("Total Terdistribusi", f"{total_distributed:.1f} kg")
        
        with col_stat2:
            avg_distance = distributions_df['distance'].mean()
            st.metric("Rata-rata Jarak", f"{avg_distance:.1f} km")
        
        with col_stat3:
            total_cost = distributions_df['estimated_cost'].sum()
            st.metric("Total Biaya", f"Rp {total_cost:,.0f}")
        
        with col_stat4:
            completion_rate = len(distributions_df[distributions_df['status'] == 'Completed']) / len(distributions_df) * 100
            st.metric("Tingkat Penyelesaian", f"{completion_rate:.1f}%")
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Status distribution
            status_counts = distributions_df['status'].value_counts()
            
            fig = px.pie(
                values=status_counts.values, 
                names=status_counts.index,
                title="Distribusi Status Pengiriman",
                color_discrete_map={"Completed": "green", "In Progress": "blue", "Pending": "orange", "Cancelled": "red"}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            # Crop type distribution
            crop_totals = distributions_df.groupby('crop_type')['quantity'].sum()
            
            fig = px.bar(
                x=crop_totals.values,
                y=crop_totals.index,
                orientation='h',
                title="Total Distribusi per Komoditas",
                color=crop_totals.values,
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Monthly trends
        st.subheader("📈 Tren Distribusi Bulanan")
        
        distributions_df['delivery_month'] = distributions_df['delivery_date_dt'].dt.to_period('M')
        monthly_totals = distributions_df.groupby('delivery_month').agg({
            'quantity': 'sum',
            'estimated_cost': 'sum'
        }).reset_index()
        monthly_totals['delivery_month'] = monthly_totals['delivery_month'].dt.to_timestamp()
        
        if not monthly_totals.empty:
            fig = px.line(
                monthly_totals, 
                x='delivery_month', 
                y='quantity',
                title="Tren Distribusi Bulanan (Jumlah)",
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Cost analysis
        st.subheader("💰 Analisis Biaya Distribusi")
        
        col_cost1, col_cost2 = st.columns(2)
        
        with col_cost1:
            # Cost per km
            distributions_df['cost_per_km'] = distributions_df['estimated_cost'] / distributions_df['distance']
            avg_cost_per_km = distributions_df['cost_per_km'].mean()
            st.metric("Biaya per km (Rata-rata)", f"Rp {avg_cost_per_km:,.0f}")
        
        with col_cost2:
            # Cost per kg
            distributions_df['cost_per_kg'] = distributions_df['estimated_cost'] / distributions_df['quantity']
            avg_cost_per_kg = distributions_df['cost_per_kg'].mean()
            st.metric("Biaya per kg (Rata-rata)", f"Rp {avg_cost_per_kg:,.0f}")
        
        # Cost by distance
        fig = px.scatter(
            distributions_df, 
            x='distance', 
            y='estimated_cost',
            color='crop_type',
            title="Biaya vs Jarak Pengiriman",
            size='quantity'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data distribusi untuk analisis.")




def get_status_emoji(status):
    """Get emoji for distribution status"""
    status_emojis = {
        'Pending': '⏳',
        'In Progress': '🚚',
        'Completed': '✅',
        'Cancelled': '❌'
    }
    return status_emojis.get(status, '📋')

def edit_distribution(distribution_id):
    """Edit distribution form"""
    st.subheader(f"✏️ Edit Distribusi")
    
    # Get distribution data
    distributions_df = get_distributions(limit=1000)
    distribution = distributions_df[distributions_df['id'] == distribution_id]
    
    if distribution.empty:
        st.error("❌ Data distribusi tidak ditemukan!")
        if st.button("Kembali"):
            del st.session_state['editing_distribution']
            st.rerun()
        return
    
    distribution = distribution.iloc[0]
    
    with st.form("edit_distribution_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Get merchants for selection
            merchants_df = get_merchants(limit=100)
            if not merchants_df.empty:
                merchant_options = {f"{row['name']} - {row['location']}": row['id'] for _, row in merchants_df.iterrows()}
                current_merchant = distribution.get('merchant_name', 'Unknown')
                current_merchant_key = next((k for k, v in merchant_options.items() if current_merchant in k), list(merchant_options.keys())[0])
                selected_merchant = st.selectbox("Pedagang*", list(merchant_options.keys()), index=list(merchant_options.keys()).index(current_merchant_key))
                merchant_id = merchant_options[selected_merchant]
            
            # Get warehouses for selection
            warehouses = get_warehouses()
            if warehouses:
                warehouse_options = {w['name']: w['id'] for w in warehouses}
                current_warehouse = distribution.get('warehouse_name', 'Unknown')
                selected_warehouse = st.selectbox("Lumbung Asal*", list(warehouse_options.keys()), 
                                                 index=list(warehouse_options.keys()).index(current_warehouse))
                warehouse_id = warehouse_options[selected_warehouse]
        
        with col2:
            delivery_date = st.date_input("Tanggal Pengiriman*", value=pd.to_datetime(distribution.get('delivery_date')).date())
            crop_type = st.selectbox("Komoditas*", ["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"],
                                    index=["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"].index(distribution.get('crop_type', 'Beras')))
            quantity = st.number_input("Jumlah*", min_value=0.1, step=0.1, value=float(distribution.get('quantity', 100.0)))
            unit = st.selectbox("Satuan*", ["kg", "ton", "karung", "sak"],
                              index=["kg", "ton", "karung", "sak"].index(distribution.get('unit', 'kg')))
        
        notes = st.text_area("Catatan", value=distribution.get('notes', ''), placeholder="Informasi tambahan tentang distribusi...")
        
        col_submit1, col_submit2 = st.columns(2)
        
        with col_submit1:
            submit_edit = st.form_submit_button("💾 Simpan Perubahan")
        
        with col_submit2:
            cancel_edit = st.form_submit_button("❌ Batal")
        
        if submit_edit:
            if delivery_date and crop_type and quantity > 0:
                # Update distribution in database
                db = get_database()
                conn = db._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE distributions 
                    SET merchant_id = ?, warehouse_id = ?, delivery_date = ?, crop_type = ?, 
                        quantity = ?, unit = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (merchant_id, warehouse_id, delivery_date.isoformat(), crop_type, quantity, unit, notes, distribution_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    st.success("✅ Data distribusi berhasil diupdate!")
                    del st.session_state['editing_distribution']
                    st.rerun()
                else:
                    st.error("❌ Gagal mengupdate data distribusi")
            else:
                st.error("❌ Mohon lengkapi field yang wajib diisi!")
        
        if cancel_edit:
            del st.session_state['editing_distribution']
            st.rerun()

def add_sample_distributions():
    """Add sample distribution data for testing"""
    # Get merchants and warehouses
    merchants_df = get_merchants(limit=10)
    warehouses = get_warehouses()
    
    if merchants_df.empty or not warehouses:
        st.error("Tidak ada data pedagang atau lumbung tersedia!")
        return
    
    merchant_id = merchants_df.iloc[0]['id']
    warehouse_id = warehouses[0]['id']
    
    sample_distributions = [
        {
            'merchant_id': merchant_id,
            'warehouse_id': warehouse_id,
            'delivery_date': (datetime.now() + timedelta(days=1)).isoformat(),
            'crop_type': 'Beras',
            'quantity': 200.0,
            'unit': 'kg',
            'priority': 'Normal',
            'delivery_method': 'Truck',
            'estimated_distance': 8.5,
            'estimated_cost': 75000,
            'notes': 'Distribusi rutin mingguan'
        },
        {
            'merchant_id': merchant_id,
            'warehouse_id': warehouse_id,
            'delivery_date': (datetime.now() + timedelta(days=3)).isoformat(),
            'crop_type': 'Jagung',
            'quantity': 150.0,
            'unit': 'kg',
            'priority': 'Tinggi',
            'delivery_method': 'Truck',
            'estimated_distance': 12.0,
            'estimated_cost': 100000,
            'notes': 'Distribusi prioritas tinggi'
        }
    ]
    
    for dist_data in sample_distributions:
        create_distribution(**dist_data)
    
    st.success("✅ Data sampel distribusi berhasil ditambahkan!")
    st.rerun()

if __name__ == "__main__":
    app()
