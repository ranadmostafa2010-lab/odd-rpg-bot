from flask import Flask, request, Response, jsonify
import random
import json
import os
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Handle Railway PostgreSQL URL format
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# CallMeBot Configuration
CALLMEBOT_API_KEY = os.getenv('CALLMEBOT_API_KEY')
CALLMEBOT_PHONE = os.getenv('CALLMEBOT_PHONE')
CALLMEBOT_BASE_URL = "https://api.callmebot.com/whatsapp.php"

# Game Constants
STARTING_POINTS = 1000
MAX_PETS = 10
COMMANDS = ['odd', 'update', 'crates', 'shop', 'code', 'leaderboard', 'donate', 'enchanter', 'bank', 'steal', 'tutorial']

# Shop Items
SHOP_ITEMS = {
    'potion_small': {'name': 'Small Potion', 'price': 100, 'heal': 20, 'emoji': '🧪'},
    'potion_medium': {'name': 'Medium Potion', 'price': 250, 'heal': 50, 'emoji': '🧪'},
    'potion_large': {'name': 'Large Potion', 'price': 500, 'heal': 100, 'emoji': '🧪'},
    'pet_food': {'name': 'Pet Food', 'price': 150, 'boost': 5, 'emoji': '🍖'},
    'lucky_charm': {'name': 'Lucky Charm', 'price': 1000, 'luck': 10, 'emoji': '🍀'}
}

# Promo Codes (single use per player)
PROMO_CODES = {
    'STARTER': {'points': 500, 'uses': 1},
    'ODD2024': {'points': 1000, 'uses': 1},
    'FREEPOINTS': {'points': 200, 'uses': 1},
    'LEGENDARY': {'points': 5000, 'uses': 1, 'pet': {'name': 'Starter Dragon', 'rarity': '🟪 LEGENDARY', 'atk': 45}}
}

# Pet Tiers
PET_TIERS = {
    'common': {'chance': 50, 'pets': [
        {'name': 'Slime', 'rarity': '⬛ COMMON', 'atk': 10},
        {'name': 'Rat', 'rarity': '⬛ COMMON', 'atk': 12},
        {'name': 'Spider', 'rarity': '⬛ COMMON', 'atk': 11}
    ]},
    'rare': {'chance': 30, 'pets': [
        {'name': 'Wolf', 'rarity': '🟩 RARE', 'atk': 25},
        {'name': 'Bear', 'rarity': '🟩 RARE', 'atk': 28},
        {'name': 'Eagle', 'rarity': '🟩 RARE', 'atk': 26}
    ]},
    'epic': {'chance': 15, 'pets': [
        {'name': 'Unicorn', 'rarity': '🟨 EPIC', 'atk': 35},
        {'name': 'Phoenix', 'rarity': '🟨 EPIC', 'atk': 38},
        {'name': 'Griffin', 'rarity': '🟨 EPIC', 'atk': 36}
    ]},
    'legendary': {'chance': 5, 'pets': [
        {'name': 'Dragon', 'rarity': '🟪 LEGENDARY', 'atk': 50},
        {'name': 'Ancient One', 'rarity': '🟪 LEGENDARY', 'atk': 55},
        {'name': 'Shadow Lord', 'rarity': '🟪 LEGENDARY', 'atk': 52}
    ]}
}

def get_db_connection():
    """Get database connection"""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        # Fallback to SQLite for local testing
        import sqlite3
        return sqlite3.connect('players.db')

def init_db():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if using PostgreSQL or SQLite
        is_postgres = isinstance(conn, psycopg2.extensions.connection)
        
        if is_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    phone VARCHAR(20) PRIMARY KEY,
                    points INTEGER DEFAULT 1000,
                    bank INTEGER DEFAULT 0,
                    power INTEGER DEFAULT 10,
                    health INTEGER DEFAULT 100,
                    max_health INTEGER DEFAULT 100,
                    pets JSONB DEFAULT '[]',
                    inventory JSONB DEFAULT '[]',
                    used_codes JSONB DEFAULT '[]',
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    steals_success INTEGER DEFAULT 0,
                    steals_failed INTEGER DEFAULT 0,
                    enchantments INTEGER DEFAULT 0,
                    joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    phone TEXT PRIMARY KEY,
                    points INTEGER DEFAULT 1000,
                    bank INTEGER DEFAULT 0,
                    power INTEGER DEFAULT 10,
                    health INTEGER DEFAULT 100,
                    max_health INTEGER DEFAULT 100,
                    pets TEXT DEFAULT '[]',
                    inventory TEXT DEFAULT '[]',
                    used_codes TEXT DEFAULT '[]',
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    steals_success INTEGER DEFAULT 0,
                    steals_failed INTEGER DEFAULT 0,
                    enchantments INTEGER DEFAULT 0,
                    joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

