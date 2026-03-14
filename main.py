from flask import Flask, request
import random
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)

DB_FILE = "players.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_player(db, user):
    if user not in db:
        db[user] = {
            "points": 1000,
            "bank": 0,
            "pets": [],
            "inventory": [],
            "power": 10,
            "last_steal": None,
            "joined": str(datetime.now())
        }
        save_db(db)
    return db[user]

@app.route('/')
def home():
    return "ODD RPG Bot Online! 🎮"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # Handle CallMeBot (GET request)
    if request.method == 'GET':
        phone = request.args.get('phone', '')
        message = request.args.get('text', '').lower().strip()
        apikey = request.args.get('apikey', '')
    else:
        data = request.json or {}
        phone = data.get('from', 'unknown')
        message = data.get('message', '').lower().strip()
        apikey = ''
    
    db = load_db()
    player = get_player(db, phone)
    
    # MENU COMMAND
    if message in ['menu', 'start', 'help']:
        reply = f"""🎮 *ODD RPG* 🪀

💰 Points: {player['points']}
🏦 Bank: {player['bank']}
⚔️ Power: {player['power']}
🎒 Pets: {len(player['pets'])}/10

☞ *odd* - Battle enemy
☞ *crate* - Open pet crate
☞ *inv* - View inventory
☞ *bank* - Save/withdraw
☞ *steal* - Steal points
☞ *tutorial* - How to play"""
    
    # BATTLE COMMAND
    elif message == 'odd':
        enemy_hp = random.randint(50, 150)
        enemy_name = random.choice(["Goblin", "Orc", "Skeleton", "Wolf", "Troll"])
        player_dmg = random.randint(player['power'], player['power'] + 20)
        
        if player_dmg >= enemy_hp:
            reward = random.randint(100, 300)
            player['points'] += reward
            save_db(db)
            reply = f"""⚔️ *VICTORY!*

Enemy: {enemy_name}
💥 Your damage: {player_dmg}
❤️ Enemy HP: {enemy_hp}

✅ You won! +{reward}💰
💰 Total: {player['points']}"""
        else:
            loss = random.randint(10, 50)
            player['points'] = max(0, player['points'] - loss)
            save_db(db)
            reply = f"""⚔️ *DEFEAT!*

Enemy: {enemy_name}
💥 Your damage: {player_dmg}
❤️ Enemy HP: {enemy_hp}

❌ You lost! -{loss}💰
💰 Total: {player['points']}"""
    
    # CRATE COMMAND
    elif message in ['crate', 'box']:
        roll = random.randint(1, 100)
        
        if roll >= 95:
            pet = {"name": "Dragon", "rarity": "🟪 LEGENDARY", "atk": 50}
            bonus = 500
        elif roll >= 80:
            pet = {"name": "Unicorn", "rarity": "🟨 EPIC", "atk": 35}
            bonus = 200
        elif roll >= 50:
            pet = {"name": "Wolf", "rarity": "🟩 RARE", "atk": 25}
            bonus = 100
        else:
            pet = {"name": "Slime", "rarity": "⬛ COMMON", "atk": 10}
            bonus = 50
        
        if len(player['pets']) < 10:
            player['pets'].append(pet)
        
        player['power'] = max([p['atk'] for p in player['pets']], default=10)
        player['points'] += bonus
        save_db(db)
        
        reply = f"""📦 *CRATE OPENED!*

🎲 Roll: {roll}
{pet['rarity']}
✨ {pet['name']}
⚔️ ATK: {pet['atk']}

💰 +{bonus} points!
🎒 Pets: {len(player['pets'])}/10
💰 Total: {player['points']}"""
    
    # INVENTORY COMMAND
    elif message in ['inv', 'inventory', 'pets']:
        if not player['pets']:
            reply = "🎒 *INVENTORY*\n\nNo pets yet!\nSend *crate* to get one."
        else:
            pet_list = "\n".join([f"{i+1}. {p['rarity']} {p['name']} (ATK:{p['atk']})" 
                                 for i, p in enumerate(player['pets'])])
            reply = f"""🎒 *YOUR PETS*

{pet_list}

💰 {player['points']} | 🏦 {player['bank']} | ⚔️ {player['power']}"""
    
    # BANK COMMAND
    elif message == 'bank':
        reply = f"""🏦 *BANK*

Wallet: {player['points']}💰
Savings: {player['bank']}💰 (Protected!)

Send:
*deposit [amount]*
*withdraw [amount]*"""
    
    # DEPOSIT
    elif message.startswith('deposit '):
        try:
            amt = int(message.replace('deposit ', ''))
            if amt <= player['points'] and amt > 0:
                player['points'] -= amt
                player['bank'] += amt
                save_db(db)
                reply = f"✅ Deposited {amt}💰 to bank!"
            else:
                reply = "❌ Not enough points!"
        except:
            reply = "❌ Use: deposit [number]"
    
    # WITHDRAW
    elif message.startswith('withdraw '):
        try:
            amt = int(message.replace('withdraw ', ''))
            if amt <= player['bank'] and amt > 0:
                player['bank'] -= amt
                player['points'] += amt
                save_db(db)
                reply = f"✅ Withdrew {amt}💰!"
            else:
                reply = "❌ Not enough in bank!"
        except:
            reply = "❌ Use: withdraw [number]"
    
    # STEAL COMMAND
    elif message == 'steal':
        if random.randint(1, 100) > 50:
            stolen = random.randint(50, 200)
            player['points'] += stolen
            save_db(db)
            reply = f"🥷 *SUCCESS!* You stole {stolen}💰!"
        else:
            player['points'] = max(0, player['points'] - 100)
            save_db(db)
            reply = "🥷 *CAUGHT!* -100💰 fine!"
    
    # TUTORIAL
    elif message == 'tutorial':
        reply = """📖 *TUTORIAL*

1️⃣ Send *menu* - Check your stats
2️⃣ Send *odd* - Battle enemies for points
3️⃣ Send *crate* - Open crates to get pets
4️⃣ Send *bank* - Deposit points (safe from steal!)
5️⃣ Send *steal* - 50% chance to steal points

💡 *Tip:* Bank your points so thieves can't get them!

Good luck! 🎮"""
    
    # DEFAULT
    else:
        reply = "❓ Unknown command. Send *menu* for options!"
    
    # Send reply back to WhatsApp (for GET requests from CallMeBot)
    if request.method == 'GET' and apikey:
        phone_clean = phone.replace('+', '')
        send_url = f"https://api.callmebot.com/whatsapp.php?phone={phone_clean}&text={requests.utils.quote(reply)}&apikey={apikey}"
        try:
            requests.get(send_url, timeout=10)
        except:
            pass
        return "OK"
    
    # Return JSON for POST requests
    return {"reply": reply}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
