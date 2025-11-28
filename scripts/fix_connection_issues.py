#!/usr/bin/env python3
"""
Script untuk otomatisasi perbaikan common connection issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import urllib.parse
from config import MONGODB_SETTINGS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_and_fix_env_file():
    """Validate dan fix .env file configuration"""
    print("🔧 Validating .env file configuration...")
    
    env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    
    if not os.path.exists(env_file_path):
        print("❌ .env file not found!")
        return False
    
    # Read current .env content
    with open(env_file_path, 'r') as f:
        content = f.read()
    
    issues_found = []
    fixes_applied = []
    
    # Check 1: Password encoding needed for special characters
    password = MONGODB_SETTINGS.get('password', '')
    if password and any(char in password for char in ['@', ':', '/', '?', '#', '[', ']', '%']):
        issues_found.append("Password contains special characters that need URL encoding")
        print("⚠️  Password contains special characters")
        
        # Check if already properly encoded
        if password != urllib.parse.quote_plus(password):
            print("🔧 Applying URL encoding to password...")
            encoded_password = urllib.parse.quote_plus(password)
            
            # Update .env file with encoded password
            content = re.sub(
                r'MONGODB_PASSWORD=(.*)',
                f'MONGODB_PASSWORD={encoded_password}',
                content
            )
            fixes_applied.append("Password URL encoded")
    
    # Check 2: Missing appName parameter
    if 'mongodb.net' in MONGODB_SETTINGS.get('host', ''):
        if 'appName' not in content:
            print("🔧 Adding appName parameter for MongoDB Atlas...")
            # This would be handled in the connection string builder
            fixes_applied.append("appName parameter will be added in connection string")
    
    # Check 3: Database name format
    database = MONGODB_SETTINGS.get('database', '')
    if database and database.startswith('_'):
        issues_found.append("Database name starts with underscore")
        print("⚠️  Database name starts with underscore (may cause issues)")
    
    # Write fixes back to .env if any fixes applied
    if fixes_applied:
        with open(env_file_path, 'w') as f:
            f.write(content)
        print(f"✅ Applied {len(fixes_applied)} fixes:")
        for fix in fixes_applied:
            print(f"   - {fix}")
    else:
        print("✅ No fixes needed for .env file")
    
    return len(issues_found) == 0

def check_dns_requirements():
    """Check DNS requirements for MongoDB Atlas"""
    print("\n🌍 Checking DNS requirements...")
    
    if 'mongodb.net' not in MONGODB_SETTINGS.get('host', ''):
        print("ℹ️  Skipping DNS check (not using MongoDB Atlas)")
        return True
    
    try:
        import dns.resolver
        
        host = MONGODB_SETTINGS['host']
        
        # Test SRV record
        srv_record = f"_mongodb._tcp.{host}"
        try:
            answers = dns.resolver.resolve(srv_record, 'SRV')
            print(f"✅ SRV record found: {len(answers)} entries")
        except Exception as e:
            print(f"❌ SRV record error: {e}")
            return False
        
        return True
        
    except ImportError:
        print("⚠️  dnspython not installed, skipping DNS checks")
        print("💡 Install with: pip install dnspython>=2.4.0")
        return True

def validate_connection_string_format():
    """Validate connection string format"""
    print("\n🔗 Validating connection string format...")
    
    host = MONGODB_SETTINGS.get('host', '')
    username = MONGODB_SETTINGS.get('username', '')
    password = MONGODB_SETTINGS.get('password', '')
    database = MONGODB_SETTINGS.get('database', '')
    
    issues = []
    
    # Check required fields for cloud
    if 'mongodb.net' in host:
        if not username:
            issues.append("Username required for MongoDB Atlas")
        if not password:
            issues.append("Password required for MongoDB Atlas")
        if not database:
            issues.append("Database name required for MongoDB Atlas")
    
    # Check host format
    if 'mongodb.net' in host and not host.endswith('.mongodb.net'):
        issues.append("Host format should end with .mongodb.net")
    
    if issues:
        print("❌ Connection string issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Connection string format is valid")
        return True

def generate_connection_string():
    """Generate and display the actual connection string"""
    print("\n🔗 Generating connection string...")
    
    try:
        if MONGODB_SETTINGS['username'] and MONGODB_SETTINGS['password']:
            if 'mongodb.net' in MONGODB_SETTINGS['host']:
                # MongoDB Atlas connection string with proper encoding
                encoded_password = urllib.parse.quote_plus(MONGODB_SETTINGS['password'])
                connection_string = f"mongodb+srv://{MONGODB_SETTINGS['username']}:{encoded_password}@{MONGODB_SETTINGS['host']}/{MONGODB_SETTINGS['database']}?retryWrites=true&w=majority&appName=Cluster0"
                print("✅ MongoDB Atlas connection string generated")
            else:
                # Local MongoDB with authentication
                connection_string = f"mongodb://{MONGODB_SETTINGS['username']}:{MONGODB_SETTINGS['password']}@{MONGODB_SETTINGS['host']}:{MONGODB_SETTINGS['port']}/{MONGODB_SETTINGS['auth_source']}"
                print("✅ Local MongoDB connection string generated")
        else:
            # Local MongoDB without authentication
            connection_string = f"mongodb://{MONGODB_SETTINGS['host']}:{MONGODB_SETTINGS['port']}"
            print("✅ Local MongoDB connection string generated (no auth)")
        
        # Display masked version for security
        masked_string = connection_string.replace(MONGODB_SETTINGS['password'], '*' * len(MONGODB_SETTINGS['password'])) if MONGODB_SETTINGS['password'] else connection_string
        print(f"🔗 Connection String: {masked_string}")
        
        return connection_string
        
    except Exception as e:
        print(f"❌ Error generating connection string: {e}")
        return None

def test_basic_connectivity():
    """Test basic connectivity without full MongoDB connection"""
    print("\n🌐 Testing basic connectivity...")
    
    host = MONGODB_SETTINGS.get('host', '')
    
    if 'mongodb.net' in host:
        try:
            import socket
            
            print(f"🔍 Testing TCP connection to {host}:27017...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            result = sock.connect_ex((host, 27017))
            sock.close()
            
            if result == 0:
                print("✅ TCP connection successful")
                return True
            else:
                print(f"❌ TCP connection failed (error code: {result})")
                print("💡 Possible causes:")
                print("   - IP not whitelisted in MongoDB Atlas")
                print("   - Firewall blocking connection")
                print("   - Network connectivity issues")
                return False
                
        except Exception as e:
            print(f"❌ Connectivity test error: {e}")
            return False
    else:
        print("ℹ️  Skipping connectivity test (not using MongoDB Atlas)")
        return True

def main():
    """Main fix function"""
    print("🔧 MONGODB CONNECTION FIXER")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all checks and fixes
    checks = [
        ("Environment Configuration", validate_and_fix_env_file),
        ("DNS Requirements", check_dns_requirements),
        ("Connection String Format", validate_connection_string_format),
        ("Basic Connectivity", test_basic_connectivity),
    ]
    
    results = {}
    for check_name, check_func in checks:
        print(f"\n🧪 {check_name}")
        print("-" * 30)
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ Check failed: {e}")
            results[check_name] = False
    
    # Generate connection string
    print(f"\n🔗 CONNECTION STRING")
    print("-" * 30)
    connection_string = generate_connection_string()
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
    
    print(f"\n📈 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Connection should work properly.")
        if connection_string:
            print("\n🚀 You can now test the connection:")
            print("   python scripts/test_cloud_connection.py")
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please fix the issues above.")
        print("\n🔧 Recommended actions:")
        
        if not results.get("Environment Configuration", True):
            print("   - Fix .env file configuration")
        
        if not results.get("DNS Requirements", True):
            print("   - Install dnspython: pip install dnspython>=2.4.0")
            print("   - Check DNS resolution")
        
        if not results.get("Connection String Format", True):
            print("   - Fix connection string format")
        
        if not results.get("Basic Connectivity", True):
            print("   - Whitelist IP in MongoDB Atlas")
            print("   - Check firewall settings")
    
    return passed == total

if __name__ == "__main__":
    main()
