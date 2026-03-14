
# main.py - The main entry point
main_code = r'''#!/usr/bin/env python3
"""
ODD RPG WhatsApp Bot
V. Re-Imagined Ultimate Edition

A comprehensive RPG bot using CallMeBot API and Flask
No external database required - uses SQLite
"""

import os
import sys
import json
import random
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, Response

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import db
from core.messaging import MessagingSystem
from core.game_engine import GameEngine
from core.trading_system import TradingSystem
from core.boss_system import BossSystem
from core.admin_system import AdminSystem
from utils.helpers import format_number, get_time_left

# Initialize Flask app
app = Flask(__name__)

# Load configurations
def load_config():
    """Load all configurations"""
    try:
        with open('config/game_config.json', 'r') as f:
            game_config = json.load(f)
    except Exception as e:
        print(f"Error loading game config: {e}")
        game_config = {}
    
    try:
        with open('config/admin_config.json', 'r') as f:
            admin_config = json.load(f)
    except Exception as e:
        print(f"Error loading admin config: {e}")
        admin_config = {'admin_phone': '', 'api_key': ''}
    
    return game_config, admin_config

game_config, admin_config = load_config()

# Initialize systems
messaging = MessagingSystem(
    api_key=admin_config.get('api_key', ''),
    phone=admin_config.get('admin_phone', '')
)
game_engine = GameEngine(game_config)
trading_system = TradingSystem(game_config)
boss_system = BossSystem(game_config)
admin_system = AdminSystem(admin_config)

# In-memory state for message editing simulation
message_history = {}
user_states = {}

@app.route('/')
def home():
    """Home page"""
    return """
    <html>
    <head><title>ODD RPG Bot</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <h1>🎮 ODD RPG Bot 🎮</h1>
        <h2>V. Re-Imagined Ultimate</h2>
        <p>Status: <span style="color: green;">● Online</span></p>
        <p>WhatsApp RPG Bot powered by CallMeBot</p>
        <hr>
        <p><a href="/health">Health Check</a> | <a href="/stats">Game Stats</a></p>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0 Ultimate",
        "players": len(db.get_all_players())
    }

@app.route('/stats')
def game_stats():
    """Game statistics"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM players")
        total_players = cursor.fetchone()['total']
        
        cursor.execute("SELECT SUM(points) as total FROM players")
        total_points = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT SUM(bank) as total FROM players")
        total_bank = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT SUM(wins) as total FROM players")
        total_wins = cursor.fetchone()['total'] or 0
        
        conn.close()
        
        return {
            "total_players": total_players,
            "total_points": total_points,
            "total_banked": total_bank,
            "total_battles_won": total_wins,
            "total_wealth": total_points + total_bank
        }
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Main webhook for incoming messages"""
    try:
        # Get parameters
        if request.method == 'GET':
            phone = request.args.get('phone', '').strip()
            message = request.args.get('text', '').strip()
        else:
            data = request.get_json() or {}
            phone = data.get('phone', '').strip()
            message = data.get('text', '').strip()
        
        if not phone or not message:
            return Response("Missing parameters", status=400)
        
        # Check maintenance mode
        if admin_config.get('maintenance_mode', False) and phone != admin_config.get('admin_phone'):
            messaging.send_message(phone, "🔧 Bot is under maintenance. Please try again later.")
            return Response("Maintenance mode", status=200)
        
        # Get or create player
        player = db.get_player(phone)
        
        # Check banned
        if player.get('banned', 0):
            messaging.send_message(phone, f"🚫 You are banned. Reason: {player.get('ban_reason', 'No reason given')}")
            return Response("Banned user", status=200)
        
        # Process command
        reply = process_message(phone, message)
        
        # Send response
        if reply:
            # Check if we should "edit" or send new
            last_msg = message_history.get(phone)
            if last_msg and (datetime.now() - last_msg['time']).seconds < 30:
                # Send as update (new message with context)
                success, msg_id = messaging.send_update(phone, reply, last_msg['id'])
            else:
                success, msg_id = messaging.send_message(phone, reply)
            
            if success:
                message_history[phone] = {'id': msg_id, 'time': datetime.now(), 'content': reply}
        
        return Response("OK", status=200)
        
    except Exception as e:
        print(f"Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return Response("Internal error", status=500)

def process_message(phone, message):
    """Process incoming message and return reply"""
    message = message.strip()
    message_lower = message.lower()
    
    # Remove / prefix if present
    if message.startswith('/'):
        message_lower = message_lower[1:]
        message = message[1:]
    
    parts = message.split()
    command = parts[0].lower() if parts else ''
    args = parts[1:] if len(parts) > 1 else []
    
    # Check for active battle first
    active_battle = db.get_active_battle(phone)
    if active_battle and command in ['1', '2', '3', '4', '5', 'attack', 'defend', 'heal', 'special', 'flee', '⚔️', '🛡️', '🧪', '✨', '🏃']:
        return game_engine.process_battle_action(phone, command)
    
    # Check for boss battle participation
    if command in ['attack', 'defend'] and len(args) > 0 and args[0].isdigit():
        return boss_system.attack_boss(phone, int(args[0]), command)
    
    # Main command router
    if command in ['menu', 'start', 'help', 'h']:
        return messaging.format_menu(db.get_player(phone), admin_config)
    
    elif command == 'next':
        return get_extended_menu(phone)
    
    elif command in ['odd', 'battle', 'fight', 'hunt']:
        return game_engine.start_battle(phone)
    
    elif command in ['stats', 'profile', 'me']:
        return game_engine.get_player_stats(phone)
    
    elif command in ['crates', 'crate', 'open']:
        crate_type = args[0] if args else 'basic'
        return game_engine.open_crate(phone, crate_type)
    
    elif command == 'shop':
        if len(args) >= 2 and args[0] == 'buy':
            return game_engine.buy_item(phone, args[1])
        return game_engine.get_shop_items()
    
    elif command == 'code':
        if args:
            return game_engine.redeem_code(phone, args[0])
        return get_code_help()
    
    elif command in ['bank', 'save']:
        if not args:
            return game_engine.bank_action(phone, 'info')
        action = args[0]
        amount = args[1] if len(args) > 1 else None
        return game_engine.bank_action(phone, action, amount)
    
    elif command in ['deposit']:
        amount = args[0] if args else None
        return game_engine.bank_action(phone, 'deposit', amount)
    
    elif command in ['withdraw']:
        amount = args[0] if args else None
        return game_engine.bank_action(phone, 'withdraw', amount)
    
    elif command in ['leaderboard', 'top', 'rank', 'ranks']:
        return get_leaderboard()
    
    elif command == 'steal':
        return process_steal(phone, args)
    
    elif command in ['pets', 'inventory', 'inv', 'pet']:
        player = db.get_player(phone)
        return messaging.format_pets_list(player['pets'])
    
    elif command in ['trade', 'trading']:
        if not args:
            return trading_system.list_trades(phone)
        if args[0] in ['accept', 'decline'] and len(args) > 1:
            return trading_system.respond_to_trade(phone, int(args[1]), args[0] == 'accept')
        if len(args) >= 2:
            target = args[0]
            offer = ' '.join(args[1:])
            return trading_system.send_trade_request(phone, target, offer)
        return trading_system.list_trades(phone)
    
    elif command in ['msg', 'message', 'pm', 'whisper']:
        if len(args) >= 2:
            target = args[0]
            msg_text = ' '.join(args[1:])
            return trading_system.send_message_to_player(phone, target, msg_text)
        return trading_system.get_inbox(phone)
    
    elif command in ['inbox', 'messages', 'mail']:
        return trading_system.get_inbox(phone)
    
    elif command == 'read':
        db.mark_messages_read(phone)
        return "✅ All messages marked as read!"
    
    elif command in ['boss', 'worldboss', 'raid']:
        if not args:
            return boss_system.get_active_bosses()
        action = args[0]
        if action == 'join' and len(args) > 1:
            return boss_system.join_boss_battle(phone, int(args[1]))
        if action in ['attack', 'defend'] and len(args) > 1:
            return boss_system.attack_boss(phone, int(args[1]), action)
        if action == 'status' and len(args) > 1:
            return boss_system.get_boss_status(int(args[1]))
        return boss_system.get_active_bosses()
    
    elif command in ['enchanter', 'merge', 'upgrade']:
        return process_enchanter(phone, args)
    
    elif command in ['daily', 'reward', 'login']:
        return process_daily(phone)
    
    elif command in ['tutorial', 'guide', 'howto']:
        return get_tutorial()
    
    elif command in ['heal', 'potion']:
        return process_heal(phone)
    
    elif command == 'admin':
        return admin_system.process_command(phone, ' '.join(args))
    
    elif command == 'update':
        return get_update_notes()
    
    else:
        return get_unknown_command()

def get_extended_menu(phone):
    """Extended menu with more options"""
    player = db.get_player(phone)
    
    # Check for unread messages
    unread = len(db.get_messages(phone, unread_only=True))
    msg_indicator = f" ({unread} unread)" if unread > 0 else ""
    
    return f"""
📱 *EXTENDED MENU* 📱

💰 Points: {format_number(player['points'])}
🏦 Bank: {format_number(player['bank'])} ({player.get('bank_tier', 'basic').title()})

*Inventory & Social:*
/pets - View your pets
/inv - Detailed inventory
/trade - Trading center
/msg - Messages{msg_indicator}
/inbox - Check mail

*Advanced:*
/boss - World bosses
/enchanter - Pet upgrades
/daily - Daily reward
/heal - Quick heal

*Info:*
/stats - Your statistics
/leaderboard - Top players
/tutorial - How to play
/update - Latest updates

Send /menu for main menu
    """.strip()

def get_leaderboard():
    """Get formatted leaderboard"""
    top = db.get_leaderboard(10)
    
    if not top:
        return "📋 No players yet! Be the first!"
    
    message = "📋 *GLOBAL LEADERBOARD* 📋\n\n"
    medals = ['🥇', '🥈', '🥉']
    
    for i, p in enumerate(top):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = p['username'] or p['phone'][:6] + "****"
        message += f"{medal} {name}\n"
        message += f"   💰 {format_number(p['total'])} | 🏆 {p['wins']} wins\n\n"
    
    return message

def process_steal(phone, args):
    """Process steal command"""
    player = db.get_player(phone)
    settings = game_config.get('game_settings', {})
    
    # Check cooldown
    if player.get('last_steal'):
        last = datetime.fromisoformat(player['last_steal'])
        cooldown = timedelta(hours=settings.get('steal_cooldown_hours', 2))
        if datetime.now() - last < cooldown:
            remaining = cooldown - (datetime.now() - last)
            return f"⏰ Steal cooldown! Wait {remaining.seconds//60} minutes."
    
    # Check protection
    effects = player.get('active_effects', {})
    if 'protection' in effects:
        if datetime.fromisoformat(effects['protection']['expires']) > datetime.now():
            return "🛡️ You have active protection! You can't steal while protected."
    
    # Get target
    if not args:
        # Random target from leaderboard (not self)
        all_players = db.get_all_players()
        valid_targets = [p for p in all_players if p['phone'] != phone and p['points'] > 100]
        if not valid_targets:
            return "❌ No valid targets to steal from!"
        target = random.choice(valid_targets)
    else:
        target = db.get_player(args[0])
        if target['phone'] == phone:
            return "❌ You can't steal from yourself!"
    
    # Check target protection
    target_effects = target.get('active_effects', {})
    if 'protection' in target_effects:
        if datetime.fromisoformat(target_effects['protection']['expires']) > datetime.now():
            return f"🛡️ {target['phone'][:6]}**** is protected! Try someone else."
    
    # Check target bank
    if target['points'] < settings.get('steal_min_amount', 100):
        return f"❌ Target has no points to steal! They're too poor."
    
    # Calculate success
    base_chance = settings.get('steal_success_rate', 0.35)
    
    # Bonus from pets
    for pet in player['pets']:
        if pet['name'] in ['Shadow Lord', 'Thief', 'Rogue', 'Assassin']:
            base_chance += 0.10
    
    # Penalty for high target power
    if target['power'] > player['power']:
        base_chance -= 0.10
    
    success = random.random() < base_chance
    
    if success:
        # Success!
        steal_amount = random.randint(
            settings.get('steal_min_amount', 100),
            min(settings.get('steal_max_amount', 1000), target['points'])
        )
        
        player['points'] += steal_amount
        target['points'] -= steal_amount
        player['steals_success'] += 1
        player['last_steal'] = datetime.now().isoformat()
        
        db.save_player(phone, player)
        db.save_player(target['phone'], target)
        
        # Notify target
        messaging.send_message(
            target['phone'],
            f"🥷 *THEFT ALERT!*\n\nSomeone stole {format_number(steal_amount)}💰 from you!\n💰 New balance: {format_number(target['points'])}💰\n\n🛡️ Buy protection in /shop to prevent this!"
        )
        
        return f"""
🥷 *THEFT SUCCESSFUL!* 🥷

You stole {format_number(steal_amount)}💰 from {target['phone'][:6]}****!
💰 New balance: {format_number(player['points'])}💰

⚠️ Watch out, they might steal back!
        """.strip()
    else:
        # Failed!
        fine = random.randint(50, 200)
        player['points'] = max(0, player['points'] - fine)
        player['steals_failed'] += 1
        player['last_steal'] = datetime.now().isoformat()
        
        db.save_player(phone, player)
        
        return f"""
🚔 *CAUGHT!* 🚔

The guards caught you!
Fine: {format_number(fine)}💰
💰 New balance: {format_number(player['points'])}💰

💡 Tip: Bank your points before stealing!
        """.strip()

def process_enchanter(phone, args):
    """Process enchanter/merge commands"""
    player = db.get_player(phone)
    
    if not args:
        return """
📚 *PET ENCHANTER* 📚

Options:
• merge [pet_name] - Merge 3 pets into 1 higher rarity
• upgrade [slot] - Enchant pet (+5 ATK) for 500💰
• list - Show mergeable pets

Examples:
enchanter merge Slime
enchanter upgrade 1
        """.strip()
    
    action = args[0]
    
    if action == 'list':
        # Show pets that can be merged
        pet_counts = {}
        for pet in player['pets']:
            name = pet['name']
            rarity = pet['rarity']
            key = f"{rarity} {name}"
            pet_counts[key] = pet_counts.get(key, 0) + 1
        
        message = "📊 *MERGEABLE PETS*\n\n"
        for pet_key, count in pet_counts.items():
            if count >= 3:
                message += f"✅ {pet_key}: {count} (can merge {count//3} times)\n"
            else:
                message += f"⬜ {pet_key}: {count} (need {3-count} more)\n"
        
        return message
    
    elif action == 'merge':
        if len(args) < 2:
            return "❌ Specify pet name! Example: enchanter merge Slime"
        
        pet_name = ' '.join(args[1:]).title()
        matching = [p for p in player['pets'] if p['name'] == pet_name]
        
        if len(matching) < 3:
            return f"❌ You need 3 {pet_name}s! You have {len(matching)}."
        
        # Remove 3 pets
        removed = 0
        new_pets = []
        for p in player['pets']:
            if p['name'] == pet_name and removed < 3:
                removed += 1
            else:
                new_pets.append(p)
        
        # Determine new rarity
        rarity_order = ['common', 'rare', 'epic', 'legendary', 'mythic']
        current_rarity = matching[0]['rarity'].lower()
        current_idx = rarity_order.index(current_rarity) if current_rarity in rarity_order else 0
        new_rarity = rarity_order[min(current_idx + 1, len(rarity_order)-1)]
        
        # Get new pet
        pets_config = game_config.get('pets', {})
        new_pets_list = pets_config.get(new_rarity, [])
        
        if new_pets_list:
            new_pet_template = random.choice(new_pets_list)
            new_pet = {
                'name': new_pet_template['name'],
                'emoji': new_pet_template['emoji'],
                'atk': int(new_pet_template['base_atk'] * 1.2),
                'rarity': new_rarity,
                'level': 1,
                'exp': 0,
                'enchanted': True,
                'growth': new_pet_template.get('growth', 2.0)
            }
        else:
            # Fallback
            new_pet = {
                'name': f"Enhanced {pet_name}",
                'emoji': '✨',
                'atk': matching[0]['atk'] + 20,
                'rarity': new_rarity,
                'level': 1,
                'exp': 0,
                'enchanted': True,
                'growth': 2.5
            }
        
        new_pets.append(new_pet)
        player['pets'] = new_pets
        player['enchantments'] += 1
        
        # Update power
        if new_pet['atk'] > player['power']:
            player['power'] = new_pet['atk']
        
        db.save_player(phone, player)
        
        rarity_emoji = {'common': '⬛', 'rare': '🟩', 'epic': '🟨', 'legendary': '🟪', 'mythic': '🟥'}.get(new_rarity, '⬜')
        
        return f"""
✨ *MERGE SUCCESSFUL!* ✨

3x {pet_name} →
{rarity_emoji} {new_rarity.upper()} {new_pet['name']}!
⚔️ ATK: {new_pet['atk']}

🎒 Pets: {len(player['pets'])}/{game_config.get('game_settings', {}).get('max_pets', 20)}
        """.strip()
    
    elif action == 'upgrade':
        if len(args) < 2:
            return "❌ Specify pet slot! Example: enchanter upgrade 1"
        
        try:
            slot = int(args[1]) - 1
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
        
        if pet['atk'] > player['power']:
            player['power'] = pet['atk']
        
        db.save_player(phone, player)
        
        return f"""
📚 *ENCHANTMENT COMPLETE!* 📚

✨ {pet['rarity']} {pet['name']}
⚔️ ATK: {pet['atk']-5} → {pet['atk']}

💰 Cost: {cost}
💰 Remaining: {format_number(player['points'])}
        """.strip()
    
    return "❌ Unknown enchanter command!"

def process_daily(phone):
    """Process daily reward"""
    player = db.get_player(phone)
    settings = game_config.get('game_settings', {})
    
    if player.get('last_daily'):
        last = datetime.fromisoformat(player['last_daily'])
        if datetime.now().date() == last.date():
            next_reset = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time())
            time_left = next_reset - datetime.now()
            return f"⏰ Daily reward already claimed!\nNext reset in: {time_left.seconds//3600}h {(time_left.seconds//60)%60}m"
    
    reward = settings.get('daily_reward', 500)
    player['points'] += reward
    player['last_daily'] = datetime.now().isoformat()
    
    # Bonus for consecutive days would go here
    
    db.save_player(phone, player)
    
    return f"""
🎁 *DAILY REWARD!* 🎁

You received: {format_number(reward)}💰
💰 New balance: {format_number(player['points'])}💰

Come back tomorrow for more!
    """.strip()

def process_heal(phone):
    """Quick heal command"""
    player = db.get_player(phone)
    
    if player['health'] >= player['max_health']:
        return "❤️ You're already at full health!"
    
    # Check for potions
    has_potion = False
    for i, item in enumerate(player['inventory']):
        if 'potion' in item.get('type', ''):
            has_potion = True
            player['inventory'].pop(i)
            heal_amount = 100
            break
    
    if has_potion:
        player['health'] = min(player['max_health'], player['health'] + heal_amount)
        db.save_player(phone, player)
        return f"❤️ Used potion! Healed {heal_amount} HP!\nHP: {player['health']}/{player['max_health']}"
    else:
        # Natural heal (costs points)
        missing_hp = player['max_health'] - player['health']
        cost = missing_hp * 2
        
        if player['points'] < cost:
            return f"❌ Need {cost}💰 to heal! You have {format_number(player['points'])}💰\n\nBuy potions in /shop"
        
        player['points'] -= cost
        player['health'] = player['max_health']
        db.save_player(phone, player)
        
        return f"❤️ *FULLY HEALED!* ❤️\n\nCost: {cost}💰\nHP: {player['health']}/{player['max_health']}\n💰 Remaining: {format_number(player['points'])}💰"

def get_code_help():
    """Get promo code help"""
    codes = game_config.get('promo_codes', {})
    
    message = "👨‍💻 *PROMO CODES* 👨‍💻\n\nRedeem codes for free rewards!\n\n*To use:*\ncode [CODE]\nExample: code STARTER\n\n*Available codes:*\n"
    
    for code, data in codes.items():
        if data.get('active', True):
            message += f"• {code} - {format_number(data.get('points', 0))}💰"
            if 'pet' in data:
                message += f" + {data['pet']['rarity']} pet"
            message += "\n"
    
    message += "\n*Note:* Each code can only be used once per player!"
    return message

def get_tutorial():
    """Get tutorial text"""
    return """
🤦‍♀️ *HOW TO PLAY ODD RPG* 🤦‍♀️

*🎯 Goal:* Become the richest and strongest player!

*📱 Getting Started:*
1. Send /menu to see your stats
2. Send /odd to start your first battle
3. Win battles to earn points and EXP
4. Use /crates to get pets (100💰 each)
5. Bank points with /bank to protect them

*⚔️ Battle System (Pokemon-style):*
When in battle, choose:
1️⃣ *Attack* - Deal damage
2️⃣ *Defend* - Reduce incoming damage
3️⃣ *Heal* - Use potion or rest
4️⃣ *Special* - Pet special attack
5️⃣ *Flee* - Try to escape (60% chance)

*💡 Pro Tips:*
• Pets increase your battle power
• Bank points before stealing
• Use /daily every day for free points
• Merge 3 pets of same type for rarity upgrade
• Check /boss for world boss events
• Trade with /trade command
• Send messages with /msg

*🎒 Pet Rarities:*
⬛ Common (50%) | 🟩 Rare (30%)
🟨 Epic (15%) | 🟪 Legendary (5%)
🟥 Mythic (1% - special crates only)

*🏦 Bank Tiers:*
Basic → Silver → Gold → Diamond
Higher tiers = better interest rates!

*🥷 Stealing:*
35% success rate. If caught, you pay a fine!
Buy Protection Shield in /shop to prevent theft.

Good luck! May the odds be ever in your favor! 🎮
    """.strip()

def get_update_notes():
    """Get latest update notes"""
    return """
🗒️ *LATEST UPDATES* 🗒️
*V. Re-Imagined Ultimate*

*🆕 New Features:*
• Pokemon-style battle system!
• World Boss battles with multiple players
• Trading system between players
• Private messaging (/msg, /inbox)
• Bank tiers with daily interest
• Self-updating messages (less spam)
• Enchantment and pet merging
• Daily login rewards
• Protection shields against stealing

*🔮 Coming Soon:*
• Guild system
• Pet breeding
• Auction house
• Seasonal events
• PvP arena

*📅 Last Updated:* 2024
*🎮 Total Features:* 50+

Send /menu to start playing!
    """.strip()

def get_unknown_command():
    """Unknown command response"""
    return """
❓ *UNKNOWN COMMAND* ❓

I didn't understand that!

*Quick commands:*
/menu - Main menu
/odd - Start battle
/crates - Get pets
/bank - Save money
/help - Full help

Send /tutorial to learn how to play!
    """.strip()

# Background tasks
def interest_task():
    """Daily interest calculation"""
    while True:
        now = datetime.now()
        # Calculate time until next midnight
        tomorrow = now + timedelta(days=1)
        midnight = datetime.combine(tomorrow.date(), datetime.min.time())
        sleep_seconds = (midnight - now).total_seconds()
        
        time.sleep(sleep_seconds)
        
        # Process interest
        try:
            game_engine.process_daily_interest()
        except Exception as e:
            print(f"Interest task error: {e}")

def boss_spawn_task():
    """Random boss spawning"""
    while True:
        # Sleep 2-6 hours randomly
        sleep_hours = random.uniform(2, 6)
        time.sleep(sleep_hours * 3600)
        
        try:
            # 30% chance to spawn
            if random.random() < 0.3:
                boss_system.spawn_boss()
        except Exception as e:
            print(f"Boss spawn error: {e}")

# Start background threads
interest_thread = threading.Thread(target=interest_task, daemon=True)
interest_thread.start()

boss_thread = threading.Thread(target=boss_spawn_task, daemon=True)
boss_thread.start()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🎮 ODD RPG Bot starting on port {port}...")
    print(f"📞 Admin phone: {admin_config.get('admin_phone', 'Not set')}")
    print(f"👥 Players in database: {len(db.get_all_players())}")
    app.run(host='0.0.0.0', port=port, debug=False)
'''

with open('main.py', 'w') as f:
    f.write(main_code)

print("✅ main.py created!")
print("\n" + "="*60)
print("🎮 ODD RPG BOT - SETUP COMPLETE!")
print("="*60)
print("\n📁 Files created:")
print("   ✓ config/game_config.json - Edit enemies/crates/codes")
print("   ✓ config/admin_config.json - Your admin settings")
print("   ✓ core/database.py - SQLite database")
print("   ✓ core/messaging.py - CallMeBot integration")
print("   ✓ core/game_engine.py - Battle system")
print("   ✓ core/trading_system.py - Player trading")
print("   ✓ core/boss_system.py - World bosses")
print("   ✓ core/admin_system.py - Admin commands")
print("   ✓ utils/helpers.py - Helper functions")
print("   ✓ main.py - Entry point")
print("\n🚀 To run locally:")
print("   python main.py")
print("\n🌐 To deploy on Railway:")
print("   1. Push all files to GitHub")
print("   2. Connect Railway to your repo")
print("   3. Set environment variables if needed")
print("   4. Deploy!")
print("\n⚙️  Configuration:")
print("   - Edit config/admin_config.json with your phone")
print("   - Edit config/game_config.json to add content")
print("   - No database setup needed (SQLite)")
print("="*60)