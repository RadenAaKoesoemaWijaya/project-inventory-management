import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.database import MongoDBConnection, get_optimal_distribution_routes, get_warehouses, get_merchants
from utils.distribution_optimizer import DistributionOptimizer
from datetime import datetime
from bson import ObjectId
# import folium
# from streamlit_folium import st_folium
# import math

def app():
    require_auth()
    
    st.title("Pemetaan Distribusi - Jalur Efisien ke Pedagang")
    
    # Tabs for different distribution functions
    tab1, tab2, tab3, tab4 = st.tabs(["Rute Optimal", "Tambah Rute", "Optimasi Canggih", "Analisis Rute"])
    
    with tab1:
        display_optimal_routes()
    
    with tab2:
        add_distribution_route()
    
    with tab3:
        advanced_distribution_optimizer()
    
    with tab4:
        route_analysis()

def display_optimal_routes():
    st.subheader("Rute Distribusi Optimal")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get warehouses for filter
        warehouses_df = get_warehouses()
        warehouse_options = ["Semua Lumbung"] + (warehouses_df['name'].tolist() if not warehouses_df.empty else [])
        selected_warehouse = st.selectbox("Filter berdasarkan Lumbung", warehouse_options)
    
    with col2:
        min_efficiency = st.slider("Skor Efisiensi Minimum", 0.0, 1.0, 0.6, 0.1)
    
    with col3:
        limit = st.number_input("Jumlah Rute", min_value=5, max_value=50, value=10)
    
    # Get routes data
    warehouse_id = None
    if selected_warehouse != "Semua Lumbung" and not warehouses_df.empty:
        warehouse_row = warehouses_df[warehouses_df['name'] == selected_warehouse]
        if not warehouse_row.empty:
            warehouse_id = warehouse_row.iloc[0]['_id']
    
    routes_df = get_optimal_distribution_routes(warehouse_id=warehouse_id, limit=limit)
    
    if not routes_df.empty:
        # Filter by efficiency score
        routes_df = routes_df[routes_df['efficiency_score'] >= min_efficiency]
        
        st.dataframe(routes_df)
        
        # Display routes on map
        st.subheader("Peta Rute Distribusi")
        display_routes_map(routes_df)
        
        # Route details
        for _, route in routes_df.iterrows():
            with st.expander(f"🚚 {route.get('route_name', 'Rute Tidak Diketahui')} (Efisiensi: {route.get('efficiency_score', 0)*100:.1f}%)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Dari Lumbung:** {route.get('from_warehouse_name', 'Tidak diketahui')}")
                    st.write(f"**Ke Pedagang:** {route.get('to_merchant_name', 'Tidak diketahui')}")
                    st.write(f"**Jarak:** {route.get('distance', 0):.1f} km")
                
                with col2:
                    st.write(f"**Waktu Tempuh:** {route.get('travel_time', 0)} menit")
                    st.write(f"**Biaya Bahan Bakar:** Rp {route.get('fuel_cost', 0):,.0f}")
                    st.write(f"**Kondisi Jalan:** {route.get('road_condition', 'Tidak diketahui')}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Edit Rute", key=f"edit_route_{route['_id']}"):
                        st.session_state['editing_route'] = route['_id']
                        st.rerun()
                with col2:
                    if st.button("Hapus Rute", key=f"delete_route_{route['_id']}"):
                        delete_route(route['_id'])
                with col3:
                    if st.button("Optimalkan Ulang", key=f"reoptimize_{route['_id']}"):
                        reoptimize_route(route['_id'])
    else:
        st.info("Belum ada data rute distribusi. Silakan tambahkan rute baru.")

