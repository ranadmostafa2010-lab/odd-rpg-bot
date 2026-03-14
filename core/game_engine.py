
# core/game_engine.py
game_engine_code = r'''import random
import json
from datetime import datetime, timedelta
from core.database import db
from utils.helpers import (format_number, roll_chance, parse_damage_range, 
                           calculate_level_up_exp, get_rarity_color)

class GameEngine:
    def __init__(self, config):
        self.config = config
        self.settings = config.get('game_settings', {})
        self.enemies = config.get('enemies', {})
        self.pets_config = config.get('pets', {})
        self.bosses = config.get('bosses', {})
    
    def get_player_stats(self, phone):
        """Get formatted player stats"""
        player = db.get_player(phone)
        total_wealth = player['points'] + player['bank']
        win_rate = (player['wins'] / (player['wins'] + player['losses']) * 100) if (player['wins'] + player['losses']) > 0 else 0
        
        return f"""
📊 *YOUR STATS* 📊

💰 Points: {format_number(player['points'])}
🏦 Bank: {format_number(player['bank'])}
💎 Total Wealth: {format_number(total_wealth)}

⚔️ Power: {player['power']}
❤️ Health: {player['health']}/{player['max_health']}
📊 Level: {player.get('level', 1)} (EXP: {format_number(player.get('exp', 0))})
🎒 Pets: {len(player['pets'])}

🏆 Wins: {player['wins']}
💀 Losses: {player['losses']}
📈 Win Rate: {win_rate:.1f}%
🥷 Steals: {player['steals_success']}/{player['steals_success'] + player['steals_failed']}
📚 Enchantments: {player['enchantments']}
        """.strip()
    
    def spawn_enemy(self, player_level=1):
        """Spawn random enemy based on rarity tiers"""
        # Roll for rarity
        roll = random.randint(1, 100)
        
        if roll <= 40:
            rarity = 'common'
        elif roll <= 70:
            rarity = 'rare'
        elif roll <= 90:
            rarity = 'epic'
        else:
            rarity = 'legendary'
        
        # Select enemy from tier
        enemies = self.enemies.get(rarity, {})
        if not enemies:
            enemies = self.enemies.get('common', {})
        
        enemy_key = random.choice(list(enemies.keys()))
        enemy_template = enemies[enemy_key]
        
        # Scale with player level
        level_scale = 1 + (player_level - 1) * 0.1
        
        enemy = {
            'name': enemy_template['name'],
            'emoji': enemy_template['emoji'],
            'hp': int(random.randint(enemy_template['min_hp'], enemy_template['max_hp']) * level_scale),
            'damage': enemy_template['damage'],
            'reward': int(random.randint(enemy_template['min_reward'], enemy_template['max_reward']) * level_scale),
            'rarity': rarity,
            'exp': int((enemy_template['max_reward'] / 10) * level_scale)
        }
        
        return enemy
    
    def start_battle(self, phone):
        """Start Pokemon-style battle"""
        player = db.get_player(phone)
        
        if player['health'] < 20:
            return "❌ You're too weak to fight! Heal first with /shop or wait for regeneration."
        
        # Check if already in battle
        existing = db.get_active_battle(phone)
        if existing:
            return self.continue_battle(phone, None)
        
        # Spawn enemy
        enemy = self.spawn_enemy(player.get('level', 1))
        enemy['player_hp'] = player['health']
        enemy['player_max_hp'] = player['max_health']
        
        # Create battle in DB
        battle_id = db.create_battle(phone, enemy)
        
        return self.format_battle_screen(phone, battle_id)
    
    def format_battle_screen(self, phone, battle_id):
        """Format battle screen with choices"""
        battle = db.get_active_battle(phone)
        if not battle:
            return "❌ Battle not found!"
        
        # Calculate player power with pets
        player = db.get_player(phone)
        pet_bonus = sum(p.get('atk', 0) for p in player['pets']) // 10
        total_power = player['power'] + pet_bonus
        
        message = f"""
⚔️ *BATTLE* ⚔️
Turn {battle['turn']}

{battle['enemy_emoji']} *{battle['enemy_name']}* ({battle['rarity'].upper()})
HP: {battle['enemy_hp']}/{battle['enemy_max_hp']}

❤️ *YOU* (Level {player['level']})
HP: {battle['player_hp']}/{player['max_health']}
⚔️ Power: {total_power} (Base: {player['power']} + Pets: {pet_bonus})

*Choose action:*
1️⃣ *Attack* ⚔️ - Strike enemy
2️⃣ *Defend* 🛡️ - Reduce damage taken
3️⃣ *Heal* 🧪 - Restore HP (uses potion)
4️⃣ *Special* ✨ - Use pet ability
5️⃣ *Flee* 🏃 - Escape battle

Send the number (1-5) or word to act
        """.strip()
        
        return message
    
    def process_battle_action(self, phone, action):
        """Process player's battle action"""
        battle = db.get_active_battle(phone)
        if not battle:
            return "❌ No active battle! Start with /odd"
        
        player = db.get_player(phone)
        battle_log = json.loads(battle['battle_log']) if battle['battle_log'] else []
        
        # Parse action
        action = str(action).lower().strip()
        
        # Get damage ranges
        enemy_min_dmg, enemy_max_dmg = parse_damage_range(battle['enemy_damage'])
        pet_bonus = sum(p.get('atk', 0) for p in player['pets']) // 10
        
        player_hp = battle['player_hp']
        enemy_hp = battle['enemy_hp']
        turn = battle['turn']
        
        # Process player action
        if action in ['1', 'attack', '⚔️']:
            # Attack
            base_dmg = random.randint(player['power'], player['power'] + 25)
            total_dmg = base_dmg + pet_bonus + random.randint(-5, 10)
            total_dmg = max(5, total_dmg)  # Minimum damage
            
            enemy_hp -= total_dmg
            battle_log.append(f"Turn {turn}: You dealt {total_dmg} damage!")
            
        elif action in ['2', 'defend', '🛡️']:
            # Defend - reduce enemy damage this turn
            battle_log.append(f"Turn {turn}: You raised your guard!")
            enemy_min_dmg = int(enemy_min_dmg * 0.3)
            enemy_max_dmg = int(enemy_max_dmg * 0.3)
            
        elif action in ['3', 'heal', '🧪']:
            # Heal - check for potions
            heal_amount = 50
            has_potion = any('potion' in item.get('type', '') for item in player['inventory'])
            
            if has_potion:
                # Use potion
                player_hp = min(player['max_health'], player_hp + heal_amount)
                # Remove one potion
                for i, item in enumerate(player['inventory']):
                    if 'potion' in item.get('type', ''):
                        player['inventory'].pop(i)
                        break
                battle_log.append(f"Turn {turn}: Used potion! Healed {heal_amount} HP!")
            else:
                # Small natural heal
                heal_amount = 15
                player_hp = min(player['max_health'], player_hp + heal_amount)
                battle_log.append(f"Turn {turn}: No potions! Rested and healed {heal_amount} HP")
                
        elif action in ['4', 'special', '✨']:
            # Special - pet attack
            if player['pets']:
                pet = random.choice(player['pets'])
                special_dmg = pet['atk'] * 2
                enemy_hp -= special_dmg
                battle_log.append(f"Turn {turn}: {pet['name']} used special attack! Dealt {special_dmg} damage!")
            else:
                battle_log.append(f"Turn {turn}: No pets! Attack missed!")
                
        elif action in ['5', 'flee', '🏃']:
            # Flee - 60% chance
            if roll_chance(60):
                db.delete_battle(battle['id'])
                return "🏃 *ESCAPED!*\n\nYou ran away safely!"
            else:
                battle_log.append(f"Turn {turn}: Failed to escape!")
        else:
            return "❓ Invalid action! Send 1-5 or the action name."
        
        # Check if enemy defeated
        if enemy_hp <= 0:
            # Victory!
            reward = battle['reward']
            bonus = random.randint(0, int(reward * 0.2)) if roll_chance(20) else 0
            exp_gain = battle.get('exp', reward // 10)
            
            player['points'] += reward + bonus
            player['wins'] += 1
            player['health'] = max(10, player_hp)
            player['exp'] = player.get('exp', 0) + exp_gain
            
            # Level up check
            level_up_msg = ""
            exp_needed = calculate_level_up_exp(player['level'])
            if player['exp'] >= exp_needed:
                player['level'] += 1
                player['power'] += 5
                player['max_health'] += 20
                player['health'] = player['max_health']
                player['exp'] -= exp_needed
                level_up_msg = f"\n\n🎉 *LEVEL UP!* 🎉\nYou reached Level {player['level']}!\n⚔️ Power +5 | ❤️ Max HP +20"
            
            db.save_player(phone, player)
            db.delete_battle(battle['id'])
            
            bonus_text = f"\n🎁 BONUS: +{bonus}💰" if bonus > 0 else ""
            
            return f"""
🎉 *VICTORY!* 🎉

{battle['enemy_emoji']} {battle['enemy_name']} defeated!
💰 Reward: {format_number(reward)}💰{bonus_text}
📈 EXP: +{exp_gain}
💰 Total: {format_number(player['points'])}

Battle log:
{chr(10).join(battle_log[-3:])}{level_up_msg}
            """.strip()
        
        # Enemy attacks back (if not defeated)
        if enemy_hp > 0 and action not in ['5', 'flee']:
            enemy_dmg = random.randint(enemy_min_dmg, enemy_max_dmg)
            
            # Crit chance based on rarity
            crit_chance = {'common': 5, 'rare': 10, 'epic': 15, 'legendary': 25}
            if roll_chance(crit_chance.get(battle['rarity'], 5)):
                enemy_dmg = int(enemy_dmg * 1.5)
                battle_log.append(f"💥 CRITICAL! Enemy dealt {enemy_dmg} damage!")
            else:
                battle_log.append(f"Enemy dealt {enemy_dmg} damage!")
            
            player_hp -= enemy_dmg
        
        # Check if player defeated
        if player_hp <= 0:
            loss = random.randint(50, 150)
            player['points'] = max(0, player['points'] - loss)
            player['losses'] += 1
            player['health'] = 50  # Recovery health
            
            db.save_player(phone, player)
            db.delete_battle(battle['id'])
            
            return f"""
💀 *DEFEAT!* 💀

You were defeated by {battle['enemy_name']}!
💰 Lost: {loss}💰
💰 Total: {format_number(player['points'])}
❤️ Health recovered to 50

Battle log:
{chr(10).join(battle_log[-3:])}

💡 Tip: Get stronger pets or heal up!
            """.strip()
        
        # Update battle state
        db.update_battle(battle['id'], {
            'enemy_hp': enemy_hp,
            'player_hp': player_hp,
            'turn': turn + 1,
            'battle_log': json.dumps(battle_log)
        })
        
        # Continue battle
        return self.format_battle_screen(phone, battle['id'])
    
    def continue_battle(self, phone, action):
        """Continue existing battle"""
        if action:
            return self.process_battle_action(phone, action)
        else:
            return self.format_battle_screen(phone, None)
    
    def open_crate(self, phone, crate_type='basic'):
        """Open a crate and get pet"""
        player = db.get_player(phone)
        crates = self.config.get('crates', {})
        
        if crate_type not in crates:
            return f"❌ Invalid crate type! Available: {', '.join(crates.keys())}"
        
        crate = crates[crate_type]
        
        # Check cost
        if player['points'] < crate['cost']:
            return f"❌ Not enough points! Need {format_number(crate['cost'])}💰"
        
        # Check inventory space
        max_pets = self.settings.get('max_pets', 20)
        if len(player['pets']) >= max_pets:
            return f"❌ Inventory full! You have {len(player['pets'])}/{max_pets} pets.\nUse /enchanter to merge or upgrade storage."
        
        # Deduct points
        player['points'] -= crate['cost']
        
        # Roll for rarity
        drops = crate['drops']
        roll = random.randint(1, 100)
        cumulative = 0
        rarity = 'common'
        
        for r, chance in drops.items():
            cumulative += chance
            if roll <= cumulative:
                rarity = r
                break
        
        # Get random pet of that rarity
        pets_of_rarity = self.pets_config.get(rarity, [])
        if not pets_of_rarity:
            pets_of_rarity = self.pets_config.get('common', [])
        
        pet_template = random.choice(pets_of_rarity)
        
        # Create pet with level scaling
        pet = {
            'name': pet_template['name'],
            'emoji': pet_template['emoji'],
            'atk': pet_template['base_atk'],
            'rarity': rarity,
            'level': 1,
            'exp': 0,
            'enchanted': False,
            'growth': pet_template.get('growth', 1.5)
        }
        
        player['pets'].append(pet)
        
        # Update player power if pet is stronger
        if pet['atk'] > player['power']:
            player['power'] = pet['atk']
        
        db.save_player(phone, player)
        
        rarity_emoji = get_rarity_color(rarity)
        
        return f"""
📦 *{crate['name']} OPENED!* 📦

Cost: {format_number(crate['cost'])}💰
🎲 Roll: {roll}/100

{rarity_emoji} *{rarity.upper()}*
{pet['emoji']} *{pet['name']}*
⚔️ ATK: {pet['atk']}
📊 Level: {pet['level']}

🎒 Pets: {len(player['pets'])}/{max_pets}
💰 Remaining: {format_number(player['points'])}
        """.strip()
    
    def get_shop_items(self):
        """Get formatted shop"""
        shop = self.config.get('shop_items', {})
        message = "🏬 *ODD SHOP* 🏬\n\n"
        
        for item_id, item in shop.items():
            message += f"{item['emoji']} *{item['name']}*\n"
            message += f"   💰 {format_number(item['price'])} - {item['description']}\n"
            message += f"   Buy: shop buy {item_id}\n\n"
        
        return message
    
    def buy_item(self, phone, item_id):
        """Buy item from shop"""
        player = db.get_player(phone)
        shop = self.config.get('shop_items', {})
        
        if item_id not in shop:
            return "❌ Item not found! Use /shop to see items."
        
        item = shop[item_id]
        
        if player['points'] < item['price']:
            return f"❌ Not enough points! You need {format_number(item['price'])}💰"
        
        player['points'] -= item['price']
        
        # Apply item effect
        if 'heal' in item:
            player['health'] = min(player['max_health'], player['health'] + item['heal'])
            effect = f"❤️ Healed {item['heal']} HP!"
        elif 'boost' in item:
            if player['pets']:
                pet = random.choice(player['pets'])
                pet['atk'] += item['boost']
                effect = f"⚔️ {pet['name']} ATK +{item['boost']}!"
            else:
                effect = "No pets to boost! Points refunded."
                player['points'] += item['price']
        elif 'luck' in item:
            player['inventory'].append({'type': item_id, 'name': item['name'], 'luck': item['luck']})
            effect = "Added to inventory! Auto-used when opening crates."
        elif 'exp_multiplier' in item:
            expires = (datetime.now() + timedelta(seconds=item.get('duration', 3600))).isoformat()
            player['active_effects']['exp_boost'] = {'multiplier': item['exp_multiplier'], 'expires': expires}
            effect = f"📈 EXP {item['exp_multiplier']}x active for {item.get('duration', 3600)//3600}h!"
        elif 'protection' in item:
            expires = (datetime.now() + timedelta(seconds=item.get('duration', 86400))).isoformat()
            player['active_effects']['protection'] = {'expires': expires}
            effect = "🛡️ Protection active for 24h! Cannot be stolen from."
        else:
            player['inventory'].append({'type': item_id, 'name': item['name']})
            effect = "Added to inventory!"
        
        db.save_player(phone, player)
        
        return f"""
✅ *PURCHASE SUCCESSFUL!*

{item['emoji']} {item['name']}
💰 Cost: {format_number(item['price'])}
{effect}

💰 Remaining: {format_number(player['points'])}
        """.strip()
    
    def redeem_code(self, phone, code):
        """Redeem promo code"""
        player = db.get_player(phone)
        codes = self.config.get('promo_codes', {})
        
        code = code.upper()
        
        if code not in codes:
            return "❌ Invalid code!"
        
        promo = codes[code]
        
        if not promo.get('active', True):
            return "❌ This code has expired!"
        
        if code in player['used_codes']:
            return "❌ You already used this code!"
        
        # Apply rewards
        reward_text = f"💰 +{format_number(promo['points'])} points!"
        player['points'] += promo['points']
        player['used_codes'].append(code)
        
        if 'pet' in promo:
            max_pets = self.settings.get('max_pets', 20)
            if len(player['pets']) < max_pets:
                pet = promo['pet']
                pet['level'] = 1
                pet['exp'] = 0
                pet['enchanted'] = False
                player['pets'].append(pet)
                reward_text += f"\n🎁 {pet['rarity']} {pet['name']} added!"
            else:
                reward_text += "\n⚠️ Inventory full, pet not added!"
        
        db.save_player(phone, player)
        
        return f"""
🎉 *CODE REDEEMED!* 🎉

Code: {code}
{reward_text}

💰 Total: {format_number(player['points'])}
        """.strip()
    
    def bank_action(self, phone, action, amount=None):
        """Handle bank operations"""
        player = db.get_player(phone)
        tiers = self.config.get('bank_tiers', {})
        current_tier = tiers.get(player.get('bank_tier', 'basic'), tiers['basic'])
        
        if action == 'info':
            interest = current_tier['daily_interest'] * 100
            fee = current_tier['withdraw_fee'] * 100
            next_tier = None
            
            message = f"""
🏦 *BANK INFO* 🏦

Current Tier: *{current_tier['name']}*
📈 Daily Interest: {interest}%
💸 Withdraw Fee: {fee}%
💰 Max Balance: {format_number(current_tier['max_balance'])}

Your Balance:
💳 Wallet: {format_number(player['points'])}
🏦 Savings: {format_number(player['bank'])}
            """.strip()
            
            # Show next tier
            tier_order = ['basic', 'silver', 'gold', 'diamond']
            current_idx = tier_order.index(player.get('bank_tier', 'basic'))
            if current_idx < len(tier_order) - 1:
                next_tier_name = tier_order[current_idx + 1]
                next_tier = tiers[next_tier_name]
                message += f"\n\n⬆️ *Next Tier: {next_tier['name']}*\n"
                message += f"Required: {format_number(next_tier['min_balance'])} in bank\n"
                message += f"Benefits: {next_tier['daily_interest']*100}% interest, {next_tier['withdraw_fee']*100}% fee"
            
            return message
        
        elif action == 'deposit':
            if amount == 'all':
                amount = player['points']
            
            try:
                amount = int(amount)
            except:
                return "❌ Invalid amount!"
            
            if amount <= 0:
                return "❌ Amount must be positive!"
            
            if amount > player['points']:
                return f"❌ You only have {format_number(player['points'])}💰!"
            
            # Check max balance
            if player['bank'] + amount > current_tier['max_balance']:
                max_dep = current_tier['max_balance'] - player['bank']
                return f"❌ Max deposit: {format_number(max_dep)}💰 (tier limit)"
            
            player['points'] -= amount
            player['bank'] += amount
            
            # Check for tier upgrade
            for tier_name, tier_data in tiers.items():
                if player['bank'] >= tier_data['min_balance']:
                    if tier_data['min_balance'] > tiers[player.get('bank_tier', 'basic')]['min_balance']:
                        player['bank_tier'] = tier_name
            
            db.save_player(phone, player)
            
            return f"""
✅ *DEPOSITED* ✅

Amount: {format_number(amount)}💰
🏦 Bank: {format_number(player['bank'])}💰
💰 Wallet: {format_number(player['points'])}💰
            """.strip()
        
        elif action == 'withdraw':
            if amount == 'all':
                amount = player['bank']
            
            try:
                amount = int(amount)
            except:
                return "❌ Invalid amount!"
            
            if amount <= 0:
                return "❌ Amount must be positive!"
            
            if amount > player['bank']:
                return f"❌ Bank only has {format_number(player['bank'])}💰!"
            
            # Apply fee
            fee = int(amount * current_tier['withdraw_fee'])
            final_amount = amount - fee
            
            player['bank'] -= amount
            player['points'] += final_amount
            
            db.save_player(phone, player)
            
            fee_text = f"\n💸 Fee: {format_number(fee)}💰 ({current_tier['withdraw_fee']*100}%)" if fee > 0 else ""
            
            return f"""
✅ *WITHDRAWN* ✅

Amount: {format_number(amount)}💰{fee_text}
Received: {format_number(final_amount)}💰
🏦 Bank: {format_number(player['bank'])}💰
💰 Wallet: {format_number(player['points'])}💰
            """.strip()
        
        return "❌ Unknown bank action!"
    
    def process_daily_interest(self):
        """Process daily interest for all players (run by scheduler)"""
        players = db.get_all_players()
        tiers = self.config.get('bank_tiers', {})
        
        for player in players:
            if player['bank'] > 0:
                tier = tiers.get(player.get('bank_tier', 'basic'), tiers['basic'])
                interest = int(player['bank'] * tier['daily_interest'])
                
                if interest > 0:
                    player['bank'] += interest
                    db.save_player(player['phone'], player)
                    
                    # Notify player
                    from core.messaging import messaging
                    messaging.send_message(
                        player['phone'], 
                        f"🏦 *DAILY INTEREST*\n\nYou earned {format_number(interest)}💰 from your savings!\nNew balance: {format_number(player['bank'])}💰"
                    )
'''

with open('core/game_engine.py', 'w') as f:
    f.write(game_engine_code)

print("✅ core/game_engine.py created!")