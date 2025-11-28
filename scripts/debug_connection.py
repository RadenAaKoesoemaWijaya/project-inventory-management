#!/usr/bin/env python3
"""
Script debugging koneksi MongoDB Cloud - Analisis menyeluruh
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
import logging
from config import MONGODB_SETTINGS
import urllib.parse

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_environment():
    """Analisis konfigurasi environment"""
    print("=" * 60)
    print("🔍 ANALISIS KONFIGURASI ENVIRONMENT")
    print("=" * 60)
    
    print(f"📋 MONGODB_HOST: {MONGODB_SETTINGS['host']}")
    print(f"📋 MONGODB_PORT: {MONGODB_SETTINGS['port']}")
    print(f"📋 MONGODB_DATABASE: {MONGODB_SETTINGS['database']}")
    print(f"📋 MONGODB_USERNAME: {MONGODB_SETTINGS['username']}")
    print(f"📋 MONGODB_PASSWORD: {'*' * len(MONGODB_SETTINGS['password']) if MONGODB_SETTINGS['password'] else 'EMPTY'}")
    print(f"📋 MONGODB_AUTH_SOURCE: {MONGODB_SETTINGS['auth_source']}")
    
    # Detect connection type
    is_cloud = 'mongodb.net' in MONGODB_SETTINGS['host']
    print(f"☁️  Connection Type: {'CLOUD (MongoDB Atlas)' if is_cloud else 'LOCAL'}")
    
    # Validate required fields
    issues = []
    if not MONGODB_SETTINGS['host']:
        issues.append("❌ MONGODB_HOST kosong")
    if not MONGODB_SETTINGS['database']:
        issues.append("❌ MONGODB_DATABASE kosong")
    if is_cloud and not MONGODB_SETTINGS['username']:
        issues.append("❌ MongoDB Cloud memerlukan username")
    if is_cloud and not MONGODB_SETTINGS['password']:
        issues.append("❌ MongoDB Cloud memerlukan password")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ Configuration looks valid!")
    
    return len(issues) == 0

def build_connection_string():
    """Build dan validate connection string"""
    print("\n" + "=" * 60)
    print("🔗 BUILDING CONNECTION STRING")
    print("=" * 60)
    
    try:
        if MONGODB_SETTINGS['username'] and MONGODB_SETTINGS['password']:
            if 'mongodb.net' in MONGODB_SETTINGS['host']:
                # MongoDB Atlas connection string
                # URL encode password untuk special characters
                encoded_password = urllib.parse.quote_plus(MONGODB_SETTINGS['password'])
                connection_string = f"mongodb+srv://{MONGODB_SETTINGS['username']}:{encoded_password}@{MONGODB_SETTINGS['host']}/{MONGODB_SETTINGS['database']}?retryWrites=true&w=majority&appName=Cluster0"
                print("☁️  Using MongoDB Atlas connection string")
            else:
                # Local MongoDB with authentication
                connection_string = f"mongodb://{MONGODB_SETTINGS['username']}:{MONGODB_SETTINGS['password']}@{MONGODB_SETTINGS['host']}:{MONGODB_SETTINGS['port']}/{MONGODB_SETTINGS['auth_source']}"
                print("🏠 Using Local MongoDB connection string")
        else:
            # Local MongoDB without authentication
            connection_string = f"mongodb://{MONGODB_SETTINGS['host']}:{MONGODB_SETTINGS['port']}"
            print("🏠 Using Local MongoDB without authentication")
        
        print(f"🔗 Connection String: {connection_string.replace(MONGODB_SETTINGS['password'], '*' * len(MONGODB_SETTINGS['password'])) if MONGODB_SETTINGS['password'] else connection_string}")
        return connection_string
        
    except Exception as e:
        print(f"❌ Error building connection string: {e}")
        return None

def test_basic_connection():
    """Test koneksi dasar dengan berbagai approaches"""
    print("\n" + "=" * 60)
    print("🔌 TESTING BASIC CONNECTION")
    print("=" * 60)
    
    connection_string = build_connection_string()
    if not connection_string:
        return False
    
    try:
        print("🔄 Attempting connection...")
        
        # Test dengan timeout yang lebih panjang untuk cloud
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=10000,  # 10 detik
            connectTimeoutMS=15000,          # 15 detik
            socketTimeoutMS=15000,          # 15 detik
            retryWrites=True,
            retryReads=True,
            maxPoolSize=1,  # Minimal untuk testing
            minPoolSize=1
        )
        
        print("✅ Client created successfully")
        
        # Test ping
        print("🏓 Testing ping command...")
        result = client.admin.command('ping')
        print(f"✅ Ping successful: {result}")
        
        # Test database access
        print(f"📊 Testing database access: {MONGODB_SETTINGS['database']}")
        db = client[MONGODB_SETTINGS['database']]
        collections = db.list_collection_names()
        print(f"✅ Database accessible, {len(collections)} collections found")
        
        # Close connection
        client.close()
        print("✅ Connection closed successfully")
        
        return True
        
    except ServerSelectionTimeoutError as e:
        print(f"❌ Server Selection Timeout: {e}")
        print("💡 Possible causes:")
        print("   - Network connectivity issues")
        print("   - Wrong host or cluster name")
        print("   - IP not whitelisted in MongoDB Atlas")
        print("   - DNS resolution issues")
        return False
        
    except ConnectionFailure as e:
        print(f"❌ Connection Failed: {e}")
        print("💡 Possible causes:")
        print("   - Authentication failed")
        print("   - Invalid credentials")
        print("   - Network firewall blocking")
        return False
        
    except OperationFailure as e:
        print(f"❌ Operation Failed: {e}")
        print("💡 Possible causes:")
        print("   - Insufficient permissions")
        print("   - Database not found")
        print("   - User doesn't have access to database")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {type(e).__name__}: {e}")
        return False

def test_dns_resolution():
    """Test DNS resolution untuk MongoDB Atlas"""
    print("\n" + "=" * 60)
    print("🌍 TESTING DNS RESOLUTION")
    print("=" * 60)
    
    if 'mongodb.net' not in MONGODB_SETTINGS['host']:
        print("ℹ️  Skipping DNS test (not using MongoDB Atlas)")
        return True
    
    try:
        import socket
        import dns.resolver
        
        host = MONGODB_SETTINGS['host']
        print(f"🔍 Resolving: {host}")
        
        # Test basic DNS resolution
        ip = socket.gethostbyname(host)
        print(f"✅ DNS Resolution successful: {host} -> {ip}")
        
        # Test SRV record (required for MongoDB Atlas)
        srv_record = f"_mongodb._tcp.{host}"
        print(f"🔍 Checking SRV record: {srv_record}")
        
        answers = dns.resolver.resolve(srv_record, 'SRV')
        print(f"✅ SRV Record found:")
        for answer in answers:
            print(f"   {answer}")
        
        # Test TXT record
        txt_record = host
        print(f"🔍 Checking TXT record: {txt_record}")
        
        try:
            txt_answers = dns.resolver.resolve(txt_record, 'TXT')
            print(f"✅ TXT Record found:")
            for answer in txt_answers:
                print(f"   {answer}")
        except:
            print("⚠️  No TXT record found (may be optional)")
        
        return True
        
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        print("💡 Possible causes:")
        print("   - No internet connection")
        print("   - DNS server issues")
        print("   - Wrong cluster name")
        return False
        
    except dns.resolver.NXDOMAIN as e:
        print(f"❌ Domain not found: {e}")
        print("💡 Possible causes:")
        print("   - Wrong cluster name")
        print("   - Cluster not active")
        print("   - Typos in connection string")
        return False
        
    except Exception as e:
        print(f"❌ DNS Test Error: {e}")
        return False

def test_network_connectivity():
    """Test network connectivity ke MongoDB Atlas"""
    print("\n" + "=" * 60)
    print("🌐 TESTING NETWORK CONNECTIVITY")
    print("=" * 60)
    
    if 'mongodb.net' not in MONGODB_SETTINGS['host']:
        print("ℹ️  Skipping network test (not using MongoDB Atlas)")
        return True
    
    try:
        import socket
        
        host = MONGODB_SETTINGS['host']
        port = 27017
        
        print(f"🔍 Testing connectivity to {host}:{port}")
        
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 detik timeout
        
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("✅ TCP Connection successful")
            return True
        else:
            print(f"❌ TCP Connection failed (error code: {result})")
            print("💡 Possible causes:")
            print("   - Firewall blocking port 27017")
            print("   - IP not whitelisted in MongoDB Atlas")
            print("   - Network connectivity issues")
            return False
            
    except Exception as e:
        print(f"❌ Network Test Error: {e}")
        return False

def test_mongodb_atlas_specific():
    """Test spesifik untuk MongoDB Atlas"""
    print("\n" + "=" * 60)
    print("☁️  TESTING MONGODB ATLAS SPECIFIC")
    print("=" * 60)
    
    if 'mongodb.net' not in MONGODB_SETTINGS['host']:
        print("ℹ️  Skipping Atlas-specific tests (not using MongoDB Atlas)")
        return True
    
    issues = []
    
    # Check password encoding
    password = MONGODB_SETTINGS['password']
    if password and any(char in password for char in ['@', ':', '/', '?', '#', '[', ']']):
        print("⚠️  Password contains special characters that need URL encoding")
        issues.append("Password needs URL encoding")
    else:
        print("✅ Password format looks good")
    
    # Check database name
    database = MONGODB_SETTINGS['database']
    if database and database.startswith('_'):
        print("⚠️  Database name starts with underscore (may cause issues)")
        issues.append("Database name format")
    else:
        print("✅ Database name format looks good")
    
    # Check connection string format
    if 'appName' not in build_connection_string():
        print("⚠️  No appName parameter in connection string")
        issues.append("Missing appName parameter")
    else:
        print("✅ Connection string includes appName")
    
    if issues:
        print(f"\n⚠️  Atlas-specific issues found: {len(issues)}")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("\n✅ Atlas configuration looks good!")
    
    return len(issues) == 0

def generate_recommendations():
    """Generate rekomendasi perbaikan"""
    print("\n" + "=" * 60)
    print("💡 REKOMENDASI PERBAIKAN")
    print("=" * 60)
    
    recommendations = []
    
    # Analyze configuration
    if not MONGODB_SETTINGS['username'] and 'mongodb.net' in MONGODB_SETTINGS['host']:
        recommendations.append("🔧 Tambahkan username di .env file")
    
    if not MONGODB_SETTINGS['password'] and 'mongodb.net' in MONGODB_SETTINGS['host']:
        recommendations.append("🔧 Tambahkan password di .env file")
    
    # Test results will be added by calling functions
    print("📋 Rekomendasi berdasarkan analisis:")
    
    if not analyze_environment():
        recommendations.append("🔧 Perbaiki konfigurasi environment variables")
    
    if not test_dns_resolution():
        recommendations.append("🌐 Periksa koneksi internet dan DNS settings")
        recommendations.append("🔧 Verifikasi cluster name di MongoDB Atlas")
    
    if not test_network_connectivity():
        recommendations.append("🔥 Whitelist IP address di MongoDB Atlas Network Access")
        recommendations.append("🔧 Periksa firewall settings")
    
    if not test_mongodb_atlas_specific():
        recommendations.append("🔐 URL encode password jika mengandung special characters")
        recommendations.append("🔧 Tambahkan appName parameter di connection string")
    
    if not recommendations:
        print("✅ Tidak ada rekomendasi - konfigurasi sudah optimal!")
    else:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    
    return recommendations

def main():
    """Main debugging function"""
    print("🚀 MONGODB CONNECTION DEBUGGER")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    tests = [
        ("Environment Configuration", analyze_environment),
        ("DNS Resolution", test_dns_resolution),
        ("Network Connectivity", test_network_connectivity),
        ("MongoDB Atlas Specific", test_mongodb_atlas_specific),
        ("Basic Connection", test_basic_connection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    # Generate recommendations
    recommendations = generate_recommendations()
    
    if passed == total:
        print("\n🎉 Semua tests passed! Koneksi MongoDB seharusnya berhasil.")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Ikuti rekomendasi di atas.")
    
    return passed == total

if __name__ == "__main__":
    from datetime import datetime
    main()
