import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from utils.auth_new import require_auth
from utils.sqlite_database import get_database
from utils.helpers_new import get_stock_status, get_department_consumption, get_top_consumed_items

def get_db_connection():
    """Get database connection safely"""
    try:
        db = get_database()
        conn = db._get_connection()
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def execute_query(query, params=None):
    """Execute query safely with error handling"""
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor
    except Exception as e:
        st.error(f"Query execution error: {e}")
        return None

def app():
    require_auth()
    
    st.title("🌾 Dashboard Lumbung Digital")
    
    # Get stock status
    stock_status = get_stock_status()
    
    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Hasil Panen", stock_status['total_items'])
    
    with col2:
        st.metric("Stok Lumbung Sehat", stock_status['healthy_stock'])
    
    with col3:
        st.metric("Stok Lumbung Rendah", stock_status['low_stock'])
    
    with col4:
        st.metric("Stok Lumbung Habis", stock_status['out_of_stock'])
    
    # Quick stats section
    st.markdown("---")
    st.header("📊 Statistik Cepat")
    
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    
    with col_stats1:
        # Get recent activity
        cursor = execute_query("SELECT COUNT(*) FROM harvests WHERE harvest_date >= date('now', '-7 days')")
        if cursor:
            weekly_harvests = cursor.fetchone()[0]
            st.metric("Panen Minggu Ini", weekly_harvests)
        else:
            st.metric("Panen Minggu Ini", 0)
    
    with col_stats2:
        cursor = execute_query("SELECT COUNT(*) FROM users WHERE is_active = 1")
        if cursor:
            active_users = cursor.fetchone()[0]
            st.metric("Pengguna Aktif", active_users)
        else:
            st.metric("Pengguna Aktif", 0)
    
    with col_stats3:
        cursor = execute_query("SELECT COUNT(*) FROM warehouses")
        if cursor:
            total_warehouses = cursor.fetchone()[0]
            st.metric("Total Lumbung", total_warehouses)
        else:
            st.metric("Total Lumbung", 0)
    
    # Don't close connection here, let the database class manage it
    
    # Stock distribution by warehouse
    st.markdown("---")
    st.header("🏪 Distribusi Stok per Lumbung")
    
    cursor = execute_query('''
        SELECT w.name, COUNT(i.id) as item_count, SUM(i.current_stock) as total_stock
        FROM warehouses w
        LEFT JOIN items i ON w.id = i.warehouse_id
        GROUP BY w.id, w.name
        ORDER BY total_stock DESC
    ''')
    
    if cursor:
        warehouse_data = cursor.fetchall()
        
        if warehouse_data:
            warehouse_df = pd.DataFrame(warehouse_data, columns=['Warehouse', 'Item Count', 'Total Stock'])
            
            fig = px.bar(
                warehouse_df, 
                x='Warehouse', 
                y='Total Stock',
                title='Total Stok per Lumbung',
                color='Total Stock',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display warehouse table
            st.subheader("Detail Lumbung")
            st.dataframe(warehouse_df, use_container_width=True)
        else:
            st.info("Belum ada data stok di lumbung")
    else:
        st.error("Tidak dapat memuat data distribusi stok")

    # Distribution analytics
    st.markdown("---")
    st.header("🚚 Distribusi Barang ke Pedagang")

    col_dist1, col_dist2 = st.columns(2)

    # Top merchants by distributed quantity
    with col_dist1:
        st.subheader("Top Pedagang berdasarkan Volume")
        cursor = execute_query('''
            SELECT 
                COALESCE(m.name, 'Tidak diketahui') AS merchant_name,
                COUNT(*) AS shipment_count,
                SUM(it.quantity) AS total_quantity
            FROM inventory_transactions it
            LEFT JOIN merchants m ON it.merchant_id = m.id
            WHERE it.transaction_type = 'distribution'
            GROUP BY m.id, merchant_name
            HAVING total_quantity IS NOT NULL
            ORDER BY total_quantity DESC
            LIMIT 10
        ''')

        if cursor:
            rows = cursor.fetchall()
            if rows:
                merchants_df = pd.DataFrame(rows, columns=[
                    "Pedagang", "Jumlah Pengiriman", "Total Volume"
                ])
                st.dataframe(merchants_df, use_container_width=True)

                fig_merchants = px.bar(
                    merchants_df,
                    x="Pedagang",
                    y="Total Volume",
                    title="Volume Distribusi per Pedagang",
                    color="Total Volume",
                    color_continuous_scale="Blues"
                )
                fig_merchants.update_layout(height=350, xaxis_tickangle=-45)
                st.plotly_chart(fig_merchants, use_container_width=True)
            else:
                st.info("Belum ada data distribusi ke pedagang.")
        else:
            st.error("Gagal memuat data distribusi pedagang.")

    # Top routes by volume
    with col_dist2:
        st.subheader("Top Rute Distribusi")
        cursor = execute_query('''
            SELECT 
                COALESCE(dr.route_name, 'Tanpa Rute') AS route_name,
                COALESCE(w.name, '-') AS from_warehouse,
                COALESCE(m.name, '-') AS merchant_name,
                COUNT(*) AS shipment_count,
                SUM(it.quantity) AS total_quantity,
                AVG(dr.distance) AS avg_distance,
                AVG(dr.fuel_cost) AS avg_fuel_cost
            FROM inventory_transactions it
            LEFT JOIN distribution_routes dr ON it.route_id = dr.id
            LEFT JOIN warehouses w ON dr.from_warehouse_id = w.id
            LEFT JOIN merchants m ON dr.to_merchant_id = m.id
            WHERE it.transaction_type = 'distribution'
            GROUP BY dr.id, route_name, from_warehouse, merchant_name
            HAVING total_quantity IS NOT NULL
            ORDER BY total_quantity DESC
            LIMIT 10
        ''')

        if cursor:
            rows = cursor.fetchall()
            if rows:
                routes_df = pd.DataFrame(rows, columns=[
                    "Rute", "Dari Lumbung", "Ke Pedagang",
                    "Jumlah Pengiriman", "Total Volume",
                    "Rata-rata Jarak", "Rata-rata Biaya BBM"
                ])
                st.dataframe(routes_df, use_container_width=True)

                fig_routes = px.bar(
                    routes_df,
                    x="Rute",
                    y="Total Volume",
                    title="Volume Distribusi per Rute",
                    color="Total Volume",
                    color_continuous_scale="Oranges"
                )
                fig_routes.update_layout(height=350, xaxis_tickangle=-45)
                st.plotly_chart(fig_routes, use_container_width=True)
            else:
                st.info("Belum ada data rute distribusi.")
        else:
            st.error("Gagal memuat data rute distribusi.")

    # Recent harvests
    st.markdown("---")
    st.header("🌾 Panen Terbaru")
    
    try:
        from utils.sqlite_database import get_harvests
        harvests = get_harvests(limit=5)
        
        if not harvests.empty:
            # Display harvest data
            for _, harvest in harvests.iterrows():
                with st.expander(f"🌾 {harvest.get('crop_type', 'Unknown')} - {harvest.get('harvest_date', 'Unknown Date')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Musim:** {harvest.get('season', 'N/A')}")
                        st.write(f"**Jumlah:** {harvest.get('quantity', 0)} {harvest.get('unit', 'kg')}")
                        st.write(f"**Kualitas:** {harvest.get('quality_grade', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Lumbung:** {harvest.get('warehouse_name', 'N/A')}")
                        st.write(f"**Catatan:** {harvest.get('notes', 'Tidak ada')}")
        else:
            st.info("Belum ada data panen")
            
    except Exception as e:
        st.error(f"Error loading harvest data: {e}")
    
    # Item categories distribution
    st.markdown("---")
    st.header("📦 Distribusi Kategori Item")
    
    try:
        db = get_database()
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, COUNT(*) as item_count, SUM(current_stock) as total_stock
            FROM items
            GROUP BY category
            ORDER BY total_stock DESC
        ''')
        
        category_data = cursor.fetchall()
        
        if category_data:
            category_df = pd.DataFrame(category_data, columns=['Category', 'Item Count', 'Total Stock'])
            
            # Create pie chart
            fig = px.pie(
                category_df, 
                values='Total Stock', 
                names='Category',
                title='Distribusi Stok per Kategori',
                color_discrete_sequence=px.colors.sequential.Greens
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display category table
            st.subheader("Detail Kategori")
            st.dataframe(category_df, use_container_width=True)
        else:
            st.info("Belum ada data kategori item")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading category data: {e}")

    # Harvest time-series (volume & value)
    st.markdown("---")
    st.header("📈 Tren Panen & Nilai Produksi")

    cursor = execute_query('''
        SELECT 
            harvest_date,
            season,
            crop_type,
            quantity,
            COALESCE(price_per_unit, 0) AS price_per_unit
        FROM harvests
    ''')

    if cursor:
        rows = cursor.fetchall()
        if rows:
            harvest_df = pd.DataFrame(rows, columns=[
                "harvest_date", "season", "crop_type", "quantity", "price_per_unit"
            ])

            # Parse dates and build monthly aggregates
            harvest_df["harvest_date"] = pd.to_datetime(harvest_df["harvest_date"], errors="coerce")
            harvest_df = harvest_df.dropna(subset=["harvest_date"])
            harvest_df["month"] = harvest_df["harvest_date"].dt.to_period("M").dt.to_timestamp()
            harvest_df["total_value"] = harvest_df["quantity"] * harvest_df["price_per_unit"]

            agg_df = harvest_df.groupby("month").agg(
                total_quantity=("quantity", "sum"),
                total_value=("total_value", "sum"),
            ).reset_index().sort_values("month")

            col_ts1, col_ts2 = st.columns(2)

            with col_ts1:
                st.subheader("Volume Panen per Bulan")
                fig_qty = px.line(
                    agg_df,
                    x="month",
                    y="total_quantity",
                    markers=True,
                    title="Total Volume Panen (Semua Komoditas)",
                )
                fig_qty.update_layout(height=350, xaxis_title="Bulan", yaxis_title="Volume")
                st.plotly_chart(fig_qty, use_container_width=True)

            with col_ts2:
                st.subheader("Nilai Produksi per Bulan")
                fig_val = px.line(
                    agg_df,
                    x="month",
                    y="total_value",
                    markers=True,
                    title="Total Nilai Produksi (Rp)",
                )
                fig_val.update_layout(height=350, xaxis_title="Bulan", yaxis_title="Nilai (Rp)")
                st.plotly_chart(fig_val, use_container_width=True)

            # Optional: filter by komoditas
            st.subheader("Tren per Komoditas (Opsional)")
            crops = sorted(harvest_df["crop_type"].dropna().unique().tolist())
            selected_crop = st.selectbox("Pilih Komoditas", ["(Semua)"] + crops)

            if selected_crop != "(Semua)":
                crop_df = harvest_df[harvest_df["crop_type"] == selected_crop]
                crop_agg = crop_df.groupby("month").agg(
                    total_quantity=("quantity", "sum"),
                    total_value=("total_value", "sum"),
                ).reset_index().sort_values("month")

                fig_crop = px.line(
                    crop_agg,
                    x="month",
                    y="total_quantity",
                    markers=True,
                    title=f"Volume Panen per Bulan - {selected_crop}",
                )
                fig_crop.update_layout(height=300, xaxis_title="Bulan", yaxis_title="Volume")
                st.plotly_chart(fig_crop, use_container_width=True)
        else:
            st.info("Belum ada data panen untuk analisis time-series.")
    else:
        st.error("Gagal memuat data panen untuk analisis time-series.")
    
    # Low stock alerts
    st.markdown("---")
    st.header("⚠️ Peringatan Stok Rendah")
    
    try:
        from utils.sqlite_database import get_items_low_stock
        low_stock_items = get_items_low_stock()
        
        if not low_stock_items.empty:
            st.warning(f"Terdapat {len(low_stock_items)} item dengan stok rendah")
            
            for _, item in low_stock_items.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{item['name']}** ({item['category']})")
                
                with col2:
                    st.metric("Stok", f"{item['current_stock']} {item.get('unit', 'unit')}")
                
                with col3:
                    st.metric("Minimum", f"{item['min_stock']} {item.get('unit', 'unit')}")
        else:
            st.success("✅ Semua item memiliki stok yang aman")
            
    except Exception as e:
        st.error(f"Error loading low stock data: {e}")
    
    # Quick actions
    st.markdown("---")
    st.header("🚀 Aksi Cepat")
    
    col_action1, col_action2, col_action3 = st.columns(3)
    
    with col_action1:
        if st.button("📊 Lihat Laporan", use_container_width=True):
            st.info("Navigasi ke halaman Laporan...")
    
    with col_action2:
        if st.button("🌾 Tambah Panen", use_container_width=True):
            st.info("Navigasi ke halaman Hasil Panen...")
    
    with col_action3:
        if st.button("👥 Manajemen Petani", use_container_width=True):
            st.info("Navigasi ke halaman Manajemen Petani...")
    
    # System information
    st.markdown("---")
    st.header("ℹ️ Informasi Sistem")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.write("**Database:** SQLite (Local)")
        st.write("**Status:** ✅ Online")
        st.write(f"**Last Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col_info2:
        st.write("**Version:** 2.0 (SQLite Migration)")
        st.write("**Environment:** Production")
        st.write("**Data Source:** Local Database")

if __name__ == "__main__":
    app()
