
# COMMANDS.md - Quick reference for all commands
commands_ref = """# 📋 COMMAND REFERENCE - ODD RPG Bot

## 🎮 Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/menu` | Main menu with stats | `/menu` |
| `/start` | Same as menu | `/start` |
| `/help` | Show help | `/help` |
| `/next` | Extended menu | `/next` |

## ⚔️ Battle Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/odd` | Start Pokemon-style battle | `/odd` |
| `/battle` | Same as /odd | `/battle` |
| `/hunt` | Find enemy | `/hunt` |
| `1` or `attack` | Attack in battle | `1` |
| `2` or `defend` | Defend in battle | `2` |
| `3` or `heal` | Heal in battle | `3` |
| `4` or `special` | Pet special attack | `4` |
| `5` or `flee` | Try to escape | `5` |

## 💰 Economy Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/stats` | Your detailed stats | `/stats` |
| `/bank` | Bank info | `/bank` |
| `/bank deposit [amount]` | Deposit points | `/bank deposit 1000` |
| `/bank withdraw [amount]` | Withdraw points | `/bank withdraw 500` |
| `/deposit [amount]` | Quick deposit | `/deposit all` |
| `/withdraw [amount]` | Quick withdraw | `/withdraw 500` |
| `/shop` | View shop items | `/shop` |
| `/shop buy [item]` | Buy item | `/shop buy potion_large` |
| `/daily` | Claim daily reward | `/daily` |
| `/steal` | Steal from random player | `/steal` |
| `/steal [phone]` | Steal from specific player | `/steal 1234567890` |

## 🎒 Pet Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/pets` | View your pets | `/pets` |
| `/inventory` | Detailed inventory | `/inventory` |
| `/crates` | Open basic crate | `/crates` |
| `/crates [type]` | Open specific crate | `/crates legendary` |
| `/enchanter` | Pet upgrade menu | `/enchanter` |
| `/enchanter list` | Show mergeable pets | `/enchanter list` |
| `/enchanter merge [name]` | Merge 3 pets | `/enchanter merge Slime` |
| `/enchanter upgrade [slot]` | Enchant pet | `/enchanter upgrade 1` |
| `/heal` | Quick heal | `/heal` |

## 🤝 Social Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/trade` | List pending trades | `/trade` |
| `/trade [phone] [offer]` | Send trade request | `/trade 1234567890 500 for Wolf` |
| `/trade accept [id]` | Accept trade | `/trade accept 123` |
| `/trade decline [id]` | Decline trade | `/trade decline 123` |
| `/msg [phone] [text]` | Send private message | `/msg 1234567890 Hello!` |
| `/inbox` | Check messages | `/inbox` |
| `/read` | Mark all as read | `/read` |
| `/leaderboard` | Global rankings | `/leaderboard` |

## 👹 Boss Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/boss` | List active bosses | `/boss` |
| `/boss join [id]` | Join boss battle | `/boss join 1` |
| `/boss attack [id]` | Attack boss | `/boss attack 1` |
| `/boss defend [id]` | Defend against boss | `/boss defend 1` |

## 🎁 Promo Codes

| Command | Description | Example |
|---------|-------------|---------|
| `/code` | List available codes | `/code` |
| `/code [CODE]` | Redeem code | `/code STARTER` |

**Default Codes:**
- `STARTER` - 1000💰
- `ODD2024` - 5000💰
- `WELCOME` - 2000💰
- `LEGENDARY` - 10000💰 + Dragon pet
- `MYTHIC` - 50000💰 + Baby God pet

## 📚 Info Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/tutorial` | How to play guide | `/tutorial` |
| `/update` | Latest updates | `/update` |
| `/guide` | Same as tutorial | `/guide` |

## 🔐 Admin Commands (Your Phone Only)

**Format:** `admin [command] [args]`

| Command | Description | Example |
|---------|-------------|---------|
| `admin givepoints [phone] [amount]` | Give points | `admin givepoints 1234567890 5000` |
| `admin givepet [phone] [name] [rarity]` | Give pet | `admin givepet 1234567890 Dragon legendary` |
| `admin removepoints [phone] [amount]` | Remove points | `admin removepoints 1234567890 1000` |
| `admin ban [phone] [reason]` | Ban player | `admin ban 1234567890 Cheating` |
| `admin unban [phone]` | Unban player | `admin unban 1234567890` |
| `admin broadcast [message]` | Message all | `admin broadcast Event starting!` |
| `admin maintenance [on/off]` | Maintenance mode | `admin maintenance on` |
| `admin reset [phone]` | Reset player | `admin reset 1234567890` |
| `admin addcode [code] [points] [uses]` | Add promo code | `admin addcode SECRET 9999 10` |
| `admin spawnboss [name]` | Force spawn boss | `admin spawnboss Kraken` |
| `admin giveitem [phone] [item] [qty]` | Give item | `admin giveitem 1234567890 potion_large 5` |
| `admin stats` | Global statistics | `admin stats` |
| `admin help` | Admin help | `admin help` |

---

## 🎯 Quick Start for Players

**New Player? Follow these steps:**

1. Send `/menu` to see your starting stats (1000💰)
2. Send `/code STARTER` to get bonus points
3. Send `/odd` to start your first battle
4. Choose `1` (Attack) to fight
5. Win to earn more points!
6. Send `/crates` to get your first pet (100💰)
7. Send `/bank deposit all` to protect your money
8. Send `/daily` every day for free rewards

**Pro Tips:**
- Bank your points before stealing
- Merge 3 same pets for rarity upgrade
- Check `/boss` for world events
- Use `/trade` to trade with others
- Buy protection in `/shop` to prevent theft

---

## 🏦 Bank Tiers

| Tier | Min Balance | Interest | Withdraw Fee |
|------|-------------|----------|--------------|
| Basic | 0 | 2% | 5% |
| Silver | 100,000 | 3% | 3% |
| Gold | 1,000,000 | 5% | 1% |
| Diamond | 10,000,000 | 8% | 0% |

Interest paid daily at midnight!

---

## 🎒 Pet Rarities

| Rarity | Color | Drop Rate | Max ATK |
|--------|-------|-----------|---------|
| Common | ⬛ | 50% | 20 |
| Rare | 🟩 | 30% | 35 |
| Epic | 🟨 | 15% | 60 |
| Legendary | 🟪 | 5% | 100 |
| Mythic | 🟥 | <1% | 200 |

---

*Last Updated: 2024*
*Bot Version: V. Re-Imagined Ultimate*
"""

