
import os
import json

# Final verification
print("="*70)
print("🔍 FINAL VERIFICATION - ALL FILES READY")
print("="*70)

# Check all critical files
files = {
    "main.py": "Main Flask application",
    "requirements.txt": "Python dependencies",
    "README.md": "Documentation",
    "DEPLOY.md": "Deployment guide",
    "COMMANDS.md": "Command reference",
    "START_HERE.txt": "Quick start guide",
    ".gitignore": "Git configuration",
    "config/game_config.json": "Game content (EDITABLE)",
    "config/admin_config.json": "Admin settings (EDIT THIS!)",
    "core/database.py": "SQLite database",
    "core/messaging.py": "WhatsApp API",
    "core/game_engine.py": "Battle system",
    "core/trading_system.py": "Player trading",
    "core/boss_system.py": "World bosses",
    "core/admin_system.py": "Admin commands",
    "core/__init__.py": "Core package",
    "utils/helpers.py": "Utilities",
    "utils/__init__.py": "Utils package"
}

all_ok = True
total_size = 0

for file, desc in files.items():
    if os.path.exists(file):
        size = os.path.getsize(file)
        total_size += size
        status = "✅"
    else:
        status = "❌"
        all_ok = False
    
    print(f"{status} {file:<35} ({size:>6,} bytes) - {desc}")

print("="*70)
print(f"📦 Total package size: {total_size:,} bytes ({total_size/1024:.1f} KB)")

# Check admin config
print("\n🔐 Checking admin configuration...")
try:
    with open('config/admin_config.json', 'r') as f:
        admin = json.load(f)
    
    phone = admin.get('admin_phone', 'NOT SET')
    api_key = admin.get('api_key', 'NOT SET')
    
    print(f"   Admin phone: {phone}")
    print(f"   API key: {api_key[:4]}****{api_key[-4:] if len(api_key) > 8 else ''}")
    
    if phone == "201061479235":
        print("   ✅ Phone configured correctly")
    else:
        print("   ⚠️  Phone not set to your number")
        
    if api_key == "2008805":
        print("   ✅ API key configured")
    else:
        print("   ⚠️  API key not set")
        
except Exception as e:
    print(f"   ❌ Error reading admin config: {e}")

print("="*70)

if all_ok:
    print("🎉 SUCCESS! All files are ready for deployment!")
    print("\n🚀 NEXT STEP:")
    print("   1. Read START_HERE.txt")
    print("   2. Push all files to GitHub")
    print("   3. Deploy to Railway")
    print("   4. Start playing! 🎮")
else:
    print("⚠️  Some files are missing!")

print("="*70)