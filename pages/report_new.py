import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.auth_new import require_auth, require_role
from utils.sqlite_database import (
    get_harvests,
    get_distributions,
    get_farmers,
    get_merchants,
    get_warehouses,
    get_database
)
import io

def app():
    require_auth()
    
    st.title("📊 Laporan Sistem Lumbung Digital")
    
    # Tabs for different report types
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Ringkasan", 
        "Laporan Panen", 
        "Laporan Distribusi", 
        "Laporan Keuangan", 
        "Export Data"
    ])
    
    with tab1:
        summary_report()
    
    with tab2:
        harvest_report()
    
    with tab3:
        distribution_report()
    
    with tab4:
        financial_report()
    
    with tab5:
        export_data()

def summary_report():
    st.subheader("📈 Ringkasan Laporan")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Tanggal Mulai", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("Tanggal Akhir", value=datetime.now())
    
    # Get data
    harvests_df = get_harvests(limit=1000)
    distributions_df = get_distributions(limit=1000)
    farmers_df = get_farmers(limit=1000)
    merchants_df = get_merchants(limit=1000)
    
    # Filter by date range
    if not harvests_df.empty:
        harvests_df['harvest_date_dt'] = pd.to_datetime(harvests_df['harvest_date'], errors='coerce')
        harvests_df = harvests_df[
            (harvests_df['harvest_date_dt'] >= pd.to_datetime(start_date)) & 
            (harvests_df['harvest_date_dt'] <= pd.to_datetime(end_date))
        ]
    
    if not distributions_df.empty:
        distributions_df['delivery_date_dt'] = pd.to_datetime(distributions_df['delivery_date'], errors='coerce')
        distributions_df = distributions_df[
            (distributions_df['delivery_date_dt'] >= pd.to_datetime(start_date)) & 
            (distributions_df['delivery_date_dt'] <= pd.to_datetime(end_date))
        ]
    
    # Overview metrics
    st.subheader("📊 Metrik Utama")
    
    col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
    
    with col_metrics1:
        total_harvest = harvests_df['quantity'].sum() if not harvests_df.empty else 0
        st.metric("Total Panen", f"{total_harvest:.1f} kg")
    
    with col_metrics2:
        total_distributed = distributions_df['quantity'].sum() if not distributions_df.empty else 0
        st.metric("Total Terdistribusi", f"{total_distributed:.1f} kg")
    
    with col_metrics3:
        total_farmers = len(farmers_df[farmers_df['is_active'] == 1]) if not farmers_df.empty else 0
        st.metric("Petani Aktif", total_farmers)
    
    with col_metrics4:
        total_merchants = len(merchants_df[merchants_df['is_active'] == 1]) if not merchants_df.empty else 0
        st.metric("Pedagang Aktif", total_merchants)
    
    # Charts
    st.subheader("📈 Visualisasi Data")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        if not harvests_df.empty:
            # Harvest by crop type
            crop_totals = harvests_df.groupby('crop_type')['quantity'].sum()
            
            fig = px.pie(
                values=crop_totals.values, 
                names=crop_totals.index,
                title="Distribusi Panen per Komoditas",
                color_discrete_sequence=px.colors.qualitative.Greens
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        if not distributions_df.empty:
            # Distribution status
            status_counts = distributions_df['status'].value_counts()
            
            fig = px.bar(
                x=status_counts.index,
                y=status_counts.values,
                title="Status Distribusi",
                color=status_counts.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Performance indicators
    st.subheader("🎯 Indikator Kinerja")
    
    col_perf1, col_perf2, col_perf3 = st.columns(3)
    
    with col_perf1:
        if not harvests_df.empty and not distributions_df.empty:
            distribution_rate = (total_distributed / total_harvest * 100) if total_harvest > 0 else 0
            st.metric("Tingkat Distribusi", f"{distribution_rate:.1f}%")
        else:
            st.metric("Tingkat Distribusi", "0%")
    
    with col_perf2:
        if not harvests_df.empty:
            avg_quality = harvests_df['quality_grade'].mode().iloc[0] if not harvests_df['quality_grade'].isna().all() else "N/A"
            st.metric("Kualitas Dominan", avg_quality)
        else:
            st.metric("Kualitas Dominan", "N/A")
    
    with col_perf3:
        if not distributions_df.empty:
            completion_rate = len(distributions_df[distributions_df['status'] == 'Completed']) / len(distributions_df) * 100
            st.metric("Tingkat Penyelesaian", f"{completion_rate:.1f}%")
        else:
            st.metric("Tingkat Penyelesaian", "0%")

def harvest_report():
    st.subheader("🌾 Laporan Hasil Panen")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("Tanggal Mulai", value=datetime.now() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("Tanggal Akhir", value=datetime.now())
    
    with col3:
        crop_filter = st.selectbox("Filter Komoditas", ["Semua", "Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah"])
    
    # Get harvest data
    harvests_df = get_harvests(limit=1000)
    
    if not harvests_df.empty:
        # Convert dates and filter
        harvests_df['harvest_date_dt'] = pd.to_datetime(harvests_df['harvest_date'], errors='coerce')
        harvests_df = harvests_df[
            (harvests_df['harvest_date_dt'] >= pd.to_datetime(start_date)) & 
            (harvests_df['harvest_date_dt'] <= pd.to_datetime(end_date))
        ]
        
        if crop_filter != "Semua":
            harvests_df = harvests_df[harvests_df['crop_type'].str.contains(crop_filter, case=False, na=False)]
        
        # Summary statistics
        st.subheader("📊 Statistik Panen")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            total_quantity = harvests_df['quantity'].sum()
            st.metric("Total Panen", f"{total_quantity:.1f} kg")
        
        with col_stat2:
            avg_quantity = harvests_df['quantity'].mean()
            st.metric("Rata-rata per Panen", f"{avg_quantity:.1f} kg")
        
        with col_stat3:
            total_harvests = len(harvests_df)
            st.metric("Jumlah Panen", total_harvests)
        
        with col_stat4:
            unique_crops = harvests_df['crop_type'].nunique()
            st.metric("Jenis Komoditas", unique_crops)
        
        # Detailed table
        st.subheader("📋 Detail Panen")
        
        # Prepare display dataframe
        display_df = harvests_df.copy()
        display_df['tanggal'] = display_df['harvest_date_dt'].dt.strftime('%Y-%m-%d')
        display_df['bulan'] = display_df['harvest_date_dt'].dt.strftime('%Y-%m')
        
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
        
        # Monthly trends
        st.subheader("📈 Tren Bulanan")
        
        monthly_totals = harvests_df.groupby('bulan')['quantity'].sum().reset_index()
        
        if not monthly_totals.empty:
            fig = px.line(
                monthly_totals, 
                x='bulan', 
                y='quantity',
                title="Tren Produksi Bulanan",
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data panen untuk periode yang dipilih.")

def distribution_report():
    st.subheader("🚚 Laporan Distribusi")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("Tanggal Mulai", value=datetime.now() - timedelta(days=30), key="dist_start")
    
    with col2:
        end_date = st.date_input("Tanggal Akhir", value=datetime.now(), key="dist_end")
    
    with col3:
        status_filter = st.selectbox("Filter Status", ["Semua", "Pending", "In Progress", "Completed", "Cancelled"])
    
    # Get distribution data
    distributions_df = get_distributions(limit=1000)
    
    if not distributions_df.empty:
        # Convert dates and filter
        distributions_df['delivery_date_dt'] = pd.to_datetime(distributions_df['delivery_date'], errors='coerce')
        distributions_df = distributions_df[
            (distributions_df['delivery_date_dt'] >= pd.to_datetime(start_date)) & 
            (distributions_df['delivery_date_dt'] <= pd.to_datetime(end_date))
        ]
        
        if status_filter != "Semua":
            distributions_df = distributions_df[distributions_df['status'].str.contains(status_filter, case=False, na=False)]
        
        # Summary statistics
        st.subheader("📊 Statistik Distribusi")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            total_quantity = distributions_df['quantity'].sum()
            st.metric("Total Terdistribusi", f"{total_quantity:.1f} kg")
        
        with col_stat2:
            total_cost = distributions_df['estimated_cost'].sum()
            st.metric("Total Biaya", f"Rp {total_cost:,.0f}")
        
        with col_stat3:
            avg_distance = distributions_df['distance'].mean() if 'distance' in distributions_df.columns else 0
            st.metric("Rata-rata Jarak", f"{avg_distance:.1f} km")
        
        with col_stat4:
            completion_rate = len(distributions_df[distributions_df['status'] == 'Completed']) / len(distributions_df) * 100
            st.metric("Tingkat Penyelesaian", f"{completion_rate:.1f}%")
        
        # Detailed table
        st.subheader("📋 Detail Distribusi")
        
        # Prepare display dataframe
        display_df = distributions_df.copy()
        display_df['tanggal'] = display_df['delivery_date_dt'].dt.strftime('%Y-%m-%d')
        display_df['bulan'] = display_df['delivery_date_dt'].dt.strftime('%Y-%m')
        
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
        
        # Status distribution
        st.subheader("📊 Distribusi Status")
        
        status_counts = distributions_df['status'].value_counts()
        
        fig = px.pie(
            values=status_counts.values, 
            names=status_counts.index,
            title="Distribusi Status Pengiriman",
            color_discrete_map={"Completed": "green", "In Progress": "blue", "Pending": "orange", "Cancelled": "red"}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data distribusi untuk periode yang dipilih.")

def financial_report():
    st.subheader("💰 Laporan Keuangan")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Tanggal Mulai", value=datetime.now() - timedelta(days=30), key="fin_start")
    with col2:
        end_date = st.date_input("Tanggal Akhir", value=datetime.now(), key="fin_end")
    
    # Get data
    distributions_df = get_distributions(limit=1000)
    
    if not distributions_df.empty:
        # Convert dates and filter
        distributions_df['delivery_date_dt'] = pd.to_datetime(distributions_df['delivery_date'], errors='coerce')
        distributions_df = distributions_df[
            (distributions_df['delivery_date_dt'] >= pd.to_datetime(start_date)) & 
            (distributions_df['delivery_date_dt'] <= pd.to_datetime(end_date))
        ]
        
        # Financial metrics
        st.subheader("💵 Metrik Keuangan")
        
        col_fin1, col_fin2, col_fin3, col_fin4 = st.columns(4)
        
        with col_fin1:
            total_revenue = distributions_df['estimated_cost'].sum()
            st.metric("Total Pendapatan", f"Rp {total_revenue:,.0f}")
        
        with col_fin2:
            avg_revenue_per_delivery = distributions_df['estimated_cost'].mean()
            st.metric("Rata-rata per Pengiriman", f"Rp {avg_revenue_per_delivery:,.0f}")
        
        with col_fin3:
            total_deliveries = len(distributions_df)
            st.metric("Total Pengiriman", total_deliveries)
        
        with col_fin4:
            # Calculate cost per kg
            distributions_df['cost_per_kg'] = distributions_df['estimated_cost'] / distributions_df['quantity']
            avg_cost_per_kg = distributions_df['cost_per_kg'].mean()
            st.metric("Biaya per kg", f"Rp {avg_cost_per_kg:,.0f}")
        
        # Revenue by month
        st.subheader("📈 Pendapatan Bulanan")
        
        distributions_df['delivery_month'] = distributions_df['delivery_date_dt'].dt.to_period('M')
        monthly_revenue = distributions_df.groupby('delivery_month')['estimated_cost'].sum().reset_index()
        monthly_revenue['delivery_month'] = monthly_revenue['delivery_month'].dt.to_timestamp()
        
        if not monthly_revenue.empty:
            fig = px.line(
                monthly_revenue, 
                x='delivery_month', 
                y='estimated_cost',
                title="Tren Pendapatan Bulanan",
                markers=True
            )
            fig.update_layout(height=400)
            fig.update_layout(yaxis_title="Pendapatan (Rp)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Revenue by crop type
        st.subheader("🌾 Pendapatan per Komoditas")
        
        crop_revenue = distributions_df.groupby('crop_type')['estimated_cost'].sum().sort_values(ascending=False)
        
        fig = px.bar(
            x=crop_revenue.values,
            y=crop_revenue.index,
            orientation='h',
            title="Pendapatan per Komoditas",
            color=crop_revenue.values,
            color_continuous_scale='Greens'
        )
        fig.update_layout(height=400)
        fig.update_layout(xaxis_title="Pendapatan (Rp)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Cost analysis
        st.subheader("📊 Analisis Biaya")
        
        col_cost1, col_cost2 = st.columns(2)
        
        with col_cost1:
            # Distance vs Cost correlation
            if 'distance' in distributions_df.columns:
                fig = px.scatter(
                    distributions_df, 
                    x='distance', 
                    y='estimated_cost',
                    title="Biaya vs Jarak",
                    color='crop_type'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col_cost2:
            # Cost per kg by crop type
            cost_per_kg_by_crop = distributions_df.groupby('crop_type')['cost_per_kg'].mean().sort_values()
            
            fig = px.bar(
                x=cost_per_kg_by_crop.values,
                y=cost_per_kg_by_crop.index,
                orientation='h',
                title="Biaya per kg per Komoditas",
                color=cost_per_kg_by_crop.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400)
            fig.update_layout(xaxis_title="Biaya per kg (Rp)")
            st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📭 Tidak ada data keuangan untuk periode yang dipilih.")

def export_data():
    st.subheader("📤 Export Data")
    
    # Export options
    export_type = st.selectbox("Pilih Tipe Export", [
        "Data Panen", 
        "Data Distribusi", 
        "Data Petani", 
        "Data Pedagang", 
        "Laporan Ringkasan"
    ])
    
    format_type = st.selectbox("Pilih Format", ["CSV", "Excel", "JSON"])
    
    # Date range for time-based exports
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Tanggal Mulai", value=datetime.now() - timedelta(days=30), key="export_start")
    with col2:
        end_date = st.date_input("Tanggal Akhir", value=datetime.now(), key="export_end")
    
    if st.button("📥 Export Data", use_container_width=True):
        try:
            # Get data based on export type
            if export_type == "Data Panen":
                df = get_harvests(limit=10000)
                if not df.empty:
                    df['harvest_date_dt'] = pd.to_datetime(df['harvest_date'], errors='coerce')
                    df = df[
                        (df['harvest_date_dt'] >= pd.to_datetime(start_date)) & 
                        (df['harvest_date_dt'] <= pd.to_datetime(end_date))
                    ]
                    filename = f"harvest_data_{start_date}_to_{end_date}"
            
            elif export_type == "Data Distribusi":
                df = get_distributions(limit=10000)
                if not df.empty:
                    df['delivery_date_dt'] = pd.to_datetime(df['delivery_date'], errors='coerce')
                    df = df[
                        (df['delivery_date_dt'] >= pd.to_datetime(start_date)) & 
                        (df['delivery_date_dt'] <= pd.to_datetime(end_date))
                    ]
                    filename = f"distribution_data_{start_date}_to_{end_date}"
            
            elif export_type == "Data Petani":
                df = get_farmers(limit=10000)
                filename = f"farmers_data_{datetime.now().strftime('%Y%m%d')}"
            
            elif export_type == "Data Pedagang":
                df = get_merchants(limit=10000)
                filename = f"merchants_data_{datetime.now().strftime('%Y%m%d')}"
            
            else:  # Laporan Ringkasan
                df = create_summary_report(start_date, end_date)
                filename = f"summary_report_{start_date}_to_{end_date}"
            
            if df.empty:
                st.warning("📭 Tidak ada data untuk diekspordalam periode yang dipilih.")
                return
            
            # Export based on format
            if format_type == "CSV":
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"{filename}.csv",
                    mime="text/csv"
                )
            
            elif format_type == "Excel":
                excel_data = io.BytesIO()
                with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
                    df.to_excel(writer, index=True, sheet_name='Data')
                excel_data.seek(0)
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            else:  # JSON
                json_data = df.to_json(orient='records', indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"{filename}.json",
                    mime="application/json"
                )
            
            st.success(f"✅ Data berhasil disiapkan untuk export!")
            
            # Show preview
            st.subheader("📋 Preview Data")
            st.dataframe(df.head(10), use_container_width=True)
            st.write(f"Total baris: {len(df)}")
            
        except Exception as e:
            st.error(f"❌ Error saat export data: {str(e)}")

def create_summary_report(start_date, end_date):
    """Create summary report data"""
    try:
        # Get all data
        harvests_df = get_harvests(limit=10000)
        distributions_df = get_distributions(limit=10000)
        farmers_df = get_farmers(limit=10000)
        merchants_df = get_merchants(limit=10000)
        
        # Filter by date
        if not harvests_df.empty:
            harvests_df['harvest_date_dt'] = pd.to_datetime(harvests_df['harvest_date'], errors='coerce')
            harvests_df = harvests_df[
                (harvests_df['harvest_date_dt'] >= pd.to_datetime(start_date)) & 
                (harvests_df['harvest_date_dt'] <= pd.to_datetime(end_date))
            ]
        
        if not distributions_df.empty:
            distributions_df['delivery_date_dt'] = pd.to_datetime(distributions_df['delivery_date'], errors='coerce')
            distributions_df = distributions_df[
                (distributions_df['delivery_date_dt'] >= pd.to_datetime(start_date)) & 
                (distributions_df['delivery_date_dt'] <= pd.to_datetime(end_date))
            ]
        
        # Create summary dataframe
        summary_data = {
            'Metrik': [
                'Total Panen (kg)',
                'Total Distribusi (kg)', 
                'Total Petani Aktif',
                'Total Pedagang Aktif',
                'Total Pendapatan (Rp)',
                'Tingkat Distribusi (%)',
                'Tingkat Penyelesaian (%)'
            ],
            'Nilai': [
                harvests_df['quantity'].sum() if not harvests_df.empty else 0,
                distributions_df['quantity'].sum() if not distributions_df.empty else 0,
                len(farmers_df[farmers_df['is_active'] == 1]) if not farmers_df.empty else 0,
                len(merchants_df[merchants_df['is_active'] == 1]) if not merchants_df.empty else 0,
                distributions_df['estimated_cost'].sum() if not distributions_df.empty else 0,
                (distributions_df['quantity'].sum() / harvests_df['quantity'].sum() * 100) if not harvests_df.empty and not distributions_df.empty and harvests_df['quantity'].sum() > 0 else 0,
                (len(distributions_df[distributions_df['status'] == 'Completed']) / len(distributions_df) * 100) if not distributions_df.empty else 0
            ]
        }
        
        return pd.DataFrame(summary_data)
        
    except Exception as e:
        st.error(f"Error creating summary report: {str(e)}")
        return pd.DataFrame()

if __name__ == "__main__":
    app()
