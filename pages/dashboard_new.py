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
