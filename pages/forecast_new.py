import streamlit as st
import pandas as pd
import numpy as np
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

def app():
    require_auth()
    
    st.title("🔮 Forecasting Kebutuhan Pertanian")
    
    # Tabs for different forecast types
    tab1, tab2, tab3, tab4 = st.tabs([
        "Forecast Produksi", 
        "Forecast Kebutuhan", 
        "Analisis Tren", 
        "Rekomendasi"
    ])
    
    with tab1:
        production_forecast()
    
    with tab2:
        needs_forecast()
    
    with tab3:
        trend_analysis()
    
    with tab4:
        recommendations()

def production_forecast():
    st.subheader("🌾 Forecast Produksi Hasil Panen")
    
    # Forecast parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        crop_type = st.selectbox("Pilih Komoditas", ["Beras", "Jagung", "Kacang-kacangan", "Sayuran", "Buah"])
    
    with col2:
        forecast_period = st.selectbox("Periode Forecast", ["1 Bulan", "3 Bulan", "6 Bulan", "1 Tahun"])
    
    with col3:
        forecast_method = st.selectbox("Metode Forecast", ["Moving Average", "Linear Regression", "Seasonal"])
    
    # Get historical data
    harvests_df = get_harvests(limit=1000)
    
    if not harvests_df.empty:
        # Filter by crop type
        crop_data = harvests_df[harvests_df['crop_type'] == crop_type].copy()
        
        if crop_data.empty:
            st.warning(f"📭 Tidak ada data historis untuk komoditas {crop_type}")
            return
        
        # Convert dates
        crop_data['harvest_date_dt'] = pd.to_datetime(crop_data['harvest_date'], errors='coerce')
        crop_data = crop_data.sort_values('harvest_date_dt')
        
        # Historical overview
        st.subheader("📊 Data Historis")
        
        col_hist1, col_hist2, col_hist3 = st.columns(3)
        
        with col_hist1:
            total_historical = crop_data['quantity'].sum()
            st.metric("Total Historis", f"{total_historical:.1f} kg")
        
        with col_hist2:
            avg_historical = crop_data['quantity'].mean()
            st.metric("Rata-rata Historis", f"{avg_historical:.1f} kg")
        
        with col_hist3:
            data_points = len(crop_data)
            st.metric("Jumlah Data Historis", data_points)
        
        # Historical trend chart
        st.subheader("📈 Tren Historis")
        
        fig = px.line(
            crop_data, 
            x='harvest_date_dt', 
            y='quantity',
            title=f"Tren Produksi {crop_type} Historis",
            markers=True
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Generate forecast
        forecast_data = generate_production_forecast(crop_data, forecast_period, forecast_method)
        
        if forecast_data is not None:
            st.subheader("🔮 Hasil Forecast")
            
            # Forecast chart
            fig = go.Figure()
            
            # Add historical data
            fig.add_trace(go.Scatter(
                x=crop_data['harvest_date_dt'],
                y=crop_data['quantity'],
                mode='lines+markers',
                name='Data Historis',
                line=dict(color='blue')
            ))
            
            # Add forecast data
            fig.add_trace(go.Scatter(
                x=forecast_data['date'],
                y=forecast_data['forecast'],
                mode='lines+markers',
                name='Forecast',
                line=dict(color='red', dash='dash')
            ))
            
            fig.update_layout(
                title=f"Forecast Produksi {crop_type} - {forecast_method}",
                height=400,
                xaxis_title="Tanggal",
                yaxis_title="Jumlah (kg)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast summary
            st.subheader("📋 Ringkasan Forecast")
            
            col_fore1, col_fore2, col_fore3 = st.columns(3)
            
            with col_fore1:
                total_forecast = forecast_data['forecast'].sum()
                st.metric("Total Forecast", f"{total_forecast:.1f} kg")
            
            with col_fore2:
                avg_forecast = forecast_data['forecast'].mean()
                st.metric("Rata-rata Forecast", f"{avg_forecast:.1f} kg")
            
            with col_fore3:
                growth_rate = ((avg_forecast - avg_historical) / avg_historical * 100) if avg_historical > 0 else 0
                st.metric("Tingkat Pertumbuhan", f"{growth_rate:.1f}%")
            
            # Forecast table
            st.subheader("📊 Detail Forecast")
            
            forecast_display = forecast_data.copy()
            forecast_display['tanggal'] = forecast_display['date'].dt.strftime('%Y-%m-%d')
            forecast_display['bulan'] = forecast_display['date'].dt.strftime('%Y-%m')
            
            st.dataframe(
                forecast_display[['tanggal', 'bulan', 'forecast', 'confidence_lower', 'confidence_upper']].rename(columns={
                    'tanggal': 'Tanggal',
                    'bulan': 'Bulan',
                    'forecast': 'Forecast (kg)',
                    'confidence_lower': 'Batas Bawah (kg)',
                    'confidence_upper': 'Batas Atas (kg)'
                }),
                use_container_width=True
            )
        
    else:
        st.info("📭 Tidak ada data panen untuk forecast.")

def needs_forecast():
    st.subheader("🎯 Forecast Kebutuhan Pertanian")
    
    # Forecast parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        need_type = st.selectbox("Tipe Kebutuhan", ["Bibit", "Pupuk", "Pestisida", "Alat Pertanian"])
    
    with col2:
        forecast_period = st.selectbox("Periode Forecast", ["1 Bulan", "3 Bulan", "6 Bulan"], key="needs_period")
    
    with col3:
        calculation_method = st.selectbox("Metode Perhitungan", ["Berdasarkan Luas Lahan", "Berdasarkan Produksi Historis", "Berdasarkan Jumlah Petani"])
    
    # Get data
    harvests_df = get_harvests(limit=1000)
    farmers_df = get_farmers(limit=1000)
    
    if not harvests_df.empty and not farmers_df.empty:
        # Calculate needs based on method
        if calculation_method == "Berdasarkan Luas Lahan":
            needs_data = calculate_needs_by_land_area(farmers_df, need_type, forecast_period)
        elif calculation_method == "Berdasarkan Produksi Historis":
            needs_data = calculate_needs_by_production(harvests_df, need_type, forecast_period)
        else:  # Berdasarkan Jumlah Petani
            needs_data = calculate_needs_by_farmers(farmers_df, need_type, forecast_period)
        
        # Display results
        st.subheader("📊 Hasil Perhitungan Kebutuhan")
        
        col_need1, col_need2, col_need3 = st.columns(3)
        
        with col_need1:
            total_need = needs_data['estimated_need'].sum()
            st.metric("Total Kebutuhan", f"{total_need:.1f} {needs_data['unit'].iloc[0] if not needs_data.empty else 'unit'}")
        
        with col_need2:
            avg_monthly = needs_data['estimated_need'].mean()
            st.metric("Rata-rata Bulanan", f"{avg_monthly:.1f} {needs_data['unit'].iloc[0] if not needs_data.empty else 'unit'}")
        
        with col_need3:
            peak_month = needs_data.loc[needs_data['estimated_need'].idxmax(), 'month'] if not needs_data.empty else "N/A"
            peak_value = needs_data['estimated_need'].max() if not needs_data.empty else 0
            st.metric("Puncak Kebutuhan", f"{peak_month}: {peak_value:.1f}")
        
        # Needs trend chart
        st.subheader("📈 Tren Kebutuhan")
        
        fig = px.bar(
            needs_data, 
            x='month', 
            y='estimated_need',
            title=f"Forecast Kebutuhan {need_type} - {calculation_method}",
            color='estimated_need',
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("📋 Detail Kebutuhan per Bulan")
        
        st.dataframe(
            needs_data[['month', 'estimated_need', 'confidence_lower', 'confidence_upper', 'unit']].rename(columns={
                'month': 'Bulan',
                'estimated_need': 'Estimasi Kebutuhan',
                'confidence_lower': 'Batas Bawah',
                'confidence_upper': 'Batas Atas',
                'unit': 'Satuan'
            }),
            use_container_width=True
        )
        
        # Recommendations
        st.subheader("💡 Rekomendasi")
        
        total_need = needs_data['estimated_need'].sum()
        peak_need = needs_data['estimated_need'].max()
        
        recommendations = []
        
        if need_type == "Bibit":
            if total_need > 1000:
                recommendations.append("🌱 Pertimbangkan untuk memesan bibit secara bulk untuk mendapatkan harga lebih baik")
            if peak_need > total_need * 0.3:
                recommendations.append("📅 Siapkan stok bibit ekstra 2 bulan sebelum musim tanam puncak")
        
        elif need_type == "Pupuk":
            if total_need > 500:
                recommendations.append("💰 Negosiasi diskon volume dengan supplier pupuk")
            recommendations.append("🗓️ Jadwalkan distribusi pupuk 1 bulan sebelum musim tanam")
        
        elif need_type == "Pestisida":
            recommendations.append("🛡️ Pastikan ketersediaan pestisida organik sebagai alternatif")
            recommendations.append("📚 Lakukan pelatihan aplikasi pestisida yang aman")
        
        else:  # Alat Pertanian
            recommendations.append("🔧 Lakukan maintenance peralatan sebelum musim panen")
            recommendations.append("🤝 Pertimbangkan sewa peralatan untuk kebutuhan sementara")
        
        for rec in recommendations:
            st.info(rec)
        
    else:
        st.info("📭 Tidak cukup data untuk perhitungan kebutuhan.")

def trend_analysis():
    st.subheader("📊 Analisis Tren Pertanian")
    
    # Analysis parameters
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_type = st.selectbox("Tipe Analisis", ["Produksi", "Kualitas", "Distribusi", "Harga"])
    
    with col2:
        time_period = st.selectbox("Periode Analisis", ["6 Bulan", "1 Tahun", "2 Tahun"])
    
    # Get data
    harvests_df = get_harvests(limit=1000)
    distributions_df = get_distributions(limit=1000)
    
    if not harvests_df.empty:
        # Convert dates
        harvests_df['harvest_date_dt'] = pd.to_datetime(harvests_df['harvest_date'], errors='coerce')
        harvests_df['harvest_month'] = harvests_df['harvest_date_dt'].dt.to_period('M')
        
        # Filter by time period
        cutoff_date = datetime.now() - timedelta(days={'6 Bulan': 180, '1 Tahun': 365, '2 Tahun': 730}[time_period])
        harvests_df = harvests_df[harvests_df['harvest_date_dt'] >= cutoff_date]
        
        # Perform analysis based on type
        if analysis_type == "Produksi":
            analysis_results = analyze_production_trends(harvests_df)
        elif analysis_type == "Kualitas":
            analysis_results = analyze_quality_trends(harvests_df)
        elif analysis_type == "Distribusi":
            if not distributions_df.empty:
                distributions_df['delivery_date_dt'] = pd.to_datetime(distributions_df['delivery_date'], errors='coerce')
                distributions_df = distributions_df[distributions_df['delivery_date_dt'] >= cutoff_date]
                analysis_results = analyze_distribution_trends(distributions_df)
            else:
                analysis_results = None
        else:  # Harga
            analysis_results = analyze_price_trends(harvests_df)
        
        if analysis_results is not None:
            # Display analysis results
            st.subheader("📈 Hasil Analisis Tren")
            
            # Trend chart
            fig = px.line(
                analysis_results, 
                x='period', 
                y='value',
                title=f"Tren {analysis_type} - {time_period}",
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Trend statistics
            st.subheader("📊 Statistik Tren")
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                trend_direction = analysis_results['trend_direction'].iloc[-1] if 'trend_direction' in analysis_results.columns else "N/A"
                st.metric("Arah Tren", trend_direction)
            
            with col_stat2:
                avg_value = analysis_results['value'].mean()
                st.metric("Rata-rata", f"{avg_value:.2f}")
            
            with col_stat3:
                volatility = analysis_results['value'].std() / analysis_results['value'].mean() * 100
                st.metric("Volatilitas", f"{volatility:.1f}%")
            
            # Detailed table
            st.subheader("📋 Detail Tren")
            
            st.dataframe(analysis_results, use_container_width=True)
            
            # Insights
            st.subheader("💡 Insight Analisis")
            
            generate_trend_insights(analysis_type, analysis_results)
        
    else:
        st.info("📭 Tidak ada data untuk analisis tren.")

def recommendations():
    st.subheader("🎯 Rekomendasi Strategis")
    
    # Get comprehensive data
    harvests_df = get_harvests(limit=1000)
    distributions_df = get_distributions(limit=1000)
    farmers_df = get_farmers(limit=1000)
    merchants_df = get_merchants(limit=1000)
    
    # Generate recommendations based on data analysis
    recommendations = generate_strategic_recommendations(harvests_df, distributions_df, farmers_df, merchants_df)
    
    # Display recommendations by category
    categories = ["Produksi", "Distribusi", "Kualitas", "Efisiensi", "Pertumbuhan"]
    
    for category in categories:
        if category in recommendations:
            st.subheader(f"📋 Rekomendasi {category}")
            
            for i, rec in enumerate(recommendations[category], 1):
                with st.expander(f"{i}. {rec['title']}"):
                    st.write(f"**Prioritas:** {'🔴 Tinggi' if rec['priority'] == 'high' else '🟡 Sedang' if rec['priority'] == 'medium' else '🟢 Rendah'}")
                    st.write(f"**Deskripsi:** {rec['description']}")
                    st.write(f"**Impact:** {rec['impact']}")
                    st.write(f"**Action Items:**")
                    for action in rec['action_items']:
                        st.write(f"- {action}")
    
    # Implementation timeline
    st.subheader("📅 Timeline Implementasi")
    
    timeline_data = create_implementation_timeline(recommendations)
    
    if timeline_data:
        fig = px.timeline(
            timeline_data, 
            x_start="start", 
            x_end="end", 
            y="task",
            title="Timeline Implementasi Rekomendasi",
            color="priority"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Resource requirements
    st.subheader("💰 Kebutuhan Sumber Daya")
    
    resource_analysis = analyze_resource_requirements(recommendations)
    
    if resource_analysis:
        col_res1, col_res2, col_res3 = st.columns(3)
        
        with col_res1:
            st.metric("Estimasi Biaya", f"Rp {resource_analysis['estimated_cost']:,.0f}")
        
        with col_res2:
            st.metric("Person yang Dibutuhkan", f"{resource_analysis['personnel']} orang")
        
        with col_res3:
            st.metric("Waktu Implementasi", f"{resource_analysis['implementation_time']} bulan")

# Helper functions for forecasting and analysis

def generate_production_forecast(data, period, method):
    """Generate production forecast using different methods"""
    try:
        # Calculate forecast period in months
        months = {'1 Bulan': 1, '3 Bulan': 3, '6 Bulan': 6, '1 Tahun': 12}[period]
        
        # Prepare data
        data = data.sort_values('harvest_date_dt')
        monthly_data = data.groupby(data['harvest_date_dt'].dt.to_period('M'))['quantity'].sum()
        
        if method == "Moving Average":
            forecast_values = moving_average_forecast(monthly_data, months)
        elif method == "Linear Regression":
            forecast_values = linear_regression_forecast(monthly_data, months)
        else:  # Seasonal
            forecast_values = seasonal_forecast(monthly_data, months)
        
        # Create forecast dataframe
        last_date = monthly_data.index[-1].to_timestamp()
        forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=months, freq='MS')
        
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'forecast': forecast_values,
            'confidence_lower': [v * 0.8 for v in forecast_values],
            'confidence_upper': [v * 1.2 for v in forecast_values]
        })
        
        return forecast_df
        
    except Exception as e:
        st.error(f"Error generating forecast: {str(e)}")
        return None

def moving_average_forecast(data, periods):
    """Simple moving average forecast"""
    window = min(3, len(data))
    last_values = data.tail(window).values
    avg_value = np.mean(last_values)
    return [avg_value] * periods

def linear_regression_forecast(data, periods):
    """Linear regression forecast"""
    if len(data) < 2:
        return [data.mean()] * periods
    
    x = np.arange(len(data))
    y = data.values
    
        # Simple linear regression
    coeffs = np.polyfit(x, y, 1)
    trend = coeffs[0]
    intercept = coeffs[1]
    
    # Forecast
    forecast_x = np.arange(len(data), len(data) + periods)
    forecast_values = trend * forecast_x + intercept
    
    # Ensure positive values
    forecast_values = np.maximum(forecast_values, 0)
    
    return forecast_values.tolist()

def seasonal_forecast(data, periods):
    """Simple seasonal forecast"""
    if len(data) < 12:
        return moving_average_forecast(data, periods)
    
    # Calculate seasonal pattern (last 12 months)
    seasonal_pattern = data.tail(12).values
    seasonal_avg = np.mean(seasonal_pattern)
    
    # Forecast based on seasonal pattern
    forecast_values = []
    for i in range(periods):
        seasonal_index = i % 12
        seasonal_factor = seasonal_pattern[seasonal_index] / seasonal_avg
        base_value = data.mean()
        forecast_values.append(base_value * seasonal_factor)
    
    return forecast_values

def calculate_needs_by_land_area(farmers_df, need_type, period):
    """Calculate needs based on land area"""
    months = {'1 Bulan': 1, '3 Bulan': 3, '6 Bulan': 6}[period]
    
    # Need coefficients (kg per hectare or units per hectare)
    need_coefficients = {
        "Bibit": (25, "kg"),
        "Pupuk": (200, "kg"), 
        "Pestisida": (5, "liter"),
        "Alat Pertanian": (0.1, "unit")
    }
    
    coefficient, unit = need_coefficients.get(need_type, (10, "unit"))
    
    # Calculate total land area
    total_land = farmers_df['land_area'].sum()
    
    # Generate monthly needs
    months_list = pd.date_range(start=datetime.now(), periods=months, freq='MS')
    base_need = total_land * coefficient / 12  # Monthly average
    
    forecast_data = []
    for i, month in enumerate(months_list):
        # Add seasonal variation
        seasonal_factor = 1.0 + 0.3 * np.sin(2 * np.pi * i / 12)
        monthly_need = base_need * seasonal_factor
        
        forecast_data.append({
            'month': month.strftime('%Y-%m'),
            'estimated_need': monthly_need,
            'confidence_lower': monthly_need * 0.8,
            'confidence_upper': monthly_need * 1.2,
            'unit': unit
        })
    
    return pd.DataFrame(forecast_data)

def calculate_needs_by_production(harvests_df, need_type, period):
    """Calculate needs based on production history"""
    months = {'1 Bulan': 1, '3 Bulan': 3, '6 Bulan': 6}[period]
    
    # Need ratios (need per kg of production)
    need_ratios = {
        "Bibit": (0.05, "kg"),
        "Pupuk": (0.2, "kg"),
        "Pestisida": (0.01, "liter"), 
        "Alat Pertanian": (0.0001, "unit")
    }
    
    ratio, unit = need_ratios.get(need_type, (0.1, "unit"))
    
    # Calculate average monthly production
    harvests_df['harvest_date_dt'] = pd.to_datetime(harvests_df['harvest_date'], errors='coerce')
    monthly_production = harvests_df.groupby(harvests_df['harvest_date_dt'].dt.to_period('M'))['quantity'].sum()
    
    if monthly_production.empty:
        return pd.DataFrame()
    
    avg_monthly_production = monthly_production.mean()
    base_need = avg_monthly_production * ratio
    
    # Generate forecast
    months_list = pd.date_range(start=datetime.now(), periods=months, freq='MS')
    forecast_data = []
    
    for i, month in enumerate(months_list):
        seasonal_factor = 1.0 + 0.2 * np.sin(2 * np.pi * i / 12)
        monthly_need = base_need * seasonal_factor
        
        forecast_data.append({
            'month': month.strftime('%Y-%m'),
            'estimated_need': monthly_need,
            'confidence_lower': monthly_need * 0.8,
            'confidence_upper': monthly_need * 1.2,
            'unit': unit
        })
    
    return pd.DataFrame(forecast_data)

def calculate_needs_by_farmers(farmers_df, need_type, period):
    """Calculate needs based on number of farmers"""
    months = {'1 Bulan': 1, '3 Bulan': 3, '6 Bulan': 6}[period]
    
    # Need per farmer
    need_per_farmer = {
        "Bibit": (2, "kg"),
        "Pupuk": (15, "kg"),
        "Pestisida": (0.5, "liter"),
        "Alat Pertanian": (0.01, "unit")
    }
    
    per_farmer, unit = need_per_farmer.get(need_type, (5, "unit"))
    
    # Calculate active farmers
    active_farmers = len(farmers_df[farmers_df['is_active'] == 1])
    base_need = active_farmers * per_farmer
    
    # Generate forecast
    months_list = pd.date_range(start=datetime.now(), periods=months, freq='MS')
    forecast_data = []
    
    for i, month in enumerate(months_list):
        seasonal_factor = 1.0 + 0.15 * np.sin(2 * np.pi * i / 12)
        monthly_need = base_need * seasonal_factor
        
        forecast_data.append({
            'month': month.strftime('%Y-%m'),
            'estimated_need': monthly_need,
            'confidence_lower': monthly_need * 0.8,
            'confidence_upper': monthly_need * 1.2,
            'unit': unit
        })
    
    return pd.DataFrame(forecast_data)

def analyze_production_trends(data):
    """Analyze production trends"""
    monthly_data = data.groupby(data['harvest_date_dt'].dt.to_period('M'))['quantity'].sum().reset_index()
    monthly_data.columns = ['period', 'value']
    monthly_data['period'] = monthly_data['period'].dt.to_timestamp()
    
    # Calculate trend direction
    if len(monthly_data) >= 2:
        recent_avg = monthly_data['value'].tail(3).mean()
        earlier_avg = monthly_data['value'].head(3).mean()
        
        if recent_avg > earlier_avg * 1.1:
            monthly_data['trend_direction'] = 'Meningkat'
        elif recent_avg < earlier_avg * 0.9:
            monthly_data['trend_direction'] = 'Menurun'
        else:
            monthly_data['trend_direction'] = 'Stabil'
    else:
        monthly_data['trend_direction'] = 'Tidak cukup data'
    
    return monthly_data

def analyze_quality_trends(data):
    """Analyze quality trends"""
    quality_mapping = {'A': 4, 'B': 3, 'C': 2, 'D': 1}
    data['quality_score'] = data['quality_grade'].map(quality_mapping)
    
    monthly_quality = data.groupby(data['harvest_date_dt'].dt.to_period('M'))['quality_score'].mean().reset_index()
    monthly_quality.columns = ['period', 'value']
    monthly_quality['period'] = monthly_quality['period'].dt.to_timestamp()
    
    return monthly_quality

def analyze_distribution_trends(data):
    """Analyze distribution trends"""
    monthly_dist = data.groupby(data['delivery_date_dt'].dt.to_period('M'))['quantity'].sum().reset_index()
    monthly_dist.columns = ['period', 'value']
    monthly_dist['period'] = monthly_dist['period'].dt.to_timestamp()
    
    return monthly_dist

def analyze_price_trends(data):
    """Analyze price trends (estimated from harvest data)"""
    # Estimate price based on quality grades
    quality_prices = {'A': 15000, 'B': 12000, 'C': 10000, 'D': 8000}
    data['estimated_price'] = data['quality_grade'].map(quality_prices)
    
    monthly_price = data.groupby(data['harvest_date_dt'].dt.to_period('M'))['estimated_price'].mean().reset_index()
    monthly_price.columns = ['period', 'value']
    monthly_price['period'] = monthly_price['period'].dt.to_timestamp()
    
    return monthly_price

def generate_trend_insights(analysis_type, data):
    """Generate insights from trend analysis"""
    insights = []
    
    if 'value' in data.columns and len(data) >= 3:
        recent_values = data['value'].tail(3).values
        overall_trend = 'increasing' if recent_values[-1] > recent_values[0] else 'decreasing'
        
        if analysis_type == "Produksi":
            if overall_trend == 'increasing':
                insights.append("📈 Produksi menunjukkan tren peningkatan, pertimbangkan untuk meningkatkan kapasitas penyimpanan")
            else:
                insights.append("📉 Produksi menurun, perlu evaluasi faktor penyebab dan intervensi")
        
        elif analysis_type == "Kualitas":
            if overall_trend == 'increasing':
                insights.append("✅ Kualitas produk membaik, tingkatkan premium pricing")
            else:
                insights.append("⚠️ Kualitas menurun, perlu program pelatihan dan quality control")
    
    for insight in insights:
        st.info(insight)

def generate_strategic_recommendations(harvests_df, distributions_df, farmers_df, merchants_df):
    """Generate strategic recommendations based on data analysis"""
    recommendations = {}
    
    # Production recommendations
    recommendations["Produksi"] = [
        {
            'title': 'Optimasi Musim Tanam',
            'description': 'Berdasarkan data historis, optimalisasi jadwal tanam dapat meningkatkan produksi hingga 15%',
            'priority': 'high',
            'impact': 'Penambahan produksi 15%',
            'action_items': ['Analisis pola musim historis', 'Buat jadwal tanam optimal', 'Sosialisasikan ke petani']
        }
    ]
    
    # Distribution recommendations
    if not distributions_df.empty:
        completion_rate = len(distributions_df[distributions_df['status'] == 'Completed']) / len(distributions_df) * 100
        
        if completion_rate < 80:
            recommendations["Distribusi"] = [
                {
                    'title': 'Tingkatkan Efisiensi Distribusi',
                    'description': f'Tingkat penyelesaian distribusi saat ini {completion_rate:.1f} perlu ditingkatkan',
                    'priority': 'high',
                    'impact': 'Peningkatan layanan ke pelanggan',
                    'action_items': ['Evaluasi proses distribusi', 'Optimasi rute pengiriman', 'Tambah kendaraan']
                }
            ]
    
    # Quality recommendations
    if not harvests_df.empty:
        quality_dist = harvests_df['quality_grade'].value_counts(normalize=True)
        
        if quality_dist.get('A', 0) < 0.3:
            recommendations["Kualitas"] = [
                {
                    'title': 'Program Peningkatan Kualitas',
                    'description': f'Hanya {quality_dist.get("A", 0)*100:.1f}% produk dengan kualitas A',
                    'priority': 'medium',
                    'impact': 'Peningkatan nilai jual produk',
                    'action_items': ['Pelatihan teknik panen', 'Quality control system', 'Insentif kualitas']
                }
            ]
    
    return recommendations

def create_implementation_timeline(recommendations):
    """Create implementation timeline for recommendations"""
    timeline_data = []
    
    for category, recs in recommendations.items():
        for rec in recs:
            timeline_data.append({
                'task': rec['title'],
                'start': datetime.now(),
                'end': datetime.now() + timedelta(days={'high': 30, 'medium': 60, 'low': 90}[rec['priority']]),
                'priority': rec['priority']
            })
    
    return timeline_data

def analyze_resource_requirements(recommendations):
    """Analyze resource requirements for implementing recommendations"""
    total_cost = 0
    personnel = 0
    max_time = 0
    
    for category, recs in recommendations.items():
        for rec in recs:
            # Simple estimation logic
            if rec['priority'] == 'high':
                total_cost += 5000000
                personnel += 3
                max_time = max(max_time, 1)
            elif rec['priority'] == 'medium':
                total_cost += 3000000
                personnel += 2
                max_time = max(max_time, 2)
            else:
                total_cost += 1000000
                personnel += 1
                max_time = max(max_time, 3)
    
    return {
        'estimated_cost': total_cost,
        'personnel': personnel,
        'implementation_time': max_time
    }

if __name__ == "__main__":
    app()
