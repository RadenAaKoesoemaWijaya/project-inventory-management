# 🔒 Security Guidelines - Lumbung Digital

## 📋 Overview

Dokumen ini berisi panduan keamanan untuk melindungi data sensitif dan credentials dalam aplikasi Lumbung Digital.

## 🛡️ Environment Variables Protection

### ✅ What's Protected
- **MongoDB Credentials**: Username, password, host
- **Application Secrets**: Secret keys, session tokens
- **Database Configuration**: Connection strings, auth sources
- **API Keys**: External service credentials

### 🔧 Implementation

#### 1. Git Protection
```bash
# .env files di-ignore
.env
.env.local
.env.development
.env.test
.env.production

# Security files
*.pem
*.key
*.crt
secrets/
credentials/
```

#### 2. Template System
- **`.env.example`**: Template untuk development
- **`.env.template`**: Template untuk production
- **`.env`**: Actual credentials (never committed)

#### 3. Access Control
```bash
# File permissions untuk .env
chmod 600 .env  # Only owner can read/write
chmod 644 .env.example  # Everyone can read
```

## 🔐 Best Practices

### Development Environment
```bash
# 1. Setup dari template
cp .env.example .env

# 2. Edit dengan credentials Anda
nano .env

# 3. Verify protection
git status  # .env should NOT appear
```

### Production Environment
```bash
# 1. Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# 2. Use environment variables
export MONGODB_PASSWORD="secure_password_here"
export SECRET_KEY="generated_secret_key_here"

# 3. Or use secrets management service
# AWS Secrets Manager, Azure Key Vault, etc.
```

## 🚨 Security Warnings

### ❌ NEVER DO This
```bash
# Hardcode credentials di code
connection_string = "mongodb://user:password@host/db"

# Commit .env file
git add .env  # DANGEROUS!

# Share credentials via chat/email
# Gunakan secure channels saja
```

### ✅ ALWAYS DO This
```bash
# Use environment variables
MONGODB_PASSWORD=${MONGODB_PASSWORD}

# Use template for team
cp .env.example .env

# Generate unique secrets
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

## 🔍 Security Checklist

### Pre-Commit Checklist
- [ ] `.env` tidak ada di git staging
- [ ] `.gitignore` contains `.env`
- [ ] Password tidak hardcoded di code
- [ ] Secret key unik untuk environment
- [ ] File permissions set correctly

### Production Checklist
- [ ] Environment variables set di server
- [ ] Secrets management configured
- [ ] Access logs enabled
- [ ] Regular credential rotation
- [ ] Backup encryption enabled

## 🛠️ Tools & Scripts

### Security Setup Script
```bash
# Run security setup
python scripts/secure_env_setup.py
```

### Environment Validation
```bash
# Check security compliance
python scripts/validate_env_security.py
```

### Secret Generation
```bash
# Generate secure secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

## 🔄 Environment Management

### Development Flow
1. **Clone Repository**
   ```bash
   git clone <repo>
   cd project-inventory-management
   ```

2. **Setup Environment**
   ```bash
   python scripts/secure_env_setup.py
   cp .env.example .env
   # Edit .env dengan credentials Anda
   ```

3. **Verify Security**
   ```bash
   git status  # .env should NOT be tracked
   ```

### Team Collaboration
1. **Share `.env.example`** - Template untuk team
2. **Never share `.env`** - Individual credentials
3. **Document setup** - Use README.md
4. **Regular audits** - Check for exposed secrets

## 🚀 Production Deployment

### Environment Variables
```bash
# Server environment
export MONGODB_HOST="cluster0.xxxxx.mongodb.net"
export MONGODB_USERNAME="production_user"
export MONGODB_PASSWORD="secure_production_password"
export SECRET_KEY="generated_production_secret"
```

### Docker Environment
```dockerfile
# Dockerfile
FROM python:3.9
ENV MONGODB_HOST=${MONGODB_HOST}
ENV MONGODB_PASSWORD=${MONGODB_PASSWORD}
ENV SECRET_KEY=${SECRET_KEY}
```

### Cloud Services
- **AWS**: Secrets Manager, Parameter Store
- **Azure**: Key Vault, Environment Variables
- **GCP**: Secret Manager, Cloud Functions
- **Heroku**: Config Vars, Heroku Redis

## 🔒 Incident Response

### If Credentials Exposed
1. **Immediate Action**
   ```bash
   # Rotate semua exposed credentials
   # Update database passwords
   # Regenerate secret keys
   ```

2. **Audit Trail**
   ```bash
   # Check git history
   git log --all --full-history -- **/.env
   
   # Check for hardcoded secrets
   grep -r "password\|secret\|key" --include="*.py" .
   ```

3. **Prevention**
   ```bash
   # Add pre-commit hooks
   # Enable branch protection
   # Setup secret scanning
   ```

## 📞 Security Contacts

### For Security Issues
- **Development Team**: [team-contact@example.com]
- **Security Team**: [security@example.com]
- **Incident Response**: [incident@example.com]

### Resources
- [OWASP Security Guidelines](https://owasp.org/)
- [Git Security Best Practices](https://github.com/github/securitylab)
- [MongoDB Security](https://docs.mongodb.com/manual/security/)

---

🔐 **Remember: Security is everyone's responsibility!**

*Keep credentials secret, stay secure, and protect user data.*
