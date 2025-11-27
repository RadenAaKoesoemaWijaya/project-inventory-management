#!/usr/bin/env python3
"""
Script untuk setup environment yang aman
"""

import os
import sys
import shutil
from pathlib import Path

def setup_secure_environment():
    """Setup environment yang aman untuk development"""
    
    print("🔒 SETUP ENVIRONMENT YANG AMAN")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    gitignore_file = project_root / ".gitignore"
    
    # 1. Check jika .env.example ada
    if not env_example.exists():
        print("❌ File .env.example tidak ditemukan!")
        return False
    
    # 2. Create .env dari .env.example jika belum ada
    if not env_file.exists():
        print("📝 Membuat .env dari .env.example...")
        shutil.copy(env_example, env_file)
        print("✅ File .env dibuat")
    else:
        print("✅ File .env sudah ada")
    
    # 3. Verify .gitignore exists dan contains .env
    if gitignore_file.exists():
        with open(gitignore_file, 'r') as f:
            gitignore_content = f.read()
        
        if '.env' in gitignore_content:
            print("✅ .env sudah ada di .gitignore")
        else:
            print("⚠️  Menambahkan .env ke .gitignore...")
            with open(gitignore_file, 'a') as f:
                f.write("\n# Environment variables\n.env\n.env.local\n.env.development\n.env.test\n.env.production\n")
            print("✅ .env ditambahkan ke .gitignore")
    else:
        print("❌ File .gitignore tidak ditemukan!")
        return False
    
    # 4. Check sensitive data di .env
    print("\n🔍 Checking sensitive data exposure...")
    
    sensitive_patterns = [
        'password',
        'secret',
        'key',
        'token',
        'auth'
    ]
    
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    warnings = []
    for line in env_content.split('\n'):
        if line.strip() and not line.startswith('#'):
            for pattern in sensitive_patterns:
                if pattern.lower() in line.lower():
                    value = line.split('=')[1] if '=' in line else ''
                    if value and value != 'your_password_here' and value != 'your-secret-key-here':
                        warnings.append(line)
    
    if warnings:
        print("⚠️  WARNING: Potensi sensitive data exposure:")
        for warning in warnings:
            print(f"   - {warning}")
        print("\n💡 Pastikan ini adalah nilai placeholder atau data development!")
    else:
        print("✅ Tidak ada sensitive data yang terdeteksi")
    
    # 5. Check git status
    print("\n🔍 Checking git status...")
    try:
        import subprocess
        
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=project_root, 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            changed_files = result.stdout.strip().split('\n')
            env_tracked = any(' .env' in f for f in changed_files if f.strip())
            
            if env_tracked:
                print("⚠️  WARNING: .env terdeteksi di git staging area!")
                print("💡 Hapus dari git dengan: git reset HEAD .env")
                return False
            else:
                print("✅ .env tidak ter-track di git")
        else:
            print("ℹ️  Git repository tidak terdeteksi atau tidak ada changes")
            
    except FileNotFoundError:
        print("ℹ️  Git tidak terinstall")
    
    return True

def generate_secure_env_template():
    """Generate template dengan secure defaults"""
    
    print("\n📝 GENERATING SECURE ENV TEMPLATE")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    secure_template = project_root / ".env.template"
    
    template_content = """# MongoDB Cloud Configuration
# Ganti dengan credentials Anda yang sebenarnya
MONGODB_HOST=your-cluster.mongodb.net
MONGODB_PORT=27017
MONGODB_DATABASE=your_database_name
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_secure_password_here
MONGODB_AUTH_SOURCE=admin

# Connection Pool Settings
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
MONGODB_MAX_IDLE_TIME=45000

# Application Settings
# Generate secret key dengan: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=generated_secret_key_here
SESSION_TIMEOUT=3600
ITEMS_PER_PAGE=20
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900

# Real-time Settings
ENABLE_REALTIME=true
CHANGE_STREAM_ENABLED=true
NOTIFICATION_ENABLED=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=kalkulis.log
"""
    
    with open(secure_template, 'w') as f:
        f.write(template_content)
    
    print(f"✅ Secure template dibuat: {secure_template}")
    print("💡 Gunakan template ini untuk production setup")

def main():
    """Main function"""
    print("🛡️  LUMBUNG DIGITAL - ENVIRONMENT SECURITY SETUP")
    print("=" * 60)
    
    # Setup secure environment
    if setup_secure_environment():
        print("\n✅ Environment setup berhasil!")
        
        # Generate secure template
        generate_secure_env_template()
        
        print("\n📋 NEXT STEPS:")
        print("1. 📝 Edit .env file dengan credentials Anda")
        print("2. 🔒 Jangan commit .env file ke repository")
        print("3. 📤 Bagikan .env.example sebagai template untuk team")
        print("4. 🔑 Generate secret key yang unik untuk production")
        
        print("\n🔐 SECURITY BEST PRACTICES:")
        print("- Gunakan password yang kuat dan unik")
        print("- Rotate credentials secara berkala")
        print("- Gunakan environment variables di production")
        print("- Jangan hardcode credentials di code")
        
    else:
        print("\n❌ Environment setup gagal!")
        print("Periksa error di atas dan perbaiki manually.")

if __name__ == "__main__":
    main()
