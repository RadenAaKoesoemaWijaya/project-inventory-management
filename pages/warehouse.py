import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.database import (
    MongoDBConnection, get_warehouses, get_warehouse_products, 
    add_warehouse_product, update_warehouse_product, get_product_categories
)
from datetime import datetime
from bson import ObjectId

def app():
    require_auth()
    
    st.title("Manajemen Lumbung Desa")
    
    # Tabs for different warehouse functions
    tab1, tab2, tab3, tab4 = st.tabs(["Stok Lumbung", "Tambah Produk", "Kategori Produk", "Analisis Stok"])
    
    with tab1:
        display_warehouse_stock()
    
    with tab2:
        add_warehouse_product()
    
    with tab3:
        manage_product_categories()
    
    with tab4:
        analyze_stock()

def display_warehouse_stock():
    st.subheader("Stok Produk di Lumbung Desa")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        product_filter = st.text_input("Filter berdasarkan nama produk", "")
    
    with col2:
        categories = get_product_categories()
        category_options = ["Semua Kategori"] + categories
        category_filter = st.selectbox("Filter berdasarkan kategori", category_options)
    
    with col3:
        stock_status_filter = st.selectbox("Filter berdasarkan status stok", ["Semua Status", "Stok Aman", "Stok Rendah", "Stok Habis"])
    
    # Get warehouse stock data
    try:
        products = get_warehouse_products()
        
        if products:
            # Apply filters
            filtered_products = products
            
            if product_filter:
                filtered_products = [p for p in filtered_products if product_filter.lower() in p.get('name', '').lower()]
            
            if category_filter != "Semua Kategori":
                filtered_products = [p for p in filtered_products if p.get('category') == category_filter]
            
            if stock_status_filter != "Semua Status":
                if stock_status_filter == "Stok Aman":
                    filtered_products = [p for p in filtered_products if p.get('current_stock', 0) > p.get('min_stock', 0)]
                elif stock_status_filter == "Stok Rendah":
                    filtered_products = [p for p in filtered_products if p.get('current_stock', 0) <= p.get('min_stock', 0) and p.get('current_stock', 0) > 0]
                elif stock_status_filter == "Stok Habis":
                    filtered_products = [p for p in filtered_products if p.get('current_stock', 0) == 0]
            
            # Display summary
            st.info(f"Menampilkan {len(filtered_products)} produk dari total {len(products)} produk")
            
            # Display products in cards
            for product in filtered_products:
                with st.expander(f"🌾 {product.get('name', 'Produk Tidak Diketahui')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Kategori:** {product.get('category', 'Tidak diketahui')}")
                        st.write(f"**Satuan:** {product.get('unit', 'Tidak diketahui')}")
                        st.write(f"**Stok Saat Ini:** {product.get('current_stock', 0):,.1f}")
                        st.write(f"**Stok Minimum:** {product.get('min_stock', 0):,.1f}")
                    
                    with col2:
                        st.write(f"**Harga per Unit:** Rp {product.get('price_per_unit', 0):,.0f}")
                        st.write(f"**Total Nilai:** Rp {product.get('current_stock', 0) * product.get('price_per_unit', 0):,.0f}")
                        st.write(f"**Lokasi Lumbung:** {product.get('warehouse_name', 'Tidak diketahui')}")
                        st.write(f"**Status:** {product.get('status', 'normal').title()}")
                    
                    # Stock status indicator
                    current_stock = product.get('current_stock', 0)
                    min_stock = product.get('min_stock', 0)
                    
                    if current_stock == 0:
                        st.error("⚠️ Stok Habis!")
                    elif current_stock <= min_stock:
                        st.warning("⚠️ Stok Rendah!")
                    else:
                        st.success("✅ Stok Aman")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Update Stok", key=f"update_{product.get('_id')}"):
                            st.session_state['updating_product'] = str(product.get('_id'))
                            st.rerun()
                    with col2:
                        if st.button("Edit Produk", key=f"edit_{product.get('_id')}"):
                            st.session_state['editing_product'] = str(product.get('_id'))
                            st.rerun()
                    with col3:
                        if st.button("Hapus Produk", key=f"delete_{product.get('_id')}"):
                            delete_warehouse_product(product.get('_id'))
        else:
            st.info("Belum ada produk di lumbung. Silakan tambahkan produk baru.")
            
    except Exception as e:
        st.error(f"Error: {e}")

