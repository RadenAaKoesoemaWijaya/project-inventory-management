import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.auth_new import require_auth, require_role
from utils.sqlite_database import (
    get_warehouses, 
    get_items, 
    create_item, 
    update_item, 
    delete_item,
    get_stock_status,
    get_items_low_stock
)

def app():
    require_auth()
    
    st.title("🏪 Manajemen Lumbung Desa")
    
    # Add new item section
    st.header("➕ Tambah Item Baru")
    
    with st.form("add_item_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Nama Item*", placeholder="Contoh: Beras Organik")
            category = st.selectbox("Kategori*", ["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"])
            unit = st.selectbox("Satuan*", ["kg", "ton", "karung", "sak", "liter"])
        
        with col2:
            current_stock = st.number_input("Stok Saat Ini*", min_value=0.0, step=0.1)
            min_stock = st.number_input("Stok Minimum*", min_value=0.0, step=0.1)
            max_stock = st.number_input("Stok Maksimum", min_value=0.0, step=0.1)
        
        with col3:
            price_per_unit = st.number_input("Harga per Satuan (Rp)", min_value=0.0, step=100.0)
            expiry_date = st.date_input("Tanggal Kadaluarsa")
            harvest_season = st.text_input("Musim Panen", placeholder="Contoh: Musim Hujan 2024")
        
        # Warehouse selection
        warehouses = get_warehouses()
        if warehouses:
            warehouse_options = {w['name']: w['id'] for w in warehouses}
            selected_warehouse = st.selectbox("Lumbung*", list(warehouse_options.keys()))
            warehouse_id = warehouse_options[selected_warehouse]
        else:
            st.error("Tidak ada lumbung tersedia!")
            warehouse_id = None
        
        submit_item = st.form_submit_button("📦 Tambah Item", use_container_width=True)
        
        if submit_item and warehouse_id:
            if name and category and current_stock >= 0 and min_stock >= 0:
                success, message = create_item(
                    name=name,
                    category=category,
                    current_stock=current_stock,
                    min_stock=min_stock,
                    max_stock=max_stock,
                    unit=unit,
                    price_per_unit=price_per_unit,
                    warehouse_id=warehouse_id,
                    expiry_date=expiry_date.isoformat() if expiry_date else None,
                    harvest_season=harvest_season
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Mohon lengkapi field yang wajib diisi!")
    
    st.markdown("---")
    
    # Filter and search section
    st.header("🔍 Cari dan Filter Item")
    
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        search_term = st.text_input("Cari Item", placeholder="Ketik nama item...")
    
    with col_filter2:
        warehouses = get_warehouses()
        warehouse_options = {"Semua Lumbung": None}
        warehouse_options.update({w['name']: w['id'] for w in warehouses})
        selected_filter_warehouse = st.selectbox("Filter Lumbung", list(warehouse_options.keys()))
    
    with col_filter3:
        categories = ["Semua Kategori", "Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah", "Lainnya"]
        selected_category = st.selectbox("Filter Kategori", categories)
    
    # Get items with filters
    warehouse_id_filter = warehouse_options[selected_filter_warehouse]
    items_df = get_items(warehouse_id=warehouse_id_filter)
    
    # Apply additional filters
    if search_term:
        items_df = items_df[items_df['name'].str.contains(search_term, case=False, na=False)]
    
    if selected_category != "Semua Kategori":
        items_df = items_df[items_df['category'] == selected_category]
    
    # Display items
    st.header("📦 Daftar Item di Lumbung")
    
    if not items_df.empty:
        # Add stock status column
        def get_stock_status(row):
            current = row['current_stock']
            minimum = row['min_stock']
            if current == 0:
                return "Habis"
            elif current <= minimum:
                return "Rendah"
            else:
                return "Aman"
        
        items_df['status'] = items_df.apply(get_stock_status, axis=1)
        
        # Display metrics
        col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
        
        with col_metrics1:
            st.metric("Total Item", len(items_df))
        
        with col_metrics2:
            total_stock = items_df['current_stock'].sum()
            st.metric("Total Stok", f"{total_stock:.1f}")
        
        with col_metrics3:
            low_stock_count = len(items_df[items_df['status'] == 'Rendah'])
            st.metric("Stok Rendah", low_stock_count)
        
        # Items table
        st.subheader("📋 Tabel Item")
        
        # Format the dataframe for display
        display_df = items_df.copy()
        display_df['harga'] = display_df['price_per_unit'].apply(lambda x: f"Rp {x:,.0f}" if pd.notna(x) else "Rp 0")
        display_df['stok'] = display_df.apply(lambda row: f"{row['current_stock']} {row['unit']}", axis=1)
        
        # Status color coding
        def status_color(status):
            if status == "Habis":
                return "🔴"
            elif status == "Rendah":
                return "🟡"
            else:
                return "🟢"
        
        display_df['status'] = display_df['status'].apply(status_color)
        
        # Select columns to display
        display_columns = ['name', 'category', 'stok', 'min_stock', 'max_stock', 'harga', 'status']
        available_columns = [col for col in display_columns if col in display_df.columns]
        
        st.dataframe(
            display_df[available_columns].rename(columns={
                'name': 'Nama Item',
                'category': 'Kategori',
                'min_stock': 'Stok Min',
                'max_stock': 'Stok Max',
                'status': 'Status'
            }),
            use_container_width=True
        )
        
        # Stock visualization
        st.subheader("📊 Visualisasi Stok")
        
        col_viz1, col_viz2 = st.columns(2)
        
        with col_viz1:
            # Stock by category
            category_stock = items_df.groupby('category')['current_stock'].sum().reset_index()
            
            fig = px.bar(
                category_stock, 
                x='category', 
                y='current_stock',
                title="Total Stok per Kategori",
                color='current_stock',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_viz2:
            # Stock status distribution
            status_counts = items_df['status'].value_counts()
            
            fig = px.pie(
                values=status_counts.values, 
                names=status_counts.index,
                title="Distribusi Status Stok",
                color_discrete_map={"Aman": "green", "Rendah": "orange", "Habis": "red"}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Low stock items
        low_stock_items = items_df[items_df['status'].isin(['Rendah', 'Habis'])]
        
        if not low_stock_items.empty:
            st.subheader("⚠️ Item Perlu Perhatian")
            
            for _, item in low_stock_items.iterrows():
                col_item1, col_item2, col_item3 = st.columns([3, 1, 1])
                
                with col_item1:
                    st.write(f"**{item['name']}** ({item['category']})")
                
                with col_item2:
                    st.metric("Stok", f"{item['current_stock']} {item['unit']}")
                
                with col_item3:
                    if item['status'] == 'Habis':
                        st.error("Habis")
                    else:
                        st.warning("Rendah")
        
        # Item management actions
        st.subheader("🔧 Aksi Item")
        
        selected_item_name = st.selectbox(
            "Pilih Item untuk Dikelola",
            options=items_df['name'].tolist(),
            key="item_management"
        )
        
        if selected_item_name:
            selected_item = items_df[items_df['name'] == selected_item_name].iloc[0]
            
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                with st.form(f"update_item_{selected_item['id']}"):
                    st.write(f"**Update Item: {selected_item_name}**")
                    
                    new_stock = st.number_input(
                        "Stok Baru", 
                        min_value=0.0, 
                        step=0.1,
                        value=float(selected_item['current_stock'])
                    )
                    new_min_stock = st.number_input(
                        "Stok Minimum Baru", 
                        min_value=0.0, 
                        step=0.1,
                        value=float(selected_item['min_stock'])
                    )
                    new_price = st.number_input(
                        "Harga Baru (Rp)", 
                        min_value=0.0, 
                        step=100.0,
                        value=float(selected_item['price_per_unit']) if pd.notna(selected_item['price_per_unit']) else 0.0
                    )
                    
                    col_update1, col_update2 = st.columns(2)
                    with col_update1:
                        update_submit = st.form_submit_button("💾 Update")
                    with col_update2:
                        delete_submit = st.form_submit_button("🗑️ Hapus", type="secondary")
                    
                    if update_submit:
                        success = update_item(selected_item['id'], {
                            'current_stock': new_stock,
                            'min_stock': new_min_stock,
                            'price_per_unit': new_price
                        })
                        
                        if success:
                            st.success("✅ Item berhasil diupdate!")
                            st.rerun()
                        else:
                            st.error("❌ Gagal mengupdate item")
                    
                    if delete_submit:
                        st.warning("⚠️ Item akan dihapus secara permanen!")
                        confirm_delete = st.checkbox("Saya yakin ingin menghapus item ini")
                        
                        if confirm_delete:
                            success = delete_item(selected_item['id'])
                            if success:
                                st.success("✅ Item berhasil dihapus!")
                                st.rerun()
                            else:
                                st.error("❌ Gagal menghapus item")
            
            with col_action2:
                st.write("**Detail Item**")
                st.write(f"**ID:** {selected_item['id']}")
                st.write(f"**Kategori:** {selected_item['category']}")
                st.write(f"**Satuan:** {selected_item['unit']}")
                st.write(f"**Stok Max:** {selected_item['max_stock']} {selected_item['unit']}")
                if pd.notna(selected_item['expiry_date']):
                    st.write(f"**Kadaluarsa:** {selected_item['expiry_date']}")
                if selected_item['harvest_season']:
                    st.write(f"**Musim:** {selected_item['harvest_season']}")
    
    else:
        st.info("📭 Tidak ada item yang ditemukan dengan filter yang dipilih.")
        
        # Add sample data button for admin users
        if st.session_state['user']['role'] == 'admin':
            if st.button("📊 Tambah Data Sampel", use_container_width=True):
                # Add sample items
                warehouses = get_warehouses()
                if warehouses:
                    warehouse_id = warehouses[0]['id']
                    
                    sample_items = [
                        ("Beras Premium", "Beras", 500, 50, 1000, "kg", 15000),
                        ("Jagung Manis", "Jagung", 300, 30, 600, "kg", 8000),
                        ("Kedelai Hitam", "Kacang-kacangan", 200, 20, 400, "kg", 12000),
                        ("Cabai Merah", "Sayuran", 100, 10, 200, "kg", 25000),
                        ("Tomat Segar", "Sayuran", 150, 15, 300, "kg", 18000)
                    ]
                    
                    for name, category, stock, min_stock, max_stock, unit, price in sample_items:
                        create_item(name, category, stock, min_stock, max_stock, unit, price, warehouse_id)
                    
                    st.success("✅ Data sampel berhasil ditambahkan!")
                    st.rerun()

if __name__ == "__main__":
    app()