def get_player(phone):
    """Get or create player"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        is_postgres = isinstance(conn, psycopg2.extensions.connection)
        
        cursor.execute("SELECT * FROM players WHERE phone = %s" if is_postgres else "SELECT * FROM players WHERE phone = ?", (phone,))
        row = cursor.fetchone()
        
        if not row:
            # Create new player
            if is_postgres:
                cursor.execute('''
                    INSERT INTO players (phone, points, bank, power, health, max_health, pets, inventory, used_codes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (phone, STARTING_POINTS, 0, 10, 100, 100, '[]', '[]', '[]'))
            else:
                cursor.execute('''
                    INSERT INTO players (phone, points, bank, power, health, max_health, pets, inventory, used_codes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (phone, STARTING_POINTS, 0, 10, 100, 100, '[]', '[]', '[]'))
            
            conn.commit()
            
            player = {
                'phone': phone,
                'points': STARTING_POINTS,
                'bank': 0,
                'power': 10,
                'health': 100,
                'max_health': 100,
                'pets': [],
                'inventory': [],
                'used_codes': [],
                'wins': 0,
                'losses': 0,
                'steals_success': 0,
                'steals_failed': 0,
                'enchantments': 0
            }
        else:
            # Parse player data
            if is_postgres:
                player = {
                    'phone': row[0],
                    'points': row[1],
                    'bank': row[2],
                    'power': row[3],
                    'health': row[4],
                    'max_health': row[5],
                    'pets': row[6] if isinstance(row[6], list) else json.loads(row[6] or '[]'),
                    'inventory': row[7] if isinstance(row[7], list) else json.loads(row[7] or '[]'),
                    'used_codes': row[8] if isinstance(row[8], list) else json.loads(row[8] or '[]'),
                    'wins': row[9],
                    'losses': row[10],
                    'steals_success': row[11],
                    'steals_failed': row[12],
                    'enchantments': row[13]
                }
            else:
                player = {
                    'phone': row[0],
                    'points': row[1],
                    'bank': row[2],
                    'power': row[3],
                    'health': row[4],
                    'max_health': row[5],
                    'pets': json.loads(row[6] or '[]'),
                    'inventory': json.loads(row[7] or '[]'),
                    'used_codes': json.loads(row[8] or '[]'),
                    'wins': row[9],
                    'losses': row[10],
                    'steals_success': row[11],
                    'steals_failed': row[12],
                    'enchantments': row[13]
                }
            
            # Update last active
            if is_postgres:
                cursor.execute("UPDATE players SET last_active = CURRENT_TIMESTAMP WHERE phone = %s", (phone,))
            else:
                cursor.execute("UPDATE players SET last_active = CURRENT_TIMESTAMP WHERE phone = ?", (phone,))
            conn.commit()
        
        cursor.close()
        conn.close()
        return player
        
    except Exception as e:
        print(f"Error getting player: {e}")
        # Return default player on error
        return {
            'phone': phone,
            'points': STARTING_POINTS,
            'bank': 0,
            'power': 10,
            'health': 100,
            'max_health': 100,
            'pets': [],
            'inventory': [],
            'used_codes': [],
            'wins': 0,
            'losses': 0,
            'steals_success': 0,
            'steals_failed': 0,
            'enchantments': 0
        }

def save_player(phone, player):
    """Save player data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        is_postgres = isinstance(conn, psycopg2.extensions.connection)
        
        pets_json = json.dumps(player['pets']) if isinstance(player['pets'], list) else player['pets']
        inventory_json = json.dumps(player['inventory']) if isinstance(player['inventory'], list) else player['inventory']
        codes_json = json.dumps(player['used_codes']) if isinstance(player['used_codes'], list) else player['used_codes']
        
        if is_postgres:
            cursor.execute('''
                UPDATE players SET 
                    points = %s, bank = %s, power = %s, health = %s, max_health = %s,
                    pets = %s, inventory = %s, used_codes = %s,
                    wins = %s, losses = %s, steals_success = %s, steals_failed = %s, enchantments = %s
                WHERE phone = %s
            ''', (
                player['points'], player['bank'], player['power'], player['health'], player['max_health'],
                pets_json, inventory_json, codes_json,
                player['wins'], player['losses'], player['steals_success'], player['steals_failed'], player['enchantments'],
                phone
            ))
        else:
            cursor.execute('''
                UPDATE players SET 
                    points = ?, bank = ?, power = ?, health = ?, max_health = ?,
                    pets = ?, inventory = ?, used_codes = ?,
                    wins = ?, losses = ?, steals_success = ?, steals_failed = ?, enchantments = ?
                WHERE phone = ?
            ''', (
                player['points'], player['bank'], player['power'], player['health'], player['max_health'],
                pets_json, inventory_json, codes_json,
                player['wins'], player['losses'], player['steals_success'], player['steals_failed'], player['enchantments'],
                phone
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving player: {e}")
        return False

def send_whatsapp_message(to_phone, message):
    """Send WhatsApp message via CallMeBot"""
    if not CALLMEBOT_API_KEY:
        print("Error: CALLMEBOT_API_KEY not set")
        return False
    
    try:
        encoded_message = requests.utils.quote(message)
        url = f"{CALLMEBOT_BASE_URL}?phone={to_phone}&text={encoded_message}&apikey={CALLMEBOT_API_KEY}"
        
        response = requests.get(url, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def get_leaderboard(limit=10):
    """Get top players by total wealth"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        is_postgres = isinstance(conn, psycopg2.extensions.connection)
        
        cursor.execute("""
            SELECT phone, points, bank, wins, (points + bank) as total 
            FROM players 
            ORDER BY total DESC 
            LIMIT %s
        """ if is_postgres else """
            SELECT phone, points, bank, wins, (points + bank) as total 
            FROM players 
            ORDER BY total DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [{
            'phone': row[0][:6] + '****' if len(row[0]) > 6 else row[0],
            'points': row[1],
            'bank': row[2],
            'wins': row[3],
            'total': row[4]
        } for row in rows]
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []

def get_random_pet():
    """Get random pet based on tiers"""
    roll = random.randint(1, 100)
    cumulative = 0
    
    for tier, data in PET_TIERS.items():
        cumulative += data['chance']
        if roll <= cumulative:
            pet = random.choice(data['pets']).copy()
            pet['level'] = 1
            pet['exp'] = 0
            pet['enchanted'] = False
            return pet
    
    return PET_TIERS['common']['pets'][0].copy()

def format_number(num):
    """Format large numbers"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

@app.route('/')
def home():
    return "ODD RPG Bot Online! 🎮 | V. Re-Imagined"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Handle incoming WhatsApp messages"""
    try:
        if request.method == 'GET':
            phone = request.args.get('phone', '').strip()
            message = request.args.get('text', '').strip()
        else:
            data = request.get_json() or {}
            phone = data.get('phone', '').strip()
            message = data.get('text', '').strip()
        
        if not phone or not message:
            return Response("Missing parameters", status=400)
        
        # Remove / prefix if present and convert to lowercase
        if message.startswith('/'):
            message = message[1:].lower().strip()
        else:
            message = message.lower().strip()
        
        # Process command
        reply = process_command(phone, message)
        
        # Send response
        if send_whatsapp_message(phone, reply):
            return Response("OK", status=200)
        else:
            return Response("Failed to send message", status=500)
            
    except Exception as e:
        print(f"Webhook error: {e}")
        return Response("Internal error", status=500)

def process_command(phone, message):
    """Process game commands"""
    player = get_player(phone)
    args = message.split()
    command = args[0] if args else ''
    
    # MENU COMMAND
    if command in ['menu', 'start', 'help']:
        return f"""🎮 *ODD RPG* 🪀 | V. Re-Imagined

💰 Points: {format_number(player['points'])}
🏦 Bank: {format_number(player['bank'])}
⚔️ Power: {player['power']}
❤️ Health: {player['health']}/{player['max_health']}
🎒 Pets: {len(player['pets'])}/{MAX_PETS}
🏆 Wins: {player['wins']}

*-----------------------------*
☞ */odd* 🪀 | Start the main game
☞ */update* 🗒️ | See latest updates
☞ */crates* 📦 | Get pets to help you
☞ */shop* 🏬 | Buy potions and items
☞ */code* 👨‍💻 | Redeem promo codes
☞ */leaderboard* 📋 | Top players
☞ */donate* 🩸 | Give points to others
☞ */enchanter* 📚 | Enchant your pets
☞ */bank* 🏦 | Save your money
☞ */steal* 🥷 | Steal from others
☞ */tutorial* 🤦‍♀️ | Learn how to play
*-----------------------------*
Send *Next page* for more info"""
    
    # NEXT PAGE
    elif message == 'next page':
        return """*📊 Your Stats*
Wins: {wins} | Losses: {losses}
Successful Steals: {steals}
Failed Steals: {fails}
Enchantments: {enchants}

*💡 Quick Tips*
• Bank your points before stealing
• Higher power = more damage
• Enchant pets to boost attack
• Use codes for free rewards

*🔄 Commands don't need / prefix*
Just type: menu, odd, crates, etc.""".format(
            wins=player['wins'],
            losses=player['losses'],
            steals=player['steals_success'],
            fails=player['steals_failed'],
            enchants=player['enchantments']
        )
    
    # ODD - BATTLE COMMAND
    elif command == 'odd':
        if player['health'] < 20:
            return "❌ You're too weak to fight! Heal first or wait for regeneration."
        
        enemy_types = [
            {'name': 'Goblin', 'hp': (30, 80), 'reward': (50, 150)},
            {'name': 'Orc', 'hp': (60, 120), 'reward': (100, 250)},
            {'name': 'Skeleton', 'hp': (40, 100), 'reward': (75, 200)},
            {'name': 'Dark Wolf', 'hp': (50, 110), 'reward': (90, 220)},
            {'name': 'Troll', 'hp': (80, 150), 'reward': (150, 350)},
            {'name': 'Dragon Whelp', 'hp': (100, 200), 'reward': (200, 500)},
            {'name': 'Demon', 'hp': (120, 250), 'reward': (300, 800)}
        ]
        
        enemy = random.choice(enemy_types)
        enemy_hp = random.randint(*enemy['hp'])
        enemy_max_hp = enemy_hp
        
        # Calculate player damage with pet bonus
        pet_bonus = sum(p.get('atk', 0) for p in player['pets']) // 10
        base_dmg = random.randint(player['power'], player['power'] + 25)
        player_dmg = base_dmg + pet_bonus
        
        # Battle simulation
        rounds = 0
        player_health = player['health']
        
        while enemy_hp > 0 and player_health > 0 and rounds < 10:
            # Player attacks
            dmg_dealt = random.randint(int(player_dmg * 0.8), player_dmg)
            enemy_hp -= dmg_dealt
            
            if enemy_hp <= 0:
                break
            
            # Enemy attacks back (30% chance)
            if random.random() < 0.3:
                enemy_dmg = random.randint(5, 20)
                player_health -= enemy_dmg
            
            rounds += 1
        
        # Determine outcome
        if enemy_hp <= 0:
            reward = random.randint(*enemy['reward'])
            bonus = random.randint(0, 100) if random.random() < 0.2 else 0
            
            player['points'] += reward + bonus
            player['wins'] += 1
            player['health'] = max(10, player_health)
            
            # Level up check
            if player['wins'] % 10 == 0:
                player['power'] += 2
                player['max_health'] += 10
            
            save_player(phone, player)
            
            bonus_text = f"\n🎁 BONUS: +{bonus}💰" if bonus > 0 else ""
            level_text = "\n⬆️ LEVEL UP! Power +2, Max Health +10!" if player['wins'] % 10 == 0 else ""
            
            return f"""⚔️ *VICTORY!* ⚔️

Enemy: {enemy['name']}
❤️ Enemy HP: 0/{enemy_max_hp}
💥 Your damage: {player_dmg}
🔄 Rounds: {rounds}

✅ You won! +{reward}💰{bonus_text}
💰 Total: {format_number(player['points'])}
❤️ Health: {player['health']}/{player['max_health']}{level_text}"""
        else:
            loss = random.randint(20, 80)
            player['points'] = max(0, player['points'] - loss)
            player['losses'] += 1
            player['health'] = max(10, player_health)
            save_player(phone, player)
            
            return f"""💀 *DEFEAT!* 💀

Enemy: {enemy['name']}
❤️ Enemy HP: {max(0, enemy_hp)}/{enemy_max_hp}
💥 Your damage: {player_dmg}

❌ You lost! -{loss}💰
💰 Total: {format_number(player['points'])}
❤️ Health: {player['health']}/{player['max_health']}

💡 Tip: Get stronger pets or heal up!"""
    
    # UPDATE COMMAND
    elif command == 'update':
        return """🗒️ *LATEST UPDATES* | V. Re-Imagined

*🆕 New in this version:*
• Enchantment system added!
• New pet tiers and rarities
• Improved battle system
• Bank protection enhanced
• Leaderboard tracking
• Promo code system

*🔮 Coming Soon:*
• Guild system
• Boss raids
• Trading between players
• Pet breeding
• Seasonal events

*📅 Last Updated:* 2024
*🎮 Total Players:* Check leaderboard!"""
    
    # CRATES COMMAND
    elif command in ['crates', 'crate']:
        if len(player['pets']) >= MAX_PETS:
            return f"""❌ *INVENTORY FULL!*

You have {len(player['pets'])}/{MAX_PETS} pets.
Use */enchanter* to merge pets or upgrade storage."""
        
        cost = 100
        if player['points'] < cost:
            return f"""❌ *NOT ENOUGH POINTS!*

Crate cost: {cost}💰
Your points: {format_number(player['points'])}💰

Win battles to earn more!"""
        
        player['points'] -= cost
        pet = get_random_pet()
        
        # Check for lucky charm
        luck_bonus = 0
        for item in player['inventory']:
            if item.get('type') == 'lucky_charm':
                luck_bonus = 10
                break
        
        # Reroll if lucky
        if random.randint(1, 100) <= luck_bonus:
            pet = get_random_pet()
            if pet['rarity'] in ['🟨 EPIC', '🟪 LEGENDARY']:
                luck_text = "\n🍀 *LUCKY CHARM ACTIVATED!*"
            else:
                luck_text = ""
        else:
            luck_text = ""
        
        player['pets'].append(pet)
        
        # Update power to best pet
        if pet['atk'] > player['power']:
            player['power'] = pet['atk']
        
        save_player(phone, player)
        
        return f"""📦 *CRATE OPENED!* 📦

Cost: {cost}💰
🎲 Roll: {random.randint(1, 100)}{luck_text}

{pet['rarity']}
✨ *{pet['name']}*
⚔️ ATK: {pet['atk']}
📊 Level: {pet['level']}

🎒 Pets: {len(player['pets'])}/{MAX_PETS}
💰 Remaining: {format_number(player['points'])}"""
    
    # SHOP COMMAND
    elif command == 'shop':
        if len(args) == 1:
            return """🏬 *ODD SHOP* 🏬

💰 Your points: """ + format_number(player['points']) + """

*Items for sale:*
🧪 Small Potion - 100💰 (Heal 20 HP)
🧪 Medium Potion - 250💰 (Heal 50 HP)
🧪 Large Potion - 500💰 (Heal 100 HP)
🍖 Pet Food - 150💰 (Pet ATK +5)
🍀 Lucky Charm - 1000💰 (+10% rare drop)

*To buy:*
shop buy [item]
Example: shop buy potion_small"""
        
        elif len(args) >= 3 and args[1] == 'buy':
            item_id = args[2]
            if item_id not in SHOP_ITEMS:
                return "❌ Item not found! Use */shop* to see items."
            
            item = SHOP_ITEMS[item_id]
            if player['points'] < item['price']:
                return f"❌ Not enough points! You need {item['price']}💰"
            
            player['points'] -= item['price']
            
            if 'heal' in item:
                player['health'] = min(player['max_health'], player['health'] + item['heal'])
                effect = f"❤️ Healed {item['heal']} HP!"
            elif 'boost' in item:
                if player['pets']:
                    pet = random.choice(player['pets'])
                    pet['atk'] += item['boost']
                    effect = f"⚔️ {pet['name']} ATK +{item['boost']}!"
                else:
                    effect = "No pets to feed! Points refunded."
                    player['points'] += item['price']
            else:
                player['inventory'].append({'type': item_id, 'name': item['name']})
                effect = "Added to inventory!"
            
            save_player(phone, player)
            return f"""✅ *PURCHASE SUCCESSFUL!*

{item['emoji']} {item['name']}
💰 Cost: {item['price']}
{effect}

💰 Remaining: {format_number(player['points'])}"""
    
    # CODE COMMAND
    elif command == 'code':
        if len(args) == 1:
            return """👨‍💻 *PROMO CODES* 👨‍💻

Redeem codes for free rewards!

*To use:*
code [CODE]
Example: code STARTER

*Available codes:*
• STARTER - 500💰
• ODD2024 - 1000💰
• FREEPOINTS - 200💰
• LEGENDARY - 5000💰 + Dragon

*Note:* Each code can only be used once per player!"""
        
        code = args[1].upper() if len(args) > 1 else ''
        
        if code not in PROMO_CODES:
            return "❌ Invalid code! Use */code* to see available codes."
        
        if code in player['used_codes']:
            return "❌ You already used this code!"
        
        promo = PROMO_CODES[code]
        player['points'] += promo['points']
        player['used_codes'].append(code)
        
        reward_text = f"💰 +{promo['points']} points!"
        
        if 'pet' in promo:
            if len(player['pets']) < MAX_PETS:
                player['pets'].append(promo['pet'])
                reward_text += f"\n🎁 {promo['pet']['rarity']} {promo['pet']['name']}!"
            else:
                reward_text += "\n⚠️ Inventory full, pet not added!"
        
        save_player(phone, player)
        
        return f"""🎉 *CODE REDEEMED!* 🎉

Code: {code}
{reward_text}

💰 Total: {format_number(player['points'])}"""
    
    # LEADERBOARD COMMAND
    elif command == 'leaderboard':
        top_players = get_leaderboard(10)
        
        if not top_players:
            return "📋 No players yet! Be the first to play!"
        
        leaderboard_text = "📋 *GLOBAL LEADERBOARD* 📋\n\n"
        
        medals = ['🥇', '🥈', '🥉']
        for i, p in enumerate(top_players):
            medal = medals[i] if i < 3 else f"{i+1}."
            leaderboard_text += f"{medal} {p['phone']}\n"
            leaderboard_text += f"   💰 {format_number(p['total'])} | 🏆 {p['wins']} wins\n\n"
        
        # Find player rank
        all_players = get_leaderboard(1000)
        player_rank = next((i+1 for i, p in enumerate(all_players) if p['phone'].replace('*', '') in phone), None)
        
        if player_rank:
            leaderboard_text += f"\n📊 *Your Rank:* #{player_rank}"
        
        return leaderboard_text
    
    # DONATE COMMAND
    elif command == 'donate':
        if len(args) < 3:
            return """🩸 *DONATE POINTS* 🩸

Give points to other players!

*Usage:*
donate [amount] [player_phone]
Example: donate 500 1234567890

*Note:* You cannot donate from your bank."""
        
        try:
            amount = int(args[1])
            target_phone = args[2]
        except:
            return "❌ Invalid format! Use: donate [amount] [phone]"
        
        if amount <= 0:
            return "❌ Amount must be positive!"
        
        if amount > player['points']:
            return f"❌ You only have {format_number(player['points'])}💰 available!"
        
        if target_phone == phone:
            return "❌ You can't donate to yourself!"
        
        # Check if target exists
        target = get_player(target_phone)
        if target['points'] == STARTING_POINTS and target['wins'] == 0 and target['losses'] == 0:
            # Might be new player, but allow anyway
            pass
        
        # Process donation
        player['points'] -= amount
        target['points'] += amount
        
        save_player(phone, player)
        save_player(target_phone, target)
        
        # Notify target
        send_whatsapp_message(target_phone, f"🎁 *DONATION RECEIVED!*\n\n{phone[:6]}**** sent you {amount}💰!\n💰 Your new total: {format_number(target['points'])}")
        
        return f"""🩸 *DONATION SUCCESSFUL!* 🩸

Sent: {amount}💰
To: {target_phone[:6]}****
💰 Remaining: {format_number(player['points'])}"""
    
    # ENCHANTER COMMAND
    elif command == 'enchanter':
        if len(args) == 1:
            return """📚 *PET ENCHANTER* 📚

Upgrade your pets to make them stronger!

*Options:*
• Merge 3 common → 1 rare
• Merge 3 rare → 1 epic
• Merge 3 epic → 1 legendary
• Enchant pet (+5 ATK) - 500💰

*To use:*
enchanter merge [pet_name]
enchanter upgrade [slot_number]
Example: enchanter merge Slime"""
        
        action = args[1] if len(args) > 1 else ''
        
        if action == 'merge':
            if len(args) < 3:
                return "❌ Specify pet name! Example: enchanter merge Slime"
            
            pet_name = ' '.join(args[2:]).title()
            matching_pets = [p for p in player['pets'] if p['name'] == pet_name]
            
            if len(matching_pets) < 3:
                return f"❌ You need 3 {pet_name}s to merge! You have {len(matching_pets)}."
            
            # Remove 3 pets
            removed = 0
            new_pets = []
            for p in player['pets']:
                if p['name'] == pet_name and removed < 3:
                    removed += 1
                else:
                    new_pets.append(p)
            
            # Create upgraded pet
            rarity_map = {'⬛ COMMON': '🟩 RARE', '🟩 RARE': '🟨 EPIC', '🟨 EPIC': '🟪 LEGENDARY'}
            current_rarity = matching_pets[0]['rarity']
            new_rarity = rarity_map.get(current_rarity, '🟪 LEGENDARY')
            
            # Find pet in new tier
            for tier, data in PET_TIERS.items():
                for pet_template in data['pets']:
                    if pet_template['rarity'] == new_rarity:
                        new_pet = pet_template.copy()
                        new_pet['level'] = 1
                        new_pet['exp'] = 0
                        new_pet['enchanted'] = True
                        new_pets.append(new_pet)
                        break
            
            player['pets'] = new_pets
            player['enchantments'] += 1
            
            # Recalculate power
            player['power'] = max([p['atk'] for p in player['pets']], default=10)
            
            save_player(phone, player)
            
            return f"""✨ *MERGE SUCCESSFUL!* ✨

3x {pet_name} → 
{new_rarity} {new_pet['name']}!
⚔️ ATK: {new_pet['atk']}

🎒 Pets: {len(player['pets'])}/{MAX_PETS}"""
        
        elif action == 'upgrade':
            if len(args) < 3:
                return "❌ Specify pet slot! Example: enchanter upgrade 1"
            
            try:
                slot = int(args[2]) - 1
                if slot < 0 or slot >= len(player['pets']):
                    return f"❌ Invalid slot! You have {len(player['pets'])} pets."
            except:
                return "❌ Invalid slot number!"
            
            cost = 500
            if player['points'] < cost:
                return f"❌ Need {cost}💰 to enchant!"
            
            pet = player['pets'][slot]
            player['points'] -= cost
            pet['atk'] += 5
            pet['enchanted'] = True
            player['enchantments'] += 1
            
            # Update power if this was best pet
            if pet['atk'] > player['power']:
                player['power'] = pet['atk']
            
            save_player(phone, player)
            
            return f"""📚 *ENCHANTMENT COMPLETE!* 📚

✨ {pet['rarity']} {pet['name']}
⚔️ ATK: {pet['atk'] - 5} → {pet['atk']}
🔮 Enchanted: Yes

💰 Cost: {cost}
💰 Remaining: {format_number(player['points'])}"""
        
        else:
            return "❌ Unknown action! Use */enchanter* for help."
    
    # BANK COMMAND
    elif command == 'bank':
        if len(args) == 1:
            return f"""🏦 *ODD BANK* 🏦

Wallet: {format_number(player['points'])}💰
Savings: {format_number(player['bank'])}💰 (Protected!)

*Commands:*
deposit [amount] - Save points
withdraw [amount] - Take points out
deposit all - Save everything
withdraw all - Empty bank

💡 Banked points cannot be stolen!"""
        
        action = args[1] if len(args) > 1 else ''
        
        if action == 'all':
            return "❌ Specify deposit all or withdraw all"
        
        if action.startswith('deposit'):
            if len(action) > 7:  # deposit100 format
                try:
                    amount = int(action[7:])
                except:
                    amount = None
            elif len(args) > 2:
                try:
                    amount = int(args[2])
                except:
                    return "❌ Invalid amount! Use: bank deposit 500"
            else:
                return "❌ Specify amount! Use: bank deposit 500"
            
            if amount is None or amount <= 0:
                return "❌ Invalid amount!"
            
            if amount > player['points']:
                return f"❌ You only have {format_number(player['points'])}💰!"
            
            player['points'] -= amount
            player['bank'] += amount
            save_player(phone, player)
            
            return f"""✅ *DEPOSITED* ✅

Amount: {format_number(amount)}💰
🏦 Bank: {format_number(player['bank'])}💰
💰 Wallet: {format_number(player['points'])}💰"""
        
        elif action.startswith('withdraw'):
            if len(action) > 8:  # withdraw100 format
                try:
                    amount = int(action[8:])
                except:
                    amount = None
            elif len(args) > 2:
                try:
                    amount = int(args[2])
                except:
                    return "❌ Invalid amount! Use: bank withdraw 500"
            else:
                return "❌ Specify amount! Use: bank withdraw 500"
            
            if amount is None or amount <= 0:
                return "❌ Invalid amount!"
            
            if amount > player['bank']:
                return f"❌ Bank only has {format_number(player['bank'])}💰!"
            
            player['bank'] -= amount
            player['points'] += amount
            save_player(phone, player)
            
            return f"""✅ *WITHDRAWN* ✅

Amount: {format_number(amount)}💰
🏦 Bank: {format_number(player['bank'])}💰
💰 Wallet: {format_number(player['points'])}💰"""
        
        elif action == 'all':
            return "❌ Use: deposit all or withdraw all"
        
        else:
            return "❌ Unknown action! Use */bank* for help."
    
    # Handle "deposit all" and "withdraw all" variations
    elif command == 'deposit' and len(args) > 1:
        if args[1] == 'all':
            amount = player['points']
            if amount <= 0:
                return "❌ No points to deposit!"
            
            player['bank'] += amount
            player['points'] = 0
            save_player(phone, player)
            
            return f"""✅ *ALL POINTS DEPOSITED* ✅

Amount: {format_number(amount)}💰
🏦 Bank: {format_number(player['bank'])}💰
💰 Wallet: 0💰"""
        else:
            try:
                amount = int(args[1])
                if amount <= 0 or amount > player['points']:
                    return "❌ Invalid amount!"
                
                player['points'] -= amount
                player['bank'] += amount
                save_player(phone, player)
                
                return f"""✅ *DEPOSITED* ✅

Amount: {format_number(amount)}💰
🏦 Bank: {format_number(player['bank'])}💰
💰 Wallet: {format_number(player['points'])}💰"""
            except:
                return "❌ Invalid amount!"
    
    elif command == 'withdraw' and len(args) > 1:
        if args[1] == 'all':
            amount = player['bank']
            if amount <= 0:
                return "❌ Bank is empty!"
            
            player['points'] += amount
            player['bank'] = 0
            save_player(phone, player)
            
            return f"""✅ *BANK EMPTIED* ✅

Amount: {format_number(amount)}💰
🏦 Bank: 0💰
💰 Wallet: {format_number(player['points'])}💰"""
        else:
            try:
                amount = int(args[1])
                if amount <= 0 or amount > player['bank']:
                    return "❌ Invalid amount!"
                
                player['bank'] -= amount
                player['points'] += amount
                save_player(phone, player)
                
                return f"""✅ *WITHDRAWN* ✅

Amount: {format_number(amount)}💰
🏦 Bank: {format_number(player['bank'])}💰
💰 Wallet: {format_number(player['points'])}💰"""
            except:
                return "❌ Invalid amount!"
    
    # STEAL COMMAND
    elif command == 'steal':
        # Check cooldown (simplified - in production use Redis or similar)
        steal_chance = 40  # Base 40% success
        
        # Bonus from pets
        for pet in player['pets']:
            if pet['name'] in ['Shadow Lord', 'Thief', 'Rogue']:
                steal_chance += 10
        
        if random.randint(1, 100) <= steal_chance:
            stolen = random.randint(100, 500)
            player['points'] += stolen
            player['steals_success'] += 1
            save_player(phone, player)
            
            return f"""🥷 *THEFT SUCCESSFUL!* 🥷

You stole {stolen}💰 from unsuspecting victims!
💰 Total: {format_number(player['points'])}

⚠️ Watch out, they might steal back!"""
        else:
            fine = random.randint(50, 150)
            player['points'] = max(0, player['points'] - fine)
            player['steals_failed'] += 1
            save_player(phone, player)
            
            return f"""🚔 *CAUGHT BY GUARDS!* 🚔

Fine: {fine}💰
💰 Total: {format_number(player['points'])}

💡 Tip: Bank your points before stealing!"""
    
    # TUTORIAL COMMAND
    elif command == 'tutorial':
        return """🤦‍♀️ *HOW TO PLAY ODD RPG* 🤦‍♀️

*🎯 Goal:* Become the richest and strongest player!

*📱 Basic Commands:*
1️⃣ */odd* - Battle enemies for points and XP
2️⃣ */crates* - Spend 100💰 to get random pets
3️⃣ */bank* - Protect your points from thieves
4️⃣ */shop* - Buy potions and items
5️⃣ */steal* - Risk it all to steal points (40% chance)

*💡 Pro Tips:*
• Pets increase your battle power
• Bank points before stealing
• Use codes for free rewards
• Merge pets at the enchanter
• Check leaderboard to see top players

*⚔️ Battle System:*
• Higher power = more damage
• Pets add bonus damage
• Win 10 battles to level up
• Health regenerates slowly

*🎒 Pet Rarities:*
⬛ Common (50%) | 🟩 Rare (30%)
🟨 Epic (15%) | 🟪 Legendary (5%)

Good luck! May the odds be ever in your favor! 🎮"""
    
    # INVENTORY (hidden command)
    elif command in ['inv', 'inventory', 'pets']:
        if not player['pets']:
            return "🎒 *INVENTORY*\n\nNo pets yet!\nSend */crates* to get one."
        
        pet_list = ""
        for i, p in enumerate(player['pets'][:10]):
            enchanted = " ✨" if p.get('enchanted') else ""
            pet_list += f"{i+1}. {p['rarity']} {p['name']}{enchanted}\n   ⚔️ATK:{p['atk']} | LVL:{p['level']}\n"
        
        if len(player['pets']) > 10:
            pet_list += f"\n...and {len(player['pets']) - 10} more"
        
        return f"""🎒 *YOUR PETS* ({len(player['pets']})

{pet_list}
💰 {format_number(player['points'])} | 🏦 {format_number(player['bank'])} | ⚔️ {player['power']}"""
    
    # HEALTH CHECK (hidden command)
    elif command == 'heal':
        if player['health'] >= player['max_health']:
            return "❤️ You're already at full health!"
        
        # Auto-heal costs points
        heal_cost = (player['max_health'] - player['health']) * 2
        
        if player['points'] < heal_cost:
            return f"❌ Healing costs {heal_cost}💰. You have {format_number(player['points'])}💰"
        
        player['points'] -= heal_cost
        player['health'] = player['max_health']
        save_player(phone, player)
        
        return f"""❤️ *FULLY HEALED!* ❤️

Cost: {heal_cost}💰
Health: {player['health']}/{player['max_health']}
💰 Remaining: {format_number(player['points'])}"""
    
    # STATS COMMAND (hidden)
    elif command == 'stats':
        total_wealth = player['points'] + player['bank']
        return f"""📊 *YOUR STATS* 📊

💰 Points: {format_number(player['points'])}
🏦 Bank: {format_number(player['bank'])}
💎 Total Wealth: {format_number(total_wealth)}

⚔️ Power: {player['power']}
❤️ Health: {player['health']}/{player['max_health']}
🎒 Pets: {len(player['pets'])}

🏆 Wins: {player['wins']}
💀 Losses: {player['losses']}
📈 Win Rate: {(player['wins']/(player['wins']+player['losses'])*100 if (player['wins']+player['losses']) > 0 else 0):.1f}%

🥷 Steals: {player['steals_success']}/{player['steals_success']+player['steals_failed']}
📚 Enchantments: {player['enchantments']}"""
    
    # DEFAULT - UNKNOWN COMMAND
    else:
        return """❓ *UNKNOWN COMMAND* ❓

I don't recognize that command!
Send */menu* for all options
Send */tutorial* to learn how to play

*Popular commands:*
• menu - Show main menu
• odd - Battle enemies
• crates - Get pets
• bank - Save your money"""

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/stats')
def game_stats():
    """Game statistics endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), SUM(points), SUM(bank), SUM(wins) FROM players")
        total_players, total_points, total_bank, total_wins = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "total_players": total_players or 0,
            "total_points_in_game": total_points or 0,
            "total_banked": total_bank or 0,
            "total_battles_won": total_wins or 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Initialize database on startup
init_db()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
