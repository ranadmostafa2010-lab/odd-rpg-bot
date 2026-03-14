# odd-rpg-bot


# requirements.txt
requirements = """Flask==2.3.3
requests==2.31.0
"""

with open('requirements.txt', 'w') as f:
    f.write(requirements)

# README.md
readme = """# 🎮 ODD RPG WhatsApp Bot

**V. Re-Imagined Ultimate Edition**

A comprehensive, feature-rich RPG bot for WhatsApp powered by CallMeBot API and Flask.

## ✨ Features

### Core Gameplay
- ⚔️ **Pokemon-style Battle System** - Choose Attack, Defend, Heal, Special, or Flee
- 🎒 **Pet Collection** - 25+ pets across 5 rarities (Common to Mythic)
- 📦 **Crate System** - 4 crate types with different drop rates
- 🏦 **Bank System** - 4 tiers (Basic → Diamond) with daily interest
- 🥷 **Stealing** - Risk/reward system with protection shields

### Social Features
- 🤝 **Player Trading** - Trade pets and points with other players
- 💬 **Private Messaging** - Inbox system between players
- 👹 **World Bosses** - Cooperative boss battles with multiple players
- 📋 **Leaderboards** - Global rankings by wealth and wins

### Admin Features
- 🔐 **Admin Commands** - Exclusive commands for bot owner
- 📢 **Broadcast** - Message all players instantly
- 🎁 **Giveaway System** - Give points/pets to specific players
- 🚫 **Ban/Unban** - Player moderation
- 🔧 **Maintenance Mode** - Temporary bot shutdown

### Technical
- 🗄️ **SQLite Database** - No external database setup required
- 🔄 **Self-Editing Messages** - Context-aware message updates
- 📊 **Daily Interest** - Automatic bank interest calculation
- 🎁 **Daily Rewards** - Login bonus system
- 🔮 **Enchanting** - Pet merging and upgrading

## 🚀 Quick Start

### 1. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

The bot will start on `http://localhost:5000`

### 2. Railway Deployment

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect Railway:**
   - Go to [Railway.app](https://railway.app)
   - New Project → Deploy from GitHub repo
   - Select your repository

3. **Configure:**
   - Railway will auto-detect Python and install requirements
   - The bot uses SQLite (no database addon needed)

4. **Set Webhook:**
   - Get your Railway URL (e.g., `https://your-bot.up.railway.app`)
   - Configure CallMeBot webhook to point to `https://your-bot.up.railway.app/webhook`

## ⚙️ Configuration

### Admin Settings (`config/admin_config.json`)

```json
{
  "admin_phone": "201061479235",
  "api_key": "2008805",
  "bot_name": "ODD RPG Bot",
  "version": "V. Re-Imagined Ultimate"
}
```

**Important:** Replace with your actual phone and API key from CallMeBot.

### Game Settings (`config/game_config.json`)

This file contains ALL game content and is designed to be easily editable:

#### Adding New Enemies
```json
"enemies": {
  "common": {
    "my_enemy": {
      "name": "My Enemy",
      "emoji": "👾",
      "min_hp": 100,
      "max_hp": 200,
      "min_reward": 500,
      "max_reward": 1000,
      "damage": "20-40",
      "rarity": "common",
      "spawn_chance": 30
    }
  }
}
```

#### Adding New Crates
```json
"crates": {
  "my_crate": {
    "name": "My Crate",
    "emoji": "🎁",
    "cost": 500,
    "description": "Awesome crate!",
    "drops": {
      "common": 20,
      "rare": 30,
      "epic": 30,
      "legendary": 20
    }
  }
}
```

#### Adding New Promo Codes
```json
"promo_codes": {
  "MYCODE": {
    "points": 5000,
    "uses": 1,
    "active": true,
    "pet": {
      "name": "Special Pet",
      "rarity": "legendary",
      "atk": 100
    }
  }
}
```

#### Adding New Shop Items
```json
"shop_items": {
  "my_item": {
    "name": "My Item",
    "emoji": "🎭",
    "price": 1000,
    "description": "Does something cool",
    "effect": "boost"
  }
}
```

## 📱 Player Commands

### Basic Commands
- `/menu` - Main menu with stats
- `/odd` or `/battle` - Start Pokemon-style battle
- `/stats` - Your detailed statistics
- `/tutorial` - How to play guide

### Economy
- `/bank` - Bank info and operations
- `/shop` - Buy items and potions
- `/crates` - Open pet crates
- `/daily` - Claim daily reward
- `/steal` - Attempt to steal from others

### Pets & Items
- `/pets` - View your pet collection
- `/enchanter` - Merge/upgrade pets
- `/heal` - Restore health

### Social
- `/trade` - Trading center
- `/msg [phone] [message]` - Send private message
- `/inbox` - Check messages
- `/leaderboard` - Global rankings
- `/boss` - World boss battles

### Info
- `/update` - Latest update notes
- `/code [CODE]` - Redeem promo code
- `/next` - Extended menu

## 🔐 Admin Commands (Your Phone Only)

All admin commands start with `admin`:

- `admin givepoints [phone] [amount]` - Give points to player
- `admin givepet [phone] [name] [rarity]` - Give specific pet
- `admin removepoints [phone] [amount]` - Remove points
- `admin ban [phone] [reason]` - Ban player
- `admin unban [phone]` - Unban player
- `admin broadcast [message]` - Message all players
- `admin maintenance [on/off]` - Toggle maintenance
- `admin reset [phone]` - Reset player data
- `admin addcode [code] [points] [uses]` - Add promo code
- `admin spawnboss [name]` - Force spawn boss
- `admin giveitem [phone] [item] [qty]` - Give shop item
- `admin stats` - Global statistics

## 🏗️ Architecture

```
main.py              # Flask entry point, webhook handler
config/
  ├── game_config.json    # All game content (editable!)
  └── admin_config.json   # Admin settings
core/
  ├── database.py         # SQLite database operations
  ├── messaging.py        # CallMeBot API integration
  ├── game_engine.py      # Battle, shop, bank systems
  ├── trading_system.py   # Player trading & messaging
  ├── boss_system.py      # World boss battles
  └── admin_system.py     # Admin commands
utils/
  └── helpers.py          # Utility functions
```

## 🎮 Game Mechanics

### Battle System
1. Use `/odd` to encounter an enemy
2. Choose your action each turn:
   - **Attack**: Deal damage based on power + pets
   - **Defend**: Reduce incoming damage by 70%
   - **Heal**: Use potion or rest for small heal
   - **Special**: Pet special attack (2x damage)
   - **Flee**: 60% chance to escape
3. Win to earn points and EXP
4. Level up every 10 wins for +Power and +HP

### Pet System
- **Rarities**: Common → Rare → Epic → Legendary → Mythic
- **Stats**: ATK power added to your damage
- **Merging**: 3 pets of same type → 1 higher rarity
- **Enchanting**: Pay 500💰 for +5 ATK

### Bank System
- **Tiers**: Basic (2% interest) → Silver (3%) → Gold (5%) → Diamond (8%)
- **Protection**: Banked points cannot be stolen
- **Interest**: Automatic daily payout at midnight

### Stealing
- 35% base success rate
- Steal 100-1000💰 from random or specific player
- Failure = Fine of 50-200💰
- Protection shields block theft for 24h

## 📝 Notes

- **No External Database**: Uses SQLite (file-based)
- **Self-Contained**: All configs in JSON files
- **Auto-Setup**: Database initializes automatically
- **Background Tasks**: Daily interest and random boss spawning
- **Message Simulation**: "Edits" are simulated by sending contextual updates

## 🐛 Troubleshooting

**Bot not responding:**
- Check CallMeBot API key is correct
- Verify webhook URL is set correctly
- Check Railway logs for errors

**Database locked:**
- SQLite handles this automatically with threading locks
- Restart if issues persist

**Messages not sending:**
- CallMeBot has rate limits
- Ensure phone number format is correct (with country code)

## 📄 License

This project is for personal use. The code is provided as-is for your WhatsApp RPG bot.

---

**Created for ODD RPG** | Powered by CallMeBot & Flask
"""

with open('README.md', 'w') as f:
    f.write(readme)

print("✅ requirements.txt created!")
print("✅ README.md created!")
print("\n📦 Deployment package complete!")