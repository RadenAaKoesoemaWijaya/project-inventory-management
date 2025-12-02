import streamlit as st
from datetime import datetime, timedelta
from utils.sqlite_database import get_database, get_items_low_stock
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict, Optional
import logging
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.db = get_database()
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@inventory.com')
    
    def check_stock_alerts(self) -> List[Dict]:
        """Check for items with low stock"""
        try:
            # Use the existing get_items_low_stock function
            low_stock_df = get_items_low_stock(limit=100)
            
            if low_stock_df.empty:
                return []
            
            low_stock_items = low_stock_df.to_dict('records')
            
            # Calculate urgency level
            for item in low_stock_items:
                min_stock = item.get('min_stock', 0) or 0
                current_stock = item.get('current_stock', 0) or 0
                
                if min_stock > 0:
                    stock_percentage = (current_stock / min_stock) * 100
                else:
                    stock_percentage = 0
                
                if stock_percentage <= 25:
                    item['urgency'] = 'critical'
                    item['urgency_color'] = '🔴'
                elif stock_percentage <= 50:
                    item['urgency'] = 'high'
                    item['urgency_color'] = '🟠'
                elif stock_percentage <= 100:
                    item['urgency'] = 'medium'
                    item['urgency_color'] = '🟡'
                else:
                    item['urgency'] = 'low'
                    item['urgency_color'] = '🟢'
                
                item['stock_percentage'] = stock_percentage
            
            return low_stock_items
            
        except Exception as e:
            logger.error(f"Error checking stock alerts: {e}")
            return []
    
    def check_recent_transactions(self, hours: int = 24) -> List[Dict]:
        """Check for recent transactions"""
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            # Get transactions from the last N hours
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute("""
                SELECT it.*, i.name as item_name, i.unit
                FROM inventory_transactions it
                LEFT JOIN items i ON it.item_id = i.id
                WHERE it.transaction_date >= ?
                ORDER BY it.transaction_date DESC
                LIMIT 50
            """, (cutoff_time,))
            
            recent_transactions = [dict(row) for row in cursor.fetchall()]
            
            return recent_transactions
            
        except Exception as e:
            logger.error(f"Error checking recent transactions: {e}")
            return []
    
    def get_real_time_alerts(self) -> Dict:
        """Get comprehensive real-time alerts"""
        try:
            alerts = {
                'stock_alerts': self.check_stock_alerts(),
                'recent_transactions': self.check_recent_transactions(),
                'timestamp': datetime.now()
            }
            
            # Add transaction statistics
            if alerts['recent_transactions']:
                alerts['transaction_stats'] = {
                    'total_transactions': len(alerts['recent_transactions']),
                    'inbound_count': len([t for t in alerts['recent_transactions'] if t.get('transaction_type') == 'in']),
                    'outbound_count': len([t for t in alerts['recent_transactions'] if t.get('transaction_type') == 'out']),
                    'transfer_count': len([t for t in alerts['recent_transactions'] if t.get('transaction_type') == 'transfer'])
                }
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting real-time alerts: {e}")
            return {}
    
    def display_notification_dashboard(self):
        """Display notification dashboard in Streamlit"""
        st.header("🔔 Sistem Notifikasi")
        
        # Create tabs for different notification features
        tab1, tab2 = st.tabs(["Peringatan Stok", "Laporan"])
        
        with tab1:
            self.display_stock_alerts()
        
        with tab2:
            self.display_reports()
    
    def display_stock_alerts(self):
        """Display stock alerts"""
        st.subheader("📊 Peringatan Stok")
        
        # Get current alerts
        alerts = self.check_stock_alerts()
        
        if alerts:
            # Display summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                critical_count = len([a for a in alerts if a['urgency'] == 'critical'])
                st.metric("Kritis", critical_count, delta=None)
            
            with col2:
                high_count = len([a for a in alerts if a['urgency'] == 'high'])
                st.metric("Tinggi", high_count, delta=None)
            
            with col3:
                medium_count = len([a for a in alerts if a['urgency'] == 'medium'])
                st.metric("Sedang", medium_count, delta=None)
            
            # Display detailed alerts
            st.subheader("Detail Peringatan")
            
            for alert in alerts:
                urgency_color = alert['urgency_color']
                stock_percentage = alert['stock_percentage']
                
                with st.expander(f"{urgency_color} {alert.get('name', 'Unknown')} - {stock_percentage:.0f}% dari stok minimum"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Kategori:** {alert.get('category', 'N/A')}")
                        st.write(f"**Stok Saat Ini:** {alert.get('current_stock', 0)} {alert.get('unit', 'unit')}")
                        st.write(f"**Stok Minimum:** {alert.get('min_stock', 0)} {alert.get('unit', 'unit')}")
                    
                    with col2:
                        st.write(f"**Persentase Stok:** {stock_percentage:.1f}%")
                        st.write(f"**Tingkat Urgensi:** {alert['urgency'].title()}")
                        
                        # Calculate days until stock runs out (simple estimation)
                        current_stock = alert.get('current_stock', 0) or 0
                        min_stock = alert.get('min_stock', 0) or 0
                        if current_stock > 0 and min_stock > 0:
                            # Assume average daily usage based on minimum stock (30 days)
                            daily_usage = min_stock / 30
                            days_remaining = current_stock / daily_usage if daily_usage > 0 else 999
                            st.write(f"**Estimasi Habis:** {days_remaining:.0f} hari")
        else:
            st.success("✅ Tidak ada peringatan stok saat ini")
    
    def display_reports(self):
        """Display notification reports"""
        st.subheader("📈 Laporan Notifikasi")
        
        # Get inventory statistics
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM items")
            total_items = cursor.fetchone()['total']
            
            low_stock_count = len(self.check_stock_alerts())
            
            cursor.execute("SELECT COUNT(*) as total FROM items WHERE current_stock = 0")
            out_of_stock = cursor.fetchone()['total']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Item", total_items)
            
            with col2:
                st.metric("Stok Rendah", low_stock_count)
            
            with col3:
                st.metric("Habis Stok", out_of_stock)
        except Exception as e:
            logger.error(f"Error displaying reports: {e}")
            st.error("Error loading report data")
    
    def generate_stock_alert_report(self) -> Dict:
        """Generate a comprehensive stock alert report"""
        try:
            alerts = self.check_stock_alerts()
            
            # Get inventory statistics
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM items")
            total_items = cursor.fetchone()['total']
            
            low_stock_count = len(alerts)
            
            cursor.execute("SELECT COUNT(*) as total FROM items WHERE current_stock = 0")
            out_of_stock = cursor.fetchone()['total']
            
            # Calculate total value at risk (if cost data available)
            total_value_at_risk = 0
            for alert in alerts:
                price_per_unit = alert.get('price_per_unit', 0) or 0
                current_stock = alert.get('current_stock', 0) or 0
                estimated_value = current_stock * price_per_unit
                total_value_at_risk += estimated_value
            
            report = {
                'generated_at': datetime.now(),
                'summary': {
                    'total_items': total_items,
                    'low_stock_items': low_stock_count,
                    'out_of_stock_items': out_of_stock,
                    'value_at_risk': total_value_at_risk
                },
                'alerts': alerts
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {}

def display_notification_widget():
    """Display a compact notification widget"""
    manager = NotificationManager()
    
    alerts = manager.check_stock_alerts()
    
    if alerts:
        st.warning(f"🔔 {len(alerts)} peringatan stok aktif")
        
        # Show top 3 alerts
        for alert in alerts[:3]:
            stock_percentage = alert['stock_percentage']
            st.text(f"• {alert.get('name', 'Unknown')}: {alert.get('current_stock', 0)}/{alert.get('min_stock', 0)} ({stock_percentage:.0f}%)")
        
        if len(alerts) > 3:
            st.text(f"... dan {len(alerts) - 3} item lainnya")
    else:
        st.success("✅ Tidak ada peringatan")

def display_realtime_notification_widget():
    """Display comprehensive real-time notification widget"""
    manager = NotificationManager()
    
    # Get real-time alerts
    realtime_data = manager.get_real_time_alerts()
    
    if not realtime_data:
        st.info("🔄 Memuat data real-time...")
        return
    
    # Create columns for different alert types
    col1, col2 = st.columns(2)
    
    with col1:
        # Stock alerts
        stock_alerts = realtime_data.get('stock_alerts', [])
        critical_alerts = [a for a in stock_alerts if a['urgency'] == 'critical']
        high_alerts = [a for a in stock_alerts if a['urgency'] == 'high']
        
        if critical_alerts:
            st.error(f"🚨 {len(critical_alerts)} Kritis")
        if high_alerts:
            st.warning(f"⚠️ {len(high_alerts)} Tinggi")
        
        if stock_alerts:
            st.metric("Total Peringatan Stok", len(stock_alerts))
        else:
            st.success("✅ Stok Aman")
    
    with col2:
        # Transaction stats
        transaction_stats = realtime_data.get('transaction_stats')
        if transaction_stats:
            st.metric("Transaksi 24h", transaction_stats['total_transactions'])
            
            col2a, col2b = st.columns(2)
            with col2a:
                st.metric("Masuk", transaction_stats['inbound_count'], delta=None)
            with col2b:
                st.metric("Keluar", transaction_stats['outbound_count'], delta=None)
        else:
            st.metric("Transaksi 24h", 0)
    
    # Show recent activity
    recent_transactions = realtime_data.get('recent_transactions', [])
    if recent_transactions:
        st.subheader("Aktivitas Terbaru")
        for transaction in recent_transactions[:3]:
            trans_type = transaction.get('transaction_type', 'unknown')
            item_name = transaction.get('item_name', 'Unknown Item')
            quantity = transaction.get('quantity', 0)
            transaction_date = transaction.get('transaction_date', datetime.now())
            
            # Format timestamp
            if isinstance(transaction_date, str):
                try:
                    transaction_date = datetime.fromisoformat(transaction_date)
                    time_str = transaction_date.strftime("%H:%M")
                except:
                    time_str = str(transaction_date)
            elif isinstance(transaction_date, datetime):
                time_str = transaction_date.strftime("%H:%M")
            else:
                time_str = str(transaction_date)
            
            # Type icons
            type_icons = {
                'in': '📥',
                'out': '📤',
                'transfer': '🔄'
            }
            icon = type_icons.get(trans_type, '📝')
            
            st.text(f"{icon} {time_str} - {item_name} ({quantity} {transaction.get('unit', 'unit')})")
    
    # Show timestamp
    timestamp = realtime_data.get('timestamp')
    if timestamp:
        st.caption(f"🕐 Update terakhir: {timestamp.strftime('%H:%M:%S')}")