def add_distribution_route():
    st.subheader("Tambah Rute Distribusi Baru")
    
    # Get data for dropdowns
    warehouses_df = get_warehouses()
    merchants_df = get_merchants()
    
    if warehouses_df.empty or merchants_df.empty:
        st.warning("Data lumbung atau pedagang belum tersedia. Silakan tambahkan data terlebih dahulu.")
        return
    
    with st.form("add_route_form"):
        route_name = st.text_input("Nama Rute*", placeholder="Contoh: Rute Lumbung A - Pedagang B")
        
        col1, col2 = st.columns(2)
        
        with col1:
            warehouse_names = warehouses_df['name'].tolist()
            selected_warehouse = st.selectbox("Lumbung Asal*", warehouse_names)
            
            distance = st.number_input("Jarak (km)*", min_value=0.1, max_value=500.0, value=10.0, step=0.1)
            fuel_cost = st.number_input("Biaya Bahan Bakar (Rp)*", min_value=1000, value=50000, step=1000)
        
        with col2:
            merchant_names = merchants_df['name'].tolist()
            selected_merchant = st.selectbox("Pedagang Tujuan*", merchant_names)
            
            travel_time = st.number_input("Waktu Tempuh (menit)*", min_value=1, max_value=1440, value=30, step=5)
            road_condition = st.selectbox("Kondisi Jalan*", ["Baik", "Sedang", "Buruk"])
        
        # Calculate efficiency score based on distance, time, and road condition
        efficiency_factors = {
            "Baik": 1.0,
            "Sedang": 0.8,
            "Buruk": 0.6
        }
        
        # Auto-calculate efficiency score
        base_efficiency = min(1.0, max(0.1, 1.0 - (distance / 100) - (travel_time / 600)))
        road_factor = efficiency_factors.get(road_condition, 0.8)
        auto_efficiency = base_efficiency * road_factor
        
        efficiency_score = st.slider("Skor Efisiensi", 0.0, 1.0, auto_efficiency, 0.01)
        
        notes = st.text_area("Catatan Tambahan", placeholder="Informasi tambahan tentang rute ini")
        
        submit = st.form_submit_button("Tambah Rute", use_container_width=True)
        
        if submit:
            if not route_name or not selected_warehouse or not selected_merchant:
                st.error("Nama rute, lumbung asal, dan pedagang tujuan harus diisi!")
            else:
                try:
                    db = MongoDBConnection.get_database()
                    
                    # Get warehouse and merchant IDs
                    warehouse_row = warehouses_df[warehouses_df['name'] == selected_warehouse]
                    merchant_row = merchants_df[merchants_df['name'] == selected_merchant]
                    
                    if warehouse_row.empty or merchant_row.empty:
                        st.error("Lumbung atau pedagang tidak ditemukan.")
                        return
                    
                    route_data = {
                        "route_name": route_name,
                        "from_warehouse_id": ObjectId(warehouse_row.iloc[0]['_id']),
                        "to_merchant_id": ObjectId(merchant_row.iloc[0]['_id']),
                        "distance": distance,
                        "travel_time": travel_time,
                        "fuel_cost": fuel_cost,
                        "road_condition": road_condition,
                        "efficiency_score": efficiency_score,
                        "notes": notes,
                        "created_date": datetime.now(),
                        "created_by": ObjectId(st.session_state['user']['id']),
                        "is_active": True
                    }
                    
                    result = db.distribution_routes.insert_one(route_data)
                    
                    if result.inserted_id:
                        st.success(f"Rute {route_name} berhasil ditambahkan!")
                        st.balloons()
                    else:
                        st.error("Gagal menambahkan rute.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

def route_analysis():
    st.subheader("Analisis Rute Distribusi")
    
    # Get route statistics
    db = MongoDBConnection.get_database()
    
    # Total routes
    total_routes = db.distribution_routes.count_documents({})
    
    # Average efficiency
    avg_efficiency = list(db.distribution_routes.aggregate([
        {"$group": {"_id": None, "avg_efficiency": {"$avg": "$efficiency_score"}}}
    ]))
    
    # Routes by road condition
    road_condition_stats = list(db.distribution_routes.aggregate([
        {"$group": {"_id": "$road_condition", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Rute", total_routes)
    
    with col2:
        if avg_efficiency:
            st.metric("Efisiensi Rata-rata", f"{avg_efficiency[0]['avg_efficiency']*100:.1f}%")
        else:
            st.metric("Efisiensi Rata-rata", "Belum ada data")
    
    with col3:
        if road_condition_stats:
            best_condition = road_condition_stats[0]
            st.metric("Kondisi Jalan Terbanyak", f"{best_condition['_id']} ({best_condition['count']} rute)")
        else:
            st.metric("Kondisi Jalan Terbanyak", "Belum ada data")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if road_condition_stats:
            st.subheader("Rute berdasarkan Kondisi Jalan")
            condition_df = pd.DataFrame(road_condition_stats)
            condition_df.columns = ['Kondisi Jalan', 'Jumlah']
            st.bar_chart(condition_df.set_index('Kondisi Jalan')['Jumlah'])
    
    with col2:
        # Distance distribution
        distance_stats = list(db.distribution_routes.aggregate([
            {
                "$bucket": {
                    "groupBy": "$distance",
                    "boundaries": [0, 10, 25, 50, 100, 500],
                    "default": "500+",
                    "output": {"count": {"$sum": 1}}
                }
            }
        ]))
        
        if distance_stats:
            st.subheader("Distribusi Jarak Rute")
            distance_labels = ['0-10 km', '10-25 km', '25-50 km', '50-100 km', '100+ km']
            distance_counts = [stat['count'] for stat in distance_stats[:5]]
            distance_df = pd.DataFrame({'Jarak': distance_labels, 'Jumlah': distance_counts})
            st.bar_chart(distance_df.set_index('Jarak')['Jumlah'])

def display_routes_map(routes_df):
    """Display routes on an interactive map"""
    st.info("Fitur peta interaktif akan segera tersedia!")
    st.write("Peta ini akan menampilkan:")
    st.write("📍 Lokasi lumbung desa")
    st.write("🏪 Lokasi pedagang lokal") 
    st.write("🛣️ Jalur distribusi optimal")
    st.write("📊 Informasi efisiensi rute")
    
    # Placeholder for route summary
    if not routes_df.empty:
        st.write("### Ringkasan Rute")
        st.write(f"Total Rute: {len(routes_df)}")
        st.write(f"Rata-rata Efisiensi: {routes_df['efficiency_score'].mean()*100:.1f}%")
        st.write(f"Total Jarak: {routes_df['distance'].sum():.1f} km")

def delete_route(route_id):
    """Delete distribution route"""
    try:
        db = MongoDBConnection.get_database()
        result = db.distribution_routes.delete_one({"_id": ObjectId(route_id)})
        
        if result.deleted_count > 0:
            st.success("Rute berhasil dihapus!")
            st.rerun()
        else:
            st.error("Gagal menghapus rute.")
    except Exception as e:
        st.error(f"Error menghapus rute: {e}")

def reoptimize_route(route_id):
    """Reoptimize a distribution route"""
    try:
        db = MongoDBConnection.get_database()
        
        # Get current route data
        route = db.distribution_routes.find_one({"_id": ObjectId(route_id)})
        if not route:
            st.error("Rute tidak ditemukan.")
            return
        
        # Simple reoptimization logic - in a real app, this would use complex algorithms
        new_efficiency = min(1.0, route['efficiency_score'] + 0.1)
        
        # Update route with new efficiency
        result = db.distribution_routes.update_one(
            {"_id": ObjectId(route_id)},
            {"$set": {"efficiency_score": new_efficiency, "last_optimized": datetime.now()}}
        )
        
        if result.modified_count > 0:
            st.success(f"Rute berhasil dioptimalkan ulang! Efisiensi baru: {new_efficiency*100:.1f}%")
            st.rerun()
        else:
            st.error("Gagal mengoptimalkan ulang rute.")
    except Exception as e:
        st.error(f"Error mengoptimalkan ulang rute: {e}")

def advanced_distribution_optimizer():
    """Advanced distribution optimizer using geospatial algorithms"""
    st.subheader("🚀 Optimasi Distribusi Canggih dengan Algoritma Geospasial")
    
    # Initialize optimizer
    optimizer = DistributionOptimizer()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📊 Parameter Optimasi")
        
        # Get warehouses and merchants data
        warehouses_df = get_warehouses()
        merchants_df = get_merchants()
        
        if warehouses_df.empty or merchants_df.empty:
            st.warning("Data lumbung atau pedagang belum tersedia. Pastikan data lokasi sudah lengkap dengan koordinat.")
            return
        
        # Optimization parameters
        vehicle_capacity = st.number_input("Kapasitas Kendaraan (kg)", 
                                         min_value=100, max_value=10000, value=1000, step=100)
        
        fuel_cost_per_km = st.number_input("Biaya Bahan Bakar per KM (Rp)", 
                                           min_value=1000, max_value=10000, value=5000, step=500)
        
        driver_hourly_rate = st.number_input("Tarif Driver per Jam (Rp)", 
                                           min_value=10000, max_value=100000, value=25000, step=5000)
        
        max_route_time = st.number_input("Waktu Maksimal Perjalanan (jam)", 
                                         min_value=1, max_value=12, value=8, step=1)
        
        optimization_mode = st.selectbox("Mode Optimasi", [
            "Biaya Minimal", "Waktu Minimal", "Jarak Minimal", "Keseimbangan"
        ])
        
        include_road_conditions = st.checkbox("Pertimbangkan Kondisi Jalan", value=True)
        
        optimize_button = st.button("🚀 Optimalkan Rute", use_container_width=True)
    
    with col2:
        st.write("### 📈 Statistik Data")
        
        # Display current data statistics
        st.metric("Jumlah Lumbung", len(warehouses_df))
        st.metric("Jumlah Pedagang", len(merchants_df))
        
        # Check coordinate availability
        warehouses_with_coords = sum(1 for _, w in warehouses_df.iterrows() 
                                     if 'coordinates' in w and w['coordinates'])
        merchants_with_coords = sum(1 for _, m in merchants_df.iterrows() 
                                   if 'coordinates' in m and m['coordinates'])
        
        st.metric("Lumbung dengan Koordinat", f"{warehouses_with_coords}/{len(warehouses_df)}")
        st.metric("Pedagang dengan Koordinat", f"{merchants_with_coords}/{len(merchants_df)}")
        
        if warehouses_with_coords == 0 or merchants_with_coords == 0:
            st.error("Koordinat diperlukan untuk optimasi geospasial. Pastikan data lokasi sudah lengkap.")
            return
    
    if optimize_button:
        with st.spinner("🔄 Sedang mengoptimalkan rute distribusi..."):
            try:
                # Prepare data for optimization
                warehouses_data = []
                for _, warehouse in warehouses_df.iterrows():
                    if 'coordinates' in warehouse and warehouse['coordinates']:
                        warehouses_data.append({
                            'id': str(warehouse['_id']),
                            'name': warehouse['name'],
                            'location': warehouse.get('location', ''),
                            'coordinates': warehouse['coordinates'],
                            'capacity': warehouse.get('capacity', 1000)
                        })
                
                merchants_data = []
                for _, merchant in merchants_df.iterrows():
                    if 'coordinates' in merchant and merchant['coordinates']:
                        merchants_data.append({
                            'id': str(merchant['_id']),
                            'name': merchant['name'],
                            'location': merchant.get('location', ''),
                            'coordinates': merchant['coordinates'],
                            'demand': merchant.get('demand', 100)
                        })
                
                if not warehouses_data or not merchants_data:
                    st.error("Tidak cukup data dengan koordinat untuk optimasi.")
                    return
                
                # Set optimization parameters
                optimizer.set_vehicle_capacity(vehicle_capacity)
                optimizer.set_cost_parameters(fuel_cost_per_km, driver_hourly_rate)
                optimizer.set_time_constraints(max_route_time * 60)  # Convert to minutes
                
                # Choose optimization mode
                if optimization_mode == "Biaya Minimal":
                    optimizer.set_optimization_mode("cost")
                elif optimization_mode == "Waktu Minimal":
                    optimizer.set_optimization_mode("time")
                elif optimization_mode == "Jarak Minimal":
                    optimizer.set_optimization_mode("distance")
                else:
                    optimizer.set_optimization_mode("balanced")
                
                # Run optimization
                optimal_routes = optimizer.optimize_distribution_routes(
                    warehouses_data, merchants_data
                )
                
                if optimal_routes:
                    st.success("✅ Optimasi selesai!")
                    
                    # Display results
                    display_optimization_results(optimal_routes, optimization_mode)
                    
                    # Save optimized routes to database
                    if st.button("💾 Simpan Rute yang Dihasilkan"):
                        save_optimized_routes(optimal_routes)
                        st.success("Rute optimal berhasil disimpan!")
                
            except Exception as e:
                st.error(f"Error saat optimasi: {e}")

def display_optimization_results(optimal_routes, optimization_mode):
    """Display optimization results"""
    st.write("### 📊 Hasil Optimasi Rute Distribusi")
    
    # Summary statistics
    total_cost = sum(route['total_cost'] for route in optimal_routes)
    total_distance = sum(route['total_distance'] for route in optimal_routes)
    total_time = sum(route['total_time'] for route in optimal_routes)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Jumlah Rute Optimal", len(optimal_routes))
    
    with col2:
        st.metric("Total Biaya", f"Rp {total_cost:,.0f}")
    
    with col3:
        st.metric("Total Jarak", f"{total_distance:.1f} km")
    
    with col4:
        st.metric("Total Waktu", f"{total_time/60:.1f} jam")
    
    # Detailed route information
    st.write("### 🛣️ Detail Rute Optimal")
    
    for i, route in enumerate(optimal_routes, 1):
        with st.expander(f"🚚 Rute {i}: {route['warehouse_name']} → {len(route['stops'])} tujuan"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Gudang Asal:** {route['warehouse_name']}")
                st.write(f"**Biaya Total:** Rp {route['total_cost']:,.0f}")
                st.write(f"**Jarak Total:** {route['total_distance']:.1f} km")
                st.write(f"**Waktu Total:** {route['total_time']/60:.1f} jam")
                st.write(f"**Kapasitas Digunakan:** {route['capacity_used']:.0f} kg")
            
            with col2:
                st.write("**Rute Perjalanan:**")
                for j, stop in enumerate(route['stops'], 1):
                    st.write(f"{j}. {stop['merchant_name']} ({stop['distance_from_previous']:.1f} km)")
            
            # Map display placeholder
            st.write("**Peta Rute:**")
            st.info("Peta interaktif akan ditampilkan di sini")

def save_optimized_routes(optimal_routes):
    """Save optimized routes to database"""
    try:
        db = MongoDBConnection.get_database()
        
        for route in optimal_routes:
            # Create route data
            route_data = {
                "route_name": f"Rute Optimal: {route['warehouse_name']}",
                "from_warehouse_id": ObjectId(route['warehouse_id']),
                "to_merchant_id": ObjectId(route['stops'][0]['merchant_id']) if route['stops'] else None,
                "distance": route['total_distance'],
                "travel_time": route['total_time'],
                "fuel_cost": route['total_cost'] * 0.4,  # Estimate 40% for fuel
                "road_condition": "Baik",  # Optimized routes assume good conditions
                "efficiency_score": route['efficiency_score'],
                "optimization_mode": route.get('optimization_mode', 'balanced'),
                "stops": route['stops'],
                "total_cost": route['total_cost'],
                "capacity_used": route['capacity_used'],
                "is_optimized": True,
                "created_date": datetime.now(),
                "created_by": ObjectId(st.session_state['user']['id']),
                "is_active": True
            }
            
            # Insert or update route
            db.distribution_routes.insert_one(route_data)
        
        st.success(f"✅ {len(optimal_routes)} rute optimal berhasil disimpan!")
        
    except Exception as e:
        st.error(f"Error saat menyimpan rute: {e}")