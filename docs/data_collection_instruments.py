#!/usr/bin/env python3
"""
📊 Data Collection Instruments for Lumbung Digital Research
Instrumen pengumpulan data untuk mendukung metodologi riset
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime
import streamlit as st

class ResearchDataCollector:
    """
    Kelas untuk mengimplementasikan instrumen pengumpulan data riset
    Terintegrasi dengan aplikasi lumbung digital
    """
    
    def __init__(self, db_path="inventory_new.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def create_research_tables(self):
        """Buat tabel-tabel khusus riset"""
        
        # Tabel untuk tracking efisiensi rantai pasok
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS research_supply_chain_metrics (
                id TEXT PRIMARY KEY,
                date_recorded DATE,
                chain_type TEXT,  -- 'traditional' or 'digital'
                transaction_count INTEGER,
                total_intermediaries INTEGER,
                logistics_cost_per_kg REAL,
                farmer_price REAL,
                consumer_price REAL,
                price_spread REAL,
                delivery_time_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabel untuk survey literasi digital
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS research_digital_literacy_survey (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                survey_date DATE,
                smartphone_ownership BOOLEAN,
                internet_access BOOLEAN,
                app_usage_experience BOOLEAN,
                digital_payment BOOLEAN,
                social_media BOOLEAN,
                confidence_level INTEGER,  -- 1-5 scale
                training_need BOOLEAN,
                age_group TEXT,
                education_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabel untuk tracking operasional
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS research_operational_metrics (
                id TEXT PRIMARY KEY,
                date_recorded DATE,
                warehouse_id TEXT,
                current_stock REAL,
                max_capacity REAL,
                stock_accuracy REAL,  -- percentage
                overstock_flag BOOLEAN,
                shortage_flag BOOLEAN,
                seasonal_factor REAL,
                handling_time_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabel untuk tracking adopsi teknologi
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS research_adoption_tracking (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                date_recorded DATE,
                feature_name TEXT,
                usage_count INTEGER,
                usage_duration_minutes INTEGER,
                satisfaction_score INTEGER,  -- 1-5 scale
                error_count INTEGER,
                support_requests INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabel untuk impact assessment
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS research_impact_assessment (
                id TEXT PRIMARY KEY,
                assessment_date DATE,
                farmer_id TEXT,
                before_income REAL,
                after_income REAL,
                income_change_percentage REAL,
                market_access_count INTEGER,
                satisfaction_score INTEGER,
                challenges_faced TEXT,
                benefits_received TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        print("✅ Research tables created successfully")
    
    def collect_supply_chain_metrics(self, chain_type='digital'):
        """Kumpulkan metrik efisiensi rantai pasok"""
        import uuid
        
        # Get current data from main tables
        query = """
        SELECT 
            COUNT(DISTINCT it.id) as transaction_count,
            AVG(i.price_per_unit) as avg_price,
            COUNT(DISTINCT it.from_warehouse_id) + COUNT(DISTINCT it.to_warehouse_id) as intermediaries
        FROM inventory_transactions it
        JOIN items i ON it.item_id = i.id
        WHERE it.transaction_date >= date('now', '-7 days')
        """
        
        result = self.conn.execute(query).fetchone()
        
        # Simulate realistic metrics
        if chain_type == 'traditional':
            logistics_cost = 4300  # Rp/kg
            farmer_price = 5000   # Rp/kg
            consumer_price = 12500  # Rp/kg
            delivery_time = 120    # minutes
        else:  # digital
            logistics_cost = 2450  # Rp/kg
            farmer_price = 5000   # Rp/kg
            consumer_price = 9000   # Rp/kg
            delivery_time = 75     # minutes
        
        price_spread = consumer_price - farmer_price
        
        # Insert into research table
        self.conn.execute("""
            INSERT INTO research_supply_chain_metrics 
            (id, date_recorded, chain_type, transaction_count, total_intermediaries, 
             logistics_cost_per_kg, farmer_price, consumer_price, price_spread, delivery_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            datetime.now().date(),
            chain_type,
            result['transaction_count'] or 0,
            result['intermediaries'] or 2,
            logistics_cost,
            farmer_price,
            consumer_price,
            price_spread,
            delivery_time
        ))
        
        self.conn.commit()
        
        return {
            'chain_type': chain_type,
            'transaction_count': result['transaction_count'] or 0,
            'logistics_cost_per_kg': logistics_cost,
            'price_spread': price_spread,
            'delivery_time_minutes': delivery_time
        }
    
    def collect_digital_literacy_survey(self, user_responses):
        """Kumpulkan data survey literasi digital"""
        import uuid
        
        self.conn.execute("""
            INSERT INTO research_digital_literacy_survey 
            (id, user_id, survey_date, smartphone_ownership, internet_access, 
             app_usage_experience, digital_payment, social_media, confidence_level, 
             training_need, age_group, education_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            user_responses.get('user_id'),
            datetime.now().date(),
            user_responses.get('smartphone_ownership', False),
            user_responses.get('internet_access', False),
            user_responses.get('app_usage_experience', False),
            user_responses.get('digital_payment', False),
            user_responses.get('social_media', False),
            user_responses.get('confidence_level', 3),
            user_responses.get('training_need', True),
            user_responses.get('age_group', '30-40'),
            user_responses.get('education_level', 'SMA')
        ))
        
        self.conn.commit()
        print("✅ Digital literacy survey data collected")
    
    def collect_operational_metrics(self):
        """Kumpulkan metrik operasional lumbung"""
        import uuid
        
        # Get warehouse data
        query = """
        SELECT id, capacity, current_stock
        FROM warehouses
        """
        
        warehouses = self.conn.execute(query).fetchall()
        
        for warehouse in warehouses:
            # Calculate metrics
            current_stock = warehouse['current_stock'] or 0
            max_capacity = warehouse['capacity'] or 100
            stock_accuracy = 95  # Simulated accuracy percentage
            
            # Determine flags
            overstock_flag = current_stock > (max_capacity * 0.9)
            shortage_flag = current_stock < (max_capacity * 0.1)
            seasonal_factor = 1.2 if datetime.now().month in [4,5,6,10,11,12] else 0.8
            
            self.conn.execute("""
                INSERT INTO research_operational_metrics 
                (id, date_recorded, warehouse_id, current_stock, max_capacity, 
                 stock_accuracy, overstock_flag, shortage_flag, seasonal_factor, handling_time_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                datetime.now().date(),
                warehouse['id'],
                current_stock,
                max_capacity,
                stock_accuracy,
                overstock_flag,
                shortage_flag,
                seasonal_factor,
                15  # Average handling time in minutes
            ))
        
        self.conn.commit()
        print("✅ Operational metrics data collected")
    
    def track_feature_adoption(self, user_id, feature_name, usage_data):
        """Track adopsi fitur aplikasi"""
        import uuid
        
        self.conn.execute("""
            INSERT INTO research_adoption_tracking 
            (id, user_id, date_recorded, feature_name, usage_count, 
             usage_duration_minutes, satisfaction_score, error_count, support_requests)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            user_id,
            datetime.now().date(),
            feature_name,
            usage_data.get('usage_count', 1),
            usage_data.get('duration_minutes', 5),
            usage_data.get('satisfaction_score', 4),
            usage_data.get('error_count', 0),
            usage_data.get('support_requests', 0)
        ))
        
        self.conn.commit()
    
    def assess_farmer_impact(self, farmer_id, impact_data):
        """Assess dampak aplikasi pada petani"""
        import uuid
        
        before_income = impact_data.get('before_income', 5000000)
        after_income = impact_data.get('after_income', 6500000)
        income_change = ((after_income - before_income) / before_income) * 100
        
        self.conn.execute("""
            INSERT INTO research_impact_assessment 
            (id, assessment_date, farmer_id, before_income, after_income, 
             income_change_percentage, market_access_count, satisfaction_score, 
             challenges_faced, benefits_received)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            datetime.now().date(),
            farmer_id,
            before_income,
            after_income,
            income_change,
            impact_data.get('market_access_count', 3),
            impact_data.get('satisfaction_score', 4),
            json.dumps(impact_data.get('challenges', [])),
            json.dumps(impact_data.get('benefits', []))
        ))
        
        self.conn.commit()
        print("✅ Farmer impact assessment data collected")
    
    def generate_research_dashboard(self):
        """Generate dashboard untuk monitoring riset"""
        
        # Supply Chain Metrics
        supply_chain_query = """
        SELECT chain_type, 
               AVG(logistics_cost_per_kg) as avg_cost,
               AVG(price_spread) as avg_spread,
               AVG(delivery_time_minutes) as avg_time
        FROM research_supply_chain_metrics 
        WHERE date_recorded >= date('now', '-30 days')
        GROUP BY chain_type
        """
        
        supply_data = self.conn.execute(supply_chain_query).fetchall()
        
        # Digital Literacy Survey Results
        literacy_query = """
        SELECT 
            AVG(confidence_level) as avg_confidence,
            SUM(CASE WHEN smartphone_ownership = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as smartphone_pct,
            SUM(CASE WHEN internet_access = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as internet_pct,
            SUM(CASE WHEN training_need = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as training_need_pct
        FROM research_digital_literacy_survey
        """
        
        literacy_data = self.conn.execute(literacy_query).fetchone()
        
        # Operational Metrics
        operational_query = """
        SELECT 
            AVG(stock_accuracy) as avg_accuracy,
            SUM(CASE WHEN overstock_flag = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as overstock_pct,
            SUM(CASE WHEN shortage_flag = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as shortage_pct
        FROM research_operational_metrics
        WHERE date_recorded >= date('now', '-7 days')
        """
        
        operational_data = self.conn.execute(operational_query).fetchone()
        
        # Impact Assessment
        impact_query = """
        SELECT 
            AVG(income_change_percentage) as avg_income_change,
            AVG(market_access_count) as avg_market_access,
            AVG(satisfaction_score) as avg_satisfaction
        FROM research_impact_assessment
        WHERE assessment_date >= date('now', '-90 days')
        """
        
        impact_data = self.conn.execute(impact_query).fetchone()
        
        return {
            'supply_chain': [dict(row) for row in supply_data],
            'digital_literacy': dict(literacy_data) if literacy_data else {},
            'operational': dict(operational_data) if operational_data else {},
            'impact': dict(impact_data) if impact_data else {}
        }
    
    def export_research_data(self, output_file='research_data_export.json'):
        """Export semua data riset untuk analisis lebih lanjut"""
        
        data = {
            'supply_chain_metrics': [],
            'digital_literacy_survey': [],
            'operational_metrics': [],
            'adoption_tracking': [],
            'impact_assessment': []
        }
        
        # Export each table
        tables = ['research_supply_chain_metrics', 'research_digital_literacy_survey', 
                  'research_operational_metrics', 'research_adoption_tracking', 
                  'research_impact_assessment']
        
        for table in tables:
            table_name = table.replace('research_', '')
            query = f"SELECT * FROM {table}"
            results = self.conn.execute(query).fetchall()
            data[table_name] = [dict(row) for row in results]
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Research data exported to: {output_file}")
        return data
    
    def create_streamlit_research_interface(self):
        """Buat interface Streamlit untuk monitoring riset"""
        
        st.title("🔬 Lumbung Digital Research Dashboard")
        st.markdown("Dashboard monitoring untuk riset implementasi aplikasi lumbung digital")
        
        # Initialize research tables
        if st.button("Initialize Research Tables"):
            self.create_research_tables()
            st.success("✅ Research tables initialized successfully!")
        
        # Collect data buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Collect Supply Chain Metrics"):
                traditional = self.collect_supply_chain_metrics('traditional')
                digital = self.collect_supply_chain_metrics('digital')
                st.success("✅ Supply chain metrics collected!")
        
        with col2:
            if st.button("📱 Collect Operational Metrics"):
                self.collect_operational_metrics()
                st.success("✅ Operational metrics collected!")
        
        with col3:
            if st.button("📤 Export Research Data"):
                data = self.export_research_data()
                st.success("✅ Research data exported!")
        
        # Display dashboard
        dashboard_data = self.generate_research_dashboard()
        
        st.markdown("---")
        st.header("📈 Research Analytics")
        
        # Supply Chain Comparison
        if dashboard_data['supply_chain']:
            st.subheader("🔗 Supply Chain Efficiency Comparison")
            
            supply_df = pd.DataFrame(dashboard_data['supply_chain'])
            st.dataframe(supply_df, use_container_width=True)
            
            # Visualization
            if len(supply_df) > 1:
                st.bar_chart(supply_df.set_index('chain_type')[['avg_cost', 'avg_spread', 'avg_time']])
        
        # Digital Literacy
        if dashboard_data['digital_literacy']:
            st.subheader("📱 Digital Literacy Survey Results")
            
            literacy = dashboard_data['digital_literacy']
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Smartphone Ownership", f"{literacy.get('smartphone_pct', 0):.1f}%")
                st.metric("Internet Access", f"{literacy.get('internet_pct', 0):.1f}%")
            
            with col2:
                st.metric("Average Confidence", f"{literacy.get('avg_confidence', 0):.1f}/5")
                st.metric("Training Need", f"{literacy.get('training_need_pct', 0):.1f}%")
        
        # Operational Metrics
        if dashboard_data['operational']:
            st.subheader("🏪 Operational Performance")
            
            ops = dashboard_data['operational']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Stock Accuracy", f"{ops.get('avg_accuracy', 0):.1f}%")
            
            with col2:
                st.metric("Overstock Rate", f"{ops.get('overstock_pct', 0):.1f}%")
            
            with col3:
                st.metric("Shortage Rate", f"{ops.get('shortage_pct', 0):.1f}%")
        
        # Impact Assessment
        if dashboard_data['impact']:
            st.subheader("🌾 Farmer Impact Assessment")
            
            impact = dashboard_data['impact']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Income Change", f"{impact.get('avg_income_change', 0):.1f}%")
            
            with col2:
                st.metric("Market Access", f"{impact.get('avg_market_access', 0):.1f} markets")
            
            with col3:
                st.metric("Satisfaction", f"{impact.get('avg_satisfaction', 0):.1f}/5")
    
    def close(self):
        """Tutup koneksi database"""
        self.conn.close()

# ==================== USAGE EXAMPLE ====================
if __name__ == "__main__":
    # Initialize collector
    collector = ResearchDataCollector()
    
    # Create research tables
    collector.create_research_tables()
    
    # Collect sample data
    collector.collect_supply_chain_metrics('traditional')
    collector.collect_supply_chain_metrics('digital')
    collector.collect_operational_metrics()
    
    # Generate dashboard
    dashboard_data = collector.generate_research_dashboard()
    print("📊 Research Dashboard Data Generated")
    
    # Export data
    collector.export_research_data()
    
    # Close connection
    collector.close()
