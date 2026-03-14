from flask import Flask, request
import random
import json
import os
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

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    user = data.get('from', 'unknown')
    msg = data.get('message', '').lower().strip()
    db = load_db()
    player = get_player(db, user)
    
    if msg in ['menu', 'start', 'help']:
        return {"reply": f"""🎮 *ODD RPG* 🪀

💰 Points: {player['points']}
🏦 Bank: {player['bank']}
⚔️ Power: {player['power']}
🎒 Pets: {len(player['pets'])}/10

☞ *odd* - Battle
☞ *crate* - Open crate
☞ *inv* - Inventory
☞ *shop* - Buy items
☞ *bank* - Save money
☞ *steal* - Steal points
☞ *lb* - Leaderboard
☞ *tutorial* - How to play"""}
    
    elif msg == 'odd':
        enemy_hp = random.randint(50, 150)
        player_dmg = random.randint(player['power'], player['power'] + 20)
        
        if player_dmg >= enemy_hp:
            reward = random.randint(100, 300)
            player['points'] += reward
            save_db(db)
            return {"reply": f"""⚔️ *VICTORY!*

💥 Damage: {player_dmg}
❤️ Enemy HP: {enemy_hp}

✅ You won! +{reward}💰
Total: {player['points']}💰"""}
        else:
            loss = random.randint(10, 50)
            player['points'] = max(0, player['points'] - loss)
            save_db(db)
            return {"reply": f"""⚔️ *DEFEAT!*

💥 Damage: {player_dmg}
❤️ Enemy HP: {enemy_hp}

❌ You lost! -{loss}💰
Total: {player['points']}💰"""}
    
    elif msg in ['crate', 'box']:
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
        
        return {"reply": f"""📦 *CRATE OPENED!*

🎲 Roll: {roll}
{pet['rarity']}
✨ {pet['name']}
⚔️ ATK: {pet['atk']}

💰 +{bonus} points!
Pets: {len(player['pets'])}/10"""}
    
    elif msg in ['inv', 'pets']:
        if not player['pets']:
            return {"reply": "🎒 Empty! Open *crate* to get pets."}
        
        pet_list = "\n".join([f"{i+1}. {p['rarity']} {p['name']}" 
                             for i, p in enumerate(player['pets'])])
        return {"reply": f"""🎒 *INVENTORY*

{pet_list}

💰 {player['points']} | 🏦 {player['bank']} | ⚔️ {player['power']}"""}
    
    elif msg == 'shop':
        return {"reply": """🏬 *SHOP*

*buy potion* - 100💰
*buy sword* - 500💰 (+5 Power)
*buy shield* - 300💰"""}
    
    elif msg.startswith('buy '):
        item = msg.replace('buy ', '')
        if item == 'potion' and player['points'] >= 100:
            player['points'] -= 100
            player['inventory'].append('potion')
            save_db(db)
            return {"reply": "✅ Bought Potion! -100💰"}
        elif item == 'sword' and player['points'] >= 500:
            player['points'] -= 500
            player['power'] += 5
            save_db(db)
            return {"reply": f"⚔️ Sword bought! Power: {player['power']}"}
        return {"reply": "❌ Need more points!"}
    
    elif msg == 'bank':
        return {"reply": f"""🏦 *BANK*

Wallet: {player['points']}💰
Savings: {player['bank']}💰 (Safe!)

*deposit [amount]*
*withdraw [amount]*"""}
    
    elif msg.startswith('deposit '):
        try:
            amt = int(msg.replace('deposit ', ''))
            if amt <= player['points']:
                player['points'] -= amt
                player['bank'] += amt
                save_db(db)
                return {"reply": f"✅ Deposited {amt}💰"}
        except:
            pass
        return {"reply": "❌ Invalid amount!"}
    
    elif msg.startswith('withdraw '):
        try:
            amt = int(msg.replace('withdraw ', ''))
            if amt <= player['bank']:
                player['bank'] -= amt
                player['points'] += amt
                save_db(db)
                return {"reply": f"✅ Withdrew {amt}💰"}
        except:
            pass
        return {"reply": "❌ Not enough in bank!"}
    
    elif msg == 'steal':
        return {"reply": "🥷 *STEAL*\n\nUse: *steal [number]*\n50% win chance!\nFail = -100💰"}
    
    elif msg.startswith('steal '):
        if random.randint(1, 100) > 50:
            stolen = random.randint(50, 200)
            player['points'] += stolen
            save_db(db)
            return {"reply": f"🥷 SUCCESS! +{stolen}💰"}
        else:
            player['points'] = max(0, player['points'] - 100)
            save_db(db)
            return {"reply": "🥷 CAUGHT! -100💰"}
    
    elif msg in ['lb', 'leaderboard']:
        top = sorted(load_db().items(), 
                    key=lambda x: x[1]['points']+x[1]['bank'], 
                    reverse=True)[:5]
        board = "\n".join([f"{i+1}. {n[:6]}... {d['points']+d['bank']}💰" 
                          for i,(n,d) in enumerate(top)])
        return {"reply": f"📋 *LEADERBOARD*\n\n{board}"}
    
    elif msg == 'tutorial':
        return {"reply": """📖 *TUTORIAL*

1. *menu* - Check status
2. *odd* - Battle enemies
3. *crate* - Get pets (gacha)
4. *bank* - Protect points
5. *steal* - Risk for reward

💡 Bank = Safe from steal!"""}
    
    else:
        return {"reply": "❓ Send *menu* for commands!"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