def add_warehouse_product():
    st.subheader("Tambah Produk Baru ke Lumbung")
    
    # Get warehouses for dropdown
    try:
        warehouses = get_warehouses()
        
        if warehouses.empty:
            st.warning("Belum ada data lumbung. Silakan tambahkan data lumbung terlebih dahulu.")
            return
        
        warehouse_names = [f"{w['name']} - {w['location']}" for w in warehouses]
        
    except Exception as e:
        st.error(f"Error getting warehouses: {e}")
        return
    
    with st.form("add_product_form"):
        name = st.text_input("Nama Produk*", placeholder="Contoh: Beras Pandan Wangi, Jagung Manis, dll")
        
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox("Kategori Produk*", ["Hasil Panen", "Bibit", "Pupuk", "Peralatan", "Lainnya"])
            unit = st.selectbox("Satuan*", ["kg", "ton", "kwintal", "ikat", "karung", "liter", "pcs"])
            current_stock = st.number_input("Stok Awal*", min_value=0.0, value=0.0, step=0.1)
        
        with col2:
            min_stock = st.number_input("Stok Minimum*", min_value=0.0, value=10.0, step=0.1)
            price_per_unit = st.number_input("Harga per Unit (Rp)*", min_value=100, value=10000, step=100)
            selected_warehouse = st.selectbox("Lokasi Lumbung*", warehouse_names)
        
        description = st.text_area("Deskripsi Produk", placeholder="Deskripsi lengkap produk")
        notes = st.text_area("Catatan Tambahan", placeholder="Informasi tambahan tentang produk")
        
        submit = st.form_submit_button("Tambah Produk ke Lumbung", use_container_width=True)
        
        if submit:
            if not name or not category or not unit:
                st.error("Semua field wajib harus diisi!")
            else:
                try:
                    # Get selected warehouse ID
                    warehouse_index = warehouse_names.index(selected_warehouse)
                    warehouse_id = warehouses[warehouse_index]['_id']
                    
                    product_data = {
                        "name": name,
                        "category": category,
                        "unit": unit,
                        "current_stock": current_stock,
                        "min_stock": min_stock,
                        "price_per_unit": price_per_unit,
                        "warehouse_id": warehouse_id,
                        "description": description,
                        "notes": notes,
                        "max_stock": min_stock * 3  # Default max stock 3x minimum
                    }
                    
                    if add_warehouse_product(product_data):
                        st.success(f"Produk {name} berhasil ditambahkan ke lumbung!")
                        st.balloons()
                    else:
                        st.error("Gagal menambahkan produk.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

def manage_product_categories():
    st.subheader("Kategori Produk Lumbung")
    
    try:
        # Get unique categories
        categories = get_product_categories()
        
        if categories:
            st.write("### Kategori yang Tersedia")
            for category in categories:
                db = MongoDBConnection.get_database()
                count = db.warehouse_products.count_documents({"category": category})
                st.write(f"**{category}:** {count} produk")
        else:
            st.info("Belum ada kategori produk.")
        
        # Add new category
        st.write("### Tambah Kategori Baru")
        with st.form("add_category_form"):
            new_category = st.text_input("Nama Kategori Baru", placeholder="Contoh: Sayuran, Buah-buahan, dll")
            submit = st.form_submit_button("Tambah Kategori")
            
            if submit and new_category:
                # Check if category already exists
                if new_category in categories:
                    st.warning(f"Kategori '{new_category}' sudah ada.")
                else:
                    st.success(f"Kategori '{new_category}' siap digunakan.")
                    
    except Exception as e:
        st.error(f"Error: {e}")

def delete_warehouse_product(product_id):
    """Delete warehouse product"""
    try:
        db = MongoDBConnection.get_database()
        result = db.warehouse_products.delete_one({"_id": ObjectId(product_id)})
        if result.deleted_count > 0:
            st.success("Produk berhasil dihapus!")
            st.rerun()
        else:
            st.error("Gagal menghapus produk.")
    except Exception as e:
        st.error(f"Error menghapus produk: {e}")

def analyze_stock():
    st.subheader("Analisis Stok Lumbung")
    
    try:
        db = MongoDBConnection.get_database()
        
        # Get stock statistics
        total_products = db.warehouse_products.count_documents({})
        
        # Products by category
        category_stats = list(db.warehouse_products.aggregate([
            {"$group": {"_id": "$category", "count": {"$sum": 1}, "total_value": {"$sum": {"$multiply": ["$current_stock", "$price_per_unit"]}}}},
            {"$sort": {"total_value": -1}}
        ]))
        
        # Stock status analysis
        low_stock_count = db.warehouse_products.count_documents({"$expr": {"$lte": ["$current_stock", "$min_stock"]}})
        out_of_stock_count = db.warehouse_products.count_documents({"current_stock": 0})
        
        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Produk", total_products)
        
        with col2:
            st.metric("Stok Rendah", low_stock_count)
        
        with col3:
            st.metric("Stok Habis", out_of_stock_count)
        
        with col4:
            total_value = sum(stat['total_value'] for stat in category_stats)
            st.metric("Nilai Total Stok", f"Rp {total_value:,.0f}")
        
        # Charts
        if category_stats:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Produk berdasarkan Kategori")
                category_df = pd.DataFrame(category_stats)
                category_df.columns = ['Kategori', 'Jumlah Produk', 'Nilai Total']
                st.bar_chart(category_df.set_index('Kategori')['Jumlah Produk'])
            
            with col2:
                st.subheader("Nilai Stok berdasarkan Kategori")
                st.bar_chart(category_df.set_index('Kategori')['Nilai Total'])
        
        # Low stock alerts
        if low_stock_count > 0:
            st.warning(f"⚠️ Ada {low_stock_count} produk dengan stok rendah atau habis!")
            
            low_stock_products = list(db.warehouse_products.find({"$expr": {"$lte": ["$current_stock", "$min_stock"]}}))
            if low_stock_products:
                st.write("### Produk dengan Stok Rendah")
                for product in low_stock_products:
                    st.write(f"- **{product['name']}** (Stok: {product['current_stock']} {product['unit']}, Minimum: {product['min_stock']} {product['unit']})")
        
    except Exception as e:
        st.error(f"Error: {e}")

def delete_warehouse_product(product_id):
    """Delete warehouse product"""
    try:
        db = MongoDBConnection.get_database()
        result = db.warehouse_products.delete_one({"_id": ObjectId(product_id)})
        
        if result.deleted_count > 0:
            st.success("Produk berhasil dihapus!")
            st.rerun()
        else:
            st.error("Gagal menghapus produk.")
    except Exception as e:
        st.error(f"Error menghapus produk: {e}")