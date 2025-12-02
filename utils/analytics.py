import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from utils.sqlite_database import get_database
from typing import Dict, List, Optional
import numpy as np
import logging

# Configure logging
logger = logging.getLogger(__name__)

class InventoryAnalytics:
    def __init__(self):
        self.db = get_database()
    
    def get_inventory_turnover(self, days: int = 30) -> Dict:
        """Calculate inventory turnover rate"""
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get all items
            cursor.execute("SELECT * FROM items")
            items = [dict(row) for row in cursor.fetchall()]
            
            turnover_data = []
            
            for item in items:
                # Get consumption data (outbound transactions)
                cursor.execute("""
                    SELECT SUM(quantity) as total_consumed
                    FROM inventory_transactions
                    WHERE item_id = ? 
                    AND transaction_type = 'out'
                    AND transaction_date >= ?
                """, (item['id'], start_date))
                
                result = cursor.fetchone()
                total_consumed = result['total_consumed'] if result and result['total_consumed'] else 0
                
                current_stock = item.get('current_stock', 0) or 0
                avg_stock = current_stock  # Simplified - would need opening stock for accurate calculation
                
                # Calculate turnover rate
                if avg_stock > 0:
                    turnover_rate = (total_consumed / avg_stock) * (365 / days)
                else:
                    turnover_rate = 0
                
                turnover_data.append({
                    'item_name': item['name'],
                    'category': item.get('category', 'N/A'),
                    'turnover_rate': turnover_rate,
                    'total_consumed': total_consumed,
                    'avg_stock': avg_stock,
                    'current_stock': current_stock
                })
            
            return {
                'turnover_data': turnover_data,
                'avg_turnover': np.mean([d['turnover_rate'] for d in turnover_data]) if turnover_data else 0,
                'total_items': len(turnover_data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating turnover: {e}")
            return {'turnover_data': [], 'avg_turnover': 0, 'total_items': 0}
    
    def get_stock_movement_analysis(self, days: int = 30) -> Dict:
        """Analyze stock movement patterns"""
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get all transactions in the period
            cursor.execute("""
                SELECT * FROM inventory_transactions
                WHERE transaction_date >= ?
            """, (start_date,))
            
            transactions = [dict(row) for row in cursor.fetchall()]
            
            # Group by transaction type
            movement_summary = {}
            
            for transaction in transactions:
                transaction_type = transaction.get('transaction_type', 'unknown')
                quantity = transaction.get('quantity', 0) or 0
                
                if transaction_type not in movement_summary:
                    movement_summary[transaction_type] = {
                        'total_transactions': 0,
                        'total_quantity': 0,
                        'avg_quantity': 0
                    }
                
                movement_summary[transaction_type]['total_transactions'] += 1
                movement_summary[transaction_type]['total_quantity'] += quantity
            
            # Calculate averages
            for trans_type in movement_summary:
                summary = movement_summary[trans_type]
                if summary['total_transactions'] > 0:
                    summary['avg_quantity'] = summary['total_quantity'] / summary['total_transactions']
            
            # Daily movement trend
            daily_movement = {}
            for transaction in transactions:
                transaction_date = transaction.get('transaction_date', '')
                if isinstance(transaction_date, str):
                    try:
                        date_obj = datetime.fromisoformat(transaction_date)
                        date_str = date_obj.strftime('%Y-%m-%d')
                    except:
                        date_str = transaction_date[:10] if len(transaction_date) >= 10 else transaction_date
                else:
                    date_str = str(transaction_date)
                
                trans_type = transaction.get('transaction_type', 'unknown')
                quantity = transaction.get('quantity', 0) or 0
                
                if date_str not in daily_movement:
                    daily_movement[date_str] = {}
                
                if trans_type not in daily_movement[date_str]:
                    daily_movement[date_str][trans_type] = 0
                
                daily_movement[date_str][trans_type] += quantity
            
            return {
                'movement_summary': movement_summary,
                'daily_movement': daily_movement,
                'total_transactions': len(transactions)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing stock movement: {e}")
            return {'movement_summary': {}, 'daily_movement': {}, 'total_transactions': 0}
    
    def get_inventory_health_score(self) -> Dict:
        """Calculate overall inventory health score"""
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            # Get all items
            cursor.execute("SELECT * FROM items")
            items = [dict(row) for row in cursor.fetchall()]
            total_items = len(items)
            
            if total_items == 0:
                return {'score': 0, 'factors': {}, 'total_items': 0}
            
            # Calculate health factors
            factors = {}
            
            # 1. Stock availability factor
            in_stock_items = len([item for item in items if (item.get('current_stock', 0) or 0) > 0])
            factors['stock_availability'] = (in_stock_items / total_items) * 100
            
            # 2. Stock level factor (items with adequate stock)
            adequate_stock_items = len([
                item for item in items 
                if (item.get('current_stock', 0) or 0) > (item.get('min_stock', 0) or 0)
            ])
            factors['stock_adequacy'] = (adequate_stock_items / total_items) * 100
            
            # 3. Turnover factor
            turnover_data = self.get_inventory_turnover(30)
            avg_turnover = turnover_data['avg_turnover']
            # Normalize turnover (ideal is 4-6 times per year)
            if avg_turnover >= 4 and avg_turnover <= 6:
                factors['turnover'] = 100
            elif avg_turnover < 4:
                factors['turnover'] = (avg_turnover / 4) * 100 if avg_turnover > 0 else 0
            else:
                factors['turnover'] = max(0, 100 - ((avg_turnover - 6) * 10))
            
            # 4. Movement factor (recent activity)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM inventory_transactions
                WHERE transaction_date >= ?
            """, (thirty_days_ago,))
            
            result = cursor.fetchone()
            recent_transactions = result['count'] if result else 0
            
            # Assume 30 transactions per month is good
            factors['movement'] = min(100, (recent_transactions / 30) * 100)
            
            # Calculate weighted score
            weights = {
                'stock_availability': 0.25,
                'stock_adequacy': 0.25,
                'turnover': 0.30,
                'movement': 0.20
            }
            
            score = sum(factors[factor] * weights[factor] for factor in weights)
            
            return {
                'score': score,
                'factors': factors,
                'total_items': total_items
            }
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return {'score': 0, 'factors': {}, 'total_items': 0}
    
    def display_analytics_dashboard(self):
        """Display comprehensive analytics dashboard"""
        st.header("📊 Analytics Dashboard")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            days_range = st.selectbox("Periode Analisis:", [7, 30, 90, 180], index=1)
        
        with col2:
            st.write("")  # Spacer
        
        # Create tabs for different analytics
        tab1, tab2, tab3 = st.tabs([
            "Ringkasan Kesehatan",
            "Perputaran Inventory", 
            "Analisis Pergerakan"
        ])
        
        with tab1:
            self.display_health_summary()
        
        with tab2:
            self.display_turnover_analysis(days_range)
        
        with tab3:
            self.display_movement_analysis(days_range)
    
    def display_health_summary(self):
        """Display inventory health summary"""
        st.subheader("🏥 Ringkasan Kesehatan Inventory")
        
        health_data = self.get_inventory_health_score()
        
        # Overall health score
        score = health_data['score']
        factors = health_data['factors']
        
        # Display score with color coding
        if score >= 80:
            score_color = "🟢"
            status = "Sangat Baik"
        elif score >= 60:
            score_color = "🟡"
            status = "Baik"
        elif score >= 40:
            score_color = "🟠"
            status = "Perlu Perhatian"
        else:
            score_color = "🔴"
            status = "Buruk"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(f"Skor Kesehatan {score_color}", f"{score:.1f}/100", status)
            st.metric("Total Item", health_data['total_items'])
        
        with col2:
            # Display factor breakdown
            st.write("**Faktor Kesehatan:**")
            for factor, value in factors.items():
                factor_name = {
                    'stock_availability': 'Ketersediaan Stok',
                    'stock_adequacy': 'Kecukupan Stok',
                    'turnover': 'Perputaran',
                    'movement': 'Aktivitas'
                }.get(factor, factor)
                
                st.write(f"• {factor_name}: {value:.1f}%")
    
    def display_turnover_analysis(self, days: int):
        """Display turnover analysis"""
        st.subheader(f"🔄 Analisis Perputaran Inventory ({days} hari)")
        
        turnover_data = self.get_inventory_turnover(days)
        
        if turnover_data['turnover_data']:
            # Convert to DataFrame
            df = pd.DataFrame(turnover_data['turnover_data'])
            
            # Display summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Rata-rata Perputaran", f"{turnover_data['avg_turnover']:.1f}x/tahun")
            
            with col2:
                high_turnover = len([d for d in turnover_data['turnover_data'] if d['turnover_rate'] > 6])
                st.metric("Item dengan Perputaran Tinggi", high_turnover)
            
            with col3:
                low_turnover = len([d for d in turnover_data['turnover_data'] if d['turnover_rate'] < 2])
                st.metric("Item dengan Perputaran Rendah", low_turnover)
            
            # Display top items by turnover
            st.subheader("Item dengan Perputaran Tertinggi")
            top_turnover = df.nlargest(10, 'turnover_rate')[['item_name', 'category', 'turnover_rate']]
            st.dataframe(top_turnover, use_container_width=True)
            
            # Turnover distribution chart
            fig = px.histogram(df, x='turnover_rate', nbins=20, 
                             title='Distribusi Tingkat Perputaran',
                             color_discrete_sequence=px.colors.sequential.Blues)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak cukup data untuk analisis perputaran")
    
    def display_movement_analysis(self, days: int):
        """Display movement analysis"""
        st.subheader(f"📈 Analisis Pergerakan Stok ({days} hari)")
        
        movement_data = self.get_stock_movement_analysis(days)
        
        if movement_data['movement_summary']:
            # Display summary
            st.write("**Ringkasan Transaksi:**")
            
            cols = st.columns(len(movement_data['movement_summary']))
            
            for idx, (trans_type, summary) in enumerate(movement_data['movement_summary'].items()):
                with cols[idx]:
                    st.metric(f"{trans_type.upper()}", summary['total_transactions'])
                    st.write(f"Total: {summary['total_quantity']:.0f}")
                    st.write(f"Rata-rata: {summary['avg_quantity']:.1f}")
            
            # Daily movement trend
            if movement_data['daily_movement']:
                st.subheader("Tren Harian")
                
                # Convert to DataFrame
                daily_df = pd.DataFrame.from_dict(movement_data['daily_movement'], orient='index')
                daily_df = daily_df.fillna(0)
                daily_df.index = pd.to_datetime(daily_df.index)
                daily_df = daily_df.sort_index()
                
                # Line chart
                fig = px.line(daily_df, title='Tren Pergerakan Harian')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak cukup data untuk analisis pergerakan")

def display_analytics_widget():
    """Display a compact analytics widget"""
    analytics = InventoryAnalytics()
    health_data = analytics.get_inventory_health_score()
    
    score = health_data['score']
    
    if score >= 80:
        status = "🟢 Sangat Baik"
    elif score >= 60:
        status = "🟡 Baik"
    elif score >= 40:
        status = "🟠 Perlu Perhatian"
    else:
        status = "🔴 Buruk"
    
    st.metric("Kesehatan Inventory", f"{score:.0f}/100", status)