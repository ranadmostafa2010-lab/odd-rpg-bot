
# core/boss_system.py
boss_code = r'''import json
import random
from datetime import datetime, timedelta
from core.database import db
from utils.helpers import format_number, roll_chance

class BossSystem:
    def __init__(self, config):
        self.config = config
        self.bosses = config.get('bosses', {}).get('world_bosses', {})
    
    def spawn_boss(self, boss_name=None, force=False):
        """Spawn a world boss"""
        if boss_name and boss_name in self.bosses:
            boss_template = self.bosses[boss_name]
        else:
            boss_template = random.choice(list(self.bosses.values()))
        
        boss = {
            'name': boss_template['name'],
            'emoji': boss_template['emoji'],
            'hp': boss_template['hp'],
            'max_hp': boss_template['hp'],
            'damage': boss_template['damage'],
            'reward': boss_template['reward'],
            'participants': [],
            'damage_dealt': {},
            'status': 'active',
            'ends': (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        # Save to DB
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO boss_battles (boss_name, boss_emoji, boss_hp, boss_max_hp, participants, damage_dealt, status, ends)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            boss['name'], boss['emoji'], boss['hp'], boss['max_hp'],
            json.dumps(boss['participants']), json.dumps(boss['damage_dealt']),
            boss['status'], boss['ends']
        ))
        boss_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Broadcast to all players
        from core.messaging import messaging
        players = db.get_all_players()
        for player in players:
            messaging.send_message(
                player['phone'],
                f"""
🚨 *WORLD BOSS SPAWNED!* 🚨

{boss['emoji']} *{boss['name']}* has appeared!
HP: {format_number(boss['hp'])}
Reward: {format_number(boss['reward'])}💰

Join the fight!
Command: boss join {boss_id}
                """.strip()
            )
        
        return boss_id
    
    def join_boss_battle(self, phone, boss_id):
        """Player joins boss battle"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM boss_battles WHERE id = ? AND status = 'active'", (boss_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return "❌ Boss battle not found or already ended!"
        
        boss = {
            'id': row['id'],
            'name': row['boss_name'],
            'emoji': row['boss_emoji'],
            'hp': row['boss_hp'],
            'max_hp': row['boss_max_hp'],
            'participants': json.loads(row['participants']),
            'damage_dealt': json.loads(row['damage_dealt'])
        }
        
        # Check if already participating
        if phone in boss['participants']:
            return self._format_boss_status(boss, phone)
        
        # Add participant
        boss['participants'].append(phone)
        boss['damage_dealt'][phone] = 0
        
        # Update DB
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE boss_battles 
            SET participants = ?, damage_dealt = ?
            WHERE id = ?
        """, (json.dumps(boss['participants']), json.dumps(boss['damage_dealt']), boss_id))
        conn.commit()
        conn.close()
        
        return f"""
⚔️ *JOINED BOSS BATTLE* ⚔️

{boss['emoji']} {boss['name']}
HP: {format_number(boss['hp'])}/{format_number(boss['max_hp'])}

You joined the fight!
Attack with: boss attack {boss_id}
        """.strip()
    
    def attack_boss(self, phone, boss_id, action='attack'):
        """Attack the boss"""
        player = db.get_player(phone)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM boss_battles WHERE id = ? AND status = 'active'", (boss_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return "❌ Boss battle not active!"
        
        boss = {
            'id': row['id'],
            'name': row['boss_name'],
            'emoji': row['boss_emoji'],
            'hp': row['boss_hp'],
            'max_hp': row['boss_max_hp'],
            'participants': json.loads(row['participants']),
            'damage_dealt': json.loads(row['damage_dealt']),
            'damage': row['boss_damage']
        }
        
        # Check participation
        if phone not in boss['participants']:
            conn.close()
            return "❌ You haven't joined this battle! Use: boss join " + str(boss_id)
        
        # Calculate damage
        from utils.helpers import parse_damage_range
        player_dmg_min, player_dmg_max = parse_damage_range(boss['damage'])
        
        # Player attack
        pet_bonus = sum(p.get('atk', 0) for p in player['pets']) // 5
        base_dmg = random.randint(player['power'], player['power'] + 50)
        total_dmg = base_dmg + pet_bonus + random.randint(10, 30)
        
        # Apply damage
        boss['hp'] -= total_dmg
        boss['damage_dealt'][phone] += total_dmg
        
        # Boss counter-attack
        boss_min, boss_max = parse_damage_range(boss['damage'])
        boss_dmg = random.randint(boss_min, boss_max)
        
        # Defense option
        if action == 'defend':
            boss_dmg = int(boss_dmg * 0.3)
            defense_msg = " (Defended!)"
        else:
            defense_msg = ""
        
        player['health'] -= boss_dmg
        
        # Check player death
        if player['health'] <= 0:
            player['health'] = 50
            db.save_player(phone, player)
            conn.close()
            return f"""
💀 *KNOCKED OUT!* 💀

You took {boss_dmg} damage and were knocked out!
HP recovered to 50.

Damage dealt this battle: {format_number(boss['damage_dealt'][phone])}
            """.strip()
        
        # Check boss death
        if boss['hp'] <= 0:
            # Boss defeated!
            reward_pool = boss['max_hp'] // 10  # Total reward based on HP
            
            # Calculate individual rewards based on damage contribution
            total_damage = sum(boss['damage_dealt'].values())
            player_damage = boss['damage_dealt'][phone]
            contribution = player_damage / total_damage if total_damage > 0 else 0
            
            personal_reward = int(reward_pool * contribution)
            bonus = random.randint(1000, 5000)
            
            player['points'] += personal_reward + bonus
            player['wins'] += 1
            db.save_player(phone, player)
            
            # Mark boss as defeated
            cursor.execute("UPDATE boss_battles SET status = 'defeated' WHERE id = ?", (boss_id,))
            conn.commit()
            conn.close()
            
            # Notify all participants
            from core.messaging import messaging
            for participant in boss['participants']:
                if participant != phone:
                    their_damage = boss['damage_dealt'].get(participant, 0)
                    their_contribution = their_damage / total_damage if total_damage > 0 else 0
                    their_reward = int(reward_pool * their_contribution)
                    messaging.send_message(
                        participant,
                        f"🎉 *BOSS DEFEATED!*\n\n{boss['emoji']} {boss['name']} was defeated!\nYour damage: {format_number(their_damage)}\nReward: {format_number(their_reward)}💰"
                    )
            
            return f"""
🎉 *BOSS DEFEATED!* 🎉

{boss['emoji']} {boss['name']} has fallen!

Your contribution:
Damage: {format_number(player_damage)} ({contribution*100:.1f}%)
Reward: {format_number(personal_reward)}💰
Bonus: {format_number(bonus)}💰
Total: {format_number(personal_reward + bonus)}💰

New balance: {format_number(player['points'])}💰
            """.strip()
        
        # Update boss state
        cursor.execute("""
            UPDATE boss_battles 
            SET boss_hp = ?, damage_dealt = ?
            WHERE id = ?
        """, (boss['hp'], json.dumps(boss['damage_dealt']), boss_id))
        conn.commit()
        conn.close()
        
        # Save player
        db.save_player(phone, player)
        
        # Format response
        hp_bar = "█" * int((boss['hp']/boss['max_hp'])*10) + "░" * (10-int((boss['hp']/boss['max_hp'])*10))
        
        return f"""
⚔️ *BOSS BATTLE* ⚔️

{boss['emoji']} {boss['name']}
HP: [{hp_bar}] {format_number(boss['hp'])}/{format_number(boss['max_hp'])}

Your attack: {format_number(total_dmg)} damage!
Boss counter: {boss_dmg} damage{defense_msg}

Your HP: {player['health']}/{player['max_health']}
Your total damage: {format_number(boss['damage_dealt'][phone])}

Actions:
1. boss attack {boss_id}
2. boss defend {boss_id}
3. boss status {boss_id}
        """.strip()
    
    def get_active_bosses(self):
        """List active boss battles"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM boss_battles WHERE status = 'active'")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "📭 No active boss battles!\nWorld bosses spawn randomly every few hours."
        
        message = "👹 *ACTIVE BOSSES* 👹\n\n"
        
        for row in rows:
            hp_percent = (row['boss_hp'] / row['boss_max_hp']) * 100
            participants = len(json.loads(row['participants']))
            
            message += f"{row['boss_emoji']} *{row['boss_name']}* (#{row['id']})\n"
            message += f"   HP: {hp_percent:.1f}% | Fighters: {participants}\n"
            message += f"   Join: boss join {row['id']}\n\n"
        
        return message
    
    def _format_boss_status(self, boss, phone):
        """Format boss status for participant"""
        my_damage = boss['damage_dealt'].get(phone, 0)
        total_damage = sum(boss['damage_dealt'].values())
        rank = sorted(boss['damage_dealt'].items(), key=lambda x: x[1], reverse=True).index((phone, my_damage)) + 1 if my_damage > 0 else 0
        
        hp_bar = "█" * int((boss['hp']/boss['max_hp'])*10) + "░" * (10-int((boss['hp']/boss['max_hp'])*10))
        
        return f"""
👹 *BOSS STATUS* 👹

{boss['emoji']} {boss['name']}
HP: [{hp_bar}] {format_number(boss['hp'])}/{format_number(boss['max_hp'])}

Your stats:
Damage dealt: {format_number(my_damage)}
Rank: #{rank} of {len(boss['participants'])}
Contribution: {(my_damage/total_damage*100) if total_damage > 0 else 0:.1f}%

Attack: boss attack {boss['id']}
        """.strip()
'''

with open('core/boss_system.py', 'w') as f:
    f.write(boss_code)

print("✅ core/boss_system.py created!")