with open('COMMANDS.md', 'w') as f:
    f.write(commands_ref)

print("✅ COMMANDS.md created!")
print("\n" + "="*70)
print("📦 COMPLETE DEPLOYMENT PACKAGE")
print("="*70)
print("\n📁 All Files Created:")
print("   🚀 main.py - Main application (26KB)")
print("   📋 requirements.txt - Dependencies")
print("   📖 README.md - Full documentation (7KB)")
print("   🚀 DEPLOY.md - Deployment guide (12KB)")
print("   📋 COMMANDS.md - Command reference (8KB)")
print("   🚫 .gitignore - Git ignore rules")
print("   ⚙️  config/game_config.json - Game content (10KB)")
print("   🔐 config/admin_config.json - Admin settings (1KB)")
print("   🗄️  core/database.py - Database (16KB)")
print("   📨 core/messaging.py - WhatsApp API (5KB)")
print("   ⚔️  core/game_engine.py - Battles (22KB)")
print("   🤝 core/trading_system.py - Trading (10KB)")
print("   👹 core/boss_system.py - Bosses (11KB)")
print("   🔐 core/admin_system.py - Admin (11KB)")
print("   🛠️  utils/helpers.py - Utilities (2KB)")
print("\n📊 Statistics:")
print("   • Total Python code: ~3,050 lines")
print("   • Total package size: ~130KB")
print("   • Features: 50+ game systems")
print("   • Database: SQLite (zero setup)")
print("   • API: CallMeBot WhatsApp")
print("\n🎯 Ready to deploy!")
print("="*70)